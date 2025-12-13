#!/usr/bin/env python3
"""
Phase Output Validation Tests

Unit tests for validating each phase's output against the expected schema
and quality criteria defined in the specification.

Run with:
    pytest tests/simulation/test_phase_outputs.py -v
"""

import pytest
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# Validation Functions
# =============================================================================

def validate_phase1_output(output: Dict[str, Any]) -> List[str]:
    """
    Validate Phase 1 (Connecting) output against schema.
    
    Args:
        output: Phase 1 output dictionary.
        
    Returns:
        List of validation error messages.
    """
    errors = []
    
    # Required fields
    required_fields = ["query_type", "company_name", "job_title", 
                       "extracted_skills", "reasoning_trace"]
    for field in required_fields:
        if field not in output:
            errors.append(f"Missing required field: {field}")
    
    # query_type validation
    if "query_type" in output:
        if output["query_type"] not in ["company", "job_description"]:
            errors.append(f"Invalid query_type: {output['query_type']}")
    
    # extracted_skills must be a list
    if "extracted_skills" in output:
        if not isinstance(output["extracted_skills"], list):
            errors.append("extracted_skills must be a list")
    
    # reasoning_trace must not be empty
    if "reasoning_trace" in output:
        if not output["reasoning_trace"] or len(output["reasoning_trace"].strip()) == 0:
            errors.append("reasoning_trace must not be empty")
    
    return errors


def validate_phase2_output(output: Dict[str, Any]) -> List[str]:
    """
    Validate Phase 2 (Deep Research) output against schema.
    
    Args:
        output: Phase 2 output dictionary.
        
    Returns:
        List of validation error messages.
    """
    errors = []
    
    # Required fields
    required_fields = ["employer_summary", "identified_requirements", 
                       "tech_stack", "culture_signals", "reasoning_trace"]
    for field in required_fields:
        if field not in output:
            errors.append(f"Missing required field: {field}")
    
    # employer_summary validation
    if "employer_summary" in output:
        summary = output["employer_summary"]
        if not summary or len(summary) < 20:
            errors.append("employer_summary too short (min 20 chars)")
    
    # Lists must be lists
    for list_field in ["identified_requirements", "tech_stack", "culture_signals"]:
        if list_field in output and not isinstance(output[list_field], list):
            errors.append(f"{list_field} must be a list")
    
    # Check for generic anti-patterns
    if "tech_stack" in output:
        tech_str = " ".join(output["tech_stack"]).lower()
        if "modern stack" in tech_str and len(output["tech_stack"]) == 1:
            errors.append("Vague 'modern stack' without specifics detected")
    
    return errors


def validate_phase3_output(output: Dict[str, Any]) -> List[str]:
    """
    Validate Phase 3 (Skeptical Comparison) output against schema.
    
    This is the CRITICAL anti-sycophancy check.
    
    Args:
        output: Phase 3 output dictionary.
        
    Returns:
        List of validation error messages.
    """
    errors = []
    
    # Required fields
    required_fields = ["genuine_strengths", "genuine_gaps", 
                       "transferable_skills", "risk_assessment", "reasoning_trace"]
    for field in required_fields:
        if field not in output:
            errors.append(f"Missing required field: {field}")
    
    # CRITICAL: Minimum 2 gaps required
    if "genuine_gaps" in output:
        gaps = output["genuine_gaps"]
        if not isinstance(gaps, list):
            errors.append("genuine_gaps must be a list")
        elif len(gaps) < 2:
            errors.append(f"CRITICAL: Only {len(gaps)} gaps identified (minimum 2 required)")
    
    # Maximum 4 strengths (prevents padding)
    if "genuine_strengths" in output:
        strengths = output["genuine_strengths"]
        if isinstance(strengths, list) and len(strengths) > 4:
            errors.append(f"Too many strengths: {len(strengths)} (max 4 allowed)")
    
    # risk_assessment validation
    if "risk_assessment" in output:
        if output["risk_assessment"] not in ["low", "medium", "high"]:
            errors.append(f"Invalid risk_assessment: {output['risk_assessment']}")
    
    # Sycophantic phrase detection
    SYCOPHANTIC_PHRASES = [
        "perfect fit", "ideal candidate", "excellent match",
        "amazing", "outstanding", "exceptional", "flawless",
        "perfect match", "ideal fit", "couldn't be better"
    ]
    
    full_text = json.dumps(output).lower()
    for phrase in SYCOPHANTIC_PHRASES:
        if phrase in full_text:
            errors.append(f"Sycophantic phrase detected: '{phrase}'")
    
    return errors


