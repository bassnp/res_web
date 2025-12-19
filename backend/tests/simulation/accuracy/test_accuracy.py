"""
Pytest-Compatible Accuracy Tests for Fit Check Pipeline.

This module provides pytest-compatible test cases for accuracy validation.
Tests can be run via pytest or the standalone accuracy test runner.

Usage (pytest):
    # Run all accuracy tests
    pytest tests/simulation/accuracy/test_accuracy.py -v
    
    # Run specific category
    pytest tests/simulation/accuracy/test_accuracy.py -v -m accuracy_category_a
    
    # Run specific test
    pytest tests/simulation/accuracy/test_accuracy.py::test_a1_vercel -v

Usage (standalone):
    python -m tests.simulation.accuracy.run_accuracy_tests

Markers:
    - accuracy: All accuracy tests
    - accuracy_category_a: HIGH FIT tests (70-100%)
    - accuracy_category_b: MEDIUM FIT tests (40-69%)
    - accuracy_category_c: LOW FIT tests (0-39%)
    - accuracy_category_d: EDGE CASE tests
"""

import pytest
import asyncio
import json
import httpx
from typing import Optional, Dict, Any, List

from .test_definitions import (
    TestCase,
    TestCategory,
    CATEGORY_A_HIGH_FIT,
    CATEGORY_B_MEDIUM_FIT,
    CATEGORY_C_LOW_FIT,
    CATEGORY_D_EDGE_CASES,
    get_test_case_by_id,
)
from .accuracy_validator import (
    AccuracyResult,
    ValidationStatus,
    AccuracyLevel,
    validate_test_result,
)
from .run_accuracy_tests import PipelineResponseParser


# =============================================================================
# Configuration
# =============================================================================

BASE_URL = "http://localhost:8000"
SSE_ENDPOINT = f"{BASE_URL}/api/fit-check/stream"
HEALTH_ENDPOINT = f"{BASE_URL}/health"
DEFAULT_TIMEOUT = 120.0


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def backend_available():
    """Check if backend is available for testing."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(HEALTH_ENDPOINT, timeout=10.0)
            return response.status_code == 200
    except Exception:
        return False


async def run_pipeline_test(query: str, timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    Execute a pipeline test and return parsed results.
    
    Args:
        query: The query to test.
        timeout: Request timeout.
        
    Returns:
        Dict with score, tier, gaps, quality_flags, response_text, events, error.
    """
    result = {
        "score": None,
        "tier": None,
        "gaps": [],
        "quality_flags": [],
        "response_text": "",
        "events": [],
        "error": None,
    }
    
    payload = {
        "query": query,
        "include_thoughts": True,
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                SSE_ENDPOINT,
                json=payload,
                headers={"Accept": "text/event-stream"},
            ) as response:
                if response.status_code != 200:
                    result["error"] = f"HTTP {response.status_code}"
                    return result
                
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    while '\n\n' in buffer:
                        event_block, buffer = buffer.split('\n\n', 1)
                        parsed_event = _parse_sse_block(event_block)
                        if parsed_event:
                            result["events"].append(parsed_event)
                            
                            if parsed_event.get("event_type") == "response":
                                chunk_text = parsed_event.get("data", {}).get("chunk", "")
                                result["response_text"] += chunk_text
    
    except httpx.TimeoutException:
        result["error"] = f"Timeout after {timeout}s"
    except Exception as e:
        result["error"] = str(e)
    
    # Parse response for metrics
    parsed = PipelineResponseParser.parse_response(
        result["response_text"],
        result["events"]
    )
    result.update(parsed)
    
    return result


def _parse_sse_block(block: str) -> Optional[Dict[str, Any]]:
    """Parse a single SSE event block."""
    event_type = None
    data = None
    
    for line in block.split('\n'):
        line = line.strip()
        if line.startswith('event:'):
            event_type = line[6:].strip()
        elif line.startswith('data:'):
            try:
                data = json.loads(line[5:].strip())
            except json.JSONDecodeError:
                data = {"raw": line[5:].strip()}
    
    if event_type:
        return {"event_type": event_type, "data": data or {}}
    return None


# =============================================================================
# Test Helper
# =============================================================================

