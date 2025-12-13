"""
Pipeline State Definitions for the Fit Check Agent.

This module defines the TypedDict state schemas for the 5-phase
LangGraph pipeline that powers the Fit Check analysis.

State Flow:
    START → CONNECTING → DEEP_RESEARCH → SKEPTICAL_COMPARISON → 
    SKILLS_MATCHING → GENERATE_RESULTS → END

Each phase reads from and writes to specific fields in FitCheckPipelineState,
enabling structured context handoff between phases.
"""

from typing import TypedDict, Optional, List, Dict, Literal, Any, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


# =============================================================================
# Phase Output Type Definitions
# =============================================================================

class Phase1Output(TypedDict):
    """
    Output from Phase 1: CONNECTING Node.
    
    Classifies the user query and extracts structured entities
    for downstream processing.
    
    Attributes:
        query_type: Classification as "company", "job_description", or "irrelevant".
        company_name: Extracted company name if present.
        job_title: Extracted job title/role if present.
        extracted_skills: List of technical skills mentioned in query.
        reasoning_trace: Post-hoc explanation of classification logic.
    """
    query_type: Literal["company", "job_description", "irrelevant"]
    company_name: Optional[str]
    job_title: Optional[str]
    extracted_skills: List[str]
    reasoning_trace: str


class Phase2Output(TypedDict):
    """
    Output from Phase 2: DEEP_RESEARCH Node.
    
    Contains synthesized employer intelligence from web research.
    
    Attributes:
        employer_summary: Concise summary of the employer/role.
        identified_requirements: Explicit job requirements found.
        tech_stack: Technologies used by the employer.
        culture_signals: Cultural indicators and values.
        search_queries_used: Queries executed during research.
        reasoning_trace: Explanation of research synthesis.
    """
    employer_summary: str
    identified_requirements: List[str]
    tech_stack: List[str]
    culture_signals: List[str]
    search_queries_used: List[str]
    reasoning_trace: str


class Phase3Output(TypedDict):
    """
    Output from Phase 3: SKEPTICAL_COMPARISON Node.
    
    Critical analysis of candidate-employer fit gaps.
    
    Attributes:
        genuine_strengths: Real alignment points with evidence.
        genuine_gaps: Honest gaps between candidate and requirements.
        unverified_claims: Claims made without supporting evidence.
        transferable_skills: Skills that could bridge gaps.
        risk_assessment: Overall risk level of fit.
        risk_justification: Specific explanation of the risk level.
        reasoning_trace: Devil's advocate reasoning.
    """
    genuine_strengths: List[str]
    genuine_gaps: List[str]
    unverified_claims: List[str]
    transferable_skills: List[str]
    risk_assessment: Literal["low", "medium", "high"]
    risk_justification: str
    reasoning_trace: str


class Phase4Output(TypedDict):
    """
    Output from Phase 4: SKILLS_MATCHING Node.
    
    Structured skill-to-requirement mapping.
    
    Attributes:
        matched_requirements: Requirements matched to candidate skills.
        unmatched_requirements: Requirements with no direct skill match.
        overall_match_score: Quantified match percentage (0.0-1.0).
        reasoning_trace: Technical recruiter's analysis.
    """
    matched_requirements: List[Dict[str, Any]]  # [{requirement, matched_skill, confidence}]
    unmatched_requirements: List[str]
    overall_match_score: float
    reasoning_trace: str


class RerankerOutput(TypedDict):
    """
    Output from Phase 5B: CONFIDENCE_RERANKER Node.
    
    LLM-as-a-Judge calibrated confidence assessment.
    
    Attributes:
        calibrated_score: Adjusted confidence score (0-100).
        tier: Confidence tier (HIGH/MEDIUM/LOW/INSUFFICIENT_DATA).
        justification: Brief explanation of the confidence level.
        quality_flags: List of quality concern flags.
        data_quality: Assessment of data quality across phases.
        adjustment_rationale: How/why this differs from raw score.
        reasoning_trace: Post-hoc evaluation logic summary.
    """
    calibrated_score: int
    tier: Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT_DATA"]
    justification: str
    quality_flags: List[str]
    data_quality: Dict[str, str]
    adjustment_rationale: str
    reasoning_trace: str


class ResearchRerankerOutput(TypedDict):
    """
    Output from Phase 2B: RESEARCH_RERANKER Node.
    
    Research quality validation with data pruning and quality gates.
    
    Attributes:
        data_quality_tier: Data triage tier (CLEAN/PARTIAL/SPARSE/UNRELIABLE/GARBAGE).
        research_quality_tier: Overall quality tier (HIGH/MEDIUM/LOW/INSUFFICIENT).
        data_confidence_score: Confidence in research data (0-100).
        quality_flags: List of specific quality issues identified.
        missing_data_categories: Data categories that are missing.
        recommended_action: Pipeline routing action.
        enhancement_queries: Queries for enhanced search if needed.
        company_verifiability: Company existence verification status.
        company_verification: Detailed verification evidence.
        pruned_data: Data elements that were pruned as unreliable.
        cleaned_data: Verified, high-quality data elements.
        early_exit_reason: Explanation if early exit recommended.
        reasoning_trace: Post-hoc quality assessment logic.
    """
    data_quality_tier: Literal["CLEAN", "PARTIAL", "SPARSE", "UNRELIABLE", "GARBAGE"]
    research_quality_tier: Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]
    data_confidence_score: int
    quality_flags: List[str]
    missing_data_categories: List[str]
    recommended_action: Literal["CONTINUE", "CONTINUE_WITH_FLAGS", "ENHANCE_SEARCH", "EARLY_EXIT"]
    enhancement_queries: List[str]
    company_verifiability: Literal["VERIFIED", "PARTIAL", "UNVERIFIED", "SUSPICIOUS"]
    company_verification: Dict[str, Any]
    pruned_data: Dict[str, List[str]]
    cleaned_data: Dict[str, Any]
    early_exit_reason: str
    reasoning_trace: str


