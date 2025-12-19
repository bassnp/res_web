"""
Accuracy Validation Utilities for Fit Check Pipeline Testing.

This module provides utilities to calculate and validate accuracy metrics
for the Fit Check pipeline test results. It implements the scoring accuracy
and tier accuracy calculations specified in the TODO documentation.

Accuracy Criteria:
    Score Accuracy:
        - ACCURATE:    |Actual - Expected| <= 15%
        - ACCEPTABLE:  |Actual - Expected| <= 25%
        - INACCURATE:  |Actual - Expected| > 25%
    
    Tier Accuracy:
        - ACCURATE:    Actual Tier == Expected Tier
        - ACCEPTABLE:  Actual Tier adjacent to Expected
        - INACCURATE:  Otherwise

Pass/Fail Thresholds:
    - Category A: >= 80% within expected range
    - Category B: >= 75% within expected range
    - Category C: >= 80% within expected range
    - Tier Accuracy: >= 75% exact match
    - Gap Identification: >= 2 genuine gaps on B/C queries
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

from .test_definitions import (
    TestCase,
    TestCategory,
    ConfidenceTier,
    ExpectedOutcome,
)


# =============================================================================
# Enums and Types
# =============================================================================

class AccuracyLevel(str, Enum):
    """Accuracy level classification for test results."""
    ACCURATE = "ACCURATE"       # Within tight tolerance
    ACCEPTABLE = "ACCEPTABLE"   # Within loose tolerance
    INACCURATE = "INACCURATE"   # Outside tolerance


class ValidationStatus(str, Enum):
    """Overall validation status for a test."""
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"


# =============================================================================
# Configuration Constants
# =============================================================================

# Score accuracy thresholds
SCORE_ACCURATE_THRESHOLD = 15    # +/-15% for ACCURATE
SCORE_ACCEPTABLE_THRESHOLD = 25  # +/-25% for ACCEPTABLE

# Tier adjacency mapping for "acceptable" tier comparisons
TIER_ADJACENCY: Dict[ConfidenceTier, List[ConfidenceTier]] = {
    ConfidenceTier.HIGH: [
        ConfidenceTier.MEDIUM_HIGH
    ],
    ConfidenceTier.MEDIUM_HIGH: [
        ConfidenceTier.HIGH, 
        ConfidenceTier.MEDIUM
    ],
    ConfidenceTier.MEDIUM: [
        ConfidenceTier.MEDIUM_HIGH, 
        ConfidenceTier.LOW_MEDIUM
    ],
    ConfidenceTier.LOW_MEDIUM: [
        ConfidenceTier.MEDIUM, 
        ConfidenceTier.LOW
    ],
    ConfidenceTier.LOW: [
        ConfidenceTier.LOW_MEDIUM, 
        ConfidenceTier.INSUFFICIENT
    ],
    ConfidenceTier.INSUFFICIENT: [
        ConfidenceTier.LOW, 
        ConfidenceTier.INSUFFICIENT_DATA
    ],
    ConfidenceTier.INSUFFICIENT_DATA: [
        ConfidenceTier.INSUFFICIENT, 
        ConfidenceTier.LOW
    ],
}

# Category pass thresholds
CATEGORY_PASS_THRESHOLDS = {
    TestCategory.A_HIGH_FIT: 0.80,      # 80%
    TestCategory.B_MEDIUM_FIT: 0.75,    # 75%
    TestCategory.C_LOW_FIT: 0.80,       # 80%
    TestCategory.D_EDGE_CASES: 0.70,    # 70% (more lenient for edge cases)
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AccuracyResult:
    """
    Result of accuracy validation for a single test case.
    
    Attributes:
        test_id: The test case ID
        test_name: Human-readable test name
        query: The query that was tested
        
        expected_score_min: Expected minimum score
        expected_score_max: Expected maximum score
        actual_score: Actual score from pipeline
        score_delta: Difference from expected range center
        score_accuracy: Accuracy level for score
        
        expected_tier: Expected confidence tier
        actual_tier: Actual confidence tier from pipeline
        tier_accuracy: Accuracy level for tier
        
        expected_gaps_min: Minimum expected gap count
        expected_gaps_max: Maximum expected gap count
        actual_gap_count: Actual number of gaps identified
        gaps_identified: List of identified gap descriptions
        gap_accuracy: Whether gap count is within range
        
        overall_status: Overall pass/fail status
        warnings: List of warning messages
        notes: Additional notes about the result
    """
    test_id: str
    test_name: str
    query: str
    
    # Score metrics
    expected_score_min: int
    expected_score_max: int
    actual_score: Optional[float] = None
    score_delta: Optional[float] = None
    score_accuracy: AccuracyLevel = AccuracyLevel.INACCURATE
    score_in_range: bool = False
    
    # Tier metrics
    expected_tier: ConfidenceTier = ConfidenceTier.MEDIUM
    actual_tier: Optional[str] = None
    tier_accuracy: AccuracyLevel = AccuracyLevel.INACCURATE
    
    # Gap metrics
    expected_gaps_min: int = 0
    expected_gaps_max: int = 10
    actual_gap_count: int = 0
    gaps_identified: List[str] = field(default_factory=list)
    gap_accuracy: bool = False
    
    # Quality flags
    expected_quality_flags: List[str] = field(default_factory=list)
    actual_quality_flags: List[str] = field(default_factory=list)
    quality_flags_match: bool = False
    
    # Overall
    overall_status: ValidationStatus = ValidationStatus.FAIL
    warnings: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class AccuracyMetrics:
    """
    Aggregate accuracy metrics across multiple test results.
    
    Attributes:
        total_tests: Total number of tests run
        passed: Number of tests that passed
        failed: Number of tests that failed
        partial: Number of tests with partial pass
        
        score_accurate: Count of ACCURATE score results
        score_acceptable: Count of ACCEPTABLE score results
        score_inaccurate: Count of INACCURATE score results
        
        tier_accurate: Count of exact tier matches
        tier_acceptable: Count of adjacent tier matches
        tier_inaccurate: Count of tier mismatches
        
        category_results: Results broken down by category
        pass_rate: Overall pass rate
    """
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    partial: int = 0
    
    score_accurate: int = 0
    score_acceptable: int = 0
    score_inaccurate: int = 0
    
    tier_accurate: int = 0
    tier_acceptable: int = 0
    tier_inaccurate: int = 0
    
    gap_accurate: int = 0
    gap_inaccurate: int = 0
    
    category_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    @property
    def pass_rate(self) -> float:
        """Calculate overall pass rate."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed + 0.5 * self.partial) / self.total_tests
    
    @property
    def score_accuracy_rate(self) -> float:
        """Calculate score accuracy rate (ACCURATE + ACCEPTABLE)."""
        if self.total_tests == 0:
            return 0.0
        return (self.score_accurate + self.score_acceptable) / self.total_tests
    
    @property
    def tier_accuracy_rate(self) -> float:
        """Calculate tier accuracy rate (exact matches)."""
        if self.total_tests == 0:
            return 0.0
        return self.tier_accurate / self.total_tests


