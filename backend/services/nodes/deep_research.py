"""
Deep Research Node - Phase 2 of the Fit Check Pipeline.

This module implements the intelligence gathering node that:
1. Executes web searches based on Phase 1 classification
2. Synthesizes findings into structured employer intelligence
3. Identifies tech stack, requirements, and culture signals

Gemini Optimization Applied:
- Uses XML-structured prompt for synthesis
- Tool calls emit explicit thought events
- Post-hoc reasoning trace, not inline CoT
- Criteria-based prompting (no "think step-by-step" anti-pattern)
- Low temperature (0.3) for synthesis accuracy

Desire: Totality of Evidence (Digital Truth)
The Deep Research agent is the investigator - gathering comprehensive,
verified intelligence about the employer from external data sources.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from langchain_core.messages import HumanMessage

from config.llm import get_llm, with_llm_throttle
from services.pipeline_state import FitCheckPipelineState, Phase2Output
from services.callbacks import ThoughtCallback
from services.tools.web_search import web_search, web_search_structured
from services.utils import get_response_text
from services.utils.query_expander import expand_queries, QueryExpansionResult
from services.prompt_loader import load_prompt, PHASE_DEEP_RESEARCH
from services.utils.circuit_breaker import llm_breaker, CircuitOpenError

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "deep_research"
PHASE_DISPLAY = "Deep Research"

# Synthesis temperature - balanced for accuracy with some creativity
SYNTHESIS_TEMPERATURE = 0.3

# Maximum characters per search result to avoid context overflow
MAX_RESULT_LENGTH = 1500

# Maximum number of search queries to execute
MAX_SEARCH_QUERIES = 5


# =============================================================================
# Search Result Formatting
# =============================================================================


def format_search_results(results: List[Dict[str, str]]) -> str:
    """
    Format multiple search results for prompt injection.
    
    Each result is wrapped in a numbered section with the query used,
    making it easier for the LLM to attribute findings to sources.
    
    Args:
        results: List of dicts with 'query' and 'result' keys.
    
    Returns:
        Formatted string for XML prompt injection.
    """
    if not results:
        return "No search results available. Limited data for synthesis."
    
    formatted_sections = []
    for i, item in enumerate(results, 1):
        query = item.get("query", "Unknown query")
        result = item.get("result", "No results")
        
        # Truncate long results to prevent context overflow
        if len(result) > MAX_RESULT_LENGTH:
            result = result[:MAX_RESULT_LENGTH] + "... [truncated]"
        
        section = f"""--- Search Result {i} ---
Query: "{query}"
Findings:
{result}"""
        formatted_sections.append(section)
    
    return "\n\n".join(formatted_sections)


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt(config_type: str = None) -> str:
    """
    Load the Phase 2 XML prompt template based on model configuration.
    
    Args:
        config_type: Model config type ("reasoning" or "standard").
                     Reasoning models get concise prompts to prevent timeouts.
    
    Returns:
        str: XML-structured prompt template.
    """
    try:
        return load_prompt(PHASE_DEEP_RESEARCH, config_type=config_type, prefer_concise=True)
    except FileNotFoundError:
        logger.warning(f"Phase 2 prompt not found, using embedded fallback")
        return _get_fallback_prompt()


def _get_fallback_prompt() -> str:
    """
    Embedded fallback prompt if file not found.
    
    Returns:
        str: Minimal XML prompt template for research synthesis.
    """
    return """<system_instruction>
  <agent_persona>Intelligence Gathering Agent for employer research.</agent_persona>
  <primary_objective>
    Synthesize web search results into structured employer intelligence.
  </primary_objective>
  <behavioral_constraints>
    <constraint>DO NOT fabricate information not present in search results</constraint>
    <constraint>DO NOT output markdown - output only valid JSON</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <prior_phase_output>
    Query Type: {query_type}, Company: {company_name}, Title: {job_title}
  </prior_phase_output>
  <search_results>
{search_results}
  </search_results>
</context_data>

<output_contract>
{{"employer_summary": "string", "identified_requirements": [], "tech_stack": [],
  "culture_signals": [], "data_quality": "medium", "reasoning_trace": "string"}}
