"""
Skeptical Comparison Node - Phase 3 of the Fit Check Pipeline.

This module implements the CRITICAL devil's advocate node that:
1. Analyzes fit with intentional skepticism
2. Identifies genuine gaps (minimum 2 required)
3. Prevents sycophantic "perfect fit" outputs
4. Provides honest risk assessment

Gemini Optimization Applied:
- Uses Step-Back prompting ("What would a critical evaluator notice?")
- Negative constraints to prevent agreeable patterns
- Mandatory gap requirements in output schema
- Post-hoc reasoning trace, not inline CoT
- Criteria-based prompting (no "think step-by-step" anti-pattern)
- Slightly higher temperature (0.4) for creative critical thinking

Desire: Veracity & Risk Assessment (Adversarial Defense)
The Skeptical Comparison agent is the devil's advocate. It operates under the
assumption that previous phases may have overstated alignment. Its purpose is to
identify genuine gaps and provide honest risk assessment.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from langchain_core.messages import HumanMessage

from config.llm import get_llm
from config.engineer_profile import get_formatted_profile
from services.pipeline_state import FitCheckPipelineState, Phase3Output
from services.callbacks import ThoughtCallback
from services.utils import get_response_text
from services.prompt_loader import load_prompt, PHASE_SKEPTICAL_COMPARISON
from services.utils.circuit_breaker import llm_breaker, CircuitOpenError

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "skeptical_comparison"
PHASE_DISPLAY = "Skeptical Comparison"

# Critical thinking temperature - slightly higher for creative skepticism
CRITICAL_THINKING_TEMPERATURE = 0.4

# Minimum gaps required for valid output - this is the anti-sycophancy enforcement
MIN_REQUIRED_GAPS = 2

# Maximum strengths allowed - prevents padding
MAX_ALLOWED_STRENGTHS = 4

# Sycophantic phrases to detect in output
SYCOPHANTIC_PHRASES = [
    "perfect fit",
    "ideal candidate",
    "excellent match",
    "amazing",
    "outstanding",
    "exceptional",
    "flawless",
    "perfect match",
    "ideal fit",
    "couldn't be better",
]


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt(config_type: str = None) -> str:
    """
    Load the Phase 3 XML prompt template based on model configuration.
    
    Args:
        config_type: Model config type ("reasoning" or "standard").
                     Reasoning models get concise prompts.
    
    Returns:
        str: XML-structured prompt template.
    """
    try:
        return load_prompt(PHASE_SKEPTICAL_COMPARISON, config_type=config_type, prefer_concise=True)
    except FileNotFoundError:
        logger.warning(f"Phase 3 prompt not found, using embedded fallback")
        return _get_fallback_prompt()


def _get_fallback_prompt() -> str:
    """
    Embedded fallback prompt if file not found.
    
    Returns:
        str: Minimal XML prompt template with anti-sycophancy rules.
    """
    return """<system_instruction>
  <agent_persona>Skeptical Hiring Manager with 15 years experience</agent_persona>
  <primary_objective>
    Evaluate candidate-employer fit with CRITICAL HONESTY. Find genuine gaps, not just strengths.
    A "perfect fit" conclusion indicates insufficient analysis.
  </primary_objective>
  <success_criteria>
    <criterion priority="critical">Identify AT LEAST 2 genuine gaps</criterion>
    <criterion priority="critical">Avoid sycophantic conclusions</criterion>
  </success_criteria>
  <behavioral_constraints>
    <constraint>DO NOT be overly positive without justification</constraint>
    <constraint>DO NOT ignore missing requirements</constraint>
    <constraint>DO NOT use phrases like "perfect fit" or "ideal candidate"</constraint>
    <constraint>DO NOT output markdown - output raw JSON only</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <employer_intel>
    Summary: {employer_summary}
    Requirements: {identified_requirements}
    Tech Stack: {tech_stack}
    Culture: {culture_signals}
  </employer_intel>
  <enriched_research_content>
{enriched_content}
  </enriched_research_content>
  <candidate_profile>{engineer_profile}</candidate_profile>
</context_data>

<output_contract>
{{"genuine_strengths": [], "genuine_gaps": ["gap1", "gap2"], 
  "transferable_skills": [], "risk_assessment": "medium", 
  "risk_justification": "string", "reasoning_trace": "string"}}
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


# =============================================================================
# Output Validation and Anti-Sycophancy Enforcement
# =============================================================================