# =============================================================================
# Core Validation Functions
# =============================================================================

def calculate_score_accuracy(
    actual_score: float,
    expected_min: int,
    expected_max: int,
) -> Tuple[AccuracyLevel, float, bool]:
    """
    Calculate score accuracy level.
    
    Args:
        actual_score: The actual score from pipeline (0-100).
        expected_min: Expected minimum score.
        expected_max: Expected maximum score.
        
    Returns:
        Tuple of (AccuracyLevel, delta_from_range_center, is_in_range).
    """
    # Check if within expected range
    in_range = expected_min <= actual_score <= expected_max
    
    # Calculate delta from range center
    expected_center = (expected_min + expected_max) / 2
    delta = abs(actual_score - expected_center)
    
    # Also check delta from nearest boundary if outside range
    if actual_score < expected_min:
        boundary_delta = expected_min - actual_score
    elif actual_score > expected_max:
        boundary_delta = actual_score - expected_max
    else:
        boundary_delta = 0
    
    # Determine accuracy level based on boundary delta
    if boundary_delta <= SCORE_ACCURATE_THRESHOLD:
        accuracy = AccuracyLevel.ACCURATE
    elif boundary_delta <= SCORE_ACCEPTABLE_THRESHOLD:
        accuracy = AccuracyLevel.ACCEPTABLE
    else:
        accuracy = AccuracyLevel.INACCURATE
    
    # If in range, always at least ACCURATE
    if in_range:
        accuracy = AccuracyLevel.ACCURATE
    
    return accuracy, delta, in_range


