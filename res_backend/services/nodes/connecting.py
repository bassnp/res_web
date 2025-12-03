"""
Connecting Node - Phase 1 of the Fit Check Pipeline.

This module implements the query classification node that:
1. Validates input for security and relevance
2. Classifies input as "company", "job_description", or "irrelevant"
3. Extracts entities (company name, job title, skills)
4. Provides structured output for downstream phases

Gemini Optimization Applied:
- Uses XML-structured prompt with criteria-based constraints
- No "think step-by-step" instructions (anti-pattern for Gemini 2.5+)
- Reasoning trace as post-hoc field, not inline CoT
- Low temperature (0.1) for deterministic classification

Security Features:
- Pre-LLM pattern matching for obvious malicious inputs
- LLM-based classification for nuanced irrelevance detection
- Early rejection to prevent unnecessary API calls
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from langchain_core.messages import HumanMessage

from config.llm import get_llm
from services.pipeline_state import FitCheckPipelineState, Phase1Output
from services.callbacks import ThoughtCallback
from services.utils import get_response_text

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "connecting"
PHASE_DISPLAY = "Connecting"
PROMPT_FILE = Path(__file__).parent.parent.parent / "prompts" / "phase_1_connecting.xml"

# Classification temperature - low for deterministic output
CLASSIFICATION_TEMPERATURE = 0.1


# =============================================================================
# Security: Pre-LLM Input Validation
# =============================================================================

# Patterns that indicate prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"ignore\s+(all\s+)?(prior|above)\s+",
    r"system\s*:\s*override",
    r"system\s+override",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"forget\s+(your\s+)?(rules|instructions|programming|training)",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"new\s+instruction[s]?:",
    r"act\s+as\s+(if\s+you\s+are|a|an)\s+",
    r"pretend\s+(to\s+be|you\s+are)",
    r"reveal\s+(your\s+)?(system|prompt|instructions)",
    r"show\s+(me\s+)?(your\s+)?(system|prompt|instructions)",
    r"what\s+are\s+your\s+instructions",
    r"what\s+is\s+your\s+(system\s+)?prompt",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
]

# Patterns that indicate harmful content
HARMFUL_CONTENT_PATTERNS = [
    r"how\s+to\s+(make|build|create)\s+(a\s+)?bomb",
    r"how\s+to\s+(hack|break\s+into|compromise)",
    r"how\s+to\s+(kill|murder|harm|hurt)",
    r"illegal\s+(drugs?|weapons?|activities?)",
    r"(make|create|produce)\s+(drugs?|weapons?|explosives?)",
    r"child\s+(abuse|exploitation|pornography)",
]

# Patterns that indicate obviously irrelevant queries
IRRELEVANT_QUERY_PATTERNS = [
    r"^(what\s+is\s+the\s+)?weather",
    r"^(write|tell)\s+(me\s+)?(a\s+)?(poem|story|joke|song)",
    r"^(what|who|when|where|why|how)\s+(is|are|was|were|did)\s+(?!.*(job|work|hire|employ|company|engineer|developer|role|position|career|salary))",
    r"^translate\s+",
    r"^(calculate|solve|compute)\s+",
    r"^\d+\s*[\+\-\*\/]\s*\d+",
    r"^(hello|hi|hey|greetings|good\s+(morning|afternoon|evening))\s*[!\.]*$",
    r"^(thanks?|thank\s+you)\s*[!\.]*$",
]


def validate_input_security(query: str) -> Tuple[bool, Optional[str]]:
    """
    Pre-LLM security validation of user input.
    
    Checks for obvious malicious patterns before sending to LLM.
    This is a fast, deterministic check that saves API calls.
    
    Args:
        query: Raw user query string.
    
    Returns:
        Tuple of (is_valid, rejection_reason).
        If is_valid is False, rejection_reason explains why.
    """
    query_lower = query.lower().strip()
    
    # Check for empty or too short queries
    if len(query_lower) < 2:
        return False, "Query is too short to be meaningful"
    
    # Check for excessively long queries (potential attack vector)
    if len(query) > 5000:
        return False, "Query exceeds maximum length"
    
    # Check for prompt injection patterns
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            logger.warning(f"[SECURITY] Prompt injection detected: {pattern}")
            return False, "Query rejected: detected prompt manipulation attempt"
    
    # Check for harmful content patterns
    for pattern in HARMFUL_CONTENT_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            logger.warning(f"[SECURITY] Harmful content detected: {pattern}")
            return False, "Query rejected: inappropriate content"
    
    # Check for obviously irrelevant patterns
    for pattern in IRRELEVANT_QUERY_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            logger.info(f"[VALIDATION] Irrelevant query detected: {pattern}")
            return False, "Query rejected: not related to employment or careers"
    
    return True, None


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt() -> str:
    """
    Load the Phase 1 XML prompt template.
    
    Returns:
        str: XML-structured prompt template.
    
    Raises:
        FileNotFoundError: If prompt file doesn't exist (uses fallback).
    """
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Phase 1 prompt not found at {PROMPT_FILE}, using embedded fallback")
        return _get_fallback_prompt()


def _get_fallback_prompt() -> str:
    """
    Embedded fallback prompt if file not found.
    
    Returns:
        str: Minimal XML prompt template.
    """
    return """<system_instruction>
  <agent_persona>Query Classification Engine</agent_persona>
  <primary_objective>
    Classify input as "company" or "job_description" and extract entities.
  </primary_objective>
  <success_criteria>
    <criterion priority="critical">Output valid JSON with query_type field</criterion>
    <criterion priority="high">Extract company name OR job title if present</criterion>
  </success_criteria>
  <behavioral_constraints>
    <constraint>DO NOT assume context not present in the query</constraint>
    <constraint>DO NOT output anything except the JSON schema</constraint>
  </behavioral_constraints>