# =============================================================================
# Main Pipeline State
# =============================================================================

class FitCheckPipelineState(TypedDict):
    """
    Global state for the Fit Check Pipeline.
    
    This is the single source of truth that flows through all phases.
    Each phase reads from prior outputs and writes to its designated field.
    
    Attributes:
        query: Original user input (company name or job description).
        current_phase: Current phase being executed.
        step_count: Running count of thoughts/steps for SSE tracking.
        
        phase_1_output: Output from CONNECTING phase.
        phase_2_output: Output from DEEP_RESEARCH phase.
        research_reranker_output: Output from RESEARCH_RERANKER phase (2B).
        phase_3_output: Output from SKEPTICAL_COMPARISON phase.
        phase_4_output: Output from SKILLS_MATCHING phase.
        reranker_output: Output from CONFIDENCE_RERANKER phase (5B).
        
        search_attempt: Current search attempt number (1 = primary, 2 = enhanced).
        low_data_flag: Flag indicating insufficient research data.
        early_exit: Flag indicating pipeline should skip to generate_results.
        
        final_response: Generated markdown response from GENERATE_RESULTS.
        
        messages: Conversation history for LangGraph compatibility.
        processing_errors: Non-fatal errors encountered during processing.
        error: Fatal error that stopped the pipeline.
        rejection_reason: Reason if query was rejected as irrelevant/malicious.
        
        model_id: AI model ID to use for analysis.
        config_type: Configuration type for the model (reasoning or standard).
    """
    # Input
    query: str
    
    # Orchestration
    current_phase: str
    step_count: int
    
    # Phase outputs
    phase_1_output: Optional[Phase1Output]
    phase_2_output: Optional[Phase2Output]
    research_reranker_output: Optional[ResearchRerankerOutput]
    phase_3_output: Optional[Phase3Output]
    phase_4_output: Optional[Phase4Output]
    reranker_output: Optional[RerankerOutput]
    
    # Research quality tracking
    search_attempt: int
    low_data_flag: bool
    early_exit: bool
    
    # Final output
    final_response: Optional[str]
    
    # LangGraph compatibility
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Error handling
    processing_errors: List[str]
    error: Optional[str]
    
    # Query rejection
    rejection_reason: Optional[str]
    
    # Model configuration
    model_id: Optional[str]
    config_type: Optional[str]


# =============================================================================
# State Factory Functions
# =============================================================================

def create_initial_state(
    query: str,
    model_id: Optional[str] = None,
    config_type: Optional[str] = None,
) -> FitCheckPipelineState:
    """
    Create the initial pipeline state from a user query.
    
    Args:
        query: The user's input (company name or job description).
        model_id: AI model ID to use (e.g., 'gemini-3-pro-preview').
        config_type: Configuration type ('reasoning' or 'standard').
    
    Returns:
        FitCheckPipelineState: Initialized state ready for phase 1.
    """
    return FitCheckPipelineState(
        query=query,
        current_phase="connecting",
        step_count=0,
        phase_1_output=None,
        phase_2_output=None,
        research_reranker_output=None,
        phase_3_output=None,
        phase_4_output=None,
        reranker_output=None,
        search_attempt=1,
        low_data_flag=False,
        early_exit=False,
        final_response=None,
        messages=[],
        processing_errors=[],
        error=None,
        rejection_reason=None,
        model_id=model_id,
        config_type=config_type,
    )


def get_phase_display_name(phase: str) -> str:
    """
    Get human-readable display name for a phase.
    
    Args:
        phase: Internal phase identifier.
    
    Returns:
        str: Display-friendly phase name.
    """
    phase_names = {
        "connecting": "Connecting",
        "deep_research": "Deep Research",
        "research_reranker": "Research Validation",
        "skeptical_comparison": "Skeptical Comparison",
        "skills_matching": "Skills Matching",
        "confidence_reranker": "Confidence Calibration",
        "generate_results": "Generate Results",
    }
    return phase_names.get(phase, phase.replace("_", " ").title())


# =============================================================================
# Phase Transition Helpers
# =============================================================================

PHASE_ORDER = [
    "connecting",
    "deep_research",
    "research_reranker",
    "skeptical_comparison",
    "skills_matching",
    "confidence_reranker",
    "generate_results",
]


def get_next_phase(current_phase: str) -> Optional[str]:
    """
    Get the next phase in the pipeline sequence.
    
    Args:
        current_phase: Current phase identifier.
    
    Returns:
        Next phase identifier, or None if at end.
    """
    try:
        current_idx = PHASE_ORDER.index(current_phase)
        if current_idx < len(PHASE_ORDER) - 1:
            return PHASE_ORDER[current_idx + 1]
        return None
    except ValueError:
        return None


def is_terminal_phase(phase: str) -> bool:
    """
    Check if a phase is the terminal (final) phase.
    
    Args:
        phase: Phase identifier.
    
    Returns:
        True if this is the last phase.
    """
    return phase == PHASE_ORDER[-1]