def calculate_tier_accuracy(
    actual_tier: str,
    expected_tier: ConfidenceTier,
    acceptable_tiers: List[ConfidenceTier] = None,
) -> AccuracyLevel:
    """
    Calculate tier accuracy level.
    
    Args:
        actual_tier: The actual tier string from pipeline.
        expected_tier: The expected ConfidenceTier.
        acceptable_tiers: Additional tiers that are acceptable.
        
    Returns:
        AccuracyLevel indicating tier match quality.
    """
    acceptable_tiers = acceptable_tiers or []
    
    # Normalize actual tier string to enum
    try:
        actual = ConfidenceTier(actual_tier.upper().replace("-", "_").replace(" ", "_"))
    except (ValueError, AttributeError):
        # Try mapping common variations
        tier_mapping = {
            "high": ConfidenceTier.HIGH,
            "medium-high": ConfidenceTier.MEDIUM_HIGH,
            "medium_high": ConfidenceTier.MEDIUM_HIGH,
            "medium": ConfidenceTier.MEDIUM,
            "low-medium": ConfidenceTier.LOW_MEDIUM,
            "low_medium": ConfidenceTier.LOW_MEDIUM,
            "low": ConfidenceTier.LOW,
            "insufficient": ConfidenceTier.INSUFFICIENT,
            "insufficient_data": ConfidenceTier.INSUFFICIENT_DATA,
        }
        actual = tier_mapping.get(actual_tier.lower() if actual_tier else "", None)
        if actual is None:
            return AccuracyLevel.INACCURATE
    
    # Exact match
    if actual == expected_tier:
        return AccuracyLevel.ACCURATE
    
    # Check explicitly acceptable tiers
    if actual in acceptable_tiers:
        return AccuracyLevel.ACCEPTABLE
    
    # Check adjacent tiers
    adjacent = TIER_ADJACENCY.get(expected_tier, [])
    if actual in adjacent:
        return AccuracyLevel.ACCEPTABLE
    
    return AccuracyLevel.INACCURATE


def validate_gap_count(
    actual_count: int,
    expected_min: int,
    expected_max: int,
) -> bool:
    """
    Validate that gap count is within expected range.
    
    Args:
        actual_count: Actual number of gaps identified.
        expected_min: Minimum expected gaps.
        expected_max: Maximum expected gaps.
        
    Returns:
        True if gap count is within range.
    """
    return expected_min <= actual_count <= expected_max


def validate_quality_flags(
    actual_flags: List[str],
    expected_flags: List[str],
) -> bool:
    """
    Validate that expected quality flags are present.
    
    Args:
        actual_flags: Flags present in result.
        expected_flags: Flags that should be present.
        
    Returns:
        True if all expected flags are present.
    """
    if not expected_flags:
        return True
    
    actual_upper = {f.upper() for f in actual_flags}
    expected_upper = {f.upper() for f in expected_flags}
    
    return expected_upper.issubset(actual_upper)


# =============================================================================
# Main Validation Function
# =============================================================================

def validate_test_result(
    test_case: TestCase,
    actual_score: Optional[float],
    actual_tier: Optional[str],
    actual_gaps: List[str] = None,
    actual_quality_flags: List[str] = None,
) -> AccuracyResult:
    """
    Validate a pipeline result against expected outcomes.
    
    Args:
        test_case: The TestCase definition with expected values.
        actual_score: Actual match score from pipeline (0-100).
        actual_tier: Actual confidence tier string.
        actual_gaps: List of gap descriptions identified.
        actual_quality_flags: Quality flags from result.
        
    Returns:
        AccuracyResult with detailed validation results.
    """
    actual_gaps = actual_gaps or []
    actual_quality_flags = actual_quality_flags or []
    expected = test_case.expected
    
    result = AccuracyResult(
        test_id=test_case.id,
        test_name=test_case.name,
        query=test_case.query,
        expected_score_min=expected.score_min,
        expected_score_max=expected.score_max,
        expected_tier=expected.confidence_tier,
        expected_gaps_min=expected.gap_count_min,
        expected_gaps_max=expected.gap_count_max,
        expected_quality_flags=expected.quality_flags,
        actual_quality_flags=actual_quality_flags,
    )
    
    # Check if this is an edge case that expects AMBIGUOUS_QUERY
    # where None results are acceptable
    is_ambiguous_edge_case = "AMBIGUOUS_QUERY" in expected.quality_flags
    
    # Validate score
    if actual_score is not None:
        result.actual_score = actual_score
        score_accuracy, delta, in_range = calculate_score_accuracy(
            actual_score,
            expected.score_min,
            expected.score_max,
        )
        result.score_accuracy = score_accuracy
        result.score_delta = delta
        result.score_in_range = in_range
    else:
        # For ambiguous queries, None is acceptable
        if is_ambiguous_edge_case:
            result.score_accuracy = AccuracyLevel.ACCEPTABLE
            result.notes = "None score is acceptable for ambiguous queries"
        else:
            result.warnings.append("No score returned from pipeline")
    
    # Validate tier
    if actual_tier is not None:
        result.actual_tier = actual_tier
        result.tier_accuracy = calculate_tier_accuracy(
            actual_tier,
            expected.confidence_tier,
            expected.confidence_tier_acceptable,
        )
    else:
        # For ambiguous queries, None tier is acceptable
        if is_ambiguous_edge_case:
            result.tier_accuracy = AccuracyLevel.ACCEPTABLE
        else:
            result.warnings.append("No confidence tier returned from pipeline")
    
    # Validate gaps
    result.actual_gap_count = len(actual_gaps)
    result.gaps_identified = actual_gaps
    result.gap_accuracy = validate_gap_count(
        len(actual_gaps),
        expected.gap_count_min,
        expected.gap_count_max,
    )
    
    # Validate quality flags (for edge cases)
    # For ambiguous queries, the fact that we got None IS the quality flag match
    if is_ambiguous_edge_case and actual_score is None:
        result.quality_flags_match = True
    else:
        result.quality_flags_match = validate_quality_flags(
            actual_quality_flags,
            expected.quality_flags,
        )
    
    # Determine overall status
    result.overall_status = _determine_overall_status(result)
    
    return result


