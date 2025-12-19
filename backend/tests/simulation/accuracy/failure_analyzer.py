"""
Failure Analysis Module for Accuracy Testing.

This module provides root cause analysis for failed accuracy tests,
implementing the failure analysis template specified in the TODO documentation.

Root Cause Categories:
    - INSUFFICIENT_RESEARCH_DATA: Pipeline couldn't find enough data
    - INCORRECT_SKILL_MAPPING: Skills not properly matched
    - SYCOPHANCY: Over-scoring (too generous)
    - HARSH_SCORING: Under-scoring (too critical)
    - MISSING_GAP_DETECTION: Failed to identify obvious gaps
    - DOMAIN_KNOWLEDGE_GAP: Prompt lacks domain context
    - QUERY_CLASSIFICATION_ERROR: Query type misclassified
    - TIER_CALIBRATION_ERROR: Confidence tier miscalibrated

Each failure is analyzed with:
    - Root cause hypothesis
    - Evidence supporting the hypothesis
    - Recommended fixes
    - Impact severity
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

from .test_definitions import TestCase, TestCategory
from .accuracy_validator import AccuracyResult, AccuracyLevel, ValidationStatus


# =============================================================================
# Enums and Types
# =============================================================================

class RootCauseCategory(str, Enum):
    """Categories of root causes for test failures."""
    INSUFFICIENT_RESEARCH_DATA = "INSUFFICIENT_RESEARCH_DATA"
    INCORRECT_SKILL_MAPPING = "INCORRECT_SKILL_MAPPING"
    SYCOPHANCY = "SYCOPHANCY"
    HARSH_SCORING = "HARSH_SCORING"
    MISSING_GAP_DETECTION = "MISSING_GAP_DETECTION"
    DOMAIN_KNOWLEDGE_GAP = "DOMAIN_KNOWLEDGE_GAP"
    QUERY_CLASSIFICATION_ERROR = "QUERY_CLASSIFICATION_ERROR"
    TIER_CALIBRATION_ERROR = "TIER_CALIBRATION_ERROR"
    EDGE_CASE_HANDLING = "EDGE_CASE_HANDLING"
    UNKNOWN = "UNKNOWN"


class ImpactSeverity(str, Enum):
    """Severity of the failure impact."""
    CRITICAL = "CRITICAL"   # Major scoring error, needs immediate fix
    HIGH = "HIGH"           # Significant but not catastrophic
    MEDIUM = "MEDIUM"       # Noticeable but acceptable short-term
    LOW = "LOW"             # Minor issue, can defer


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class FailureAnalysis:
    """
    Detailed failure analysis for a single test case.
    
    Attributes:
        test_id: The failed test case ID
        query: The query that was tested
        expected_score_range: Expected score range as string
        actual_score: Actual score received
        score_delta: Difference from expected
        expected_tier: Expected tier
        actual_tier: Actual tier
        
        root_cause: Primary root cause category
        root_cause_confidence: How confident we are in this diagnosis (0-1)
        secondary_causes: Additional contributing factors
        
        evidence: Evidence supporting the diagnosis
        recommended_fixes: Suggested fixes
        impact_severity: How severe this issue is
        
        notes: Additional analysis notes
    """
    test_id: str
    query: str
    expected_score_range: str
    actual_score: Optional[float]
    score_delta: Optional[float]
    expected_tier: str
    actual_tier: Optional[str]
    
    root_cause: RootCauseCategory = RootCauseCategory.UNKNOWN
    root_cause_confidence: float = 0.0
    secondary_causes: List[RootCauseCategory] = field(default_factory=list)
    
    evidence: List[str] = field(default_factory=list)
    recommended_fixes: List[str] = field(default_factory=list)
    impact_severity: ImpactSeverity = ImpactSeverity.MEDIUM
    
    notes: str = ""


# =============================================================================
# Analysis Rules
# =============================================================================

def _detect_sycophancy(result: AccuracyResult, test_case: TestCase) -> tuple[bool, float]:
    """
    Detect if the failure is due to sycophancy (over-scoring).
    
    Returns:
        Tuple of (is_sycophancy, confidence).
    """
    if result.actual_score is None:
        return False, 0.0
    
    # Check if score is significantly above expected max
    if result.actual_score > result.expected_score_max:
        overshoot = result.actual_score - result.expected_score_max
        
        # Strong sycophancy: 15+ points over
        if overshoot >= 15:
            return True, 0.9
        # Moderate sycophancy: 10-15 points over
        elif overshoot >= 10:
            return True, 0.7
        # Mild sycophancy: 5-10 points over
        elif overshoot >= 5:
            return True, 0.5
    
    # Also check for HIGH tier when LOW expected (Category C)
    if test_case.category == TestCategory.C_LOW_FIT:
        if result.actual_tier and "high" in result.actual_tier.lower():
            return True, 0.85
    
    return False, 0.0


def _detect_harsh_scoring(result: AccuracyResult, test_case: TestCase) -> tuple[bool, float]:
    """
    Detect if the failure is due to harsh scoring (under-scoring).
    
    Returns:
        Tuple of (is_harsh, confidence).
    """
    if result.actual_score is None:
        return False, 0.0
    
    # Check if score is significantly below expected min
    if result.actual_score < result.expected_score_min:
        undershoot = result.expected_score_min - result.actual_score
        
        # Strong under-scoring: 15+ points under
        if undershoot >= 15:
            return True, 0.9
        # Moderate under-scoring: 10-15 points under
        elif undershoot >= 10:
            return True, 0.7
        # Mild under-scoring: 5-10 points under
        elif undershoot >= 5:
            return True, 0.5
    
    # Also check for LOW tier when HIGH expected (Category A)
    if test_case.category == TestCategory.A_HIGH_FIT:
        if result.actual_tier and "low" in result.actual_tier.lower():
            return True, 0.85
    
    return False, 0.0


def _detect_gap_detection_failure(result: AccuracyResult, test_case: TestCase) -> tuple[bool, float]:
    """
    Detect if gaps were not properly identified.
    
    Returns:
        Tuple of (is_gap_failure, confidence).
    """
    # Check if we expected gaps but got none or too few
    if result.expected_gaps_min > 0 and result.actual_gap_count < result.expected_gaps_min:
        gap_deficit = result.expected_gaps_min - result.actual_gap_count
        confidence = min(0.9, 0.3 + (gap_deficit * 0.2))
        return True, confidence
    
    # For Category B/C, should always have some gaps
    if test_case.category in [TestCategory.B_MEDIUM_FIT, TestCategory.C_LOW_FIT]:
        if result.actual_gap_count < 2:
            return True, 0.7
    
    return False, 0.0


def _detect_data_quality_issue(result: AccuracyResult) -> tuple[bool, float]:
    """
    Detect if the issue is due to insufficient research data.
    
    Returns:
        Tuple of (is_data_issue, confidence).
    """
    # Check for quality flags indicating data issues
    data_issue_flags = ["INSUFFICIENT_DATA", "SPARSE", "GARBAGE", "UNRELIABLE"]
    
    for flag in result.actual_quality_flags:
        if flag.upper() in data_issue_flags:
            return True, 0.85
    
    # Check for warnings about data quality
    for warning in result.warnings:
        if any(kw in warning.lower() for kw in ["data", "research", "search", "insufficient"]):
            return True, 0.6
    
    return False, 0.0


def _detect_tier_calibration_error(result: AccuracyResult) -> tuple[bool, float]:
    """
    Detect if the tier is miscalibrated relative to the score.
    
    Returns:
        Tuple of (is_tier_error, confidence).
    """
    if result.actual_score is None or result.actual_tier is None:
        return False, 0.0
    
    # Define expected tier ranges
    tier_score_ranges = {
        "high": (70, 100),
        "medium_high": (55, 80),
        "medium-high": (55, 80),
        "medium": (40, 65),
        "low_medium": (25, 50),
        "low-medium": (25, 50),
        "low": (10, 35),
        "insufficient": (0, 25),
    }
    
    actual_tier_lower = result.actual_tier.lower().replace(" ", "_")
    expected_range = tier_score_ranges.get(actual_tier_lower)
    
    if expected_range:
        tier_min, tier_max = expected_range
        # Tier doesn't match score
        if result.actual_score < tier_min - 10 or result.actual_score > tier_max + 10:
            return True, 0.8
    
    return False, 0.0


# =============================================================================
# Main Analysis Function
# =============================================================================

def analyze_failure(
    result: AccuracyResult,
    test_case: TestCase,
) -> FailureAnalysis:
    """
    Perform root cause analysis on a failed test.
    
    Args:
        result: The AccuracyResult that failed.
        test_case: The original TestCase definition.
        
    Returns:
        FailureAnalysis with diagnosis and recommendations.
    """
    analysis = FailureAnalysis(
        test_id=result.test_id,
        query=result.query,
        expected_score_range=f"{result.expected_score_min}-{result.expected_score_max}%",
        actual_score=result.actual_score,
        score_delta=result.score_delta,
        expected_tier=result.expected_tier.value,
        actual_tier=result.actual_tier,
    )
    
    # Collect all potential causes with confidence
    causes: List[tuple[RootCauseCategory, float, List[str], List[str]]] = []
    
    # Check for sycophancy (over-scoring)
    is_sycophancy, syc_conf = _detect_sycophancy(result, test_case)
    if is_sycophancy:
        evidence = [
            f"Actual score ({result.actual_score}%) exceeds expected max ({result.expected_score_max}%)",
        ]
        fixes = [
            "Review anti-sycophancy prompts in Phase 3 (skeptical_comparison)",
            "Strengthen gap detection in Phase 4 (skills_matching)",
            "Add calibration examples for this query type",
        ]
        causes.append((RootCauseCategory.SYCOPHANCY, syc_conf, evidence, fixes))
    
    # Check for harsh scoring (under-scoring)
    is_harsh, harsh_conf = _detect_harsh_scoring(result, test_case)
    if is_harsh:
        evidence = [
            f"Actual score ({result.actual_score}%) below expected min ({result.expected_score_min}%)",
        ]
        fixes = [
            "Review skill matching logic in Phase 4",
            "Check if transferable skills are being recognized",
            "Verify confidence calibration in Phase 5b",
        ]
        causes.append((RootCauseCategory.HARSH_SCORING, harsh_conf, evidence, fixes))
    
    # Check for gap detection failure
    is_gap_fail, gap_conf = _detect_gap_detection_failure(result, test_case)
    if is_gap_fail:
        evidence = [
            f"Identified {result.actual_gap_count} gaps, expected {result.expected_gaps_min}-{result.expected_gaps_max}",
        ]
        fixes = [
            "Enhance gap detection prompts in Phase 3",
            "Add specific skill gap categories for this domain",
            "Review Phase 4 gap analysis logic",
        ]
        causes.append((RootCauseCategory.MISSING_GAP_DETECTION, gap_conf, evidence, fixes))
    
    # Check for data quality issues
    is_data_issue, data_conf = _detect_data_quality_issue(result)
    if is_data_issue:
        evidence = [
            f"Quality flags: {result.actual_quality_flags}",
        ]
        fixes = [
            "Improve search query expansion in Phase 2",
            "Add fallback data sources for obscure queries",
            "Consider graceful degradation with partial data",
        ]
        causes.append((RootCauseCategory.INSUFFICIENT_RESEARCH_DATA, data_conf, evidence, fixes))
    
    # Check for tier calibration error
    is_tier_error, tier_conf = _detect_tier_calibration_error(result)
    if is_tier_error:
        evidence = [
            f"Tier '{result.actual_tier}' inconsistent with score {result.actual_score}%",
        ]
        fixes = [
            "Review confidence tier logic in Phase 5b (confidence_reranker)",
            "Add score-to-tier validation in generate_results",
            "Calibrate tier boundaries with test examples",
        ]
        causes.append((RootCauseCategory.TIER_CALIBRATION_ERROR, tier_conf, evidence, fixes))
    
    # Edge case specific analysis
    if test_case.category == TestCategory.D_EDGE_CASES:
        if not result.quality_flags_match:
            evidence = [
                f"Expected quality flags {result.expected_quality_flags} not in actual {result.actual_quality_flags}",
            ]
            fixes = [
                "Improve edge case detection in Phase 2b (research_reranker)",
                "Add specific handling for ambiguous/obscure queries",
            ]
            causes.append((RootCauseCategory.EDGE_CASE_HANDLING, 0.7, evidence, fixes))
    
    # Select primary cause (highest confidence)
    if causes:
        causes.sort(key=lambda x: x[1], reverse=True)
        primary = causes[0]
        analysis.root_cause = primary[0]
        analysis.root_cause_confidence = primary[1]
        analysis.evidence = primary[2]
        analysis.recommended_fixes = primary[3]
        
        # Add secondary causes
        for cause in causes[1:3]:  # Up to 2 secondary causes
            analysis.secondary_causes.append(cause[0])
    else:
        analysis.root_cause = RootCauseCategory.UNKNOWN
        analysis.evidence = ["No clear root cause identified"]
        analysis.recommended_fixes = ["Manual investigation required"]
    
    # Determine impact severity
    analysis.impact_severity = _determine_severity(result, test_case)
    
    return analysis


def _determine_severity(result: AccuracyResult, test_case: TestCase) -> ImpactSeverity:
    """
    Determine the severity of the failure.
    
    Args:
        result: The failed AccuracyResult.
        test_case: The TestCase definition.
        
    Returns:
        ImpactSeverity level.
    """
    # Critical: Category A failures (should be our best matches)
    if test_case.category == TestCategory.A_HIGH_FIT:
        if result.score_accuracy == AccuracyLevel.INACCURATE:
            return ImpactSeverity.CRITICAL
        return ImpactSeverity.HIGH
    
    # Critical: Category C scored as high (sycophancy)
    if test_case.category == TestCategory.C_LOW_FIT:
        if result.actual_score and result.actual_score > 50:
            return ImpactSeverity.CRITICAL
        return ImpactSeverity.HIGH
    
    # High: Category B with significant errors
    if test_case.category == TestCategory.B_MEDIUM_FIT:
        if result.score_accuracy == AccuracyLevel.INACCURATE:
            return ImpactSeverity.HIGH
        return ImpactSeverity.MEDIUM
    
    # Medium: Edge cases
    return ImpactSeverity.MEDIUM


# =============================================================================
# Report Generation
# =============================================================================

def generate_failure_report(analyses: List[FailureAnalysis]) -> str:
    """
    Generate a formatted failure analysis report.
    
    Args:
        analyses: List of FailureAnalysis objects.
        
    Returns:
        Formatted report string.
    """
    if not analyses:
        return "No failures to analyze."
    
    lines = [
        "",
        "=" * 70,
        "  FAILURE ANALYSIS REPORT",
        "=" * 70,
        f"  Total Failures Analyzed: {len(analyses)}",
        "",
    ]
    
    # Group by severity
    by_severity: Dict[ImpactSeverity, List[FailureAnalysis]] = {}
    for analysis in analyses:
        if analysis.impact_severity not in by_severity:
            by_severity[analysis.impact_severity] = []
        by_severity[analysis.impact_severity].append(analysis)
    
    # Report by severity (CRITICAL first)
    for severity in [ImpactSeverity.CRITICAL, ImpactSeverity.HIGH, 
                     ImpactSeverity.MEDIUM, ImpactSeverity.LOW]:
        if severity not in by_severity:
            continue
        
        severity_symbol = {
            ImpactSeverity.CRITICAL: "[!!!]",
            ImpactSeverity.HIGH: "[!!]",
            ImpactSeverity.MEDIUM: "[!]",
            ImpactSeverity.LOW: "[.]",
        }[severity]
        
        lines.append(f"\n{severity_symbol} {severity.value} SEVERITY ({len(by_severity[severity])} issues)")
        lines.append("-" * 60)
        
        for analysis in by_severity[severity]:
            lines.extend([
                "",
                f"  TEST FAILURE: {analysis.test_id}",
                f"  -----------------------------------------",
                f"  Query: {analysis.query[:50]}{'...' if len(analysis.query) > 50 else ''}",
                f"  Expected: {analysis.expected_score_range}, {analysis.expected_tier}",
                f"  Actual: {analysis.actual_score}%, {analysis.actual_tier}",
                f"  Delta: {analysis.score_delta if analysis.score_delta else 'N/A'}",
                "",
                f"  ROOT CAUSE: {analysis.root_cause.value}",
                f"  Confidence: {analysis.root_cause_confidence:.0%}",
            ])
            
            if analysis.secondary_causes:
                lines.append(f"  Secondary: {', '.join(c.value for c in analysis.secondary_causes)}")
            
            lines.append("")
            lines.append("  Evidence:")
            for evidence in analysis.evidence:
                lines.append(f"    * {evidence}")
            
            lines.append("")
            lines.append("  Recommended Fixes:")
            for fix in analysis.recommended_fixes:
                lines.append(f"    -> {fix}")
    
    # Summary of root causes
    cause_counts: Dict[RootCauseCategory, int] = {}
    for analysis in analyses:
        cause_counts[analysis.root_cause] = cause_counts.get(analysis.root_cause, 0) + 1
    
    lines.extend([
        "",
        "-" * 70,
        "  ROOT CAUSE SUMMARY",
        "-" * 70,
    ])
    
    for cause, count in sorted(cause_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  {cause.value}: {count} occurrence(s)")
    
    lines.extend([
        "",
        "=" * 70,
        "  END OF FAILURE ANALYSIS",
        "=" * 70,
        "",
    ])
    
    return "\n".join(lines)


def generate_individual_failure_template(analysis: FailureAnalysis) -> str:
    """
    Generate the failure analysis template for a single test.
    
    This follows the exact template format from the TODO documentation.
    
    Args:
        analysis: FailureAnalysis object.
        
    Returns:
        Formatted template string.
    """
    checkboxes = {
        RootCauseCategory.INSUFFICIENT_RESEARCH_DATA: "[ ]",
        RootCauseCategory.INCORRECT_SKILL_MAPPING: "[ ]",
        RootCauseCategory.SYCOPHANCY: "[ ]",
        RootCauseCategory.HARSH_SCORING: "[ ]",
        RootCauseCategory.MISSING_GAP_DETECTION: "[ ]",
        RootCauseCategory.DOMAIN_KNOWLEDGE_GAP: "[ ]",
        RootCauseCategory.QUERY_CLASSIFICATION_ERROR: "[ ]",
        RootCauseCategory.TIER_CALIBRATION_ERROR: "[ ]",
        RootCauseCategory.EDGE_CASE_HANDLING: "[ ]",
        RootCauseCategory.UNKNOWN: "[ ]",
    }
    
    # Mark the identified cause
    checkboxes[analysis.root_cause] = "[X]"
    for cause in analysis.secondary_causes:
        if cause in checkboxes:
            checkboxes[cause] = "[~]"  # Partial/secondary
    
    template = f"""
