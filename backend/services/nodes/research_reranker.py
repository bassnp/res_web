"""
Research Re-Ranker Node - Phase 2B of the Fit Check Pipeline.

This module implements a research quality validation and DATA PRUNING layer that:
1. Evaluates the quality of Phase 2 (Deep Research) outputs
2. DETECTS bad data patterns (hallucinations, fabrications, inconsistencies)
3. PRUNES unreliable data elements before downstream processing
4. Determines routing: CONTINUE, ENHANCE_SEARCH, or EARLY_EXIT
5. Flags quality concerns for downstream transparency

Core Philosophy: BAD DATA IS WORSE THAN NO DATA
- Prune aggressively rather than pass garbage downstream
- Flag uncertainty explicitly rather than interpolate
- Early exit saves compute and prevents false confidence

This is the critical quality gate ensuring robust context before downstream
nodes attempt gap analysis, skills matching, and fit scoring.

Key Design Principles:
- LLM-as-a-Judge for nuanced quality assessment
- Aggressive data pruning for unreliable elements
- Explicit rubric for consistent evaluation
- Early exit for fabricated/garbage data
- Low temperature (0.1) for reproducible judgments

Gemini Optimization Applied:
- XML containerization for structured evaluation
- Criteria-based prompting (NO "think step-by-step")
- Post-hoc reasoning trace for audit trail
- Explicit behavioral constraints

Desire: Research Integrity & Garbage-In Prevention
The Research Re-Ranker is the data quality firewall. It ensures only
clean, verified, sufficient data proceeds to downstream analysis.
Bad data is pruned. Insufficient data triggers enhancement or early exit.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from langchain_core.messages import HumanMessage

from config.llm import get_llm
from services.pipeline_state import FitCheckPipelineState, Phase2Output
from services.callbacks import ThoughtCallback
from services.utils import get_response_text
from services.prompt_loader import load_prompt, PHASE_RESEARCH_RERANKER
from services.utils.parallel_scorer import (
    score_documents_parallel,
    calculate_adaptive_threshold,
)
from services.utils.source_classifier import classify_source, SourceType
from models.fit_check import DocumentScore, ScoringResult
from services.utils.circuit_breaker import llm_breaker, CircuitOpenError

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "research_reranker"
PHASE_DISPLAY = "Research Validation"

# Low temperature for consistent, calibrated judgments
RERANKER_TEMPERATURE = 0.1

# Timeout for this phase (in seconds) - informational
PHASE_TIMEOUT_SECONDS = 8

# Quality thresholds for heuristic pre-check
MIN_TECH_STACK_HIGH = 3
MIN_TECH_STACK_MEDIUM = 1
MIN_REQUIREMENTS_HIGH = 3
MIN_REQUIREMENTS_MEDIUM = 2
MIN_CULTURE_SIGNALS_HIGH = 2
MIN_EMPLOYER_SUMMARY_WORDS = 15


# =============================================================================
# Industry Inference Engine
# =============================================================================

INDUSTRY_TECH_DEFAULTS = {
    "fintech": {
        "core": ["Python", "Java", "Go"],
        "data": ["PostgreSQL", "Kafka", "Redis"],
        "infra": ["Kubernetes", "AWS", "Docker"],
        "signals": ["fintech", "financial", "payments", "banking", "compliance", "regulated"],
    },
    "ai_ml": {
        "core": ["Python", "C++"],
        "frameworks": ["PyTorch", "TensorFlow", "JAX", "Hugging Face"],
        "infra": ["CUDA", "Ray", "Kubernetes", "GPU"],
        "signals": ["ai", "ml", "machine learning", "deep learning", "models", "training", "llm"],
    },
    "saas_b2b": {
        "core": ["TypeScript", "Python", "Go"],
        "frontend": ["React", "Next.js", "Vue.js"],
        "infra": ["AWS", "GCP", "PostgreSQL", "Redis"],
        "signals": ["saas", "enterprise", "b2b", "subscription", "platform", "cloud"],
    },
    "e_commerce": {
        "core": ["Python", "Node.js", "Java", "PHP"],
        "frontend": ["React", "Vue.js"],
        "data": ["PostgreSQL", "MySQL", "Redis", "Elasticsearch"],
        "signals": ["e-commerce", "marketplace", "retail", "shopping", "checkout", "cart"],
    },
    "streaming_media": {
        "core": ["Java", "Scala", "Go", "Rust"],
        "data": ["Kafka", "Spark", "Cassandra", "Redis"],
        "infra": ["Kubernetes", "CDN", "AWS"],
        "signals": ["streaming", "media", "video", "audio", "content", "entertainment"],
    },
    "healthcare": {
        "core": ["Python", "Java", "C#"],
        "data": ["PostgreSQL", "MongoDB", "FHIR"],
        "infra": ["AWS", "Azure", "HIPAA"],
        "signals": ["healthcare", "health", "medical", "patient", "clinical", "hipaa"],
    },
    "gaming": {
        "core": ["C++", "C#", "Unity", "Unreal"],
        "backend": ["Go", "Node.js", "Python"],
        "infra": ["AWS", "GCP", "Redis"],
        "signals": ["gaming", "game", "esports", "mobile games", "unity", "unreal"],
    },
    "cybersecurity": {
        "core": ["Python", "Go", "Rust", "C"],
        "infra": ["Kubernetes", "AWS", "Linux"],
        "tools": ["Splunk", "SIEM", "IDS"],
        "signals": ["security", "cybersecurity", "infosec", "threat", "vulnerability"],
    },
}


def infer_industry_from_context(
    company_name: str,
    employer_summary: str,
    job_title: Optional[str] = None,
) -> Tuple[Optional[str], List[str]]:
    """
    Detect industry from available context to provide fallback tech assumptions.
    
    Uses keyword matching against known industry signals.
    
    Args:
        company_name: Name of the company.
        employer_summary: Summary text from Phase 2.
        job_title: Optional job title for additional context.
    
    Returns:
        Tuple of (industry_key, inferred_technologies).
        Returns (None, []) if no industry can be inferred.
    """
    # Combine all text for signal detection
    context_text = f"{company_name} {employer_summary} {job_title or ''}".lower()
    
    # Score each industry by signal matches
    industry_scores = {}
    for industry, config in INDUSTRY_TECH_DEFAULTS.items():
        signals = config.get("signals", [])
        score = sum(1 for signal in signals if signal in context_text)
        if score > 0:
            industry_scores[industry] = score
    
    if not industry_scores:
        return None, []
    
    # Get highest scoring industry
    best_industry = max(industry_scores, key=industry_scores.get)
    config = INDUSTRY_TECH_DEFAULTS[best_industry]
    
    # Collect representative technologies
    inferred_tech = []
    for category in ["core", "data", "infra", "frameworks", "frontend", "backend", "tools"]:
        if category in config:
            inferred_tech.extend(config[category][:2])  # Take top 2 from each category
    
    return best_industry, inferred_tech[:5]  # Limit to 5 inferred technologies


# =============================================================================
# Bad Data Detection Patterns
# =============================================================================

# Generic/vague terms that should be pruned from tech stack
GENERIC_TECH_TERMS = {
    "modern stack", "cloud", "databases", "web technologies", "modern technologies",
    "latest technologies", "cutting-edge", "best practices", "agile", "devops",
    "full stack", "backend", "frontend", "microservices", "api", "rest",
    "scalable", "distributed", "high performance", "enterprise", "solutions",
}

# Generic requirement phrases that indicate low-quality data
GENERIC_REQUIREMENT_PATTERNS = [
    r"must have experience",
    r"strong (communication|skills|background)",
    r"team player",
    r"fast-paced environment",
    r"passion for",
    r"self-starter",
    r"excellent (written|verbal)",
    r"ability to (work|learn|adapt)",
    r"problem.?solving",
    r"detail.?oriented",
]

# Platitude culture signals to prune
PLATITUDE_CULTURE_SIGNALS = {
    "innovative culture", "great benefits", "competitive salary", "work-life balance",
    "collaborative environment", "fast-growing", "exciting opportunity",
    "dynamic team", "cutting-edge", "industry leader", "best in class",
    "passionate team", "make an impact", "growth opportunities",
}

# Suspicious company name patterns (potential injection or fake)
SUSPICIOUS_NAME_PATTERNS = [
    r"ignore\s*ai",
    r"test\s*corp",
    r"fake\s*company",
    r"example\s*inc",
    r"acme\s*corp",
    r"<[^>]+>",  # HTML/XML tags
    r"\{[^}]+\}",  # Template variables
    r"prompt|inject|ignore|bypass|override",  # Injection keywords
]


def detect_bad_data_patterns(
    phase_2_output: Phase2Output,
    company_name: Optional[str],
) -> Dict[str, Any]:
    """
    Detect patterns indicating unreliable, fabricated, or low-quality data.
    
    This is a heuristic pre-filter before LLM evaluation.
    
    Args:
        phase_2_output: Output from Phase 2 Deep Research.
        company_name: Company name from Phase 1.
    
    Returns:
        Dict with detected bad data patterns and risk assessment.
    """
    patterns_detected = []
    risk_level = "LOW"
    
    tech_stack = phase_2_output.get("tech_stack", [])
    requirements = phase_2_output.get("identified_requirements", [])
    culture_signals = phase_2_output.get("culture_signals", [])
    employer_summary = phase_2_output.get("employer_summary", "")
    
    # Check for generic tech terms
    generic_tech_count = sum(
        1 for tech in tech_stack 
        if tech.lower() in GENERIC_TECH_TERMS
    )
    if generic_tech_count > 0:
        patterns_detected.append(f"GENERIC_TECH_TERMS:{generic_tech_count}")
    
    # Check for generic requirements
    generic_req_count = 0
    for req in requirements:
        req_lower = req.lower()
        for pattern in GENERIC_REQUIREMENT_PATTERNS:
            if re.search(pattern, req_lower):
                generic_req_count += 1
                break
    if generic_req_count > len(requirements) // 2:
        patterns_detected.append("MOSTLY_GENERIC_REQUIREMENTS")
    
    # Check for platitude culture signals
    platitude_count = sum(
        1 for signal in culture_signals
        if any(p in signal.lower() for p in PLATITUDE_CULTURE_SIGNALS)
    )
    if platitude_count > 0:
        patterns_detected.append(f"PLATITUDE_CULTURE:{platitude_count}")
    
    # Check for suspicious company name
    if company_name:
        company_lower = company_name.lower()
        for pattern in SUSPICIOUS_NAME_PATTERNS:
            if re.search(pattern, company_lower):
                patterns_detected.append("SUSPICIOUS_COMPANY_NAME")
                risk_level = "CRITICAL"
                break
    
    # Check for hallucination signals in summary
    summary_lower = employer_summary.lower()
    hallucination_signals = [
        "innovative company that",
        "leading provider of",
        "world-class",
        "state-of-the-art",
        "revolutionary",
    ]
    if any(sig in summary_lower for sig in hallucination_signals):
        if len(tech_stack) == 0:  # Vague praise with no specifics
            patterns_detected.append("HALLUCINATION_RISK")
            risk_level = "HIGH" if risk_level != "CRITICAL" else risk_level
    
    # Check for research failure indicators
    failure_indicators = [
        "unable to find",
        "no information available",
        "could not determine",
        "limited data",
        "insufficient information",
    ]
    if any(ind in summary_lower for ind in failure_indicators):
        patterns_detected.append("RESEARCH_FAILED")
    
    # Determine overall risk level
    if len(patterns_detected) >= 3:
        risk_level = "HIGH" if risk_level != "CRITICAL" else risk_level
    elif len(patterns_detected) >= 1 and risk_level == "LOW":
        risk_level = "MEDIUM"
    
    return {
        "patterns_detected": patterns_detected,
        "risk_level": risk_level,
        "generic_tech_count": generic_tech_count,
        "generic_req_count": generic_req_count,
        "platitude_count": platitude_count,
    }


def prune_low_quality_data(phase_2_output: Phase2Output) -> Dict[str, Any]:
    """
    Pre-prune obviously low-quality data elements before LLM evaluation.
    
    This provides a cleaner input for the LLM to evaluate.
    
    Args:
        phase_2_output: Output from Phase 2 Deep Research.
    
    Returns:
        Dict with pruned and retained data elements.
    """
    tech_stack = phase_2_output.get("tech_stack", [])
    requirements = phase_2_output.get("identified_requirements", [])
    culture_signals = phase_2_output.get("culture_signals", [])
    
    # Prune generic tech terms
    pruned_tech = []
    retained_tech = []
    for tech in tech_stack:
        if tech.lower() in GENERIC_TECH_TERMS:
            pruned_tech.append(tech)
        else:
            retained_tech.append(tech)
    
    # Prune generic requirements
    pruned_reqs = []
    retained_reqs = []
    for req in requirements:
        req_lower = req.lower()
        is_generic = any(
            re.search(pattern, req_lower) 
            for pattern in GENERIC_REQUIREMENT_PATTERNS
        )
        if is_generic and len(req.split()) < 10:  # Short generic phrases
            pruned_reqs.append(req)
        else:
            retained_reqs.append(req)
    
    # Prune platitude culture signals
    pruned_culture = []
    retained_culture = []
    for signal in culture_signals:
        if any(p in signal.lower() for p in PLATITUDE_CULTURE_SIGNALS):
            pruned_culture.append(signal)
        else:
            retained_culture.append(signal)
    
    return {
        "pruned_tech": pruned_tech,
        "retained_tech": retained_tech,
        "pruned_requirements": pruned_reqs,
        "retained_requirements": retained_reqs,
        "pruned_culture": pruned_culture,
        "retained_culture": retained_culture,
        "total_pruned": len(pruned_tech) + len(pruned_reqs) + len(pruned_culture),
    }


# =============================================================================
# Heuristic Quality Assessment
# =============================================================================

def assess_quality_heuristically(phase_2_output: Phase2Output) -> Dict[str, Any]:
    """
    Perform a quick heuristic assessment of research quality.
    
    This provides a baseline before LLM evaluation, useful for
    early exit decisions and providing context to the LLM judge.
    
    Args:
        phase_2_output: Output from Phase 2 Deep Research.
    
    Returns:
        Dict with heuristic scores and flags.
    """
    tech_stack = phase_2_output.get("tech_stack", [])
    requirements = phase_2_output.get("identified_requirements", [])
    culture_signals = phase_2_output.get("culture_signals", [])
    employer_summary = phase_2_output.get("employer_summary", "")
    
    # Pre-prune to get accurate counts
    pruned = prune_low_quality_data(phase_2_output)
    
    # Use post-prune counts for quality assessment
    tech_count = len(pruned["retained_tech"])
    req_count = len(pruned["retained_requirements"])
    culture_count = len(pruned["retained_culture"])
    summary_words = len(employer_summary.split())
    
    # Determine preliminary tier based on CLEANED data
    if tech_count >= MIN_TECH_STACK_HIGH and req_count >= MIN_REQUIREMENTS_HIGH:
        preliminary_tier = "HIGH"
        data_quality_tier = "CLEAN"
    elif tech_count >= MIN_TECH_STACK_MEDIUM and req_count >= MIN_REQUIREMENTS_MEDIUM:
        preliminary_tier = "MEDIUM"
        data_quality_tier = "PARTIAL"
    elif tech_count == 0 and req_count == 0:
        preliminary_tier = "INSUFFICIENT"
        data_quality_tier = "GARBAGE" if summary_words < 10 else "SPARSE"
    else:
        preliminary_tier = "LOW"
        data_quality_tier = "SPARSE"
    
    # Collect quality flags
    flags = []
    if tech_count < 2:
        flags.append("SPARSE_TECH_STACK")
    if req_count == 0:
        flags.append("NO_REQUIREMENTS")
    if culture_count == 0:
        flags.append("NO_CULTURE_SIGNALS")
    if summary_words < MIN_EMPLOYER_SUMMARY_WORDS:
        flags.append("SPARSE_SUMMARY")
    if pruned["total_pruned"] > 0:
        flags.append(f"DATA_PRUNED:{pruned['total_pruned']}")
    
    # Check for research failure patterns
    summary_lower = employer_summary.lower()
    if "unable to" in summary_lower or "limited information" in summary_lower:
        flags.append("RESEARCH_LIMITATIONS_NOTED")
    if "no results" in summary_lower or "could not find" in summary_lower:
        flags.append("SEARCH_FAILED")
        data_quality_tier = "GARBAGE"
    
    return {
        "tech_count": tech_count,
        "tech_count_raw": len(tech_stack),
        "requirements_count": req_count,
        "requirements_count_raw": len(requirements),
        "culture_count": culture_count,
        "summary_words": summary_words,
        "preliminary_tier": preliminary_tier,
        "data_quality_tier": data_quality_tier,
        "quality_flags": flags,
        "pruned_data": pruned,
    }


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt(config_type: str = None) -> str:
    """
    Load the Phase 2B XML prompt template based on model configuration.
    
    Args:
        config_type: Model config type ("reasoning" or "standard").
                     Reasoning models get concise prompts.
    
    Returns:
        str: XML-structured prompt template.
    """
    try:
        return load_prompt(PHASE_RESEARCH_RERANKER, config_type=config_type, prefer_concise=True)
    except FileNotFoundError:
        logger.warning(f"Phase 2B prompt not found, using embedded fallback")
        return _get_fallback_prompt()


def _get_fallback_prompt() -> str:
    """
    Embedded fallback prompt if file not found.
    
    Returns:
        str: Minimal prompt template for research quality validation.
    """
    return """<system_instruction>
  <agent_persona>Research Quality Auditor for employer intelligence validation.</agent_persona>
  <primary_objective>
    Evaluate Phase 2 research output quality and determine:
    1. Quality tier (HIGH/MEDIUM/LOW/INSUFFICIENT)
    2. Confidence score (0-100)
    3. Recommended action (CONTINUE/ENHANCE_SEARCH/FLAG_LOW_DATA)
    4. Company verifiability (VERIFIED/PARTIAL/UNVERIFIED/SUSPICIOUS)
  </primary_objective>
  <behavioral_constraints>
    <constraint>DO NOT pass insufficient data to downstream phases</constraint>
    <constraint>DO penalize sparse tech stack (fewer than 2 items)</constraint>
    <constraint>DO flag companies that cannot be verified</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <company_name>{company_name}</company_name>
  <heuristic_assessment>
    <tech_stack_count>{tech_count}</tech_stack_count>
    <tech_stack_items>{tech_stack_items}</tech_stack_items>
    <requirements_count>{req_count}</requirements_count>
    <requirements_items>{requirements_items}</requirements_items>
    <culture_signals_count>{culture_count}</culture_signals_count>
    <employer_summary_words>{summary_words}</employer_summary_words>
    <preliminary_tier>{preliminary_tier}</preliminary_tier>
    <preliminary_flags>{quality_flags}</preliminary_flags>
  </heuristic_assessment>
  <employer_summary>{employer_summary}</employer_summary>