def _determine_overall_status(result: AccuracyResult) -> ValidationStatus:
    """
    Determine overall validation status based on individual metrics.
    
    Args:
        result: AccuracyResult with individual validations.
        
    Returns:
        ValidationStatus (PASS, FAIL, or PARTIAL).
    """
    # Count passing criteria
    criteria_passed = 0
    total_criteria = 3  # score, tier, gaps
    
    # Score: ACCURATE or ACCEPTABLE
    if result.score_accuracy in [AccuracyLevel.ACCURATE, AccuracyLevel.ACCEPTABLE]:
        criteria_passed += 1
    
    # Tier: ACCURATE or ACCEPTABLE
    if result.tier_accuracy in [AccuracyLevel.ACCURATE, AccuracyLevel.ACCEPTABLE]:
        criteria_passed += 1
    
    # Gaps: within range
    if result.gap_accuracy:
        criteria_passed += 1
    
    # For edge cases, also check quality flags
    if result.expected_quality_flags:
        total_criteria += 1
        if result.quality_flags_match:
            criteria_passed += 1
    
    # Determine status
    if criteria_passed == total_criteria:
        return ValidationStatus.PASS
    elif criteria_passed >= total_criteria / 2:
        return ValidationStatus.PARTIAL
    else:
        return ValidationStatus.FAIL


# =============================================================================
# Aggregate Metrics Calculation
# =============================================================================

def calculate_aggregate_metrics(
    results: List[AccuracyResult],
) -> AccuracyMetrics:
    """
    Calculate aggregate metrics across all test results.
    
    Args:
        results: List of AccuracyResult objects.
        
    Returns:
        AccuracyMetrics with aggregate statistics.
    """
    metrics = AccuracyMetrics(total_tests=len(results))
    
    # Category tracking
    category_counts: Dict[str, Dict[str, int]] = {}
    
    for result in results:
        # Overall status counts
        if result.overall_status == ValidationStatus.PASS:
            metrics.passed += 1
        elif result.overall_status == ValidationStatus.PARTIAL:
            metrics.partial += 1
        else:
            metrics.failed += 1
        
        # Score accuracy counts
        if result.score_accuracy == AccuracyLevel.ACCURATE:
            metrics.score_accurate += 1
        elif result.score_accuracy == AccuracyLevel.ACCEPTABLE:
            metrics.score_acceptable += 1
        else:
            metrics.score_inaccurate += 1
        
        # Tier accuracy counts
        if result.tier_accuracy == AccuracyLevel.ACCURATE:
            metrics.tier_accurate += 1
        elif result.tier_accuracy == AccuracyLevel.ACCEPTABLE:
            metrics.tier_acceptable += 1
        else:
            metrics.tier_inaccurate += 1
        
        # Gap accuracy counts
        if result.gap_accuracy:
            metrics.gap_accurate += 1
        else:
            metrics.gap_inaccurate += 1
        
        # Category tracking
        category = result.test_id[0]  # First letter is category
        if category not in category_counts:
            category_counts[category] = {"passed": 0, "failed": 0, "total": 0}
        category_counts[category]["total"] += 1
        if result.overall_status == ValidationStatus.PASS:
            category_counts[category]["passed"] += 1
        elif result.overall_status != ValidationStatus.FAIL:
            category_counts[category]["passed"] += 0.5
        else:
            category_counts[category]["failed"] += 1
    
    # Calculate category pass rates
    for category, counts in category_counts.items():
        if counts["total"] > 0:
            pass_rate = counts["passed"] / counts["total"]
            metrics.category_results[category] = {
                "passed": counts["passed"],
                "failed": counts["failed"],
                "total": counts["total"],
                "pass_rate": pass_rate,
            }
    
    return metrics