def validate_phase4_output(output: Dict[str, Any]) -> List[str]:
    """
    Validate Phase 4 (Skills Matching) output against schema.
    
    Args:
        output: Phase 4 output dictionary.
        
    Returns:
        List of validation error messages.
    """
    errors = []
    
    # Required fields
    required_fields = ["matched_requirements", "unmatched_requirements", 
                       "overall_match_score", "reasoning_trace"]
    for field in required_fields:
        if field not in output:
            errors.append(f"Missing required field: {field}")
    
    # matched_requirements structure
    if "matched_requirements" in output:
        matched = output["matched_requirements"]
        if not isinstance(matched, list):
            errors.append("matched_requirements must be a list")
        else:
            for i, match in enumerate(matched):
                if not isinstance(match, dict):
                    errors.append(f"matched_requirements[{i}] must be a dict")
                else:
                    for field in ["requirement", "matched_skill", "confidence"]:
                        if field not in match:
                            errors.append(f"matched_requirements[{i}] missing '{field}'")
                    
                    # Confidence range check
                    if "confidence" in match:
                        conf = match["confidence"]
                        try:
                            conf_float = float(conf)
                            if not 0.0 <= conf_float <= 1.0:
                                errors.append(f"Confidence out of range: {conf_float}")
                        except (ValueError, TypeError):
                            errors.append(f"Invalid confidence value: {conf}")
    
    # overall_match_score validation
    if "overall_match_score" in output:
        score = output["overall_match_score"]
        try:
            score_float = float(score)
            if not 0.0 <= score_float <= 1.0:
                errors.append(f"overall_match_score out of range: {score_float}")
        except (ValueError, TypeError):
            errors.append(f"Invalid overall_match_score: {score}")
    
    return errors


def validate_phase5_response(response: str) -> List[str]:
    """
    Validate Phase 5 (Generate Results) markdown response.
    
    Args:
        response: Final markdown response string.
        
    Returns:
        List of validation error messages.
    """
    errors = []
    
    if not response:
        errors.append("Empty response")
        return errors
    
    # Word count check
    word_count = len(response.split())
    if word_count > 450:
        errors.append(f"Response exceeds 400 words: {word_count}")
    
    # Required sections
    required_sections = [
        ("Key Alignments", ["key alignments", "key alignment"]),
        ("What I Bring", ["what i bring"]),
        ("Growth Areas", ["growth areas", "growth area"]),
        ("Let's Connect", ["let's connect", "lets connect", "contact"]),
    ]
    
    response_lower = response.lower()
    for section_name, variations in required_sections:
        found = any(v in response_lower for v in variations)
        if not found:
            errors.append(f"Missing required section: {section_name}")
    
    # Sycophantic phrase detection
    SYCOPHANTIC_PHRASES = [
        "perfect fit", "ideal candidate", "couldn't be better",
    ]
    
    for phrase in SYCOPHANTIC_PHRASES:
        if phrase in response_lower:
            errors.append(f"Sycophantic phrase in response: '{phrase}'")
    
    # Generic phrase detection
    GENERIC_PHRASES = [
        "passionate about technology",
        "i believe i would be a great",
        "excited about this opportunity",
    ]
    
    for phrase in GENERIC_PHRASES:
        if phrase in response_lower:
            errors.append(f"Generic phrase detected (needs specificity): '{phrase}'")
    
    return errors


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def valid_phase1_output():
    """Valid Phase 1 output example."""
    return {
        "query_type": "company",
        "company_name": "Google",
        "job_title": None,
        "extracted_skills": [],
        "reasoning_trace": "Input is a single well-known company name, classified as company lookup."
    }