</context_data>

<output_contract>
  Output strictly valid JSON:
  {{
    "research_quality_tier": "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT",
    "data_confidence_score": 0-100,
    "quality_flags": ["string"],
    "missing_data_categories": ["string"],
    "recommended_action": "CONTINUE" | "ENHANCE_SEARCH" | "FLAG_LOW_DATA",
    "enhancement_queries": ["string"],
    "company_verifiability": "VERIFIED" | "PARTIAL" | "UNVERIFIED" | "SUSPICIOUS",
    "reasoning_trace": "string"
  }}
</output_contract>"""


# =============================================================================
# JSON Parsing Utilities
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


def validate_reranker_output(data: Dict[str, Any], heuristics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize the reranker output with pruning data.
    
    Args:
        data: Raw parsed JSON from LLM.
        heuristics: Heuristic assessment including pruned data.
    
    Returns:
        Validated output dictionary with cleaned data.
    """
    # Validate data_quality_tier (new field for data triage)
    data_tier = data.get("data_quality_tier", "PARTIAL")
    if data_tier not in ["CLEAN", "PARTIAL", "SPARSE", "UNRELIABLE", "GARBAGE"]:
        data_tier = heuristics.get("data_quality_tier", "PARTIAL")
    
    # Validate research_quality_tier
    tier = data.get("research_quality_tier", "MEDIUM")
    if tier not in ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]:
        tier = "MEDIUM"
    
    # Validate data_confidence_score
    score = data.get("data_confidence_score", 50)
    if not isinstance(score, (int, float)):
        score = 50
    score = max(0, min(100, int(score)))
    
    # Validate quality_flags
    flags = data.get("quality_flags", [])
    if not isinstance(flags, list):
        flags = []
    flags = [str(f) for f in flags if f]
    
    # Validate missing_data_categories
    missing = data.get("missing_data_categories", [])
    if not isinstance(missing, list):
        missing = []
    missing = [str(m) for m in missing if m]
    
    # Validate recommended_action - now includes EARLY_EXIT
    action = data.get("recommended_action", "CONTINUE")
    valid_actions = ["CONTINUE", "CONTINUE_WITH_FLAGS", "ENHANCE_SEARCH", "EARLY_EXIT"]
    if action not in valid_actions:
        # Map old actions to new
        if action == "FLAG_LOW_DATA":
            action = "CONTINUE_WITH_FLAGS"
        else:
            action = "CONTINUE"
    
    # Force EARLY_EXIT for garbage data
    if data_tier == "GARBAGE" or tier == "INSUFFICIENT":
        action = "EARLY_EXIT"
    
    # Validate enhancement_queries
    queries = data.get("enhancement_queries", [])
    if not isinstance(queries, list):
        queries = []
    queries = [str(q) for q in queries if q]
    
    # Validate company_verifiability
    verifiability = data.get("company_verifiability", "PARTIAL")
    if verifiability not in ["VERIFIED", "PARTIAL", "UNVERIFIED", "SUSPICIOUS"]:
        verifiability = "PARTIAL"
    
    # If company is suspicious, escalate action
    if verifiability == "SUSPICIOUS" and action != "EARLY_EXIT":
        action = "EARLY_EXIT"
        if "SUSPICIOUS_COMPANY" not in flags:
            flags.append("SUSPICIOUS_COMPANY")
    
    # Validate early_exit_reason
    exit_reason = data.get("early_exit_reason", "")
    if not isinstance(exit_reason, str):
        exit_reason = ""
    if action == "EARLY_EXIT" and not exit_reason:
        exit_reason = "Insufficient or unreliable data for analysis"
    
    # Validate reasoning_trace
    reasoning = data.get("reasoning_trace", "Quality assessment completed.")
    if not isinstance(reasoning, str):
        reasoning = "Quality assessment completed."
    
    # Extract pruned/cleaned data from LLM output or use heuristic pruning
    pruned_data = data.get("pruned_data", {})
    cleaned_data = data.get("cleaned_data", {})
    
    # If LLM didn't provide cleaned data, use heuristic pruning
    if not cleaned_data and heuristics.get("pruned_data"):
        pruned = heuristics["pruned_data"]
        cleaned_data = {
            "verified_tech_stack": pruned.get("retained_tech", []),
            "verified_requirements": pruned.get("retained_requirements", []),
            "verified_culture_signals": pruned.get("retained_culture", []),
        }
        pruned_data = {
            "removed_tech_stack": pruned.get("pruned_tech", []),
            "removed_requirements": pruned.get("pruned_requirements", []),
            "removed_culture_signals": pruned.get("pruned_culture", []),
        }
    
    # Company verification details
    company_verification = data.get("company_verification", {})
    if not isinstance(company_verification, dict):
        company_verification = {
            "status": verifiability,
            "evidence": "",
            "risk_factors": [],
        }
    
    return {
        "data_quality_tier": data_tier,
        "research_quality_tier": tier,
        "data_confidence_score": score,
        "quality_flags": flags,
        "missing_data_categories": missing,
        "recommended_action": action,
        "enhancement_queries": queries,
        "company_verifiability": verifiability,
        "company_verification": company_verification,
        "pruned_data": pruned_data,
        "cleaned_data": cleaned_data,
        "early_exit_reason": exit_reason,
        "reasoning_trace": reasoning,
    }


