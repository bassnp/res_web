"""
Skills Matching Node - Phase 4 of the Fit Check Pipeline.

This module implements the skill alignment node that:
1. Invokes skill_matcher and experience_matcher tools
2. Synthesizes tool outputs into structured skill-to-requirement matches
3. Produces quantified match scores with transparent calculation
4. Integrates skeptical comparison gaps into the assessment

Gemini Optimization Applied:
- Uses XML-structured prompt for synthesis with criteria-based success metrics
- Tool calls emit explicit thought events for frontend visibility
- Confidence calibration provided in prompt for consistent scoring
- Low temperature (0.2) for precision in quantified output
- Post-hoc reasoning trace, not inline CoT (Gemini 2.5 anti-pattern)
- Negative constraints prevent confidence inflation

Desire: Semantic Alignment & Quantification
The Skills Matching agent is the technical recruiter. It operates with precision,
mapping each employer requirement to specific candidate skills with quantified
confidence, or explicitly identifying them as unmatched.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from langchain_core.messages import HumanMessage

from config.llm import get_llm
from services.pipeline_state import FitCheckPipelineState, Phase4Output
from services.callbacks import ThoughtCallback
from services.tools.skill_matcher import analyze_skill_match
from services.tools.experience_matcher import analyze_experience_relevance
from services.utils import get_response_text
from services.prompt_loader import load_prompt, PHASE_SKILLS_MATCHING
from services.utils.circuit_breaker import llm_breaker, CircuitOpenError

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "skills_matching"
PHASE_DISPLAY = "Skills Matching"

# Precision temperature - low for accurate quantified output
SYNTHESIS_TEMPERATURE = 0.2

# Maximum input length for tool calls to avoid token overflow
MAX_TOOL_INPUT_LENGTH = 500

# Timeout for this phase (in seconds) - informational
PHASE_TIMEOUT_SECONDS = 15


# =============================================================================
# Score Calculation
# =============================================================================

def calculate_overall_score(
    matched: List[Dict[str, Any]],
    unmatched: List[str],
) -> Tuple[float, str]:
    """
    Calculate overall match score with transparent breakdown.
    
    This implements a consistent, reproducible scoring algorithm:
        1. Average confidence of matched requirements
        2. Multiply by coverage ratio (matched / total)
        3. Apply gap penalty if unmatched > 30% of total
    
    The algorithm ensures that:
        - High confidence matches are weighted appropriately
        - Coverage matters (matching 2/10 requirements != good fit)
        - Heavy gaps receive additional penalty
    
    Args:
        matched: List of matched requirement dicts with confidence scores.
        unmatched: List of unmatched requirement strings.
    
    Returns:
        Tuple of (score: float, breakdown_explanation: str)
    
    Examples:
        >>> calculate_overall_score([{"confidence": 0.9}], [])
        (0.9, "Avg confidence: 0.90 × Coverage: 1.00 (1/1) = 0.90")
        
        >>> calculate_overall_score([{"confidence": 0.8}], ["gap1", "gap2"])
        (0.27, "Avg confidence: 0.80 × Coverage: 0.33 (1/3) = 0.27")
    """
    total_requirements = len(matched) + len(unmatched)
    
    # Edge case: no requirements identified
    if total_requirements == 0:
        return 0.5, "No requirements identified; defaulting to neutral score."
    
    # Calculate average confidence of matched requirements
    if matched:
        confidences = [
            max(0.0, min(1.0, float(m.get("confidence", 0.5))))
            for m in matched
        ]
        avg_confidence = sum(confidences) / len(confidences)
    else:
        avg_confidence = 0.0
    
    # Calculate coverage ratio
    coverage = len(matched) / total_requirements
    
    # Base score: average confidence weighted by coverage
    base_score = avg_confidence * coverage
    
    # Gap penalty if more than 30% of requirements are unmatched
    gap_ratio = len(unmatched) / total_requirements
    penalty = 0.0
    if gap_ratio > 0.3:
        # 20% penalty per 10% gap over the 30% threshold
        penalty = (gap_ratio - 0.3) * 0.2
        base_score = max(0, base_score - penalty)
    
    # Clamp final score to valid range
    final_score = max(0.0, min(1.0, base_score))
    
    # Build transparent breakdown string
    breakdown = (
        f"Avg confidence: {avg_confidence:.2f} × "
        f"Coverage: {coverage:.2f} ({len(matched)}/{total_requirements}) = "
        f"{(avg_confidence * coverage):.2f}"
    )
    if penalty > 0:
        breakdown += f" - penalty {penalty:.2f} (gap ratio {gap_ratio:.1%} > 30%)"
    breakdown += f" → Final: {final_score:.2f}"
    
    return round(final_score, 2), breakdown


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt(config_type: str = None) -> str:
    """
    Load the Phase 4 XML prompt template based on model configuration.
    
    Args:
        config_type: Model config type ("reasoning" or "standard").
                     Reasoning models get concise prompts.
    
    Returns:
        str: XML-structured prompt template.
    """
    try:
        return load_prompt(PHASE_SKILLS_MATCHING, config_type=config_type, prefer_concise=True)
    except FileNotFoundError:
        logger.warning(f"Phase 4 prompt not found, using embedded fallback")
        return _get_fallback_prompt()


def _get_fallback_prompt() -> str:
    """
    Embedded fallback prompt if file not found.
    
    Returns:
        str: Minimal XML prompt template for skill matching.
    """
    return """<system_instruction>
  <agent_persona>Technical Recruiter with skill matching expertise.</agent_persona>
  <primary_objective>
    Map each employer requirement to a specific candidate skill with confidence score.
  </primary_objective>
  <behavioral_constraints>
    <constraint>DO NOT inflate confidence without evidence</constraint>
    <constraint>DO NOT output markdown - output raw JSON only</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <employer_requirements>
    Requirements: {identified_requirements}
    Tech Stack: {tech_stack}
  </employer_requirements>
  <skill_analysis_tool_output>{skill_matcher_output}</skill_analysis_tool_output>
  <experience_analysis_tool_output>{experience_matcher_output}</experience_analysis_tool_output>
  <skeptical_review>
    Gaps: {genuine_gaps}
    Transferable: {transferable_skills}
    Risk: {risk_assessment}
  </skeptical_review>
