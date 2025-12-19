"""
Accuracy Testing Module for Fit Check Pipeline.

This module provides systematic accuracy validation of the Fit Check pipeline
using real-world queries with visual reasoning and structured test cases.

Modules:
    - test_definitions: Test case definitions by category (A/B/C/D)
    - accuracy_validator: Accuracy calculation and validation utilities
    - run_accuracy_tests: Main test runner for accuracy testing
    - failure_analyzer: Root cause analysis for failed tests
"""

from .test_definitions import (
    TestCase,
    TestCategory,
    ExpectedOutcome,
    get_all_test_cases,
    get_test_cases_by_category,
    CATEGORY_A_HIGH_FIT,
    CATEGORY_B_MEDIUM_FIT,
    CATEGORY_C_LOW_FIT,
    CATEGORY_D_EDGE_CASES,
)
from .accuracy_validator import (
    AccuracyResult,
    AccuracyMetrics,
    calculate_score_accuracy,
    calculate_tier_accuracy,
    validate_test_result,
)
from .failure_analyzer import (
    FailureAnalysis,
    RootCauseCategory,
    analyze_failure,
    generate_failure_report,
)

__all__ = [
    # Test Definitions
    "TestCase",
    "TestCategory",
    "ExpectedOutcome",
    "get_all_test_cases",
    "get_test_cases_by_category",
    "CATEGORY_A_HIGH_FIT",
    "CATEGORY_B_MEDIUM_FIT",
    "CATEGORY_C_LOW_FIT",
    "CATEGORY_D_EDGE_CASES",
    # Accuracy Validation
    "AccuracyResult",
    "AccuracyMetrics",
    "calculate_score_accuracy",
    "calculate_tier_accuracy",
    "validate_test_result",
    # Failure Analysis
    "FailureAnalysis",
    "RootCauseCategory",
    "analyze_failure",
    "generate_failure_report",
]