</output_contract>"""


# =============================================================================
# JSON Parsing Utilities
# =============================================================================

def extract_json_from_response(response: str) -> Dict[str, Any]:
    """
    Extract JSON from LLM response, handling various formats.
    
    The LLM may return JSON in several formats:
    - Clean JSON
    - JSON wrapped in markdown code blocks
    - JSON with surrounding prose
    
    Args:
        response: Raw LLM response text.
    
    Returns:
        Parsed JSON dictionary.
    
    Raises:
        ValueError: If JSON cannot be extracted or parsed.
    """
    text = response.strip()
    
    # Try direct JSON parse first (cleanest case)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from markdown code blocks
    json_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    matches = re.findall(json_block_pattern, text)
    if matches:
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
    
    # Try to find JSON object in text (for prose wrapping)
    brace_pattern = r'\{[\s\S]*\}'
    matches = re.findall(brace_pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")


def validate_phase2_output(data: Dict[str, Any], queries_used: List[str]) -> Phase2Output:
    """
    Validate and normalize Phase 2 output.
    
    Applies recovery logic for edge cases where the LLM
    returns slightly malformed data.
    
    Args:
        data: Raw parsed JSON from LLM.
        queries_used: List of search queries that were executed.
    
    Returns:
        Validated Phase2Output TypedDict.
    """
    # Normalize employer_summary
    employer_summary = data.get("employer_summary")
    if not employer_summary or not isinstance(employer_summary, str):
        employer_summary = "Limited employer information available from search results."
    
    # Normalize identified_requirements
    identified_requirements = data.get("identified_requirements")
    if not isinstance(identified_requirements, list):
        identified_requirements = []
    else:
        identified_requirements = [
            str(r).strip() for r in identified_requirements
            if r and str(r).strip()
        ]
    
    # Normalize tech_stack
    tech_stack = data.get("tech_stack")
    if not isinstance(tech_stack, list):
        tech_stack = []
    else:
        tech_stack = [
            str(t).strip() for t in tech_stack
            if t and str(t).strip()
        ]
    
    # Normalize culture_signals
    culture_signals = data.get("culture_signals")
    if not isinstance(culture_signals, list):
        culture_signals = []
    else:
        culture_signals = [
            str(c).strip() for c in culture_signals
            if c and str(c).strip()
        ]
    
    # Normalize reasoning_trace
    reasoning_trace = data.get("reasoning_trace")
    if not reasoning_trace or not isinstance(reasoning_trace, str):
        reasoning_trace = "Research synthesis completed based on available search data."
    
    return Phase2Output(
        employer_summary=employer_summary,
        identified_requirements=identified_requirements,
        tech_stack=tech_stack,
        culture_signals=culture_signals,
        search_queries_used=queries_used,
        reasoning_trace=reasoning_trace,
    )


# =============================================================================
# Main Node Function
# =============================================================================

async def deep_research_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 2: DEEP_RESEARCH - Intelligence Gathering Node.
    
    Executes web searches based on Phase 1 classification and synthesizes
    the results into structured employer intelligence. This phase gathers
    external data to inform the downstream comparison and matching phases.
    
    Args:
        state: Current pipeline state with Phase 1 output.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update dict with:
            - phase_2_output: Validated research synthesis
            - current_phase: Next phase ("skeptical_comparison")
            - step_count: Incremented step counter
            - processing_errors: Any non-fatal errors (optional)
    
    SSE Events Emitted:
        - phase: "deep_research" at start
        - thought (tool_call): For each web search
        - thought (observation): For each search result
        - thought (reasoning): For synthesis step
        - phase_complete: With research summary
    
    Graceful Degradation:
        On search or LLM failure, returns minimal research output
        to allow downstream phases to proceed with limited data.
    """
    logger.info("[DEEP_RESEARCH] Starting phase 2")
    step = state.get("step_count", 0)
    phase_1 = state.get("phase_1_output") or {}
    queries_executed = []
    expansion_result = None
    
    # Emit phase start event
    if callback and hasattr(callback, 'on_phase'):
        await callback.on_phase(
            PHASE_NAME,
            "Researching for info..."
        )
    elif callback:
        await callback.on_status(
            "researching",
            "Researching for info..."
        )
    
    try:
        # Construct search queries based on Phase 1 classification
        expansion_result = expand_queries(
            phase_1_output=phase_1,
            original_query=state.get("query", ""),
            iteration=state.get("search_attempt", 1),
        )
        search_results = []
        
        # Execute web searches
        all_raw_results = []
        for expanded_query in expansion_result.queries:
            query = expanded_query.query
            step += 1
            
            # Emit tool call thought
            if callback:
                await callback.on_thought(
                    step=step,
                    thought_type="tool_call",
                    content=f"Searching: {expanded_query.purpose}",
                    tool="web_search",
                    tool_input=query,
                    phase=PHASE_NAME,
                )
            
            # Execute search
            try:
                # Get structured results for scoring (async function)
                raw_results = await web_search_structured(query)
                all_raw_results.extend(raw_results)
                
                # Get formatted string for synthesis (async tool call)
                result = await web_search.ainvoke(query)
                queries_executed.append(query)
                search_results.append({
                    "query": query,
                    "purpose": expanded_query.purpose,
                    "result": result,
                })
                
                step += 1
                # Emit observation thought
                if callback:
                    await callback.on_thought(
                        step=step,
                        thought_type="observation",
                        content=f"Found info for: {expanded_query.purpose}",
                        tool=None,
                        tool_input=None,
                        phase=PHASE_NAME,
                    )
                    
            except Exception as e:
                logger.warning(f"[DEEP_RESEARCH] Search failed for query '{query}': {e}")
                queries_executed.append(query)
                search_results.append({
                    "query": query,
                    "purpose": expanded_query.purpose,
                    "result": f"Search unavailable: {str(e)[:100]}",
                })
        
        # Format results for synthesis prompt
        formatted_results = format_search_results(search_results)
        
        # Load prompt based on model config type (concise for reasoning models)
        config_type = state.get("config_type")
        prompt_template = load_phase_prompt(config_type=config_type)
        
        # Build format kwargs - include all possible placeholders for compatibility
        format_kwargs = {
            "query_type": phase_1.get("query_type", "unknown"),
            "company_name": phase_1.get("company_name") or "Not specified",
            "job_title": phase_1.get("job_title") or "Software Engineer",
            "extracted_skills": ", ".join(phase_1.get("extracted_skills", [])) or "None",
            "search_results": formatted_results,
        }
        prompt = prompt_template.format(**format_kwargs)
        
        step += 1
        # Emit reasoning thought for synthesis
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content="Synthesizing search results into structured employer profile...",
                tool=None,
                tool_input=None,
                phase=PHASE_NAME,
            )
        
        # Get LLM for synthesis (lower temperature for accuracy)
        # Uses model config from state if provided
        llm = get_llm(
            streaming=False,
            temperature=SYNTHESIS_TEMPERATURE,
            model_id=state.get("model_id"),
            config_type=state.get("config_type"),
        )
        
        # Invoke LLM with XML-structured prompt
        messages = [HumanMessage(content=prompt)]
        
        async with llm_breaker.call():
            response = await with_llm_throttle(llm.ainvoke(messages))
        
        # Extract response text (handles Gemini's structured format)
        response_text = get_response_text(response)
        logger.debug(f"[DEEP_RESEARCH] Raw LLM response: {response_text[:300]}...")
        
        # Parse and validate response
        parsed_data = extract_json_from_response(response_text)
        validated_output = validate_phase2_output(parsed_data, queries_executed)
        
        # Build completion summary
        tech_count = len(validated_output["tech_stack"])
        req_count = len(validated_output["identified_requirements"])
        culture_count = len(validated_output["culture_signals"])
        summary = f"Identified {tech_count} technologies, {req_count} requirements, {culture_count} culture signals"
        
        # Emit phase complete event with enriched metadata
        if callback and hasattr(callback, 'on_phase_complete'):
            # Build rich metadata for frontend transparency
            enriched_data = {
                # Counts for quick display
                "tech_count": tech_count,
                "requirements_count": req_count,
                "culture_count": culture_count,
                "search_count": len(search_results),
                # Actual items for insight (limit to prevent bloat)
                "tech_stack": validated_output["tech_stack"][:5],
                "top_requirements": validated_output["identified_requirements"][:3],
                "culture_signals": validated_output["culture_signals"][:3],
                # Search transparency
                "search_queries": [
                    {"query": sr["query"], "purpose": sr.get("purpose", "general")}
                    for sr in search_results[:3]
                ],
                "expansion_strategy": expansion_result.expansion_strategy if expansion_result else "default",
                # Reasoning excerpt for understanding
                "synthesis_reasoning": validated_output["reasoning_trace"][:200] if validated_output["reasoning_trace"] else None,
            }
            await callback.on_phase_complete(
                PHASE_NAME, 
                summary,
                data=enriched_data
            )
        
        logger.info(f"[DEEP_RESEARCH] Phase 2 complete: {len(search_results)} searches, {summary}")
        
        return {
            "phase_2_output": validated_output,
            "current_phase": "skeptical_comparison",
            "step_count": step,
            "raw_search_results": all_raw_results,
            "expanded_queries": [
                {"query": q.query, "purpose": q.purpose} 
                for q in expansion_result.queries
            ],
            "query_expansion_strategy": expansion_result.expansion_strategy,
        }
        
    except Exception as e:
        logger.error(f"[DEEP_RESEARCH] Phase 2 failed: {e}", exc_info=True)
        
        # Graceful degradation - return minimal research output
        fallback_output = Phase2Output(
            employer_summary="Unable to gather complete employer information due to research limitations.",
            identified_requirements=[],
            tech_stack=[],
            culture_signals=[],
            search_queries_used=queries_executed,
            reasoning_trace=f"Research phase encountered an error: {str(e)[:100]}",
        )
        
        # Emit phase complete with degradation notice
        if callback and hasattr(callback, 'on_phase_complete'):
            await callback.on_phase_complete(
                PHASE_NAME,
                "Research completed with limited data"
            )
        
        return {
            "phase_2_output": fallback_output,
            "current_phase": "skeptical_comparison",
            "step_count": step,
            "raw_search_results": [],
            "processing_errors": state.get("processing_errors", []) + [f"Phase 2 error: {str(e)}"],
            "expanded_queries": [
                {"query": q.query, "purpose": q.purpose} 
                for q in expansion_result.queries
            ] if expansion_result else None,
            "query_expansion_strategy": expansion_result.expansion_strategy if expansion_result else None,
        }