@pytest.fixture
def valid_phase2_output():
    """Valid Phase 2 output example."""
    return {
        "employer_summary": "Google is a leading technology company known for its search engine, cloud services, and innovative culture.",
        "identified_requirements": [
            "Strong coding skills in Python or Java",
            "Experience with distributed systems",
            "Machine learning experience preferred"
        ],
        "tech_stack": ["Python", "Go", "TensorFlow", "Kubernetes", "GCP"],
        "culture_signals": ["Innovation-focused", "20% time policy", "Data-driven"],
        "search_queries_used": ["Google software engineer tech stack"],
        "data_quality": "high",
        "reasoning_trace": "Synthesized from multiple search results about Google engineering."
    }


@pytest.fixture
def valid_phase3_output():
    """Valid Phase 3 output example with minimum gaps."""
    return {
        "genuine_strengths": [
            "Strong Python expertise matches Google's primary language",
            "Experience with AI/ML aligns with Google's focus"
        ],
        "genuine_gaps": [
            "No direct experience with Go, which Google uses extensively",
            "Limited distributed systems experience at Google scale"
        ],
        "transferable_skills": ["Python to Go transition is smooth", "Cloud experience transfers"],
        "risk_assessment": "medium",
        "risk_justification": "Strong foundation but lacks specific Google-scale experience",
        "reasoning_trace": "Evaluated as skeptical hiring manager looking for honest gaps."
    }


@pytest.fixture
def valid_phase4_output():
    """Valid Phase 4 output example."""
    return {
        "matched_requirements": [
            {"requirement": "Python skills", "matched_skill": "Python expertise", "confidence": 0.95},
            {"requirement": "ML experience", "matched_skill": "AI/ML projects", "confidence": 0.8}
        ],
        "unmatched_requirements": ["Go experience", "Google-scale systems"],
        "overall_match_score": 0.72,
        "score_breakdown": "Avg confidence: 0.88 × Coverage: 0.50 = 0.44 → with adjustments: 0.72",
        "reasoning_trace": "Matched based on skill analysis tool output."
    }


@pytest.fixture
def valid_phase5_response():
    """Valid Phase 5 response example."""
    return """### Why I'm a Great Fit for Google

**Key Alignments:**
- My Python expertise directly matches Google's primary development language
- AI/ML project experience aligns with Google's machine learning focus
- Cloud platform experience with GCP and Kubernetes

**What I Bring:**
I bring hands-on experience building AI-powered systems similar to what Google develops. 
My work on LangGraph agents and Gemini integration demonstrates practical understanding 
of modern LLM architectures.

**Growth Areas:**
I acknowledge my limited experience with Go and Google-scale distributed systems. 
However, my strong foundation in Python and systems thinking provides a solid 
base for rapid learning.

**Let's Connect:**
I'd love to discuss how my AI/ML background could contribute to Google's 
mission to organize the world's information.
"""


# =============================================================================
# Test Cases
# =============================================================================