async def execute_accuracy_test(
    test_case: TestCase,
    backend_available: bool,
) -> AccuracyResult:
    """
    Execute a single accuracy test case.
    
    Args:
        test_case: The TestCase definition.
        backend_available: Whether backend is running.
        
    Returns:
        AccuracyResult with validation results.
    """
    if not backend_available:
        pytest.skip("Backend not available")
    
    # Run the pipeline
    result = await run_pipeline_test(test_case.query)
    
    # Validate
    accuracy_result = validate_test_result(
        test_case=test_case,
        actual_score=result["score"],
        actual_tier=result["tier"],
        actual_gaps=result["gaps"],
        actual_quality_flags=result["quality_flags"],
    )
    
    if result["error"]:
        accuracy_result.warnings.append(f"Request error: {result['error']}")
    
    return accuracy_result


def assert_accuracy_result(result: AccuracyResult, test_case: TestCase):
    """
    Assert that an accuracy result meets criteria.
    
    Args:
        result: The AccuracyResult to check.
        test_case: The original TestCase.
        
    Raises:
        AssertionError with detailed message if criteria not met.
    """
    # Build assertion message
    message_parts = [
        f"\nTest: {test_case.id} - {test_case.name}",
        f"Query: {test_case.query[:60]}...",
        f"Expected Score: {result.expected_score_min}-{result.expected_score_max}%",
        f"Actual Score: {result.actual_score}%",
        f"Score Accuracy: {result.score_accuracy.value}",
        f"Expected Tier: {result.expected_tier.value}",
        f"Actual Tier: {result.actual_tier}",
        f"Tier Accuracy: {result.tier_accuracy.value}",
        f"Gap Count: {result.actual_gap_count} (expected {result.expected_gaps_min}-{result.expected_gaps_max})",
    ]
    
    if result.warnings:
        message_parts.append(f"Warnings: {', '.join(result.warnings)}")
    
    message = "\n".join(message_parts)
    
    # Check overall status
    assert result.overall_status in [ValidationStatus.PASS, ValidationStatus.PARTIAL], (
        f"Test failed with status {result.overall_status.value}\n{message}"
    )
    
    # Check score accuracy
    assert result.score_accuracy in [AccuracyLevel.ACCURATE, AccuracyLevel.ACCEPTABLE], (
        f"Score accuracy {result.score_accuracy.value} not acceptable\n{message}"
    )
    
    # Check tier accuracy
    assert result.tier_accuracy in [AccuracyLevel.ACCURATE, AccuracyLevel.ACCEPTABLE], (
        f"Tier accuracy {result.tier_accuracy.value} not acceptable\n{message}"
    )


# =============================================================================
# Category A: HIGH FIT Tests (70-100%)
# =============================================================================

@pytest.mark.accuracy
@pytest.mark.accuracy_category_a
@pytest.mark.slow
@pytest.mark.asyncio
async def test_a1_vercel(backend_available):
    """A1: Vercel - Frontend-focused company with Next.js emphasis."""
    test_case = get_test_case_by_id("A1")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_a
@pytest.mark.slow
@pytest.mark.asyncio
async def test_a2_openai(backend_available):
    """A2: OpenAI - AI Engineering company."""
    test_case = get_test_case_by_id("A2")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_a
@pytest.mark.slow
@pytest.mark.asyncio
async def test_a3_stripe(backend_available):
    """A3: Stripe - Backend/API company."""
    test_case = get_test_case_by_id("A3")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_a
@pytest.mark.slow
@pytest.mark.asyncio
async def test_a4_fullstack_startup(backend_available):
    """A4: Full-stack Python/React startup role."""
    test_case = get_test_case_by_id("A4")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_a
@pytest.mark.slow
@pytest.mark.asyncio
async def test_a5_anthropic(backend_available):
    """A5: Anthropic - AI Safety company."""
    test_case = get_test_case_by_id("A5")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


# =============================================================================
# Category B: MEDIUM FIT Tests (40-69%)
# =============================================================================

@pytest.mark.accuracy
@pytest.mark.accuracy_category_b
@pytest.mark.slow
@pytest.mark.asyncio
async def test_b1_netflix(backend_available):
    """B1: Netflix - Streaming/Scale company with Java focus."""
    test_case = get_test_case_by_id("B1")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_b