def validate_phase3_output(data: Dict[str, Any]) -> Phase3Output:
    """
    Validate and normalize Phase 3 output with anti-sycophancy enforcement.
    
    This function enforces the minimum gap requirement - the critical
    anti-sycophancy measure. If the LLM returns fewer than MIN_REQUIRED_GAPS,
    default gaps are added to ensure honest output.
    
    Args:
        data: Raw parsed JSON from LLM response.
    
    Returns:
        Phase3Output: Validated and normalized output.
    """
    genuine_gaps = data.get("genuine_gaps") or []
    genuine_strengths = data.get("genuine_strengths") or []
    
    # CRITICAL: Enforce minimum gaps - this is the anti-sycophancy defense
    if len(genuine_gaps) < MIN_REQUIRED_GAPS:
        logger.warning(
            f"[SKEPTICAL_COMPARISON] Anti-sycophancy triggered: "
            f"only {len(genuine_gaps)} gaps provided, adding defaults"
        )
        default_gaps = [
            "Limited direct experience with employer's specific domain or industry vertical",
            "Some technologies in the employer's stack may require additional ramping time",
        ]
        while len(genuine_gaps) < MIN_REQUIRED_GAPS:
            gap_to_add = default_gaps[len(genuine_gaps)]
            if gap_to_add not in genuine_gaps:
                genuine_gaps.append(gap_to_add)
            else:
                # Avoid duplicates - use alternate defaults
                alternate = "Further verification needed for specific role requirements"
                if alternate not in genuine_gaps:
                    genuine_gaps.append(alternate)
                else:
                    break
    
    # Enforce maximum strengths to prevent padding
    if len(genuine_strengths) > MAX_ALLOWED_STRENGTHS:
        logger.info(
            f"[SKEPTICAL_COMPARISON] Trimming strengths from {len(genuine_strengths)} "
            f"to {MAX_ALLOWED_STRENGTHS}"
        )
        genuine_strengths = genuine_strengths[:MAX_ALLOWED_STRENGTHS]
    
    # Validate risk_assessment
    risk = data.get("risk_assessment", "medium")
    if risk not in ("low", "medium", "high"):
        logger.warning(f"[SKEPTICAL_COMPARISON] Invalid risk '{risk}', defaulting to 'medium'")
        risk = "medium"
    
    # Validate risk consistency - low risk with many gaps is inconsistent
    if risk == "low" and len(genuine_gaps) > 2:
        logger.warning(
            "[SKEPTICAL_COMPARISON] Risk 'low' inconsistent with multiple gaps, upgrading to 'medium'"
        )
        risk = "medium"
    
    # Extract risk_justification
    risk_justification = data.get("risk_justification") or ""
    if not risk_justification:
        # Generate basic justification from gaps
        risk_justification = f"Identified {len(genuine_gaps)} gaps that require attention."
    
    # Extract unverified_claims (new field for verification tracking)
    unverified_claims = data.get("unverified_claims") or []
    
    return Phase3Output(
        genuine_strengths=genuine_strengths,
        genuine_gaps=genuine_gaps,
        unverified_claims=unverified_claims,
        transferable_skills=data.get("transferable_skills") or [],
        risk_assessment=risk,
        risk_justification=risk_justification,
        reasoning_trace=data.get("reasoning_trace") or "Critical analysis completed.",
    )


def detect_sycophantic_content(output: Phase3Output) -> List[str]:
    """
    Detect sycophantic patterns in the output for logging/review.
    
    This is a post-validation check for quality monitoring. It doesn't
    modify the output but logs warnings for human review.
    
    Args:
        output: Validated Phase 3 output.
    
    Returns:
        List of warning messages if sycophantic patterns detected.
    """
    warnings = []
    
    # Check gap count (already enforced, but log if it was triggered)
    if len(output["genuine_gaps"]) < MIN_REQUIRED_GAPS:
        warnings.append(f"Insufficient gaps: only {len(output['genuine_gaps'])}")
    
    # Check for sycophantic phrases in strengths
    for strength in output["genuine_strengths"]:
        strength_lower = strength.lower()
        for phrase in SYCOPHANTIC_PHRASES:
            if phrase in strength_lower:
                warnings.append(f"Sycophantic phrase detected: '{phrase}' in strength")
    
    # Check for sycophantic phrases in reasoning
    reasoning_lower = output.get("reasoning_trace", "").lower()
    for phrase in SYCOPHANTIC_PHRASES:
        if phrase in reasoning_lower:
            warnings.append(f"Sycophantic phrase detected: '{phrase}' in reasoning")
    
    # Check risk-gap consistency
    if output["risk_assessment"] == "low" and len(output["genuine_gaps"]) > 2:
        warnings.append("Risk 'low' with multiple gaps is inconsistent")
    
    return warnings