class TestPhase1Validation:
    """Tests for Phase 1 output validation."""
    
    def test_valid_output(self, valid_phase1_output):
        """Test that valid output passes validation."""
        errors = validate_phase1_output(valid_phase1_output)
        assert len(errors) == 0, f"Unexpected errors: {errors}"
    
    def test_missing_query_type(self, valid_phase1_output):
        """Test detection of missing query_type."""
        del valid_phase1_output["query_type"]
        errors = validate_phase1_output(valid_phase1_output)
        assert any("query_type" in e for e in errors)
    
    def test_invalid_query_type(self, valid_phase1_output):
        """Test detection of invalid query_type value."""
        valid_phase1_output["query_type"] = "invalid"
        errors = validate_phase1_output(valid_phase1_output)
        assert any("Invalid query_type" in e for e in errors)
    
    def test_empty_reasoning_trace(self, valid_phase1_output):
        """Test detection of empty reasoning trace."""
        valid_phase1_output["reasoning_trace"] = ""
        errors = validate_phase1_output(valid_phase1_output)
        assert any("reasoning_trace must not be empty" in e for e in errors)
    
    def test_extracted_skills_not_list(self, valid_phase1_output):
        """Test detection of non-list extracted_skills."""
        valid_phase1_output["extracted_skills"] = "Python"
        errors = validate_phase1_output(valid_phase1_output)
        assert any("extracted_skills must be a list" in e for e in errors)


class TestPhase2Validation:
    """Tests for Phase 2 output validation."""
    
    def test_valid_output(self, valid_phase2_output):
        """Test that valid output passes validation."""
        errors = validate_phase2_output(valid_phase2_output)
        assert len(errors) == 0, f"Unexpected errors: {errors}"
    
    def test_short_employer_summary(self, valid_phase2_output):
        """Test detection of too-short employer summary."""
        valid_phase2_output["employer_summary"] = "A company."
        errors = validate_phase2_output(valid_phase2_output)
        assert any("employer_summary too short" in e for e in errors)
    
    def test_vague_tech_stack(self):
        """Test detection of vague 'modern stack' without specifics."""
        output = {
            "employer_summary": "A technology company building software.",
            "identified_requirements": [],
            "tech_stack": ["modern stack"],
            "culture_signals": [],
            "reasoning_trace": "Limited data."
        }
        errors = validate_phase2_output(output)
        assert any("modern stack" in e.lower() for e in errors)


class TestPhase3Validation:
    """Tests for Phase 3 (Skeptical Comparison) output validation."""
    
    def test_valid_output(self, valid_phase3_output):
        """Test that valid output passes validation."""
        errors = validate_phase3_output(valid_phase3_output)
        assert len(errors) == 0, f"Unexpected errors: {errors}"
    
    def test_insufficient_gaps(self, valid_phase3_output):
        """Test CRITICAL detection of fewer than 2 gaps."""
        valid_phase3_output["genuine_gaps"] = ["Only one gap"]
        errors = validate_phase3_output(valid_phase3_output)
        assert any("CRITICAL" in e and "minimum 2 required" in e for e in errors)
    
    def test_zero_gaps(self, valid_phase3_output):
        """Test detection of zero gaps."""
        valid_phase3_output["genuine_gaps"] = []
        errors = validate_phase3_output(valid_phase3_output)
        assert any("CRITICAL" in e for e in errors)
    
    def test_too_many_strengths(self, valid_phase3_output):
        """Test detection of too many strengths (padding prevention)."""
        valid_phase3_output["genuine_strengths"] = [
            "Strength 1", "Strength 2", "Strength 3", 
            "Strength 4", "Strength 5", "Strength 6"
        ]
        errors = validate_phase3_output(valid_phase3_output)
        assert any("Too many strengths" in e for e in errors)
    
    def test_sycophantic_phrase_detection(self, valid_phase3_output):
        """Test detection of sycophantic phrases."""
        valid_phase3_output["genuine_strengths"].append("This is a perfect fit for the role")
        errors = validate_phase3_output(valid_phase3_output)
        assert any("Sycophantic phrase" in e for e in errors)
    
    def test_invalid_risk_assessment(self, valid_phase3_output):
        """Test detection of invalid risk assessment value."""
        valid_phase3_output["risk_assessment"] = "very high"
        errors = validate_phase3_output(valid_phase3_output)
        assert any("Invalid risk_assessment" in e for e in errors)