</context_data>

<output_contract>
{{"matched_requirements": [], "unmatched_requirements": [], 
  "overall_match_score": 0.5, "score_breakdown": "string", 
  "reasoning_trace": "string"}}
</output_contract>"""


# =============================================================================
# JSON Parsing Utilities
# =============================================================================

def extract_json_from_response(response: str) -> Dict[str, Any]:
    """
    Extract JSON from LLM response, handling various formats.
    
    The LLM may return JSON in several formats:
    - Clean JSON (ideal)
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
# Output Validation
# =============================================================================

def validate_phase4_output(data: Dict[str, Any]) -> Phase4Output:
    """
    Validate and normalize Phase 4 output.
    
    This function ensures:
    - Confidence scores are clamped to valid 0-1 range
    - Missing fields have sensible defaults
    - Overall score is recalculated for consistency (prevents LLM gaming)
    - All required fields are present
    
    Args:
        data: Raw parsed JSON from LLM response.
    
    Returns:
        Phase4Output: Validated and normalized output dictionary.
    """
    matched_raw = data.get("matched_requirements") or []
    unmatched = data.get("unmatched_requirements") or []
    
    # Validate and normalize matched items
    validated_matched: List[Dict[str, Any]] = []
    for item in matched_raw:
        if isinstance(item, dict):
            # Clamp confidence to 0-1 range
            raw_confidence = item.get("confidence", 0.5)
            try:
                confidence = max(0.0, min(1.0, float(raw_confidence)))
            except (ValueError, TypeError):
                confidence = 0.5
                logger.warning(
                    f"[SKILLS_MATCHING] Invalid confidence '{raw_confidence}', defaulting to 0.5"
                )
            
            validated_matched.append({
                "requirement": str(item.get("requirement", "Unknown requirement")),
                "matched_skill": str(item.get("matched_skill", "General experience")),
                "confidence": confidence,
                "evidence": str(item.get("evidence", "Skill match identified")),
            })
    
    # Ensure unmatched is a list of strings
    validated_unmatched = [str(u) for u in unmatched if u]
    
    # CRITICAL: Recalculate score for consistency
    # This prevents the LLM from gaming the score with inflated values
    calculated_score, breakdown = calculate_overall_score(validated_matched, validated_unmatched)
    
    # Log if LLM's score significantly differs from calculated
    llm_score = data.get("overall_match_score")
    if llm_score is not None:
        try:
            llm_score_float = float(llm_score)
            if abs(llm_score_float - calculated_score) > 0.15:
                logger.info(
                    f"[SKILLS_MATCHING] LLM score {llm_score_float:.2f} differs from "
                    f"calculated {calculated_score:.2f}, using calculated value"
                )
        except (ValueError, TypeError):
            pass
    
    return Phase4Output(
        matched_requirements=validated_matched,
        unmatched_requirements=validated_unmatched,
        overall_match_score=calculated_score,
        reasoning_trace=data.get("reasoning_trace") or f"Score breakdown: {breakdown}",
    )


