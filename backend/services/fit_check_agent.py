"""
Fit Check Agent - LangGraph-based AI Agent for Employer Fit Analysis.

This module implements a multi-phase pipeline agent that:
1.  CONNECTING: Classifies employer queries (company name vs. job description)
2.  DEEP_RESEARCH: Researches using web search and analysis tools
2B. RESEARCH_RERANKER: Validates research quality, prunes bad data, routes pipeline
3.  SKEPTICAL_COMPARISON: Critical gap analysis (anti-sycophancy)
4.  SKILLS_MATCHING: Maps skills to requirements with confidence scores
5B. CONFIDENCE_RERANKER: LLM-as-a-Judge confidence calibration
5.  GENERATE_RESULTS: Synthesizes personalized fit analysis response

Key Features:
- Conditional routing based on data quality (early exit for garbage data)
- Data pruning to prevent bad data from polluting downstream analysis
- Enhanced search retry for obscure companies
- Quality flags for transparency in final output

Events are streamed via callbacks for real-time frontend updates.
"""

import logging
import time
from typing import TypedDict, Optional, List, Dict, Any, AsyncGenerator

from langgraph.graph import StateGraph, END

from services.pipeline_state import (
    FitCheckPipelineState,
    create_initial_state,
    PHASE_ORDER,
    get_next_phase,
    is_terminal_phase,
)
from services.nodes import (
    connecting_node,
    deep_research_node,
    research_reranker_node,
    content_enrich_node,
    skeptical_comparison_node,
    skills_matching_node,
    confidence_reranker_node,
    generate_results_node,
)
from services.callbacks import ThoughtCallback

logger = logging.getLogger(__name__)


# =============================================================================
# Pipeline Node Wrappers (for LangGraph compatibility)
# =============================================================================

def create_node_wrapper(node_func, callback_holder, phase_name: str):
    """
    Create a LangGraph-compatible node wrapper with error handling.
    
    LangGraph nodes are sync functions by default. This wrapper
    enables async node functions with callbacks and centralized error handling.
    
    Args:
        node_func: Async node function.
        callback_holder: Dict holding the callback reference.
        phase_name: Name of the phase for error reporting.
    
    Returns:
        Sync wrapper function for LangGraph.
    """
    async def async_wrapper(state: FitCheckPipelineState) -> Dict[str, Any]:
        callback = callback_holder.get("callback")
        try:
            return await node_func(state, callback)
        except Exception as e:
            from services.utils.error_handling import handle_node_error
            return handle_node_error(e, phase_name, state)
    return async_wrapper


# =============================================================================
# Pipeline Builder
# =============================================================================