# =============================================================================
# Context Formatting
# =============================================================================

def format_employer_intel(phase_2: Dict[str, Any], enriched_content: Optional[List[Dict[str, Any]]] = None) -> Dict[str, str]:
    """
    Format Phase 2 output for prompt injection.
    
    Structures the employer intelligence into separate fields for
    clean XML template injection.
    
    Args:
        phase_2: Output from the Deep Research phase.
        enriched_content: Optional full content from top sources.
    
    Returns:
        Dict with formatted fields for prompt template.
    """
    formatted = {
        "employer_summary": phase_2.get("employer_summary", "No summary available"),
        "identified_requirements": _format_list(
            phase_2.get("identified_requirements", []),
            "No specific requirements identified"
        ),
        "tech_stack": _format_list(
            phase_2.get("tech_stack", []),
            "No specific technologies identified"
        ),
        "culture_signals": _format_list(
            phase_2.get("culture_signals", []),
            "No culture signals identified"
        ),
    }
    
    # Format enriched content if available
    if enriched_content:
        enriched_parts = []
        for i, item in enumerate(enriched_content, 1):
            title = item.get("title", "Unknown Source")
            url = item.get("url", "No URL")
            content = item.get("content", "No content")
            enriched_parts.append(f"--- Source {i}: {title} ({url}) ---\n{content[:2000]}")
        formatted["enriched_content"] = "\n\n".join(enriched_parts)
    else:
        formatted["enriched_content"] = "No enriched content available. Using snippets only."
        
    return formatted


def _format_list(items: List[str], empty_message: str) -> str:
    """
    Format a list for prompt injection.
    
    Args:
        items: List of strings to format.
        empty_message: Message to use if list is empty.
    
    Returns:
        Formatted string with bullet points or empty message.
    """
    if not items:
        return empty_message
    return "\n".join(f"      - {item}" for item in items)


# =============================================================================
# Main Node Function
# =============================================================================