# =============================================================================
# Enhancement Query Generation
# =============================================================================

def generate_enhancement_queries(
    company_name: Optional[str],
    job_title: Optional[str],
    inferred_industry: Optional[str],
) -> List[str]:
    """
    Generate enhanced search queries for a second research pass.
    
    These queries target alternative data sources like GitHub,
    LinkedIn, tech blogs, and Crunchbase.
    
    Args:
        company_name: Company name if known.
        job_title: Job title if known.
        inferred_industry: Industry inferred from context.
    
    Returns:
        List of enhanced search queries.
    """
    queries = []
    
    if company_name:
        # Alternative source queries
        queries.extend([
            f"{company_name} github engineering open source",
            f"{company_name} engineering blog technology",
            f"{company_name} linkedin engineering team",
            f"{company_name} crunchbase funding technology stack",
            f"{company_name} glassdoor engineer interview",
        ])
    
    if job_title and inferred_industry:
        # Industry-specific queries
        queries.append(f"{inferred_industry} {job_title} typical tech stack 2024")
    
    if job_title and not company_name:
        # Role-focused queries when no company
        queries.append(f"{job_title} job requirements skills 2024")
    
    return queries[:4]  # Limit to 4 enhancement queries


# =============================================================================
# Main Node Function
# =============================================================================

