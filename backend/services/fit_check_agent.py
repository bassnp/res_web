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

def create_node_wrapper(node_func, callback_holder):
    """
    Create a LangGraph-compatible node wrapper.
    
    LangGraph nodes are sync functions by default. This wrapper
    enables async node functions with callbacks.
    
    Args:
        node_func: Async node function.
        callback_holder: Dict holding the callback reference.
    
    Returns:
        Sync wrapper function for LangGraph.
    """
    async def async_wrapper(state: FitCheckPipelineState) -> Dict[str, Any]:
        callback = callback_holder.get("callback")
        return await node_func(state, callback)
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
    workflow.add_node("connecting", create_node_wrapper(connecting_node, callback_holder))
    workflow.add_node("deep_research", create_node_wrapper(deep_research_node, callback_holder))
    workflow.add_node("research_reranker", create_node_wrapper(research_reranker_node, callback_holder))
    workflow.add_node("skeptical_comparison", create_node_wrapper(skeptical_comparison_node, callback_holder))
    workflow.add_node("skills_matching", create_node_wrapper(skills_matching_node, callback_holder))
    workflow.add_node("confidence_reranker", create_node_wrapper(confidence_reranker_node, callback_holder))
    workflow.add_node("generate_results", create_node_wrapper(generate_results_node, callback_holder))
    
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
        
        Returns:
            Next node name based on data quality.
        """
        reranker_output = state.get("research_reranker_output") or {}
        search_attempt = state.get("search_attempt", 1)
        early_exit = state.get("early_exit", False)
        
        # Get quality assessment
        data_tier = reranker_output.get("data_quality_tier", "PARTIAL")
        action = reranker_output.get("recommended_action", "CONTINUE")
        
        # CRITICAL: Early exit for garbage/suspicious data
        if early_exit or action == "EARLY_EXIT" or data_tier == "GARBAGE":
            logger.info(f"[ROUTER] Early exit triggered: data_tier={data_tier}, action={action}")
            return "generate_results"
        
        # ENHANCE: Retry search for sparse data (first attempt only)
        if action == "ENHANCE_SEARCH" and search_attempt < 2:
            logger.info(f"[ROUTER] Enhanced search triggered: attempt={search_attempt}")
            return "deep_research"
        
        # CONTINUE: Good or acceptable data proceeds to skeptical analysis
        if action in ["CONTINUE", "CONTINUE_WITH_FLAGS"]:
            return "skeptical_comparison"
        
        # Default: proceed with caution
        return "skeptical_comparison"
    
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
    
    # After research_reranker: conditional routing based on data quality
    workflow.add_conditional_edges(
        "research_reranker",
        route_after_research_reranker,
        {
            "skeptical_comparison": "skeptical_comparison",
            "deep_research": "deep_research",  # Enhanced search retry
            "generate_results": "generate_results",  # Early exit
        }
    )
    
    # Remaining sequential edges (normal flow)
    workflow.add_edge("skeptical_comparison", "skills_matching")
    workflow.add_edge("skills_matching", "confidence_reranker")
    workflow.add_edge("confidence_reranker", "generate_results")
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
        """Initialize the agent."""
        self._callback_holder = {}
    
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
        
        # Build pipeline without callback
        pipeline = build_fit_check_pipeline(self._callback_holder)
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
        
        # Set callback for pipeline nodes
        self._callback_holder["callback"] = callback
        
        try:
            # Build pipeline with callback
            pipeline = build_fit_check_pipeline(self._callback_holder)
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
            # Clear callback reference
            self._callback_holder.pop("callback", None)


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
