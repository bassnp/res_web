"""
Confidence Re-Ranker Node - Phase 5B of the Fit Check Pipeline.

This module implements an LLM-as-a-Judge meta-reasoning layer that:
1. Evaluates the quality of prior phase outputs
2. Calibrates confidence with explicit rubric
3. Provides nuanced fit assessment beyond raw match scores
4. Flags any concerns about data quality or gaps

This replaces the raw overall_match_score with a calibrated confidence
that factors in data quality, gap severity, and evidence strength.

Key Design Principles:
- Skeptical second look at the entire analysis
- Penalizes for insufficient data (few tech stack items)
- Penalizes for insufficient skepticism (few gaps identified)
- Uses explicit rubric for consistent calibration
- Low temperature (0.1) for reproducible judgments

Desire: Honest Calibration & Meta-Reasoning
The Re-Ranker agent is the hiring committee reviewer. It takes a skeptical
second look at the entire analysis, ensuring the match score reflects
reality rather than optimistic interpolation.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from langchain_core.messages import HumanMessage

from config.llm import get_llm
from services.pipeline_state import FitCheckPipelineState
from services.callbacks import ThoughtCallback
from services.utils import get_response_text
from services.prompt_loader import load_prompt, PHASE_CONFIDENCE_RERANKER
from services.utils.circuit_breaker import llm_breaker, CircuitOpenError

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "confidence_reranker"
PHASE_DISPLAY = "Confidence Re-Ranking"

# Low temperature for consistent, calibrated judgments
RERANKER_TEMPERATURE = 0.1

# Timeout for this phase (in seconds) - informational
PHASE_TIMEOUT_SECONDS = 10


# =============================================================================
# Output Type Definition
# =============================================================================

class RerankerOutput:
    """
    Output structure for the confidence re-ranker.
    
    Attributes:
        calibrated_score: Adjusted confidence score (0-100)
        tier: Confidence tier (HIGH/MEDIUM/LOW/INSUFFICIENT_DATA)
        justification: Brief explanation of the confidence level
        quality_flags: List of quality concern flags
        data_quality: Assessment of data quality across phases
        adjustment_rationale: How/why this differs from raw score
        reasoning_trace: Post-hoc evaluation logic summary
    """
    
    def __init__(
        self,
        calibrated_score: int,
        tier: str,
        justification: str,
        quality_flags: List[str],
        data_quality: Dict[str, str],
        adjustment_rationale: str,
        reasoning_trace: str,
    ):
        self.calibrated_score = calibrated_score
        self.tier = tier
        self.justification = justification
        self.quality_flags = quality_flags
        self.data_quality = data_quality
        self.adjustment_rationale = adjustment_rationale
        self.reasoning_trace = reasoning_trace
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for state storage."""
        return {
            "calibrated_score": self.calibrated_score,
            "tier": self.tier,
            "justification": self.justification,
            "quality_flags": self.quality_flags,
            "data_quality": self.data_quality,
            "adjustment_rationale": self.adjustment_rationale,
            "reasoning_trace": self.reasoning_trace,
        }


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt(config_type: str = None) -> str:
    """
    Load the Phase 5B XML prompt template based on model configuration.
    
    Args:
        config_type: Model config type ("reasoning" or "standard").
                     Reasoning models get concise prompts.
    
    Returns:
        str: XML-structured prompt template.
    """
    try:
        return load_prompt(PHASE_CONFIDENCE_RERANKER, config_type=config_type, prefer_concise=True)
    except FileNotFoundError:
        logger.warning(f"Phase 5B prompt not found, using embedded fallback")
        return _get_fallback_prompt()


def _get_fallback_prompt() -> str:
    """
    Embedded fallback prompt if file not found.
    
    Returns:
        str: Minimal prompt template for confidence re-ranking.
    """
    return """<system_instruction>
  <agent_persona>Senior Hiring Committee Reviewer</agent_persona>
  <primary_objective>
    Evaluate the fit analysis and provide a CALIBRATED confidence score.
    Penalize for sparse data. Be skeptical.
  </primary_objective>
</system_instruction>

<context_data>
  <phase_2_data>
    <tech_stack_count>{tech_stack_count}</tech_stack_count>
    <requirements_count>{requirements_count}</requirements_count>
  </phase_2_data>
  <phase_3_data>
    <gaps_count>{gaps_count}</gaps_count>
    <risk_assessment>{risk_assessment}</risk_assessment>
  </phase_3_data>
  <phase_4_data>
    <raw_match_score>{raw_match_score}</raw_match_score>
    <matched_count>{matched_count}</matched_count>
  </phase_4_data>
</context_data>

<output_contract>
{{"calibrated_confidence": {{"score": 50, "tier": "MEDIUM", "justification": "string"}},
  "quality_flags": [], "data_quality_assessment": {{}},
  "adjustment_rationale": "string", "reasoning_trace": "string"}}
</output_contract>"""