def build_fit_check_pipeline(callback_holder: Dict = None):
    """
    Build the multi-phase LangGraph pipeline for the Fit Check Agent.
    
    The pipeline follows this sequence with conditional routing:
        START → connecting → (route) → deep_research → research_reranker → (route)
              → skeptical_comparison → skills_matching → confidence_reranker 
              → generate_results → END
    
    Conditional routing points:
        1. After connecting:
           - Valid query → deep_research
           - Irrelevant/malicious → END
        
        2. After research_reranker:
           - CLEAN/PARTIAL data → skeptical_comparison (continue)
           - SPARSE data (attempt 1) → deep_research (enhanced retry)
           - GARBAGE/UNRELIABLE data → generate_results (early exit)
           - SPARSE data (attempt 2) → skeptical_comparison (proceed with flags)
    
    Args:
        callback_holder: Dict containing 'callback' key for async callback reference.
    
    Returns:
        Compiled LangGraph ready for execution.
    """
    if callback_holder is None:
        callback_holder = {}
    
    # Create the graph
    workflow = StateGraph(FitCheckPipelineState)
    
    # Add phase nodes
    workflow.add_node("connecting", create_node_wrapper(connecting_node, callback_holder, "connecting"))
    workflow.add_node("deep_research", create_node_wrapper(deep_research_node, callback_holder, "deep_research"))
    workflow.add_node("research_reranker", create_node_wrapper(research_reranker_node, callback_holder, "research_reranker"))
    workflow.add_node("content_enrich", create_node_wrapper(content_enrich_node, callback_holder, "content_enrich"))
    workflow.add_node("skeptical_comparison", create_node_wrapper(skeptical_comparison_node, callback_holder, "skeptical_comparison"))
    workflow.add_node("skills_matching", create_node_wrapper(skills_matching_node, callback_holder, "skills_matching"))
    workflow.add_node("confidence_reranker", create_node_wrapper(confidence_reranker_node, callback_holder, "confidence_reranker"))
    workflow.add_node("generate_results", create_node_wrapper(generate_results_node, callback_holder, "generate_results"))
    
    # Set entry point
    workflow.set_entry_point("connecting")
    
    # -------------------------------------------------------------------------
    # Routing Function: After Connecting
    # -------------------------------------------------------------------------
    def route_after_connecting(state: FitCheckPipelineState) -> str:
        """
        Route based on query classification result.
        
        Returns:
            Next node name or END.
        """
        # Check for fatal errors
        if state.get("should_abort"):
            return "generate_results"
            
        current_phase = state.get("current_phase", "deep_research")
        
        # Check if query was rejected (irrelevant or malicious)
        if current_phase == "__end__":
            return END
        
        # Check phase 1 output for irrelevant classification
        phase1_output = state.get("phase_1_output")
        if phase1_output and phase1_output.get("query_type") == "irrelevant":
            return END
        
        # Continue to deep research
        return "deep_research"
    
    # -------------------------------------------------------------------------
    # Routing Function: After Research Reranker (CRITICAL QUALITY GATE)
    # -------------------------------------------------------------------------
    def route_after_research_reranker(state: FitCheckPipelineState) -> str:
        """
        Route based on research quality assessment.
        
        This is the critical quality gate that:
        - Allows good data to continue
        - Triggers enhanced search for sparse data
        - Forces early exit for garbage/unreliable data
        
        IMPORTANT: For job_description queries, we ALWAYS proceed to skills_matching
        because the requirements come FROM THE QUERY ITSELF, not from web research.
        Early exit only makes sense for company queries where we need external data.
        
        Returns:
            Next node name based on data quality.
        """
        # Check for fatal errors
        if state.get("should_abort"):
            return "generate_results"
        
        # Check if this is a job_description query - these should ALWAYS proceed
        # to skills matching because the requirements are in the query itself.
        phase_1_output = state.get("phase_1_output") or {}
        query_type = phase_1_output.get("query_type", "company")
        extracted_skills = phase_1_output.get("extracted_skills") or []
        
        # Job descriptions with extracted skills should NEVER early exit
        # because we can match candidate skills against query requirements
        if query_type == "job_description" and len(extracted_skills) > 0:
            logger.info(
                f"[ROUTING] Job description with {len(extracted_skills)} extracted skills - "
                "proceeding to skills matching regardless of web research quality"
            )
            return "content_enrich"
            
        # Use the next phase determined by the node itself
        next_phase = state.get("current_phase")
        
        # Fallback logic if current_phase is not set correctly
        if not next_phase or next_phase == "research_reranker":
            reranker_output = state.get("research_reranker_output") or {}
            search_attempt = state.get("search_attempt", 1)
            early_exit = state.get("early_exit", False)
            
            # Get quality assessment
            data_tier = reranker_output.get("data_quality_tier", "PARTIAL")
            action = reranker_output.get("recommended_action", "CONTINUE")
            
            # CRITICAL: Early exit for garbage/suspicious data (company queries only)
            if early_exit or action == "EARLY_EXIT" or data_tier == "GARBAGE":
                return "generate_results"
            
            # ENHANCE: Retry search for sparse data (up to 3 attempts)
            if action == "ENHANCE_SEARCH" and search_attempt < 3:
                return "deep_research"
            
            # CONTINUE: Good or acceptable data proceeds to enrichment
            return "content_enrich"
        
        return next_phase
    
    # -------------------------------------------------------------------------
    # Routing Function: Generic (for sequential nodes)
    # -------------------------------------------------------------------------
    def route_generic(state: FitCheckPipelineState) -> str:
        """
        Generic routing that checks for abort flags.
        """
        if state.get("should_abort"):
            return "generate_results"
        return "CONTINUE"

    # -------------------------------------------------------------------------
    # Add Conditional Edges
    # -------------------------------------------------------------------------
    
    # After connecting: route to deep_research or END
    workflow.add_conditional_edges(
        "connecting",
        route_after_connecting,
        {
            "deep_research": "deep_research",
            END: END,
        }
    )
    
    # After deep_research: always go to research_reranker for quality check
    workflow.add_edge("deep_research", "research_reranker")
    
    # After research_reranker: route to deep_research (retry), content_enrich, or generate_results
    workflow.add_conditional_edges(
        "research_reranker",
        route_after_research_reranker,
        {
            "deep_research": "deep_research",
            "content_enrich": "content_enrich",
            "skeptical_comparison": "skeptical_comparison",
            "generate_results": "generate_results",
        }
    )
    
    # After content_enrich: route to skeptical_comparison or generate_results (if error)
    workflow.add_conditional_edges(
        "content_enrich",
        route_generic,
        {
            "CONTINUE": "skeptical_comparison",
            "generate_results": "generate_results",
        }
    )
    
    # Remaining sequential edges (normal flow)
    workflow.add_conditional_edges(
        "skeptical_comparison",
        route_generic,
        {
            "CONTINUE": "skills_matching",
            "generate_results": "generate_results",
        }
    )
    
    workflow.add_conditional_edges(
        "skills_matching",
        route_generic,
        {
            "CONTINUE": "confidence_reranker",
            "generate_results": "generate_results",
        }
    )
    
    workflow.add_conditional_edges(
        "confidence_reranker",
        route_generic,
        {
            "CONTINUE": "generate_results",
            "generate_results": "generate_results",
        }
    )
    
    workflow.add_edge("generate_results", END)
    
    # Compile the graph
    return workflow.compile()


