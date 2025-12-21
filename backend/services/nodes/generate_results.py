"""
Generate Results Node - Phase 5 of the Fit Check Pipeline.

This module implements the final response generation node that:
1. Synthesizes all prior phase outputs into a cohesive narrative
2. Generates streaming markdown response to the frontend
3. Ensures honest acknowledgment of gaps from skeptical analysis
4. Creates compelling, personalized pitch tailored to employer context

Gemini Optimization Applied:
- Uses XML-structured prompt with tone calibration
- Criteria-based success metrics (not inline CoT)
- Streams response chunks via callback for real-time frontend updates
- Evidence-based constraints prevent generic output
- Reasoning trace as post-hoc verification, not generation
- Temperature 0.7 for creative but controlled output

Desire: Actionable Insight & Honest Synthesis
The Generate Results agent is the career advisor and technical writer.
Its desire is to synthesize rigorous analysis into a compelling narrative
that is both persuasive AND honest. It must not ignore gaps and must
reference specific findings to avoid generic template output.

This is the ONLY phase that streams response chunks to the frontend.
All prior phases emit structured JSON; this phase emits visible response.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from langchain_core.messages import HumanMessage

from config.llm import get_llm, with_llm_throttle_stream
from services.pipeline_state import FitCheckPipelineState
from services.callbacks import ThoughtCallback
from services.utils import extract_text_from_content
from services.prompt_loader import load_prompt, PHASE_GENERATE_RESULTS
from services.utils.circuit_breaker import llm_breaker, CircuitOpenError

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "generate_results"
PHASE_DISPLAY = "Generate Results"

# Creative temperature for compelling narrative generation
GENERATION_TEMPERATURE = 0.7

# Maximum response word count for validation
MAX_RESPONSE_WORDS = 400

# Timeout for this phase (in seconds) - informational
PHASE_TIMEOUT_SECONDS = 20


# =============================================================================
# Context Formatting Utilities
# =============================================================================

def format_matched_skills_summary(phase_4: Dict[str, Any]) -> str:
    """
    Format matched requirements into readable summary for prompt injection.
    
    Creates a bullet list of matched skills with their confidence percentages,
    ready for the LLM to reference in the final response.
    
    Args:
        phase_4: Phase 4 output dictionary with matched_requirements.
    
    Returns:
        Formatted string with skill matches and confidence levels.
    
    Example Output:
        - Python: Matched with Python expertise (90% confidence)
        - React: Matched with React/Next.js experience (85% confidence)
    """
    matched = phase_4.get("matched_requirements") or []
    
    if not matched:
        return "No specific skill matches identified."
    
    lines = []
    # Limit to top 5 matches to prevent prompt bloat
    for match in matched[:5]:
        requirement = match.get("requirement", "Unknown")
        matched_skill = match.get("matched_skill", "general experience")
        confidence = match.get("confidence", 0.5)
        confidence_pct = int(float(confidence) * 100)
        
        lines.append(
            f"- {requirement}: Matched with {matched_skill} ({confidence_pct}% confidence)"
        )
    
    if len(matched) > 5:
        lines.append(f"- ... and {len(matched) - 5} additional matches")
    
    return "\n".join(lines)


def format_gaps_for_prompt(phase_3: Dict[str, Any]) -> str:
    """
    Format genuine gaps from skeptical analysis for prompt injection.
    
    Args:
        phase_3: Phase 3 output dictionary with genuine_gaps.
    
    Returns:
        Formatted string listing gaps that MUST be acknowledged.
    """
    gaps = phase_3.get("genuine_gaps") or []
    
    if not gaps:
        return "No significant gaps identified (unusual - review analysis)."
    
    return "\n".join(f"- {gap}" for gap in gaps)


def format_strengths_for_prompt(phase_3: Dict[str, Any]) -> str:
    """
    Format genuine strengths from skeptical analysis for prompt injection.
    
    Args:
        phase_3: Phase 3 output dictionary with genuine_strengths.
    
    Returns:
        Formatted string listing verified strengths.
    """
    strengths = phase_3.get("genuine_strengths") or []
    
    if not strengths:
        return "Strengths to be highlighted from skill matching."
    
    return "\n".join(f"- {strength}" for strength in strengths)


def format_transferable_skills(phase_3: Dict[str, Any]) -> str:
    """
    Format transferable skills from skeptical analysis.
    
    Args:
        phase_3: Phase 3 output dictionary with transferable_skills.
    
    Returns:
        Formatted string or default message.
    """
    skills = phase_3.get("transferable_skills") or []
    
    if not skills:
        return "None specifically identified"
    
    return ", ".join(str(s) for s in skills)


def detect_employer_context(phase_2: Dict[str, Any], phase_1: Dict[str, Any]) -> str:
    """
    Detect employer context type for tone calibration.
    
    Analyzes employer summary, culture signals, and tech stack to determine
    the appropriate tone for the response (startup, enterprise, AI/ML, fintech).
    
    Args:
        phase_2: Phase 2 employer intelligence output.
        phase_1: Phase 1 classification output.
    
    Returns:
        Context type string: "startup", "enterprise", "ai_ml", "fintech", or "default".
    """
    summary = (phase_2.get("employer_summary") or "").lower()
    culture = " ".join(phase_2.get("culture_signals") or []).lower()
    tech = " ".join(phase_2.get("tech_stack") or []).lower()
    
    combined = f"{summary} {culture} {tech}"
    
    # Priority order detection - check most specific contexts first
    if any(kw in combined for kw in ["ai", "ml", "machine learning", "llm", "deep learning", "gpt", "neural"]):
        return "ai_ml"
    if any(kw in combined for kw in ["fintech", "finance", "payment", "banking", "trading", "financial"]):
        return "fintech"
    if any(kw in combined for kw in ["startup", "early stage", "seed", "series a", "series b", "fast-paced", "scrappy"]):
        return "startup"
    if any(kw in combined for kw in ["enterprise", "fortune 500", "large scale", "global", "multinational", "established"]):
        return "enterprise"
    
    return "default"


def get_company_or_role(phase_1: Dict[str, Any], original_query: str) -> str:
    """
    Extract company name or role for response personalization.
    
    Args:
        phase_1: Phase 1 classification output.
        original_query: Original user query as fallback.
    
    Returns:
        Company name, job title, or truncated query.
    """
    if phase_1.get("company_name"):
        return phase_1["company_name"]
    if phase_1.get("job_title"):
        return phase_1["job_title"]
    # Fallback: use first 50 chars of query
    return original_query[:50] if len(original_query) > 50 else original_query


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt(config_type: str = None) -> str:
    """
    Load the Phase 5 XML prompt template based on model configuration.
    
    Args:
        config_type: Model config type ("reasoning" or "standard").
                     Reasoning models get concise prompts.
    
    Returns:
        str: XML-structured prompt template.
    """
    try:
        return load_prompt(PHASE_GENERATE_RESULTS, config_type=config_type, prefer_concise=True)
    except FileNotFoundError:
        logger.warning(f"Phase 5 prompt not found, using embedded fallback")
        return _get_fallback_prompt()


def _get_fallback_prompt() -> str:
    """
    Embedded fallback prompt if file not found.
    
    Returns:
        str: Minimal prompt template for response generation.
    """
    return """<system_instruction>
  <agent_persona>Career Advisor and Technical Writer</agent_persona>
  <primary_objective>
    Generate a compelling, honest fit analysis using SPECIFIC evidence from the analysis.
    MUST acknowledge at least one gap. Keep under 400 words.
  </primary_objective>
  <behavioral_constraints>
    <constraint>DO NOT use generic phrases without context</constraint>
    <constraint>DO NOT ignore gaps from skeptical analysis</constraint>
    <constraint>DO NOT exceed 400 words</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <query_context>
    Company/Role: {company_or_role}
    Context Type: {employer_context_type}
  </query_context>
  <employer_intelligence>
    Summary: {employer_summary}
    Tech Stack: {tech_stack}
    Culture: {culture_signals}
  </employer_intelligence>
  <fit_analysis>
    Match Score: {match_score}%
    Matched Skills: {matched_skills_summary}
    Gaps (MUST acknowledge): {genuine_gaps}
    Transferable Skills: {transferable_skills}
    Strengths: {genuine_strengths}
  </fit_analysis>