# =============================================================================
# Report Generation
# =============================================================================

def generate_accuracy_report(
    results: List[AccuracyResult],
    metrics: AccuracyMetrics,
) -> str:
    """
    Generate a formatted accuracy report.
    
    Args:
        results: List of AccuracyResult objects.
        metrics: Aggregate AccuracyMetrics.
        
    Returns:
        Formatted report string.
    """
    lines = [
        "",
        "=" * 70,
        "  ACCURACY TEST RESULTS REPORT",
        "=" * 70,
        "",
        f"  Total Tests: {metrics.total_tests}",
        f"  Passed: {metrics.passed} | Partial: {metrics.partial} | Failed: {metrics.failed}",
        f"  Overall Pass Rate: {metrics.pass_rate:.1%}",
        "",
        "-" * 70,
        "  SCORE ACCURACY",
        "-" * 70,
        f"  Accurate (+/-15%): {metrics.score_accurate}",
        f"  Acceptable (+/-25%): {metrics.score_acceptable}",
        f"  Inaccurate (>25%): {metrics.score_inaccurate}",
        f"  Score Accuracy Rate: {metrics.score_accuracy_rate:.1%}",
        "",
        "-" * 70,
        "  TIER ACCURACY",
        "-" * 70,
        f"  Exact Match: {metrics.tier_accurate}",
        f"  Adjacent Match: {metrics.tier_acceptable}",
        f"  Mismatch: {metrics.tier_inaccurate}",
        f"  Tier Accuracy Rate: {metrics.tier_accuracy_rate:.1%}",
        "",
        "-" * 70,
        "  GAP IDENTIFICATION",
        "-" * 70,
        f"  Within Range: {metrics.gap_accurate}",
        f"  Outside Range: {metrics.gap_inaccurate}",
        "",
        "-" * 70,
        "  CATEGORY BREAKDOWN",
        "-" * 70,
    ]
    
    category_names = {
        "A": "HIGH FIT (70-100%)",
        "B": "MEDIUM FIT (40-69%)",
        "C": "LOW FIT (0-39%)",
        "D": "EDGE CASES",
    }
    
    for cat, name in category_names.items():
        if cat in metrics.category_results:
            data = metrics.category_results[cat]
            status = "[PASS]" if data["pass_rate"] >= CATEGORY_PASS_THRESHOLDS.get(
                TestCategory(cat), 0.75
            ) else "[FAIL]"
            lines.append(
                f"  Category {cat} ({name}): {data['pass_rate']:.1%} {status}"
            )
    
    lines.extend([
        "",
        "-" * 70,
        "  INDIVIDUAL TEST RESULTS",
        "-" * 70,
    ])
    
    for result in results:
        status_symbol = {
            ValidationStatus.PASS: "[+]",
            ValidationStatus.PARTIAL: "[~]",
            ValidationStatus.FAIL: "[-]",
        }[result.overall_status]
        
        score_str = f"{result.actual_score:.0f}%" if result.actual_score else "N/A"
        expected_str = f"{result.expected_score_min}-{result.expected_score_max}%"
        
        lines.append(f"")
        lines.append(f"  {status_symbol} {result.test_id}: {result.test_name}")
        lines.append(f"      Query: \"{result.query[:40]}{'...' if len(result.query) > 40 else ''}\"")
        lines.append(f"      Score: {score_str} (expected {expected_str}) [{result.score_accuracy.value}]")
        lines.append(f"      Tier: {result.actual_tier or 'N/A'} (expected {result.expected_tier.value}) [{result.tier_accuracy.value}]")
        lines.append(f"      Gaps: {result.actual_gap_count} (expected {result.expected_gaps_min}-{result.expected_gaps_max}) [{'OK' if result.gap_accuracy else 'MISS'}]")
        
        if result.warnings:
            for warning in result.warnings:
                lines.append(f"      [!] {warning}")
    
    lines.extend([
        "",
        "=" * 70,
        "  END OF REPORT",
        "=" * 70,
        "",
    ])
    
    return "\n".join(lines)