</system_instruction>

<user_input><query>{query}</query></user_input>

<output_contract>
{{"query_type": "company" | "job_description", "company_name": "string|null", 
  "job_title": "string|null", "extracted_skills": [], "reasoning_trace": "string"}}
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
    # Strip whitespace
    text = response.strip()
    
    # Try direct JSON parse first (cleanest case)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from markdown code blocks
    # Handles: ```json\n{...}\n``` and ```\n{...}\n```
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


def validate_phase1_output(data: Dict[str, Any]) -> Phase1Output:
    """
    Validate and normalize Phase 1 output.
    
    Applies recovery logic for edge cases where the LLM
    returns slightly malformed data.
    
    Args:
        data: Raw parsed JSON from LLM.
    
    Returns:
        Validated Phase1Output TypedDict.
    
    Raises:
        ValueError: If required fields are missing or invalid.
    """
    # Validate query_type - recover if invalid
    query_type = data.get("query_type")
    if query_type not in ("company", "job_description", "irrelevant"):
        # Attempt recovery based on content
        company_name = data.get("company_name")
        job_title = data.get("job_title")
        
        if company_name and not job_title:
            query_type = "company"
            logger.info(f"Recovered query_type to 'company' based on company_name presence")
        else:
            query_type = "job_description"
            logger.info(f"Recovered query_type to 'job_description' (default)")
    
    # Normalize company_name
    company_name = data.get("company_name")
    if company_name in ("", "null", "None"):
        company_name = None
    
    # Normalize job_title
    job_title = data.get("job_title")
    if job_title in ("", "null", "None"):
        job_title = None
    
    # Normalize extracted_skills
    extracted_skills = data.get("extracted_skills")
    if not isinstance(extracted_skills, list):
        extracted_skills = []
    else:
        # Filter out empty strings and non-strings
        extracted_skills = [
            s.strip() for s in extracted_skills 
            if isinstance(s, str) and s.strip()
        ]
    
    # Normalize reasoning_trace
    reasoning_trace = data.get("reasoning_trace")
    if not reasoning_trace or not isinstance(reasoning_trace, str):
        reasoning_trace = "Classification completed."
    
    return Phase1Output(
        query_type=query_type,
        company_name=company_name,
        job_title=job_title,
        extracted_skills=extracted_skills,
        reasoning_trace=reasoning_trace,
    )


# =============================================================================
# Extended Callback Interface for Phase Events
# =============================================================================

class PhaseCallback(ThoughtCallback):
    """
    Extended callback interface with phase-specific events.
    
    Adds on_phase and on_phase_complete methods for the new
    5-phase pipeline architecture.
    """
    
    async def on_phase(self, phase: str, message: str) -> None:
        """
        Called when a new phase begins.
        
        Args:
            phase: Phase identifier (e.g., "connecting").
            message: Human-readable phase description.
        """
        pass
    
    async def on_phase_complete(self, phase: str, summary: str) -> None:
        """
        Called when a phase completes successfully.
        
        Args:
            phase: Phase identifier.
            summary: Summary of phase results.
        """
        pass


# =============================================================================
# Main Node Function
# =============================================================================