</context_data>

<output_template>
### Why I'm a Great Fit for [Company/Position]

**At a Glance:** [Match score and key strength]

**Where I Align:**
- [Specific match]
- [Specific match]

**What I Bring:**
[Specific skills and projects]

**The Learning Curve:**
[Honest gap acknowledgment]

**Let's Connect:**
[Personalized call to action]
</output_template>"""


# =============================================================================
# Response Quality Validation
# =============================================================================

def validate_response_quality(response: str, phase_3: Dict[str, Any]) -> List[str]:
    """
    Validate that the generated response meets quality criteria.
    
    Performs post-generation quality checks:
    1. Word count within limit
    2. Gap acknowledgment present
    3. Generic phrase detection
    
    Args:
        response: Generated response text.
        phase_3: Phase 3 output with gaps to check for acknowledgment.
    
    Returns:
        List of warning strings if quality issues detected, empty if all good.
    """
    warnings: List[str] = []
    
    # Check word count
    word_count = len(response.split())
    if word_count > MAX_RESPONSE_WORDS:
        warnings.append(f"Response exceeds {MAX_RESPONSE_WORDS} words: {word_count} words")
    
    # Check for gap acknowledgment
    gaps = phase_3.get("genuine_gaps") or []
    response_lower = response.lower()
    
    gap_acknowledged = False
    
    # Check if any significant words from gaps appear in response
    for gap in gaps:
        # Extract meaningful words (5+ chars) from gap
        gap_words = [w.lower() for w in gap.split() if len(w) > 4]
        if any(word in response_lower for word in gap_words):
            gap_acknowledged = True
            break
    
    # Also check for "growth areas" or "learning curve" section
    learning_keywords = ["growth", "learning", "ramp", "curve", "opportunity", "develop"]
    if any(kw in response_lower for kw in learning_keywords):
        gap_acknowledged = True
    
    if not gap_acknowledged and gaps:
        warnings.append(
            f"Response may not acknowledge gaps from Phase 3: {gaps[:2]}"
        )
    
    # Check for generic phrases that indicate low-quality output
    generic_phrases = [
        "passionate about technology",
        "excited about this opportunity", 
        "great culture fit",
        "perfect match for this role",
        "believe in your mission",
        "my extensive experience",
    ]
    for phrase in generic_phrases:
        if phrase in response_lower:
            warnings.append(f"Generic phrase detected: '{phrase}'")
    
    return warnings


def generate_fallback_response(
    company_or_role: str,
    phase_4: Dict[str, Any],
    reranker: Dict[str, Any],
    error_message: str,
) -> str:
    """
    Generate a minimal fallback response when LLM fails.
    
    This ensures the user always gets some response, even if limited.
    
    Args:
        company_or_role: Company name or job title.
        phase_4: Phase 4 output for match score if available.
        reranker: Reranker output for calibrated score if available.
        error_message: The error that occurred.
    
    Returns:
        Fallback markdown response.
    """
    # Prefer calibrated score from reranker
    calibrated_score = reranker.get("calibrated_score") if reranker else None
    if calibrated_score is not None:
        score_pct = int(calibrated_score)
        tier = reranker.get("tier", "MEDIUM")
    else:
        match_score = (phase_4.get("overall_match_score") if phase_4 else None) or 0.5
        try:
            score_pct = int(float(match_score) * 100)
        except (ValueError, TypeError):
            score_pct = 50
        tier = "MEDIUM"
    
    return f"""### Fit Analysis for {company_or_role}