async def skeptical_comparison_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 3: SKEPTICAL_COMPARISON - Critical Gap Analysis Node.
    
    This is the CRITICAL anti-sycophancy phase. It performs devil's advocate
    analysis to identify genuine fit gaps and prevent overly positive outputs.
    
    Key Anti-Sycophancy Measures:
    1. Role framing as skeptical hiring manager
    2. Mandatory minimum 2 gaps in output
    3. Negative constraints in prompt
    4. Step-back evaluation question
    5. Post-validation sycophancy detection
    
    Args:
        state: Current pipeline state with Phase 2 output.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update with phase_3_output and phase transition to skills_matching.
    
    SSE Events Emitted:
        - phase: "skeptical_comparison" at start
        - thought (reasoning): Initial analysis announcement
        - thought (reasoning): Analysis summary with gaps/strengths count
        - phase_complete: Summary of findings
    """
    logger.info("[SKEPTICAL_COMPARISON] Starting Phase 3 - CRITICAL GAP ANALYSIS")
    step = state.get("step_count", 0) + 1
    phase_2 = state.get("phase_2_output") or {}
    
    # Emit phase start event
    if callback:
        await callback.on_phase(
            PHASE_NAME,
            "Performing critical fit analysis from skeptical perspective..."
        )
    
    try:
        # Format context data for prompt
        enriched_content = state.get("enriched_content")
        employer_intel = format_employer_intel(phase_2, enriched_content)
        engineer_profile = get_formatted_profile()
        
        # Load prompt based on model config type (concise for reasoning models)
        config_type = state.get("config_type")
        prompt_template = load_phase_prompt(config_type=config_type)
        prompt = prompt_template.format(
            employer_summary=employer_intel["employer_summary"],
            identified_requirements=employer_intel["identified_requirements"],
            tech_stack=employer_intel["tech_stack"],
            culture_signals=employer_intel["culture_signals"],
            enriched_content=employer_intel["enriched_content"],
            engineer_profile=engineer_profile,
        )
        
        # Emit initial reasoning thought
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content="Analyzing fit from a skeptical hiring manager's perspective - identifying genuine gaps and potential concerns...",
                phase=PHASE_NAME,
            )
        
        # Get LLM with critical thinking temperature
        # Uses model config from state if provided
        llm = get_llm(
            streaming=False,
            temperature=CRITICAL_THINKING_TEMPERATURE,
            model_id=state.get("model_id"),
            config_type=state.get("config_type"),
        )
        
        # Invoke LLM with formatted prompt
        messages = [HumanMessage(content=prompt)]
        
        async with llm_breaker.call():
            response = await llm.ainvoke(messages)
        
        # Extract response text (handles Gemini's structured format)
        response_text = get_response_text(response)
        logger.debug(f"[SKEPTICAL_COMPARISON] Raw LLM response: {response_text[:500]}...")
        
        # Parse JSON from response
        parsed_data = extract_json_from_response(response_text)
        
        # Validate and enforce anti-sycophancy rules
        validated_output = validate_phase3_output(parsed_data)
        
        # Check for sycophantic patterns (logging only)
        sycophancy_warnings = detect_sycophantic_content(validated_output)
        if sycophancy_warnings:
            logger.warning(
                f"[SKEPTICAL_COMPARISON] Sycophancy warnings: {sycophancy_warnings}"
            )
        
        step += 1
        # Emit analysis summary thought
        if callback:
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
                validated_output["risk_assessment"], "🟡"
            )
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content=(
                    f"Critical review complete: Identified {len(validated_output['genuine_strengths'])} strengths, "
                    f"{len(validated_output['genuine_gaps'])} gaps. "
                    f"Risk assessment: {risk_emoji} {validated_output['risk_assessment']}"
                ),
                phase=PHASE_NAME,
            )
        
        # Emit phase complete event with enriched metadata
        if callback:
            summary = (
                f"Found {len(validated_output['genuine_gaps'])} gaps, "
                f"{len(validated_output['genuine_strengths'])} strengths. "
                f"Risk level: {validated_output['risk_assessment']}"
            )
            # Build rich metadata for frontend transparency
            enriched_data = {
                "gap_count": len(validated_output['genuine_gaps']),
                "strength_count": len(validated_output['genuine_strengths']),
                "risk_level": validated_output['risk_assessment'],
                # Actual content for insight
                "genuine_gaps": validated_output['genuine_gaps'][:4],
                "genuine_strengths": validated_output['genuine_strengths'][:4],
                "transferable_skills": validated_output.get('transferable_skills', [])[:3],
                "risk_justification": validated_output.get('risk_justification', '')[:200],
                "unverified_claims_count": len(validated_output.get('unverified_claims', [])),
            }
            await callback.on_phase_complete(
                PHASE_NAME, 
                summary,
                data=enriched_data
            )
        
        logger.info(
            f"[SKEPTICAL_COMPARISON] Phase 3 complete: "
            f"gaps={len(validated_output['genuine_gaps'])}, "
            f"strengths={len(validated_output['genuine_strengths'])}, "
            f"risk={validated_output['risk_assessment']}"
        )
        
        return {
            "phase_3_output": validated_output,
            "current_phase": "skills_matching",
            "step_count": step,
        }
        
    except Exception as e:
        logger.error(f"[SKEPTICAL_COMPARISON] Phase 3 failed: {e}", exc_info=True)
        
        # Graceful degradation with HONEST, CONSERVATIVE defaults
        # Even in failure, we don't provide sycophantic output
        fallback_output = Phase3Output(
            genuine_strengths=["Technical background indicates relevant foundational experience"],
            genuine_gaps=[
                "Unable to fully verify specific alignment with employer requirements due to analysis error",
                "Further manual review recommended to assess complete technical fit",
            ],
            transferable_skills=[],
            risk_assessment="medium",
            reasoning_trace=f"Analysis encountered an error, providing conservative assessment: {str(e)[:100]}",
        )
        
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content="Analysis encountered an issue - providing conservative assessment",
                phase=PHASE_NAME,
            )
            await callback.on_phase_complete(
                PHASE_NAME,
                "Critical analysis completed with conservative defaults"
            )
        
        return {
            "phase_3_output": fallback_output,
            "current_phase": "skills_matching",
            "step_count": step,
            "processing_errors": state.get("processing_errors", []) + [
                f"Phase 3 error: {str(e)[:200]}"
            ],
        }