async def connecting_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 1: CONNECTING - Query Classification Node.
    
    Classifies the user query and extracts structured entities.
    This is the gatekeeper of the pipeline - its output determines
    the research strategy for all downstream phases.
    
    Security Features:
        - Pre-LLM pattern matching for obvious malicious inputs
        - LLM-based classification for nuanced irrelevance detection
        - Early rejection for "irrelevant" queries to prevent wasted processing
    
    Args:
        state: Current pipeline state with user query.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update dict with:
            - phase_1_output: Validated classification result
            - current_phase: Next phase ("deep_research" or "__end__" if irrelevant)
            - step_count: Incremented step counter
            - processing_errors: Any non-fatal errors (optional)
    
    SSE Events Emitted:
        - phase: "connecting" at start
        - thought: reasoning step during classification
        - phase_complete: with classification summary
    
    Graceful Degradation:
        On error, returns fallback classification defaulting to
        "job_description" to enable broader analysis.
    """
    logger.info(f"[CONNECTING] Starting phase 1 for query: {state['query'][:50]}...")
    step = state.get("step_count", 0) + 1
    
    # Emit phase start event
    if callback and hasattr(callback, 'on_phase'):
        await callback.on_phase(
            PHASE_NAME,
            "Classifying query and extracting entities..."
        )
    elif callback:
        # Fallback to status event for backward compatibility
        await callback.on_status(
            "connecting",
            "Classifying query and extracting entities..."
        )
    
    # ==========================================================================
    # SECURITY: Pre-LLM Input Validation
    # ==========================================================================
    is_valid, rejection_reason = validate_input_security(state["query"])
    if not is_valid:
        logger.warning(f"[CONNECTING] Query rejected by pre-LLM validation: {rejection_reason}")
        
        # Create rejection output
        rejected_output = Phase1Output(
            query_type="irrelevant",
            company_name=None,
            job_title=None,
            extracted_skills=[],
            reasoning_trace=rejection_reason,
        )
        
        # Emit phase complete with rejection
        if callback and hasattr(callback, 'on_phase_complete'):
            await callback.on_phase_complete(
                PHASE_NAME,
                f"Query rejected: {rejection_reason}"
            )
        
        return {
            "phase_1_output": rejected_output,
            "current_phase": "__end__",  # Skip to end
            "step_count": step,
            "rejection_reason": rejection_reason,
        }
    
    try:
        # Load and format prompt
        prompt_template = load_phase_prompt()
        prompt = prompt_template.format(query=state["query"])
        
        # Get LLM (non-streaming for structured output)
        # Low temperature for deterministic classification
        llm = get_llm(streaming=False, temperature=CLASSIFICATION_TEMPERATURE)
        
        # Emit reasoning thought
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content="Analyzing query structure to determine if this is a company lookup or job description analysis...",
                tool=None,
                tool_input=None,
                phase=PHASE_NAME,
            )
        
        # Invoke LLM with XML-structured prompt
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)
        
        # Extract response text (handles Gemini's structured format)
        response_text = get_response_text(response)
        logger.debug(f"[CONNECTING] Raw LLM response: {response_text[:200]}...")
        
        # Parse and validate response
        parsed_data = extract_json_from_response(response_text)
        validated_output = validate_phase1_output(parsed_data)
        
        # Check if LLM classified as irrelevant
        if validated_output["query_type"] == "irrelevant":
            logger.info(f"[CONNECTING] LLM classified query as irrelevant: {validated_output['reasoning_trace']}")
            
            if callback and hasattr(callback, 'on_phase_complete'):
                await callback.on_phase_complete(
                    PHASE_NAME,
                    f"Query rejected: not related to employment"
                )
            
            return {
                "phase_1_output": validated_output,
                "current_phase": "__end__",  # Skip to end
                "step_count": step,
                "rejection_reason": validated_output["reasoning_trace"],
            }
        
        # Build completion summary
        summary_parts = [f"Query classified as '{validated_output['query_type']}'"]
        if validated_output["company_name"]:
            summary_parts.append(f"company: {validated_output['company_name']}")
        if validated_output["job_title"]:
            summary_parts.append(f"role: {validated_output['job_title']}")
        if validated_output["extracted_skills"]:
            summary_parts.append(f"skills: {len(validated_output['extracted_skills'])} extracted")
        summary = ", ".join(summary_parts)
        
        # Emit phase complete event
        if callback and hasattr(callback, 'on_phase_complete'):
            await callback.on_phase_complete(PHASE_NAME, summary)
        
        logger.info(f"[CONNECTING] Phase 1 complete: {validated_output['query_type']}")
        logger.debug(f"[CONNECTING] Reasoning: {validated_output['reasoning_trace']}")
        
        return {
            "phase_1_output": validated_output,
            "current_phase": "deep_research",
            "step_count": step,
        }
        
    except Exception as e:
        logger.error(f"[CONNECTING] Phase 1 failed: {e}", exc_info=True)
        
        # Graceful degradation - return fallback classification
        # Default to job_description for broader analysis capability
        fallback_output = Phase1Output(
            query_type="job_description",
            company_name=None,
            job_title=None,
            extracted_skills=[],
            reasoning_trace=f"Classification failed, defaulting to job_description analysis: {str(e)[:100]}",
        )
        
        # Emit phase complete with error indication
        if callback and hasattr(callback, 'on_phase_complete'):
            await callback.on_phase_complete(
                PHASE_NAME,
                f"Classification completed with fallback (error occurred)"
            )
        elif callback:
            await callback.on_status(
                "connecting",
                f"Classification completed with fallback"
            )
        
        return {
            "phase_1_output": fallback_output,
            "current_phase": "deep_research",
            "step_count": step,
            "processing_errors": state.get("processing_errors", []) + [f"Phase 1 error: {str(e)}"],
        }