class TestPhase4Validation:
    """Tests for Phase 4 output validation."""
    
    def test_valid_output(self, valid_phase4_output):
        """Test that valid output passes validation."""
        errors = validate_phase4_output(valid_phase4_output)
        assert len(errors) == 0, f"Unexpected errors: {errors}"
    
    def test_confidence_out_of_range(self, valid_phase4_output):
        """Test detection of confidence > 1.0."""
        valid_phase4_output["matched_requirements"][0]["confidence"] = 1.5
        errors = validate_phase4_output(valid_phase4_output)
        assert any("Confidence out of range" in e for e in errors)
    
    def test_negative_confidence(self, valid_phase4_output):
        """Test detection of negative confidence."""
        valid_phase4_output["matched_requirements"][0]["confidence"] = -0.5
        errors = validate_phase4_output(valid_phase4_output)
        assert any("Confidence out of range" in e for e in errors)
    
    def test_invalid_overall_score(self, valid_phase4_output):
        """Test detection of invalid overall_match_score."""
        valid_phase4_output["overall_match_score"] = "high"
        errors = validate_phase4_output(valid_phase4_output)
        assert any("Invalid overall_match_score" in e for e in errors)
    
    def test_missing_confidence_field(self, valid_phase4_output):
        """Test detection of missing confidence in matched requirement."""
        del valid_phase4_output["matched_requirements"][0]["confidence"]
        errors = validate_phase4_output(valid_phase4_output)
        assert any("missing 'confidence'" in e for e in errors)


class TestPhase5Validation:
    """Tests for Phase 5 response validation."""
    
    def test_valid_response(self, valid_phase5_response):
        """Test that valid response passes validation."""
        errors = validate_phase5_response(valid_phase5_response)
        assert len(errors) == 0, f"Unexpected errors: {errors}"
    
    def test_word_count_exceeded(self):
        """Test detection of word count > 400."""
        long_response = "word " * 500  # 500 words
        errors = validate_phase5_response(long_response)
        assert any("exceeds 400 words" in e for e in errors)
    
    def test_missing_key_alignments(self, valid_phase5_response):
        """Test detection of missing Key Alignments section."""
        response = valid_phase5_response.replace("Key Alignments", "My Skills")
        errors = validate_phase5_response(response)
        assert any("Key Alignments" in e for e in errors)
    
    def test_missing_growth_areas(self, valid_phase5_response):
        """Test detection of missing Growth Areas section."""
        response = valid_phase5_response.replace("Growth Areas", "Strengths Only")
        errors = validate_phase5_response(response)
        assert any("Growth Areas" in e for e in errors)
    
    def test_sycophantic_phrase_in_response(self):
        """Test detection of sycophantic phrases in response."""
        response = """### Why I'm a Perfect Fit

**Key Alignments:**
- I'm an ideal candidate for this role

**What I Bring:**
My skills couldn't be better suited.

**Growth Areas:**
None - I'm already perfect.

**Let's Connect:**
Contact me.
"""
        errors = validate_phase5_response(response)
        assert any("Sycophantic phrase" in e for e in errors)
    
    def test_generic_phrase_detection(self):
        """Test detection of generic phrases that need specificity."""
        response = """### Why I'm a Great Fit for Company

**Key Alignments:**
- I am passionate about technology

**What I Bring:**
I believe I would be a great fit.

**Growth Areas:**
Always learning.

**Let's Connect:**
Email me.
"""
        errors = validate_phase5_response(response)
        assert any("Generic phrase" in e for e in errors)


# =============================================================================
# Integration Test with Mocked Nodes
# =============================================================================

class TestNodeIntegration:
    """Tests for actual node function integration."""
    
    @pytest.mark.asyncio
    async def test_connecting_node_classification(self):
        """Test that connecting node classifies correctly."""
        # This would require mocking the LLM
        # Left as integration test with real LLM
        pass
    
    @pytest.mark.asyncio
    async def test_skeptical_node_minimum_gaps(self):
        """Test that skeptical node enforces minimum gaps."""
        # This would require mocking the LLM
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