I apologize, but I encountered an issue generating a complete personalized analysis. 
Based on the research conducted, here's a brief summary:

**At a Glance:** {score_pct}% overall match ({tier} confidence) based on available data.

**Key Points:**
- Technical background aligns with general software engineering requirements
- Further conversation would help identify specific alignment areas

**Next Steps:**
I'd be happy to discuss my background and how it might fit your needs in more detail.

*Note: This response was generated with limited analysis due to a processing error.*
"""


# =============================================================================
# Main Node Function
# =============================================================================

async def generate_results_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 5: GENERATE_RESULTS - Final Response Generation Node.
    
    Synthesizes all prior phase outputs into a streaming markdown response
    that will be displayed directly to the user.
    
    This is the ONLY phase that streams response chunks. All prior phases
    emit structured JSON silently; this phase produces visible output.
    
    Args:
        state: Current pipeline state with all prior phase outputs.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update dictionary containing:
        - final_response: Generated markdown response
        - step_count: Updated step count
        - processing_errors: Any non-fatal warnings (e.g., quality issues)
    
    Emits Events (via callback):
        - phase: "generate_results" at start
        - thought (reasoning): For synthesis step
        - response: Streaming chunks of the final response
        - phase_complete: When done with word count summary
    
    Graceful Degradation:
        On LLM failure, returns a minimal fallback response rather than
        crashing the pipeline. User always gets something.
    """
    logger.info("[GENERATE_RESULTS] Starting phase 5 - FINAL SYNTHESIS")
    
    # Initialize from state
    step = state.get("step_count", 0) + 1

    # Check for abort flag from prior phases
    if state.get("should_abort"):
        abort_reason = state.get("abort_reason", "An unexpected error occurred.")
        logger.warning(f"[GENERATE_RESULTS] Aborting due to prior error: {abort_reason}")
        
        # Stream error message as response
        error_response = f"### Analysis Interrupted\n\nI'm sorry, but I encountered an issue that prevents me from completing the full analysis.\n\n**Reason:** {abort_reason}\n\nPlease try again later or with a different query."
        
        if callback:
            await callback.on_response_chunk(error_response)
        if hasattr(callback, 'on_phase_complete'):
            await callback.on_phase_complete(
                PHASE_NAME, 
                "Aborted due to error",
                data={"error": str(e), "is_fallback": True}
            )
        
        return {
            "final_response": error_response,
            "step_count": step,
        }

    phase_1 = state.get("phase_1_output") or {}
    phase_2 = state.get("phase_2_output") or {}
    phase_3 = state.get("phase_3_output") or {}
    phase_4 = state.get("phase_4_output") or {}
    reranker = state.get("reranker_output") or {}
    errors: List[str] = list(state.get("processing_errors") or [])
    
    # Extract key identifiers
    company_or_role = get_company_or_role(phase_1, state["query"])
    employer_context = detect_employer_context(phase_2, phase_1)
    
    # Emit phase start event
    if callback and hasattr(callback, 'on_phase'):
        await callback.on_phase(
            PHASE_NAME,
            "Generating personalized fit analysis..."
        )
    elif callback:
        await callback.on_status(
            "generating",
            "Generating personalized fit analysis..."
        )
    
    try:
        # =====================================================================
        # Format context for prompt - Use RERANKER output for confidence
        # =====================================================================
        # Use calibrated score from reranker, fall back to raw score
        calibrated_score = reranker.get("calibrated_score")
        if calibrated_score is not None:
            match_score_pct = int(calibrated_score)
        else:
            match_score = phase_4.get("overall_match_score") or 0.5
            try:
                match_score_pct = int(float(match_score) * 100)
            except (ValueError, TypeError):
                match_score_pct = 50
        
        confidence_tier = reranker.get("tier", "MEDIUM")
        confidence_justification = reranker.get("justification", "")
        quality_flags = reranker.get("quality_flags", [])
        data_quality = reranker.get("data_quality", {})
        
        # Format quality flags and data quality for prompt
        quality_flags_str = ", ".join(quality_flags) if quality_flags else "None"
        data_quality_notes = "; ".join(
            f"{k}: {v}" for k, v in data_quality.items()
        ) if data_quality else "Data quality assessment not available"
        
        # Emit reasoning thought
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content=f"Synthesizing {match_score_pct}% match ({confidence_tier}) into personalized narrative for {company_or_role}...",
                phase=PHASE_NAME,
            )
        
        # Load prompt based on model config type (concise for reasoning models)
        config_type = state.get("config_type")
        prompt_template = load_phase_prompt(config_type=config_type)
        prompt = prompt_template.format(
            query_type=phase_1.get("query_type", "unknown"),
            company_or_role=company_or_role,
            employer_context_type=employer_context,
            employer_summary=phase_2.get("employer_summary") or "No summary available",
            tech_stack=", ".join(phase_2.get("tech_stack") or []) or "Not identified",
            culture_signals=", ".join(phase_2.get("culture_signals") or []) or "Not identified",
            calibrated_score=match_score_pct,
            confidence_tier=confidence_tier,
            confidence_justification=confidence_justification,
            quality_flags=quality_flags_str,
            data_quality_notes=data_quality_notes,
            matched_skills_summary=format_matched_skills_summary(phase_4),
            genuine_gaps=format_gaps_for_prompt(phase_3),
            transferable_skills=format_transferable_skills(phase_3),
            risk_assessment=phase_3.get("risk_assessment", "medium"),
            genuine_strengths=format_strengths_for_prompt(phase_3),
        )
        
        # =====================================================================
        # Stream response from LLM
        # =====================================================================
        # Uses model config from state if provided
        llm = get_llm(
            streaming=True,
            temperature=GENERATION_TEMPERATURE,
            model_id=state.get("model_id"),
            config_type=state.get("config_type"),
        )
        messages = [HumanMessage(content=prompt)]
        
        full_response = ""
        
        async with llm_breaker.call():
            async for chunk in with_llm_throttle_stream(llm.astream(messages)):
                # Extract text content from chunk (handles Gemini's structured format)
                chunk_content = chunk.content if hasattr(chunk, 'content') else chunk
                chunk_text = extract_text_from_content(chunk_content)
                
                if chunk_text:
                    full_response += chunk_text
                    
                    # Stream chunk to frontend
                    if callback:
                        await callback.on_response_chunk(chunk_text)
        
        # =====================================================================
        # Validate response quality
        # =====================================================================
        validation_warnings = validate_response_quality(full_response, phase_3)
        
        if validation_warnings:
            logger.warning(f"[GENERATE_RESULTS] Quality warnings: {validation_warnings}")
            # Add warnings to processing errors for visibility
            for warning in validation_warnings:
                errors.append(f"Quality: {warning}")
        
        # =====================================================================
        # Emit phase complete with enriched metadata
        # =====================================================================
        word_count = len(full_response.split())
        
        if callback and hasattr(callback, 'on_phase_complete'):
            enriched_data = {
                "word_count": word_count,
                "char_count": len(full_response),
                "quality_warnings": validation_warnings,
                # Rich metadata for transparency
                "employer_context_type": employer_context,
                "calibrated_score": match_score_pct,
                "confidence_tier": confidence_tier,
                "gaps_acknowledged": len(phase_3.get("genuine_gaps", [])),
                "response_preview": full_response[:100] + "..." if len(full_response) > 100 else full_response,
            }
            await callback.on_phase_complete(
                PHASE_NAME,
                f"Generated {word_count} word response",
                data=enriched_data
            )
        
        logger.info(
            f"[GENERATE_RESULTS] Phase 5 complete: {len(full_response)} chars, "
            f"{word_count} words, {len(validation_warnings)} quality warnings"
        )
        
        return {
            "final_response": full_response,
            "step_count": step,
            "processing_errors": errors if errors else state.get("processing_errors", []),
        }
        
    except Exception as e:
        logger.error(f"[GENERATE_RESULTS] Phase 5 failed: {e}", exc_info=True)
        
        # Generate minimal fallback response
        fallback_response = generate_fallback_response(
            company_or_role=company_or_role,
            phase_4=phase_4,
            reranker=reranker,
            error_message=str(e),
        )
        
        # Stream fallback to frontend
        if callback:
            await callback.on_response_chunk(fallback_response)
            
            if hasattr(callback, 'on_phase_complete'):
                await callback.on_phase_complete(
                    PHASE_NAME,
                    "Generated fallback response due to error",
                    data={"is_fallback": True, "error": str(e)}
                )
        
        errors.append(f"Phase 5 error: {str(e)}")
        
        return {
            "final_response": fallback_response,
            "step_count": step,
            "processing_errors": errors,
        }