async def research_reranker_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 2B: RESEARCH_RERANKER - Research Quality Validation Node.
    
    Evaluates the quality of Phase 2 research output and determines
    whether the pipeline should continue, enhance search, or flag
    insufficient data.
    
    Args:
        state: Current pipeline state with Phase 2 output.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update dict with:
            - research_reranker_output: Quality assessment results
            - current_phase: Next phase based on routing decision
            - step_count: Incremented step counter
    
    SSE Events Emitted:
        - phase: "research_reranker" at start
        - thought (reasoning): Quality evaluation
        - phase_complete: With quality tier and action
    
    Routing Decisions:
        - HIGH/MEDIUM quality → continue to skeptical_comparison
        - LOW quality (first attempt) → trigger enhanced search
        - INSUFFICIENT or LOW (retry) → proceed with low_data_flag
    """
    logger.info("[RESEARCH_RERANKER] Starting phase 2B")
    step = state.get("step_count", 0)
    phase_2 = state.get("phase_2_output") or {}
    phase_1 = state.get("phase_1_output") or {}
    search_attempt = state.get("search_attempt", 1)
    
    # Emit phase start event
    if callback and hasattr(callback, 'on_phase'):
        await callback.on_phase(
            PHASE_NAME,
            "Validating research quality..."
        )
    elif callback:
        await callback.on_status(
            "validating",
            "Validating research quality..."
        )
    
    try:
        # NEW: Parallel AI scoring of raw search results
        raw_results = state.get("raw_search_results") or []
        scoring_result = None
        top_sources = []
        
        if raw_results:
            # Emit scoring start event
            if callback:
                await callback.on_thought(
                    step=step + 1,
                    thought_type="reasoning",
                    content=f"Scoring {len(raw_results)} sources with multi-dimensional AI evaluation...",
                    phase=PHASE_NAME,
                )
            
            # Parallel AI scoring
            scores = await score_documents_parallel(
                documents=raw_results,
                query=state.get("query", ""),
                max_concurrent=5,
            )
            
            if scores:
                # Calculate social media ratio
                social_count = sum(1 for s in scores if s.source_type == SourceType.SOCIAL_MEDIA)
                social_ratio = social_count / len(scores) if scores else 0.0
                
                # Calculate adaptive threshold
                threshold = calculate_adaptive_threshold(
                    total_results=len(raw_results),
                    social_media_ratio=social_ratio,
                )
                
                # Count passing sources
                passing_scores = [s for s in scores if s.final_score >= threshold]
                
                # Create scoring result
                scoring_result = ScoringResult(
                    scores=scores,
                    adaptive_threshold=threshold,
                    passing_count=len(passing_scores),
                    total_count=len(scores),
                    social_media_ratio=social_ratio,
                )
                
                # Sort by final score and take top 5
                top_sources = sorted(scores, key=lambda x: x.final_score, reverse=True)[:5]
                
                step += 1
                if callback:
                    await callback.on_thought(
                        step=step,
                        thought_type="reasoning",
                        content=f"Source scoring complete: {len(passing_scores)}/{len(scores)} sources passed quality gate (threshold: {threshold:.2f})",
                        phase=PHASE_NAME,
                    )

        # Perform heuristic assessment (legacy but still useful for tech/req counts)
        heuristics = assess_quality_heuristically(phase_2)
        
        # Update heuristics with AI scoring data if available
        if scoring_result:
            if scoring_result.passing_count >= 3:
                heuristics["preliminary_tier"] = "HIGH"
            elif scoring_result.passing_count >= 1:
                heuristics["preliminary_tier"] = "MEDIUM"
            else:
                heuristics["preliminary_tier"] = "LOW"
            
            heuristics["quality_flags"].append(f"AI_SCORING_PASSED_{scoring_result.passing_count}")
        
        # Attempt industry inference if tech stack is sparse
        inferred_industry = None
        inferred_tech = []
        if heuristics["tech_count"] < 2:
            company_name = phase_1.get("company_name", "")
            employer_summary = phase_2.get("employer_summary", "")
            job_title = phase_1.get("job_title")
            inferred_industry, inferred_tech = infer_industry_from_context(
                company_name, employer_summary, job_title
            )
            if inferred_industry:
                heuristics["inferred_industry"] = inferred_industry
                heuristics["inferred_tech"] = inferred_tech
        
        step += 1
        # Emit reasoning thought
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content=f"Assessing research quality: {heuristics['preliminary_tier']} tier detected",
                tool=None,
                tool_input=None,
                phase=PHASE_NAME,
            )
        
        # Load prompt based on model config type (concise for reasoning models)
        config_type = state.get("config_type")
        prompt_template = load_phase_prompt(config_type=config_type)
        
        # Get culture items for prompt
        culture_items = phase_2.get("culture_signals", [])
        
        prompt = prompt_template.format(
            original_query=state.get("query", ""),
            company_name=phase_1.get("company_name") or "Not specified",
            job_title=phase_1.get("job_title") or "Not specified",
            query_type=phase_1.get("query_type", "unknown"),
            tech_count=heuristics["tech_count"],
            tech_stack_items=", ".join(phase_2.get("tech_stack", [])) or "None",
            req_count=heuristics["requirements_count"],
            requirements_items=", ".join(phase_2.get("identified_requirements", [])[:5]) or "None",
            culture_count=heuristics["culture_count"],
            culture_items=", ".join(culture_items[:3]) or "None",
            summary_words=heuristics["summary_words"],
            preliminary_tier=heuristics["preliminary_tier"],
            quality_flags=", ".join(heuristics["quality_flags"]) or "None",
            employer_summary=phase_2.get("employer_summary", "No summary available"),
            data_quality=phase_2.get("data_quality", "unknown"),
            search_queries=", ".join(phase_2.get("search_queries_used", [])) or "None",
            search_attempt=search_attempt,
            inferred_industry=inferred_industry or "Unknown",
            inferred_tech=", ".join(inferred_tech) if inferred_tech else "None",
        )
        
        # Get LLM for evaluation
        # Uses model config from state if provided
        llm = get_llm(
            streaming=False,
            temperature=RERANKER_TEMPERATURE,
            model_id=state.get("model_id"),
            config_type=state.get("config_type"),
        )
        
        # Invoke LLM
        messages = [HumanMessage(content=prompt)]
        
        async with llm_breaker.call():
            response = await llm.ainvoke(messages)
        
        # Extract and validate response
        response_text = get_response_text(response)
        logger.debug(f"[RESEARCH_RERANKER] Raw LLM response: {response_text[:300]}...")
        
        parsed_data = extract_json_from_response(response_text)
        validated_output = validate_reranker_output(parsed_data, heuristics)
        
        # Generate enhancement queries if action is ENHANCE_SEARCH
        if validated_output["recommended_action"] == "ENHANCE_SEARCH":
            if not validated_output["enhancement_queries"]:
                validated_output["enhancement_queries"] = generate_enhancement_queries(
                    phase_1.get("company_name"),
                    phase_1.get("job_title"),
                    inferred_industry,
                )
        
        # Detect bad data patterns
        bad_data = detect_bad_data_patterns(phase_2, phase_1.get("company_name"))
        if bad_data["risk_level"] == "CRITICAL":
            heuristics["quality_flags"].append("CRITICAL_DATA_RISK")
        
        # Add inferred data to output if applicable
        if inferred_industry:
            if "INFERRED_INDUSTRY" not in validated_output["quality_flags"]:
                validated_output["quality_flags"].append("INFERRED_INDUSTRY")
        
        # Add bad data detection flags
        for pattern in bad_data["patterns_detected"]:
            if pattern not in validated_output["quality_flags"]:
                validated_output["quality_flags"].append(pattern)
        
        # Determine next phase based on routing logic
        tier = validated_output["research_quality_tier"]
        data_tier = validated_output.get("data_quality_tier", "PARTIAL")
        action = validated_output["recommended_action"]
        
        # NEW: Integrate AI scoring into routing decision
        is_sufficient = False
        if scoring_result:
            is_sufficient = scoring_result.passing_count >= 3
            
            # If no sources passed AI scoring, force ENHANCE_SEARCH or EARLY_EXIT
            if scoring_result.passing_count == 0:
                if search_attempt < 3:
                    action = "ENHANCE_SEARCH"
                else:
                    action = "EARLY_EXIT"
                    validated_output["early_exit_reason"] = "No high-quality sources found after 3 search attempts."
            
            # If very few sources passed, ensure we flag it
            elif scoring_result.passing_count < 3 and action == "CONTINUE":
                action = "ENHANCE_SEARCH" if search_attempt < 3 else "CONTINUE_WITH_FLAGS"
                if "LOW_SOURCE_COUNT" not in validated_output["quality_flags"]:
                    validated_output["quality_flags"].append("LOW_SOURCE_COUNT")
        
        # CRITICAL: Early exit for garbage/suspicious data
        if action == "EARLY_EXIT" or data_tier == "GARBAGE":
            next_phase = "generate_results"  # Skip to final with early exit message
            low_data_flag = True
            early_exit = True
        elif is_sufficient and action in ["CONTINUE", "CONTINUE_WITH_FLAGS"]:
            next_phase = "content_enrich"
            low_data_flag = action == "CONTINUE_WITH_FLAGS"
            early_exit = False
        elif action == "ENHANCE_SEARCH" and search_attempt < 3:
            next_phase = "deep_research"  # Will be handled by conditional routing
            low_data_flag = False
            early_exit = False
            # INCREMENT search_attempt to prevent infinite loop
            search_attempt += 1
        elif action in ["CONTINUE", "CONTINUE_WITH_FLAGS"]:
            # Proceed to enrichment even if not fully sufficient if we've exhausted retries
            next_phase = "content_enrich" if top_sources else "skeptical_comparison"
            low_data_flag = True
            early_exit = False
        else:
            # INSUFFICIENT or exhausted retries - continue but flagged
            next_phase = "skeptical_comparison"
            low_data_flag = True
            early_exit = False
        
        # Build completion summary
        scoring_summary = f" | AI Scores: {scoring_result.passing_count}/{scoring_result.total_count}" if scoring_result else ""
        summary = f"Data: {data_tier} | Quality: {tier} | Confidence: {validated_output['data_confidence_score']}% | Action: {action}{scoring_summary}"
        
        # Emit phase complete event
        if callback and hasattr(callback, 'on_phase_complete'):
            await callback.on_phase_complete(PHASE_NAME, summary)
        
        logger.info(f"[RESEARCH_RERANKER] Phase 2B complete: {summary}")
        
        return {
            "research_reranker_output": validated_output,
            "current_phase": next_phase,
            "step_count": step,
            "low_data_flag": low_data_flag,
            "early_exit": early_exit,
            "search_attempt": search_attempt,  # Pass updated attempt count to state
            "scoring_result": scoring_result,
            "top_sources": top_sources,
        }
        
    except Exception as e:
        logger.error(f"[RESEARCH_RERANKER] Phase 2B failed: {e}", exc_info=True)
        
        # Fallback to heuristic-based decision
        heuristics = assess_quality_heuristically(phase_2)
        bad_data = detect_bad_data_patterns(phase_2, phase_1.get("company_name"))
        
        # Determine if we should early exit based on heuristics
        is_garbage = heuristics["data_quality_tier"] == "GARBAGE"
        is_critical_risk = bad_data["risk_level"] == "CRITICAL"
        
        fallback_output = {
            "data_quality_tier": heuristics["data_quality_tier"],
            "research_quality_tier": heuristics["preliminary_tier"],
            "data_confidence_score": 30 if is_garbage else 50,
            "quality_flags": heuristics["quality_flags"] + ["EVALUATION_ERROR"] + bad_data["patterns_detected"],
            "missing_data_categories": [],
            "recommended_action": "EARLY_EXIT" if (is_garbage or is_critical_risk) else "CONTINUE_WITH_FLAGS",
            "enhancement_queries": [],
            "company_verifiability": "SUSPICIOUS" if is_critical_risk else "PARTIAL",
            "company_verification": {},
            "pruned_data": heuristics.get("pruned_data", {}),
            "cleaned_data": {},
            "early_exit_reason": "Data quality too low for reliable analysis" if is_garbage else "",
            "reasoning_trace": f"Fallback assessment due to evaluation error: {str(e)[:100]}",
        }
        
        # Emit phase complete with degradation notice
        if callback and hasattr(callback, 'on_phase_complete'):
            await callback.on_phase_complete(
                PHASE_NAME,
                f"Data: {fallback_output['data_quality_tier']} | Quality: {fallback_output['research_quality_tier']} (fallback)"
            )
        
        return {
            "research_reranker_output": fallback_output,
            "current_phase": "generate_results" if (is_garbage or is_critical_risk) else "skeptical_comparison",
            "step_count": step,
            "low_data_flag": True,
            "early_exit": is_garbage or is_critical_risk,
            "search_attempt": search_attempt + 1,  # Increment to prevent retry loops on errors
            "processing_errors": state.get("processing_errors", []) + [f"Phase 2B error: {str(e)}"],
            "scoring_result": None,
            "top_sources": [],
        }