# =============================================================================
# Context Formatting
# =============================================================================

def format_list_for_prompt(items: List[str], default: str = "None identified") -> str:
    """
    Format a list for prompt injection.
    
    Args:
        items: List of items to format.
        default: Default value if list is empty.
    
    Returns:
        Formatted string suitable for XML prompt.
    """
    if not items:
        return default
    return ", ".join(str(item) for item in items if item)


def truncate_tool_input(text: str) -> str:
    """
    Truncate tool input to prevent token overflow.
    
    Args:
        text: Input text for tool.
    
    Returns:
        Truncated text with ellipsis if needed.
    """
    if len(text) > MAX_TOOL_INPUT_LENGTH:
        return text[:MAX_TOOL_INPUT_LENGTH] + "..."
    return text


# =============================================================================
# Main Node Function
# =============================================================================

async def skills_matching_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 4: SKILLS_MATCHING - Skill Alignment Node.
    
    This node performs structured skill-to-requirement mapping:
    1. Invokes skill_matcher tool with employer requirements
    2. Invokes experience_matcher tool with employer context
    3. Synthesizes tool outputs with LLM to produce matches and scores
    4. Validates output and recalculates scores for consistency
    
    Args:
        state: Current pipeline state with Phases 1-3 output.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update dictionary containing:
        - phase_4_output: Validated Phase4Output
        - current_phase: Next phase ("generate_results")
        - step_count: Updated step count
        - processing_errors: Any non-fatal errors encountered
    
    Emits Events (via callback):
        - phase: "skills_matching" at start
        - thought (tool_call): For each tool invocation
        - thought (observation): For each tool result
        - thought (reasoning): For synthesis step
        - phase_complete: With match score summary
    
    Graceful Degradation:
        On tool or LLM failure, returns neutral output with error logging
        rather than crashing the pipeline.
    """
    logger.info("[SKILLS_MATCHING] Starting phase 4")
    
    # Initialize from state
    step = state.get("step_count", 0)
    phase_2 = state.get("phase_2_output") or {}
    phase_3 = state.get("phase_3_output") or {}
    errors: List[str] = list(state.get("processing_errors") or [])
    
    # Emit phase start event
    if callback and hasattr(callback, 'on_phase'):
        await callback.on_phase(
            PHASE_NAME,
            "Mapping skills to requirements..."
        )
    elif callback:
        await callback.on_status(
            "analyzing",
            "Mapping skills to requirements..."
        )
    
    try:
        # =====================================================================
        # Step 1: Gather requirements for tool input
        # IMPORTANT: For job_description queries, prioritize extracted_skills
        # from Phase 1 (the query itself) over web-researched requirements.
        # This prevents false gaps from unrelated web content.
        # =====================================================================
        phase_1 = state.get("phase_1_output") or {}
        query_type = phase_1.get("query_type", "company")
        extracted_skills = phase_1.get("extracted_skills") or []
        
        requirements = phase_2.get("identified_requirements") or []
        tech_stack = phase_2.get("tech_stack") or []
        
        # For job descriptions, prioritize query-extracted skills
        if query_type == "job_description" and extracted_skills:
            # Use extracted skills as PRIMARY requirements, then supplement
            # with web research (but mark them as secondary)
            primary_requirements = extracted_skills
            secondary_requirements = [
                r for r in (requirements + tech_stack) 
                if r.lower() not in [s.lower() for s in extracted_skills]
            ][:5]  # Limit secondary to prevent noise
            all_requirements = primary_requirements + secondary_requirements
            logger.info(
                f"[SKILLS_MATCHING] Job description mode: {len(primary_requirements)} "
                f"primary skills from query, {len(secondary_requirements)} secondary from research"
            )
        else:
            # Standard mode: combine requirements and tech stack
            all_requirements = list(dict.fromkeys(requirements + tech_stack))
        
        requirements_str = (
            ", ".join(all_requirements)
            if all_requirements
            else "General software engineering skills"
        )
        
        # =====================================================================
        # Step 2: Invoke skill_matcher tool
        # =====================================================================
        step += 1
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="tool_call",
                content="Analyzing skill alignment against requirements...",
                tool="analyze_skill_match",
                tool_input=truncate_tool_input(requirements_str),
                phase=PHASE_NAME,
            )
        
        try:
            skill_output = analyze_skill_match.invoke(requirements_str)
            logger.debug(f"[SKILLS_MATCHING] Skill matcher output: {skill_output[:200]}...")
        except Exception as e:
            logger.warning(f"[SKILLS_MATCHING] Skill matcher failed: {e}")
            skill_output = "Skill analysis unavailable due to tool error."
            errors.append(f"Skill matcher error: {str(e)}")
        
        step += 1
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="observation",
                content="Skill analysis complete - identified matching skills and gaps.",
                phase=PHASE_NAME,
            )
        
        # =====================================================================
        # Step 3: Invoke experience_matcher tool
        # =====================================================================
        employer_context = phase_2.get("employer_summary") or state.get("query", "")
        
        step += 1
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="tool_call",
                content="Analyzing experience relevance to employer context...",
                tool="analyze_experience_relevance",
                tool_input=truncate_tool_input(employer_context),
                phase=PHASE_NAME,
            )
        
        try:
            experience_output = analyze_experience_relevance.invoke(employer_context)
            logger.debug(f"[SKILLS_MATCHING] Experience matcher output: {experience_output[:200]}...")
        except Exception as e:
            logger.warning(f"[SKILLS_MATCHING] Experience matcher failed: {e}")
            experience_output = "Experience analysis unavailable due to tool error."
            errors.append(f"Experience matcher error: {str(e)}")
        
        step += 1
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="observation",
                content="Experience analysis complete - identified relevant background.",
                phase=PHASE_NAME,
            )
        
        # =====================================================================
        # Step 4: Load and format synthesis prompt
        # =====================================================================
        step += 1
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content="Synthesizing skill matches with quantified confidence scores...",
                phase=PHASE_NAME,
            )
        
        # Load prompt based on model config type (concise for reasoning models)
        config_type = state.get("config_type")
        prompt_template = load_phase_prompt(config_type=config_type)
        prompt = prompt_template.format(
            identified_requirements=format_list_for_prompt(requirements),
            tech_stack=format_list_for_prompt(tech_stack),
            skill_matcher_output=skill_output,
            experience_matcher_output=experience_output,
            genuine_gaps=format_list_for_prompt(phase_3.get("genuine_gaps", [])),
            transferable_skills=format_list_for_prompt(phase_3.get("transferable_skills", [])),
            risk_assessment=phase_3.get("risk_assessment", "medium"),
        )
        
        # =====================================================================
        # Step 5: LLM synthesis
        # =====================================================================
        # Uses model config from state if provided
        llm = get_llm(
            streaming=False,
            temperature=SYNTHESIS_TEMPERATURE,
            model_id=state.get("model_id"),
            config_type=state.get("config_type"),
        )
        
        messages = [HumanMessage(content=prompt)]
        
        async with llm_breaker.call():
            response = await llm.ainvoke(messages)
        
        # Extract and parse response (handles Gemini's structured format)
        response_text = get_response_text(response)
        logger.debug(f"[SKILLS_MATCHING] LLM response: {response_text[:300]}...")
        
        # Parse and validate output
        parsed_data = extract_json_from_response(response_text)
        validated_output = validate_phase4_output(parsed_data)
        
        # =====================================================================
        # Step 6: Emit phase completion
        # =====================================================================
        if callback and hasattr(callback, 'on_phase_complete'):
            score_pct = int(validated_output["overall_match_score"] * 100)
            matched_count = len(validated_output["matched_requirements"])
            unmatched_count = len(validated_output["unmatched_requirements"])
            summary = f"Match score: {score_pct}% ({matched_count} matched, {unmatched_count} gaps)"
            await callback.on_phase_complete(PHASE_NAME, summary)
        
        logger.info(
            f"[SKILLS_MATCHING] Phase 4 complete: "
            f"score={validated_output['overall_match_score']}, "
            f"matched={len(validated_output['matched_requirements'])}, "
            f"unmatched={len(validated_output['unmatched_requirements'])}"
        )
        
        return {
            "phase_4_output": validated_output,
            "current_phase": "generate_results",
            "step_count": step,
            "processing_errors": errors if errors else state.get("processing_errors", []),
        }
        
    except Exception as e:
        logger.error(f"[SKILLS_MATCHING] Phase 4 failed: {e}", exc_info=True)
        
        # Graceful degradation - return neutral output
        fallback_output = Phase4Output(
            matched_requirements=[],
            unmatched_requirements=["Unable to complete skill analysis"],
            overall_match_score=0.5,
            reasoning_trace=f"Skill matching encountered an error: {str(e)}. Defaulting to neutral assessment.",
        )
        
        if callback and hasattr(callback, 'on_phase_complete'):
            await callback.on_phase_complete(
                PHASE_NAME,
                "Skill matching completed with limited data"
            )
        
        errors.append(f"Phase 4 error: {str(e)}")
        
        return {
            "phase_4_output": fallback_output,
            "current_phase": "generate_results",
            "step_count": step,
            "processing_errors": errors,
        }