# =============================================================================
# JSON Extraction
# =============================================================================

def extract_json_from_response(response: str) -> Dict[str, Any]:
    """
    Extract JSON from LLM response, handling various formats.
    
    Args:
        response: Raw LLM response text.
    
    Returns:
        Parsed JSON dictionary.
    
    Raises:
        ValueError: If JSON cannot be extracted or parsed.
    """
    text = response.strip()
    
    # Try direct JSON parse first
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
    
    # Try to find JSON object in text
    brace_pattern = r'\{[\s\S]*\}'
    matches = re.findall(brace_pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")


# =============================================================================
# Context Preparation
# =============================================================================

def prepare_context_data(state: FitCheckPipelineState) -> Dict[str, Any]:
    """
    Prepare context data from prior phases for reranker evaluation.
    
    Args:
        state: Current pipeline state with Phases 1-4 output.
    
    Returns:
        Dictionary of context variables for prompt formatting.
    """
    phase_1 = state.get("phase_1_output") or {}
    phase_2 = state.get("phase_2_output") or {}
    phase_3 = state.get("phase_3_output") or {}
    phase_4 = state.get("phase_4_output") or {}
    
    # Phase 1 metrics
    query_type = phase_1.get("query_type", "company")
    extracted_skills = phase_1.get("extracted_skills") or []
    
    # Phase 2 metrics
    tech_stack = phase_2.get("tech_stack") or []
    requirements = phase_2.get("identified_requirements") or []
    culture_signals = phase_2.get("culture_signals") or []
    
    # Phase 3 metrics
    gaps = phase_3.get("genuine_gaps") or []
    strengths = phase_3.get("genuine_strengths") or []
    unverified = phase_3.get("unverified_claims") or []
    risk_assessment = phase_3.get("risk_assessment", "unknown")
    risk_justification = phase_3.get("risk_justification", "")
    
    # Phase 4 metrics
    matched = phase_4.get("matched_requirements") or []
    unmatched = phase_4.get("unmatched_requirements") or []
    raw_score = phase_4.get("overall_match_score", 0.5)
    reasoning = phase_4.get("reasoning_trace", "")
    
    # Calculate average confidence from matched requirements
    if matched:
        confidences = [float(m.get("confidence", 0.5)) for m in matched]
        avg_confidence = sum(confidences) / len(confidences)
    else:
        avg_confidence = 0.0
    
    # For job descriptions, calculate how many query skills were matched
    query_skills_matched = 0
    if query_type == "job_description" and extracted_skills:
        for skill in extracted_skills:
            skill_lower = skill.lower()
            for m in matched:
                matched_skill = m.get("matched_skill", "").lower()
                requirement = m.get("requirement", "").lower()
                if skill_lower in matched_skill or skill_lower in requirement:
                    query_skills_matched += 1
                    break
    
    return {
        # Phase 1
        "query_type": query_type,
        "extracted_skills_count": len(extracted_skills),
        "extracted_skills_items": ", ".join(extracted_skills) if extracted_skills else "None",
        "query_skills_matched": query_skills_matched,
        
        # Phase 2
        "tech_stack_count": len(tech_stack),
        "tech_stack_items": ", ".join(tech_stack) if tech_stack else "None extracted",
        "requirements_count": len(requirements),
        "requirements_items": "; ".join(requirements) if requirements else "None identified",
        "culture_signals_count": len(culture_signals),
        
        # Phase 3
        "gaps_count": len(gaps),
        "gaps_items": "; ".join(gaps) if gaps else "None identified",
        "strengths_count": len(strengths),
        "risk_assessment": risk_assessment,
        "risk_justification": risk_justification,
        "unverified_claims_count": len(unverified),
        
        # Phase 4
        "raw_match_score": int(raw_score * 100),
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "average_confidence": f"{avg_confidence * 100:.0f}%",
        "score_breakdown": reasoning,
        
        # Company context
        "company_name": phase_1.get("company_name", "Unknown"),
        "employer_summary": phase_2.get("employer_summary", "")[:300],
    }


# =============================================================================
# Output Validation
# =============================================================================

def validate_reranker_output(data: Dict[str, Any]) -> RerankerOutput:
    """
    Validate and normalize reranker output.
    
    Args:
        data: Raw parsed JSON from LLM response.
    
    Returns:
        RerankerOutput: Validated and normalized output.
    """
    calibrated = data.get("calibrated_confidence", {})
    
    # Extract and clamp score
    raw_score = calibrated.get("score", 50)
    try:
        score = max(0, min(100, int(raw_score)))
    except (ValueError, TypeError):
        score = 50
        logger.warning(f"[RERANKER] Invalid score '{raw_score}', defaulting to 50")
    
    # Validate tier
    tier = calibrated.get("tier", "MEDIUM")
    valid_tiers = ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT_DATA"]
    if tier not in valid_tiers:
        # Infer tier from score
        if score >= 75:
            tier = "HIGH"
        elif score >= 40:
            tier = "MEDIUM"
        elif score >= 15:
            tier = "LOW"
        else:
            tier = "INSUFFICIENT_DATA"
        logger.info(f"[RERANKER] Inferred tier {tier} from score {score}")
    
    justification = calibrated.get("justification", "Confidence calibrated based on available evidence.")
    
    # Quality flags
    quality_flags = data.get("quality_flags", [])
    if not isinstance(quality_flags, list):
        quality_flags = []
    
    # Data quality assessment
    data_quality = data.get("data_quality_assessment", {})
    if not isinstance(data_quality, dict):
        data_quality = {}
    
    adjustment_rationale = data.get("adjustment_rationale", "Score adjusted based on evidence quality.")
    reasoning_trace = data.get("reasoning_trace", "")
    
    return RerankerOutput(
        calibrated_score=score,
        tier=tier,
        justification=justification,
        quality_flags=quality_flags,
        data_quality=data_quality,
        adjustment_rationale=adjustment_rationale,
        reasoning_trace=reasoning_trace,
    )


# =============================================================================
# Fallback Logic
# =============================================================================

def calculate_fallback_confidence(state: FitCheckPipelineState) -> RerankerOutput:
    """
    Calculate confidence using deterministic fallback logic.
    
    Used when LLM call fails or returns invalid output.
    
    Args:
        state: Current pipeline state.
    
    Returns:
        RerankerOutput with fallback calculation.
    """
    phase_1 = state.get("phase_1_output") or {}
    phase_2 = state.get("phase_2_output") or {}
    phase_3 = state.get("phase_3_output") or {}
    phase_4 = state.get("phase_4_output") or {}
    
    query_type = phase_1.get("query_type", "company")
    extracted_skills = phase_1.get("extracted_skills") or []
    tech_stack = phase_2.get("tech_stack") or []
    requirements = phase_2.get("identified_requirements") or []
    gaps = phase_3.get("genuine_gaps") or []
    matched = phase_4.get("matched_requirements") or []
    raw_score = phase_4.get("overall_match_score", 0.5)
    
    quality_flags = []
    
    # Start with raw score
    score = int(raw_score * 100)
    
    # For job descriptions, give a boost if query skills were matched
    if query_type == "job_description" and extracted_skills:
        query_skills_matched = 0
        for skill in extracted_skills:
            skill_lower = skill.lower()
            for m in matched:
                matched_skill = m.get("matched_skill", "").lower()
                requirement = m.get("requirement", "").lower()
                if skill_lower in matched_skill or skill_lower in requirement:
                    query_skills_matched += 1
                    break
        
        # Boost for matching query-specified skills (up to 15 points)
        match_ratio = query_skills_matched / len(extracted_skills) if extracted_skills else 0
        skill_boost = int(match_ratio * 15)
        score = min(100, score + skill_boost)
        
        if match_ratio >= 0.8:
            quality_flags.append("strong_query_skill_match")
        elif match_ratio < 0.5:
            quality_flags.append("weak_query_skill_match")
    else:
        # Standard company query penalties
        # Penalty for sparse tech stack
        if len(tech_stack) < 2:
            score = max(0, score - 15)
            quality_flags.append("sparse_tech_stack")
        
        # Penalty for no requirements
        if len(requirements) == 0:
            score = max(0, score - 10)
            quality_flags.append("no_requirements")
    
    # Penalty for insufficient gaps (suggests incomplete skeptical analysis)
    # But be more lenient for job descriptions with good matches
    if len(gaps) < 2 and score < 80:
        score = max(0, score - 10)
        quality_flags.append("insufficient_gaps")
    
    # Penalty if raw score was exactly 50% (likely default)
    if raw_score == 0.5 and len(matched) == 0:
        score = max(0, score - 20)
        quality_flags.append("default_score_suspected")
    
    # Determine tier
    if score >= 75:
        tier = "HIGH"
    elif score >= 40:
        tier = "MEDIUM"
    elif score >= 15:
        tier = "LOW"
    else:
        tier = "INSUFFICIENT_DATA"
    
    return RerankerOutput(
        calibrated_score=score,
        tier=tier,
        justification="Confidence calculated via fallback algorithm due to processing constraints.",
        quality_flags=quality_flags,
        data_quality={
            "tech_stack_quality": "weak" if len(tech_stack) < 2 else "moderate",
            "requirements_quality": "missing" if len(requirements) == 0 else "moderate",
            "skeptical_analysis_quality": "superficial" if len(gaps) < 2 else "adequate",
        },
        adjustment_rationale="Score adjusted based on data availability penalties.",
        reasoning_trace="Fallback calculation applied: tech_stack={}, requirements={}, gaps={}".format(
            len(tech_stack), len(requirements), len(gaps)
        ),
    )


# =============================================================================
# Main Node Function
# =============================================================================

async def confidence_reranker_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 5B: CONFIDENCE_RERANKER - LLM-as-a-Judge Meta-Reasoning Node.
    
    This node evaluates the quality of the fit analysis and produces a
    calibrated confidence score that reflects the true strength of evidence.
    
    Args:
        state: Current pipeline state with Phases 1-4 output.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update dictionary containing:
        - reranker_output: RerankerOutput as dict
        - current_phase: Next phase ("generate_results")
        - step_count: Updated step count
    
    Emits Events (via callback):
        - phase: "confidence_reranker" at start
        - thought (reasoning): For evaluation process
        - phase_complete: With calibrated confidence summary
    """
    logger.info("[RERANKER] Starting confidence re-ranking phase")
    
    step_count = state.get("step_count", 0)
    errors = list(state.get("processing_errors") or [])
    
    # Emit phase start
    if callback:
        await callback.on_phase(PHASE_NAME, "Calibrating confidence with LLM-as-a-Judge...")
    
    try:
        # Prepare context from prior phases
        context = prepare_context_data(state)
        
        # Emit thought about evaluation
        step_count += 1
        if callback:
            await callback.on_thought(
                step=step_count,
                thought_type="reasoning",
                content="Evaluating analysis quality and calibrating confidence score...",
                phase=PHASE_NAME,
            )
        
        # Load prompt based on model config type (concise for reasoning models)
        config_type = state.get("config_type")
        prompt_template = load_phase_prompt(config_type=config_type)
        formatted_prompt = prompt_template.format(**context)
        
        # Call LLM with low temperature for consistent judgment
        # Uses model config from state if provided
        llm = get_llm(
            temperature=RERANKER_TEMPERATURE,
            model_id=state.get("model_id"),
            config_type=state.get("config_type"),
        )
        
        async with llm_breaker.call():
            response = await llm.ainvoke([HumanMessage(content=formatted_prompt)])
            
        response_text = get_response_text(response)
        
        # Parse and validate output
        parsed_data = extract_json_from_response(response_text)
        reranker_output = validate_reranker_output(parsed_data)
        
        logger.info(
            f"[RERANKER] Calibrated score: {reranker_output.calibrated_score}% "
            f"({reranker_output.tier}), flags: {reranker_output.quality_flags}"
        )
        
    except Exception as e:
        logger.warning(f"[RERANKER] LLM call failed, using fallback: {e}")
        errors.append(f"Reranker LLM error: {str(e)}")
        reranker_output = calculate_fallback_confidence(state)
    
    # Emit completion thought
    step_count += 1
    if callback:
        await callback.on_thought(
            step=step_count,
            thought_type="reasoning",
            content=f"Confidence calibrated: {reranker_output.calibrated_score}% ({reranker_output.tier}) - {reranker_output.justification}",
            phase=PHASE_NAME,
        )
    
    # Build summary and enriched metadata
    flags_str = f", {len(reranker_output.quality_flags)} quality flags" if reranker_output.quality_flags else ""
    summary = f"Calibrated confidence: {reranker_output.calibrated_score}% ({reranker_output.tier}){flags_str}"
    
    # Emit phase complete with enriched metadata
    if callback:
        enriched_data = {
            "calibrated_score": reranker_output.calibrated_score,
            "tier": reranker_output.tier,
            "quality_flags": reranker_output.quality_flags,
            "adjustment_rationale": reranker_output.adjustment_rationale,
            # Rich metadata for transparency
            "justification": reranker_output.justification[:200] if reranker_output.justification else None,
            "data_quality": reranker_output.data_quality,
            "reasoning_trace": reranker_output.reasoning_trace[:150] if reranker_output.reasoning_trace else None,
        }
        await callback.on_phase_complete(
            PHASE_NAME, 
            summary,
            data=enriched_data
        )
    
    return {
        "reranker_output": reranker_output.to_dict(),
        "current_phase": "generate_results",
        "step_count": step_count,
        "processing_errors": errors,
    }