# =============================================================================
# FitCheckAgent Class
# =============================================================================

class FitCheckAgent:
    """
    High-level interface for the Fit Check Agent.
    
    Provides methods to run the 5-phase pipeline with or without streaming.
    """
    
    def __init__(self):
        """Initialize the agent (stateless - no shared mutable state)."""
        pass
    
    async def analyze(
        self,
        query: str,
        model_id: str = None,
        config_type: str = None,
    ) -> str:
        """
        Run fit analysis without streaming.
        
        Args:
            query: Company name or job description.
            model_id: AI model ID to use (e.g., 'gemini-3-pro-preview').
            config_type: Configuration type ('reasoning' or 'standard').
        
        Returns:
            str: Final analysis response.
        
        Raises:
            Exception: If analysis fails.
        """
        logger.info(f"Starting analysis for query: {query[:50]}... model={model_id}")
        
        # Build pipeline without callback (empty holder for non-streaming)
        callback_holder = {}
        pipeline = build_fit_check_pipeline(callback_holder)
        initial_state = create_initial_state(query, model_id, config_type)
        
        # Run the pipeline
        final_state = await pipeline.ainvoke(initial_state)
        
        # Check for errors
        if final_state.get("error"):
            raise Exception(final_state["error"])
        
        # Return final response
        return final_state.get("final_response", "Unable to generate analysis. Please try again.")
    
    async def stream_analysis(
        self,
        query: str,
        callback: ThoughtCallback,
        model_id: str = None,
        config_type: str = None,
    ) -> AsyncGenerator[str, None]:
        """
        Run fit analysis with streaming thoughts and response.
        
        This method streams the agent's thinking process in real-time
        via the callback, while yielding response chunks.
        
        Args:
            query: Company name or job description.
            callback: Callback for receiving thoughts and status updates.
            model_id: AI model ID to use (e.g., 'gemini-3-pro-preview').
            config_type: Configuration type ('reasoning' or 'standard').
        
        Yields:
            str: Response text chunks.
        
        Raises:
            Exception: If analysis fails.
        """
        start_time = time.time()
        
        logger.info(f"Starting streaming analysis for query: {query[:50]}... model={model_id}")
        
        # Emit initial status
        await callback.on_status("connecting", "Initializing AI agent...")
        
        # Create ISOLATED callback holder for this request (prevents cross-session contamination)
        callback_holder = {"callback": callback}
        
        try:
            # Build pipeline with request-local callback holder
            pipeline = build_fit_check_pipeline(callback_holder)
            initial_state = create_initial_state(query, model_id, config_type)
            
            # Stream through the pipeline
            final_response = ""
            rejection_reason = None
            
            async for event in pipeline.astream(initial_state):
                # Process events from each node
                for node_name, node_output in event.items():
                    logger.debug(f"Pipeline event from {node_name}: {list(node_output.keys())}")
                    
                    # Check for errors
                    if node_output.get("error"):
                        await callback.on_error("PIPELINE_ERROR", node_output["error"])
                        return
                    
                    # Check for query rejection (from connecting node)
                    if node_output.get("rejection_reason"):
                        rejection_reason = node_output["rejection_reason"]
                        logger.info(f"Query rejected: {rejection_reason}")
                    
                    # Check for final response (from generate_results node)
                    # Note: Response streaming is handled by the node itself via callback.
                    # We only capture the final response here for the yield/return.
                    if node_name == "generate_results":
                        response = node_output.get("final_response")
                        if response:
                            final_response = response
                            # Yield the complete response for the generator interface
                            yield response
            
            # Handle rejection case - emit rejection response
            if rejection_reason and not final_response:
                rejection_response = f"I cannot process this request.\n\n{rejection_reason}\n\nPlease provide a valid company name or job description for career fit analysis."
                
                # Emit the rejection as a response
                await callback.on_response_chunk(rejection_response)
                yield rejection_response
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            await callback.on_complete(duration_ms)
            
        except Exception as e:
            logger.error(f"Streaming analysis error: {e}")
            await callback.on_error("AGENT_ERROR", str(e))
            raise
        finally:
            # Callback holder is request-local, cleaned up automatically
            pass


# =============================================================================
# Singleton Instance
# =============================================================================

_agent_instance: Optional[FitCheckAgent] = None


def get_agent() -> FitCheckAgent:
    """
    Get or create the singleton FitCheckAgent instance.
    
    Returns:
        FitCheckAgent: The agent instance.
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = FitCheckAgent()
    return _agent_instance