TEST FAILURE ANALYSIS
---------------------
Test ID: {analysis.test_id}
Query: {analysis.query}
Expected: {analysis.expected_score_range}, Tier {analysis.expected_tier}
Actual: {analysis.actual_score}%, Tier {analysis.actual_tier}
Delta: +/-{abs(analysis.score_delta) if analysis.score_delta else 0:.1f}%

Root Cause Hypothesis:
{checkboxes[RootCauseCategory.INSUFFICIENT_RESEARCH_DATA]} Insufficient research data
{checkboxes[RootCauseCategory.INCORRECT_SKILL_MAPPING]} Incorrect skill mapping
{checkboxes[RootCauseCategory.SYCOPHANCY]} Sycophancy (over-scoring)
{checkboxes[RootCauseCategory.HARSH_SCORING]} Harsh scoring (under-scoring)
{checkboxes[RootCauseCategory.MISSING_GAP_DETECTION]} Missing gap detection
{checkboxes[RootCauseCategory.DOMAIN_KNOWLEDGE_GAP]} Domain knowledge gap in prompts
{checkboxes[RootCauseCategory.QUERY_CLASSIFICATION_ERROR]} Query classification error
{checkboxes[RootCauseCategory.TIER_CALIBRATION_ERROR]} Tier calibration error
{checkboxes[RootCauseCategory.EDGE_CASE_HANDLING]} Edge case handling
{checkboxes[RootCauseCategory.UNKNOWN]} Unknown/requires investigation

Recommended Fixes:
{chr(10).join(f'  - {fix}' for fix in analysis.recommended_fixes)}

Impact Severity: {analysis.impact_severity.value}
"""
    return template
