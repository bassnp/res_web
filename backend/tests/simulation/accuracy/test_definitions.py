"""
Test Case Definitions for Accuracy Testing.

This module defines all test cases with expected outcomes based on the engineer's
profile capabilities. Test cases are organized into four categories:

Category A: Expected HIGH Fit (70-100%)
    - Direct skill alignment with engineer profile
    
Category B: Expected MEDIUM Fit (40-69%)
    - Partial alignment with transferable skills but notable gaps
    
Category C: Expected LOW Fit (0-39%)
    - Fundamental skill mismatches
    
Category D: Edge Cases
    - Ambiguous queries, obscure companies, malformed inputs

Each test case includes:
    - Query string
    - Expected score range
    - Expected confidence tier
    - Expected gap count range
    - Visual reasoning explanation
    - Key validation points
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple


# =============================================================================
# Enums and Types
# =============================================================================

class TestCategory(str, Enum):
    """Test categories based on expected fit level."""
    A_HIGH_FIT = "A"       # 70-100% expected
    B_MEDIUM_FIT = "B"     # 40-69% expected
    C_LOW_FIT = "C"        # 0-39% expected
    D_EDGE_CASES = "D"     # Edge cases with special handling


class ConfidenceTier(str, Enum):
    """Expected confidence tier classifications."""
    HIGH = "HIGH"
    MEDIUM_HIGH = "MEDIUM_HIGH"
    MEDIUM = "MEDIUM"
    LOW_MEDIUM = "LOW_MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ExpectedOutcome:
    """
    Expected outcome for a test case.
    
    Attributes:
        score_min: Minimum expected score (0-100)
        score_max: Maximum expected score (0-100)
        confidence_tier: Primary expected confidence tier
        confidence_tier_acceptable: List of acceptable alternative tiers
        gap_count_min: Minimum expected number of gaps identified
        gap_count_max: Maximum expected number of gaps identified
        quality_flags: Expected quality flags (for edge cases)
        reasoning: Human-readable reasoning for the expected outcome
    """
    score_min: int
    score_max: int
    confidence_tier: ConfidenceTier
    confidence_tier_acceptable: List[ConfidenceTier] = field(default_factory=list)
    gap_count_min: int = 0
    gap_count_max: int = 10
    quality_flags: List[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class TestCase:
    """
    A single accuracy test case.
    
    Attributes:
        id: Unique test case identifier (e.g., "A1", "B2", "C3")
        category: Test category (A, B, C, or D)
        name: Human-readable test name
        query: The query string to test
        expected: Expected outcome object
        skill_alignment: Key skills that should/shouldn't match
        description: Detailed description of what this tests
        key_validation: The primary thing being validated
    """
    id: str
    category: TestCategory
    name: str
    query: str
    expected: ExpectedOutcome
    skill_alignment: Dict[str, List[str]] = field(default_factory=dict)
    description: str = ""
    key_validation: str = ""


# =============================================================================
# Category A: Expected HIGH Fit (70-100%)
# =============================================================================

CATEGORY_A_HIGH_FIT: List[TestCase] = [
    TestCase(
        id="A1",
        category=TestCategory.A_HIGH_FIT,
        name="Vercel (Frontend-Focused Company)",
        query="Vercel",
        expected=ExpectedOutcome(
            score_min=75,
            score_max=90,
            confidence_tier=ConfidenceTier.HIGH,
            confidence_tier_acceptable=[ConfidenceTier.MEDIUM_HIGH],
            gap_count_min=0,
            gap_count_max=2,
            reasoning="Direct alignment with Next.js, React, TypeScript stack",
        ),
        skill_alignment={
            "match": ["Next.js", "React", "TypeScript", "JavaScript"],
            "partial": ["Edge Computing", "Serverless"],
            "gap": [],
        },
        description="Tests matching against a frontend-focused company with Next.js emphasis",
        key_validation="Next.js/React direct match",
    ),
    
    TestCase(
        id="A2",
        category=TestCategory.A_HIGH_FIT,
        name="OpenAI (AI Engineering Company)",
        query="OpenAI",
        expected=ExpectedOutcome(
            score_min=55,
            score_max=75,
            confidence_tier=ConfidenceTier.MEDIUM_HIGH,
            confidence_tier_acceptable=[ConfidenceTier.HIGH, ConfidenceTier.MEDIUM],
            gap_count_min=2,
            gap_count_max=4,
            reasoning="Strong applied AI skills, but research depth gap",
        ),
        skill_alignment={
            "match": ["Python", "LangChain", "LangGraph", "FastAPI", "Prompt Engineering"],
            "partial": ["API Development", "AI Systems"],
            "gap": ["ML Research", "PhD", "Publications", "Distributed Systems at Scale"],
        },
        description="Tests matching against premier AI research company",
        key_validation="AI skills present, research background gap",
    ),
    
    TestCase(
        id="A3",
        category=TestCategory.A_HIGH_FIT,
        name="Stripe (Backend/API Company)",
        query="Stripe",
        expected=ExpectedOutcome(
            score_min=60,
            score_max=75,
            confidence_tier=ConfidenceTier.MEDIUM_HIGH,
            confidence_tier_acceptable=[ConfidenceTier.MEDIUM, ConfidenceTier.HIGH],
            gap_count_min=2,
            gap_count_max=4,
            reasoning="API design skills transfer, but Ruby and fintech domain gap",
        ),
        skill_alignment={
            "match": ["REST APIs", "FastAPI", "Python", "PostgreSQL"],
            "partial": ["Backend Systems", "API Design"],
            "gap": ["Ruby", "Fintech Domain", "Payment Systems", "Scale"],
        },
        description="Tests matching against payments/API infrastructure company",
        key_validation="API skills transfer, Ruby gap",
    ),
    
    TestCase(
        id="A4",
        category=TestCategory.A_HIGH_FIT,
        name="Full-Stack Python/React Startup",
        query="Full-stack engineer position using Python, React, and PostgreSQL for a SaaS startup",
        expected=ExpectedOutcome(
            score_min=85,
            score_max=95,
            confidence_tier=ConfidenceTier.HIGH,
            confidence_tier_acceptable=[],
            gap_count_min=0,
            gap_count_max=1,
            reasoning="Near-perfect stack alignment with all core requirements",
        ),
        skill_alignment={
            "match": ["Python", "React", "PostgreSQL", "Full-Stack"],
            "partial": ["SaaS patterns"],
            "gap": [],
        },
        description="Tests perfect skill match for typical startup role",
        key_validation="Perfect stack match",
    ),
    
    TestCase(
        id="A5",
        category=TestCategory.A_HIGH_FIT,
        name="Anthropic (AI Safety Company)",
        query="Anthropic",
        expected=ExpectedOutcome(
            score_min=50,
            score_max=70,
            confidence_tier=ConfidenceTier.MEDIUM,
            confidence_tier_acceptable=[ConfidenceTier.MEDIUM_HIGH, ConfidenceTier.LOW_MEDIUM],
            gap_count_min=2,
            gap_count_max=4,
            reasoning="Applied AI skills present, research/safety specialization gap",
        ),
        skill_alignment={
            "match": ["Python", "LangChain", "AI Integration"],
            "partial": ["LLM Development"],
            "gap": ["AI Safety Research", "PhD", "Publications"],
        },
        description="Tests matching against AI safety research company",
        key_validation="Applied AI vs research depth",
    ),
]


# =============================================================================
# Category B: Expected MEDIUM Fit (40-69%)
# =============================================================================

CATEGORY_B_MEDIUM_FIT: List[TestCase] = [
    TestCase(
        id="B1",
        category=TestCategory.B_MEDIUM_FIT,
        name="Netflix (Streaming/Scale Company)",
        query="Netflix",
        expected=ExpectedOutcome(
            score_min=40,
            score_max=55,
            confidence_tier=ConfidenceTier.MEDIUM,
            confidence_tier_acceptable=[ConfidenceTier.LOW_MEDIUM],
            gap_count_min=3,
            gap_count_max=5,
            reasoning="Frontend aligns with React, but backend Java/scale gap",
        ),
        skill_alignment={
            "match": ["React", "JavaScript"],
            "partial": ["Frontend", "Web Development"],
            "gap": ["Java", "Microservices at Scale", "Distributed Systems", "AWS Deep"],
        },
        description="Tests matching against streaming company with Java/scale focus",
        key_validation="Java/scale gap",
    ),
    
    TestCase(
        id="B2",
        category=TestCategory.B_MEDIUM_FIT,
        name="Datadog (Observability/Go Company)",
        query="Datadog",
        expected=ExpectedOutcome(
            score_min=45,
            score_max=60,
            confidence_tier=ConfidenceTier.MEDIUM,
            confidence_tier_acceptable=[ConfidenceTier.LOW_MEDIUM],
            gap_count_min=2,
            gap_count_max=4,
            reasoning="Python transfers, but Go and Kubernetes expertise gap",
        ),
        skill_alignment={
            "match": ["Python", "React"],
            "partial": ["Cloud Infrastructure", "Docker"],
            "gap": ["Go", "Kubernetes", "Observability Domain"],
        },
        description="Tests matching against observability company with Go/K8s focus",
        key_validation="Go/K8s gap",
    ),
    
    TestCase(
        id="B3",
        category=TestCategory.B_MEDIUM_FIT,
        name="ML Platform Engineer Role",
        query="ML Engineer building training pipelines with PyTorch and distributed GPU computing",
        expected=ExpectedOutcome(
            score_min=30,
            score_max=45,
            confidence_tier=ConfidenceTier.LOW_MEDIUM,
            confidence_tier_acceptable=[ConfidenceTier.LOW, ConfidenceTier.MEDIUM],
            gap_count_min=4,
            gap_count_max=6,
            reasoning="Python base present, but ML infrastructure stack missing",
        ),
        skill_alignment={
            "match": ["Python"],
            "partial": ["AI/ML Concepts"],
            "gap": ["PyTorch", "GPU/CUDA", "Training Pipelines", "Distributed Computing"],
        },
        description="Tests matching against ML infrastructure role",
        key_validation="PyTorch/GPU gap",
    ),
    
    TestCase(
        id="B4",
        category=TestCategory.B_MEDIUM_FIT,
        name="Salesforce (Enterprise Java/Apex)",
        query="Salesforce",
        expected=ExpectedOutcome(
            score_min=35,
            score_max=50,
            confidence_tier=ConfidenceTier.LOW_MEDIUM,
            confidence_tier_acceptable=[ConfidenceTier.MEDIUM, ConfidenceTier.LOW],
            gap_count_min=3,
            gap_count_max=5,
            reasoning="React/web skills transfer, but Java/Apex ecosystem gap",
        ),
        skill_alignment={
            "match": ["React"],
            "partial": ["Frontend", "Cloud"],
            "gap": ["Java", "Apex", "CRM Domain", "Enterprise Architecture"],
        },
        description="Tests matching against enterprise platform company",
        key_validation="Apex/enterprise gap",
    ),
    
    TestCase(
        id="B5",
        category=TestCategory.B_MEDIUM_FIT,
        name="Uber (Mobile/Scale Company)",
        query="Uber",
        expected=ExpectedOutcome(
            score_min=40,
            score_max=55,
            confidence_tier=ConfidenceTier.MEDIUM,
            confidence_tier_acceptable=[ConfidenceTier.LOW_MEDIUM],
            gap_count_min=2,
            gap_count_max=4,
            reasoning="Backend concepts transfer, but mobile and scale gaps",
        ),
        skill_alignment={
            "match": ["Python", "REST APIs"],
            "partial": ["Backend", "Microservices"],
            "gap": ["Mobile Development", "Go", "Large Scale Systems"],
        },
        description="Tests matching against rideshare company",
        key_validation="Mobile/scale requirements",
    ),
]


# =============================================================================
# Category C: Expected LOW Fit (0-39%)
# =============================================================================

CATEGORY_C_LOW_FIT: List[TestCase] = [
    TestCase(
        id="C1",
        category=TestCategory.C_LOW_FIT,
        name="Apple iOS Engineer",
        query="iOS Engineer at Apple",
        expected=ExpectedOutcome(
            score_min=10,
            score_max=25,
            confidence_tier=ConfidenceTier.LOW,
            confidence_tier_acceptable=[ConfidenceTier.INSUFFICIENT],
            gap_count_min=5,
            gap_count_max=8,
            reasoning="Complete platform mismatch - no iOS/Swift experience",
        ),
        skill_alignment={
            "match": [],
            "partial": ["Programming fundamentals", "Problem solving"],
            "gap": ["Swift", "iOS SDK", "Objective-C", "UIKit", "SwiftUI", "App Store"],
        },
        description="Tests recognition of complete platform mismatch",
        key_validation="Swift/iOS missing",
    ),
    
    TestCase(
        id="C2",
        category=TestCategory.C_LOW_FIT,
        name="Embedded Systems IoT Role",
        query="Embedded software engineer for IoT devices using C and RTOS",
        expected=ExpectedOutcome(
            score_min=5,
            score_max=15,
            confidence_tier=ConfidenceTier.INSUFFICIENT,
            confidence_tier_acceptable=[ConfidenceTier.LOW],
            gap_count_min=5,
            gap_count_max=8,
            reasoning="Fundamentally different domain - no embedded experience",
        ),
        skill_alignment={
            "match": [],
            "partial": [],
            "gap": ["C", "RTOS", "Hardware Interfaces", "Memory Management", "IoT Protocols"],
        },
        description="Tests recognition of domain mismatch",
        key_validation="C/RTOS missing",
    ),
    
    TestCase(
        id="C3",
        category=TestCategory.C_LOW_FIT,
        name="DeFi/Solidity Developer",
        query="Solidity developer for DeFi protocols on Ethereum",
        expected=ExpectedOutcome(
            score_min=15,
            score_max=25,
            confidence_tier=ConfidenceTier.LOW,
            confidence_tier_acceptable=[ConfidenceTier.INSUFFICIENT],
            gap_count_min=5,
            gap_count_max=8,
            reasoning="JavaScript knowledge present, but blockchain stack missing",
        ),
        skill_alignment={
            "match": ["JavaScript"],
            "partial": [],
            "gap": ["Solidity", "Smart Contracts", "Ethereum/EVM", "DeFi Protocols", "Web3.js"],
        },
        description="Tests recognition of blockchain domain mismatch",
        key_validation="Blockchain stack missing",
    ),
    
    TestCase(
        id="C4",
        category=TestCategory.C_LOW_FIT,
        name="Game Developer (Unity/C++)",
        query="Game developer using Unity and C++ for AAA games",
        expected=ExpectedOutcome(
            score_min=10,
            score_max=20,
            confidence_tier=ConfidenceTier.INSUFFICIENT,
            confidence_tier_acceptable=[ConfidenceTier.LOW],
            gap_count_min=5,
            gap_count_max=8,
            reasoning="Different programming paradigm - no game dev experience",
        ),
        skill_alignment={
            "match": [],
            "partial": ["Problem solving"],
            "gap": ["C++", "Unity", "C#", "Game Physics", "3D Graphics", "Shaders"],
        },
        description="Tests recognition of game dev domain mismatch",
        key_validation="C++/Unity missing",
    ),
    
    TestCase(
        id="C5",
        category=TestCategory.C_LOW_FIT,
        name="Android/Kotlin Developer",
        query="Android developer with Kotlin expertise for mobile fintech app",
        expected=ExpectedOutcome(
            score_min=10,
            score_max=25,
            confidence_tier=ConfidenceTier.LOW,
            confidence_tier_acceptable=[ConfidenceTier.INSUFFICIENT, ConfidenceTier.INSUFFICIENT_DATA],
            gap_count_min=4,
            gap_count_max=7,
            reasoning="Mobile platform mismatch - no Android/Kotlin experience",
        ),
        skill_alignment={
            "match": [],
            "partial": ["Programming", "API Integration"],
            "gap": ["Kotlin", "Android SDK", "Jetpack", "Mobile UI", "Fintech Domain"],
        },
        description="Tests recognition of Android platform mismatch",
        key_validation="Kotlin/Android missing",
    ),
]


# =============================================================================
# Category D: Edge Cases
# =============================================================================

CATEGORY_D_EDGE_CASES: List[TestCase] = [
    TestCase(
        id="D1",
        category=TestCategory.D_EDGE_CASES,
        name="Obscure/Unknown Company",
        query="TechVenture Innovations LLC 2024",
        expected=ExpectedOutcome(
            score_min=0,  # N/A is acceptable
            score_max=50,
            confidence_tier=ConfidenceTier.INSUFFICIENT_DATA,
            confidence_tier_acceptable=[ConfidenceTier.LOW, ConfidenceTier.MEDIUM],
            gap_count_min=0,
            gap_count_max=5,
            quality_flags=["INSUFFICIENT_DATA", "SPARSE", "UNVERIFIED"],
            reasoning="Cannot verify company - should gracefully degrade",
        ),
        skill_alignment={},
        description="Tests graceful degradation for unknown companies",
        key_validation="Data quality check - no fabrication",
    ),
    
    TestCase(
        id="D2",
        category=TestCategory.D_EDGE_CASES,
        name="Ambiguous Query",
        query="Software",
        expected=ExpectedOutcome(
            score_min=40,
            score_max=60,
            confidence_tier=ConfidenceTier.LOW,
            confidence_tier_acceptable=[ConfidenceTier.MEDIUM, ConfidenceTier.LOW_MEDIUM],
            gap_count_min=0,
            gap_count_max=3,
            quality_flags=["AMBIGUOUS_QUERY"],
            reasoning="Too vague for accurate matching - should flag ambiguity",
        ),
        skill_alignment={},
        description="Tests handling of overly vague queries",
        key_validation="Ambiguity handling",
    ),
    
    TestCase(
        id="D3",
        category=TestCategory.D_EDGE_CASES,
        name="Mixed Signal Query (Partial Match)",
        query="Full-stack developer with Java, Python, and React experience for fintech",
        expected=ExpectedOutcome(
            score_min=55,
            score_max=80,  # Higher max since Python + React is 2/3 of tech requirements
            confidence_tier=ConfidenceTier.MEDIUM,
            confidence_tier_acceptable=[ConfidenceTier.MEDIUM_HIGH, ConfidenceTier.HIGH, ConfidenceTier.LOW_MEDIUM],
            gap_count_min=2,
            gap_count_max=7,  # More gaps from web research about fintech requirements
            reasoning="2/3 languages match (Python, React), Java and fintech gap",
        ),
        skill_alignment={
            "match": ["Python", "React"],
            "partial": ["Full-Stack"],
            "gap": ["Java", "Fintech Domain"],
        },
        description="Tests handling of partial requirement matches",
        key_validation="Partial match handling",
    ),
    
    TestCase(
        id="D4",
        category=TestCategory.D_EDGE_CASES,
        name="Senior/Staff Level (Seniority Inference)",
        query="Staff Software Engineer at Google",
        expected=ExpectedOutcome(
            score_min=35,
            score_max=50,
            confidence_tier=ConfidenceTier.MEDIUM,
            confidence_tier_acceptable=[ConfidenceTier.LOW_MEDIUM, ConfidenceTier.LOW],
            gap_count_min=3,
            gap_count_max=6,
            reasoning="Technical skills partial, seniority/experience gap significant",
        ),
        skill_alignment={
            "match": ["Python"],
            "partial": ["Backend", "System Design"],
            "gap": ["10+ Years Experience", "Technical Leadership", "Scale", "PhD"],
        },
        description="Tests seniority level inference and gap identification",
        key_validation="Seniority inference",
    ),
    
    TestCase(
        id="D5",
        category=TestCategory.D_EDGE_CASES,
        name="Emerging Tech Company",
        query="Startup using AI agents with LangGraph for enterprise automation",
        expected=ExpectedOutcome(
            score_min=80,
            score_max=95,
            confidence_tier=ConfidenceTier.HIGH,
            confidence_tier_acceptable=[ConfidenceTier.MEDIUM_HIGH],
            gap_count_min=0,
            gap_count_max=4,  # Web research may identify additional enterprise-scale requirements
            reasoning="Direct match with LangGraph/AI agent expertise",
        ),
        skill_alignment={
            "match": ["LangGraph", "AI Agents", "Python", "Enterprise Integration"],
            "partial": [],
            "gap": [],
        },
        description="Tests matching against cutting-edge AI role",
        key_validation="LangGraph direct match",
    ),
]


# =============================================================================
# Utility Functions
# =============================================================================

def get_all_test_cases() -> List[TestCase]:
    """
    Get all test cases across all categories.
    
    Returns:
        List of all TestCase objects.
    """
    return (
        CATEGORY_A_HIGH_FIT +
        CATEGORY_B_MEDIUM_FIT +
        CATEGORY_C_LOW_FIT +
        CATEGORY_D_EDGE_CASES
    )


def get_test_cases_by_category(category: TestCategory) -> List[TestCase]:
    """
    Get test cases for a specific category.
    
    Args:
        category: The test category to filter by.
        
    Returns:
        List of TestCase objects for that category.
    """
    category_map = {
        TestCategory.A_HIGH_FIT: CATEGORY_A_HIGH_FIT,
        TestCategory.B_MEDIUM_FIT: CATEGORY_B_MEDIUM_FIT,
        TestCategory.C_LOW_FIT: CATEGORY_C_LOW_FIT,
        TestCategory.D_EDGE_CASES: CATEGORY_D_EDGE_CASES,
    }
    return category_map.get(category, [])


def get_test_case_by_id(test_id: str) -> Optional[TestCase]:
    """
    Get a specific test case by ID.
    
    Args:
        test_id: The test case ID (e.g., "A1", "B2").
        
    Returns:
        TestCase if found, None otherwise.
    """
    for test in get_all_test_cases():
        if test.id == test_id:
            return test
    return None


def get_expected_score_range(category: TestCategory) -> Tuple[int, int]:
    """
    Get the expected score range for a category.
    
    Args:
        category: The test category.
        
    Returns:
        Tuple of (min_score, max_score).
    """
    ranges = {
        TestCategory.A_HIGH_FIT: (70, 100),
        TestCategory.B_MEDIUM_FIT: (40, 69),
        TestCategory.C_LOW_FIT: (0, 39),
        TestCategory.D_EDGE_CASES: (0, 100),  # Variable
    }
    return ranges.get(category, (0, 100))


# =============================================================================
# Summary Generation
# =============================================================================

def generate_test_summary() -> str:
    """
    Generate a summary of all test cases.
    
    Returns:
        Formatted string with test case summary.
    """
    lines = [
        "=" * 70,
        "  ACCURACY TEST CASE SUMMARY",
        "=" * 70,
        "",
    ]
    
    for category in TestCategory:
        tests = get_test_cases_by_category(category)
        min_score, max_score = get_expected_score_range(category)
        
        lines.append(f"Category {category.value}: Expected {min_score}-{max_score}%")
        lines.append("-" * 50)
        
        for test in tests:
            exp = test.expected
            lines.append(
                f"  {test.id}: {test.name}"
            )
            lines.append(
                f"      Query: \"{test.query[:50]}{'...' if len(test.query) > 50 else ''}\""
            )
            lines.append(
                f"      Expected: {exp.score_min}-{exp.score_max}% | Tier: {exp.confidence_tier.value}"
            )
            lines.append(
                f"      Validation: {test.key_validation}"
            )
            lines.append("")
        
        lines.append("")
    
    lines.append("=" * 70)
    lines.append(f"  Total Test Cases: {len(get_all_test_cases())}")
    lines.append("=" * 70)
    
    return "\n".join(lines)
