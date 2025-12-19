# Accuracy Testing Framework for Fit Check Pipeline

This directory contains a comprehensive accuracy testing framework for validating the Fit Check pipeline's ability to correctly assess engineer-employer fit.

## Overview

The accuracy testing framework systematically validates that the pipeline produces accurate match scores, confidence tiers, and gap identifications based on the engineer's known skill profile.

## Test Categories

### Category A: Expected HIGH FIT (70-100%)
Tests where the engineer should score well due to direct skill alignment.

| ID | Test Name | Query | Expected Score |
|----|-----------|-------|----------------|
| A1 | Vercel | "Vercel" | 75-90% |
| A2 | OpenAI | "OpenAI" | 55-75% |
| A3 | Stripe | "Stripe" | 60-75% |
| A4 | Full-Stack Startup | Full-stack Python/React role | 85-95% |
| A5 | Anthropic | "Anthropic" | 50-70% |

### Category B: Expected MEDIUM FIT (40-69%)
Tests with partial alignment - transferable skills but notable gaps.

| ID | Test Name | Query | Expected Score |
|----|-----------|-------|----------------|
| B1 | Netflix | "Netflix" | 40-55% |
| B2 | Datadog | "Datadog" | 45-60% |
| B3 | ML Platform | PyTorch/GPU role | 30-45% |
| B4 | Salesforce | "Salesforce" | 35-50% |
| B5 | Uber | "Uber" | 40-55% |

### Category C: Expected LOW FIT (0-39%)
Tests where the engineer lacks core requirements.

| ID | Test Name | Query | Expected Score |
|----|-----------|-------|----------------|
| C1 | Apple iOS | iOS Engineer at Apple | 10-25% |
| C2 | Embedded IoT | C/RTOS embedded role | 5-15% |
| C3 | DeFi Solidity | Solidity developer | 15-25% |
| C4 | Game Dev | Unity/C++ developer | 10-20% |
| C5 | Android | Kotlin/Android developer | 10-25% |

### Category D: Edge Cases
Ambiguous queries, obscure companies, malformed inputs.

| ID | Test Name | Query | Validation Point |
|----|-----------|-------|------------------|
| D1 | Unknown Company | "TechVenture Innovations LLC" | Data quality handling |
| D2 | Ambiguous Query | "Software" | Ambiguity detection |
| D3 | Mixed Signal | Java+Python+React role | Partial match handling |
| D4 | Senior Level | "Staff Engineer at Google" | Seniority inference |
| D5 | Emerging Tech | LangGraph startup | Direct skill match |

## Usage

### Standalone Runner

```bash
# Run all tests
python -m tests.simulation.accuracy.run_accuracy_tests

# Run specific category
python -m tests.simulation.accuracy.run_accuracy_tests --category A

# Run single test
python -m tests.simulation.accuracy.run_accuracy_tests --test-id A1

# Save results to file
python -m tests.simulation.accuracy.run_accuracy_tests --output results.json

# Dry run (show tests without executing)
python -m tests.simulation.accuracy.run_accuracy_tests --dry-run
```

### Pytest Integration

```bash
# Run all accuracy tests
pytest tests/simulation/accuracy/test_accuracy.py -v

# Run Category A only
pytest tests/simulation/accuracy/test_accuracy.py -v -m accuracy_category_a

# Run specific test
pytest tests/simulation/accuracy/test_accuracy.py::test_a1_vercel -v
```

## Accuracy Criteria

### Score Accuracy
- **ACCURATE**: |Actual - Expected| ≤ 15%
- **ACCEPTABLE**: |Actual - Expected| ≤ 25%
- **INACCURATE**: |Actual - Expected| > 25%

### Tier Accuracy
- **ACCURATE**: Exact tier match
- **ACCEPTABLE**: Adjacent tier (e.g., HIGH vs MEDIUM_HIGH)
- **INACCURATE**: Non-adjacent tier

### Pass/Fail Thresholds
| Category | Pass Threshold |
|----------|---------------|
| A (HIGH FIT) | ≥ 80% |
| B (MEDIUM FIT) | ≥ 75% |
| C (LOW FIT) | ≥ 80% |
| Tier Accuracy | ≥ 75% |

## Module Structure

```
accuracy/
├── __init__.py              # Module exports
├── test_definitions.py      # Test case definitions
├── accuracy_validator.py    # Validation utilities
├── failure_analyzer.py      # Root cause analysis
├── run_accuracy_tests.py    # Standalone test runner
├── test_accuracy.py         # Pytest-compatible tests
└── README.md               # This file
```

## Output

Results are saved to `tests/simulation/outputs/accuracy/` with:
- Accuracy report (human-readable)
- Failure analysis (for failed tests)
- Raw JSON results

## Root Cause Categories

When tests fail, the failure analyzer identifies potential causes:

1. **SYCOPHANCY**: Over-scoring (too generous)
2. **HARSH_SCORING**: Under-scoring (too critical)
3. **MISSING_GAP_DETECTION**: Gaps not properly identified
4. **INSUFFICIENT_RESEARCH_DATA**: Not enough data found
5. **TIER_CALIBRATION_ERROR**: Tier doesn't match score
6. **DOMAIN_KNOWLEDGE_GAP**: Prompts lack domain context
7. **QUERY_CLASSIFICATION_ERROR**: Query type misclassified

## Extending Tests

To add new test cases, edit `test_definitions.py`:

```python
TestCase(
    id="A6",
    category=TestCategory.A_HIGH_FIT,
    name="Your Test Name",
    query="Your test query",
    expected=ExpectedOutcome(
        score_min=70,
        score_max=85,
        confidence_tier=ConfidenceTier.HIGH,
        gap_count_min=0,
        gap_count_max=2,
        reasoning="Why this is expected",
    ),
    skill_alignment={
        "match": ["Skill1", "Skill2"],
        "partial": ["Skill3"],
        "gap": ["Skill4"],
    },
    key_validation="What this test validates",
)
```

## Requirements

- Backend container running at `localhost:8000`
- Python 3.11+
- `httpx` for async HTTP requests
- `pytest-asyncio` for async test support