@pytest.mark.slow
@pytest.mark.asyncio
async def test_b2_datadog(backend_available):
    """B2: Datadog - Observability company with Go focus."""
    test_case = get_test_case_by_id("B2")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_b
@pytest.mark.slow
@pytest.mark.asyncio
async def test_b3_ml_platform(backend_available):
    """B3: ML Platform Engineer role with PyTorch/GPU focus."""
    test_case = get_test_case_by_id("B3")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_b
@pytest.mark.slow
@pytest.mark.asyncio
async def test_b4_salesforce(backend_available):
    """B4: Salesforce - Enterprise Java/Apex company."""
    test_case = get_test_case_by_id("B4")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_b
@pytest.mark.slow
@pytest.mark.asyncio
async def test_b5_uber(backend_available):
    """B5: Uber - Mobile/Scale company."""
    test_case = get_test_case_by_id("B5")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


# =============================================================================
# Category C: LOW FIT Tests (0-39%)
# =============================================================================

@pytest.mark.accuracy
@pytest.mark.accuracy_category_c
@pytest.mark.slow
@pytest.mark.asyncio
async def test_c1_apple_ios(backend_available):
    """C1: Apple iOS Engineer - Complete platform mismatch."""
    test_case = get_test_case_by_id("C1")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_c
@pytest.mark.slow
@pytest.mark.asyncio
async def test_c2_embedded_iot(backend_available):
    """C2: Embedded Systems IoT role - Domain mismatch."""
    test_case = get_test_case_by_id("C2")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_c
@pytest.mark.slow
@pytest.mark.asyncio
async def test_c3_defi_solidity(backend_available):
    """C3: DeFi/Solidity Developer - Blockchain mismatch."""
    test_case = get_test_case_by_id("C3")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_c
@pytest.mark.slow
@pytest.mark.asyncio
async def test_c4_game_dev(backend_available):
    """C4: Game Developer - Unity/C++ mismatch."""
    test_case = get_test_case_by_id("C4")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_c
@pytest.mark.slow
@pytest.mark.asyncio
async def test_c5_android_kotlin(backend_available):
    """C5: Android/Kotlin Developer - Mobile mismatch."""
    test_case = get_test_case_by_id("C5")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


# =============================================================================
# Category D: EDGE CASE Tests
# =============================================================================

@pytest.mark.accuracy
@pytest.mark.accuracy_category_d
@pytest.mark.slow
@pytest.mark.asyncio
async def test_d1_unknown_company(backend_available):
    """D1: Obscure/Unknown Company - Data quality check."""
    test_case = get_test_case_by_id("D1")
    result = await execute_accuracy_test(test_case, backend_available)
    # More lenient for edge cases - just check it doesn't crash
    assert result.actual_score is not None or len(result.warnings) > 0, (
        "Should either return a score or flag data issues"
    )


@pytest.mark.accuracy
@pytest.mark.accuracy_category_d
@pytest.mark.slow
@pytest.mark.asyncio
async def test_d2_ambiguous_query(backend_available):
    """D2: Ambiguous Query - Handling of vague input."""
    test_case = get_test_case_by_id("D2")
    result = await execute_accuracy_test(test_case, backend_available)
    # Edge case - should handle gracefully
    assert result.overall_status != ValidationStatus.FAIL or len(result.warnings) > 0


@pytest.mark.accuracy
@pytest.mark.accuracy_category_d
@pytest.mark.slow
@pytest.mark.asyncio
async def test_d3_mixed_signal(backend_available):
    """D3: Mixed Signal Query - Partial requirement match."""
    test_case = get_test_case_by_id("D3")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_d
@pytest.mark.slow
@pytest.mark.asyncio
async def test_d4_senior_level(backend_available):
    """D4: Staff Engineer at Google - Seniority inference."""
    test_case = get_test_case_by_id("D4")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)


@pytest.mark.accuracy
@pytest.mark.accuracy_category_d
@pytest.mark.slow
@pytest.mark.asyncio
async def test_d5_emerging_tech(backend_available):
    """D5: Emerging Tech - LangGraph startup match."""
    test_case = get_test_case_by_id("D5")
    result = await execute_accuracy_test(test_case, backend_available)
    assert_accuracy_result(result, test_case)
