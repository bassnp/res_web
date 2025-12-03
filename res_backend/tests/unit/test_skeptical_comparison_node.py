"""
Unit tests for Phase 3: SKEPTICAL_COMPARISON node.

CRITICAL: These tests verify the anti-sycophancy measures are working correctly.

Tests cover:
- Output validation with mandatory gap enforcement
- Sycophantic phrase detection and logging
- Risk assessment validation and consistency
- JSON extraction from various LLM response formats
- Node function execution with mocked LLM
- Callback event emission
- Error handling with conservative fallback
- Anti-sycophancy enforcement (the core feature)

Location: res_backend/tests/unit/test_skeptical_comparison_node.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.nodes.skeptical_comparison import (
    skeptical_comparison_node,
    validate_phase3_output,
    detect_sycophantic_content,
    format_employer_intel,
    extract_json_from_response,
    load_phase_prompt,
    PHASE_NAME,
    MIN_REQUIRED_GAPS,
    MAX_ALLOWED_STRENGTHS,
    SYCOPHANTIC_PHRASES,
)
from services.pipeline_state import (
    create_initial_state,
    Phase2Output,
    Phase3Output,
)


# =============================================================================
# Test Output Validation - Anti-Sycophancy Enforcement
# =============================================================================

class TestOutputValidation:
    """
    Test Phase 3 output validation, especially gap requirements.
    
    This is the CRITICAL anti-sycophancy enforcement layer.
    """
    
    def test_valid_output_with_sufficient_gaps(self):
        """Output with sufficient gaps validates correctly without modification."""
        data = {
            "genuine_strengths": ["Python expertise", "AI experience"],
            "genuine_gaps": [
                "No Kubernetes production experience",
                "Limited fintech domain knowledge"
            ],
            "transferable_skills": ["Docker knowledge applies to K8s"],
            "risk_assessment": "medium",
            "risk_justification": "Some gaps require learning time",
            "reasoning_trace": "Critical analysis complete",
        }
        result = validate_phase3_output(data)
        
        assert len(result["genuine_gaps"]) >= MIN_REQUIRED_GAPS
        assert result["risk_assessment"] == "medium"
        assert "Kubernetes" in result["genuine_gaps"][0]
    
    def test_insufficient_gaps_gets_defaults(self):
        """Output with only 1 gap receives default gap to meet minimum."""
        data = {
            "genuine_strengths": ["Good technical skills"],
            "genuine_gaps": ["Minor issue with one technology"],  # Only 1 gap
            "risk_assessment": "low",
            "reasoning_trace": "Analysis done",
        }
        result = validate_phase3_output(data)
        
        # Should have at least MIN_REQUIRED_GAPS
        assert len(result["genuine_gaps"]) >= MIN_REQUIRED_GAPS
        # Original gap should be preserved
        assert "Minor issue" in result["genuine_gaps"][0]
    
    def test_zero_gaps_gets_multiple_defaults(self):
        """Sycophantic output with zero gaps receives default gaps."""
        data = {
            "genuine_strengths": ["Perfect match!", "Ideal candidate!"],
            "genuine_gaps": [],  # Sycophantic output - no gaps
            "risk_assessment": "low",
            "reasoning_trace": "This candidate is amazing",
        }
        result = validate_phase3_output(data)
        
        # Should have at least MIN_REQUIRED_GAPS
        assert len(result["genuine_gaps"]) >= MIN_REQUIRED_GAPS
        # Default gaps should be meaningful and specific
        combined_gaps = " ".join(result["genuine_gaps"]).lower()
        assert any(term in combined_gaps for term in [
            "experience", "domain", "technology", "verification"
        ])
    
    def test_too_many_strengths_gets_trimmed(self):
        """Padding with excessive strengths gets trimmed."""
        data = {
            "genuine_strengths": [
                "Strength 1", "Strength 2", "Strength 3",
                "Strength 4", "Strength 5", "Strength 6"  # More than MAX_ALLOWED
            ],
            "genuine_gaps": ["Gap 1", "Gap 2"],
            "risk_assessment": "medium",
        }
        result = validate_phase3_output(data)
        
        assert len(result["genuine_strengths"]) <= MAX_ALLOWED_STRENGTHS
    
    def test_invalid_risk_defaults_to_medium(self):
        """Invalid risk assessment value defaults to medium."""
        data = {
            "genuine_gaps": ["Gap 1", "Gap 2"],
            "risk_assessment": "perfect",  # Invalid value
            "reasoning_trace": "Analysis",
        }
        result = validate_phase3_output(data)
        
        assert result["risk_assessment"] == "medium"
    
    def test_inconsistent_low_risk_with_many_gaps_corrected(self):
        """Risk 'low' with many gaps is upgraded to 'medium' for consistency."""
        data = {
            "genuine_gaps": ["Gap 1", "Gap 2", "Gap 3"],  # 3 gaps
            "risk_assessment": "low",  # Inconsistent
            "reasoning_trace": "Analysis",
        }
        result = validate_phase3_output(data)
        
        # Low risk should be upgraded given 3 gaps
        assert result["risk_assessment"] == "medium"
    
    def test_empty_transferable_skills_handled(self):
        """Empty transferable skills is valid and returns empty list."""
        data = {
            "genuine_gaps": ["Gap 1", "Gap 2"],
            "transferable_skills": None,
            "risk_assessment": "medium",
        }
        result = validate_phase3_output(data)
        
        assert result["transferable_skills"] == []
    
    def test_missing_reasoning_trace_gets_default(self):
        """Missing reasoning trace gets default message."""
        data = {
            "genuine_gaps": ["Gap 1", "Gap 2"],
            "risk_assessment": "medium",
            # No reasoning_trace
        }
        result = validate_phase3_output(data)
        
        assert result["reasoning_trace"] == "Critical analysis completed."


# =============================================================================
# Test Sycophancy Detection
# =============================================================================

class TestSycophancyDetection:
    """Test detection of sycophantic patterns in output."""
    
    def test_detects_sycophantic_phrases_in_strengths(self):
        """Sycophantic phrases in strengths are detected."""
        output: Phase3Output = {
            "genuine_strengths": ["This is a perfect fit for the role"],
            "genuine_gaps": ["Gap 1", "Gap 2"],
            "transferable_skills": [],
            "risk_assessment": "low",
            "reasoning_trace": "Analysis complete",
        }
        warnings = detect_sycophantic_content(output)
        
        assert len(warnings) > 0
        assert any("perfect fit" in w.lower() for w in warnings)
    
    def test_detects_multiple_sycophantic_phrases(self):
        """Multiple sycophantic phrases are all detected."""
        output: Phase3Output = {
            "genuine_strengths": [
                "Ideal candidate for this position",
                "Amazing technical skills",
            ],
            "genuine_gaps": ["Gap 1", "Gap 2"],
            "transferable_skills": [],
            "risk_assessment": "low",
            "reasoning_trace": "Outstanding match overall",
        }
        warnings = detect_sycophantic_content(output)
        
        # Should detect in strengths and reasoning
        assert len(warnings) >= 2
    
    def test_clean_output_no_warnings(self):
        """Professional output without sycophancy has no warnings."""
        output: Phase3Output = {
            "genuine_strengths": [
                "Strong Python experience demonstrated through projects",
                "FastAPI knowledge aligns with backend requirements",
            ],
            "genuine_gaps": [
                "No Kubernetes experience for container orchestration needs",
                "Limited exposure to financial services domain",
            ],
            "transferable_skills": ["Docker experience provides foundation for K8s"],
            "risk_assessment": "medium",
            "reasoning_trace": "Analyzed tech stack alignment and domain experience",
        }
        warnings = detect_sycophantic_content(output)
        
        assert len(warnings) == 0
    
    def test_detects_inconsistent_risk_and_gaps(self):
        """Inconsistent low risk with many gaps is flagged."""
        output: Phase3Output = {
            "genuine_strengths": ["Strength 1"],
            "genuine_gaps": ["Gap 1", "Gap 2", "Gap 3"],  # 3 gaps
            "transferable_skills": [],
            "risk_assessment": "low",  # Inconsistent with 3 gaps
            "reasoning_trace": "Analysis",
        }
        warnings = detect_sycophantic_content(output)
        
        assert any("inconsistent" in w.lower() for w in warnings)


# =============================================================================
# Test Employer Intel Formatting
# =============================================================================

class TestEmployerIntelFormatting:
    """Test employer intelligence formatting for prompt injection."""
    
    def test_complete_phase2_formats_correctly(self):
        """Complete Phase 2 output formats all fields correctly."""
        phase_2 = {
            "employer_summary": "Google is a tech giant specializing in AI",
            "identified_requirements": ["Python", "Machine Learning", "Distributed Systems"],
            "tech_stack": ["Python", "TensorFlow", "GCP", "Kubernetes"],
            "culture_signals": ["Innovation-focused", "Scale-oriented", "Remote-friendly"],
        }
        formatted = format_employer_intel(phase_2)
        
        assert formatted["employer_summary"] == "Google is a tech giant specializing in AI"
        assert "Python" in formatted["identified_requirements"]
        assert "TensorFlow" in formatted["tech_stack"]
        assert "Innovation" in formatted["culture_signals"]
    
    def test_empty_fields_return_defaults(self):
        """Empty Phase 2 fields return informative default messages."""
        phase_2 = {}
        formatted = format_employer_intel(phase_2)
        
        assert "No summary available" in formatted["employer_summary"]
        assert "no specific" in formatted["identified_requirements"].lower()
    
    def test_empty_lists_handled(self):
        """Empty requirement/tech lists handled gracefully."""
        phase_2 = {
            "employer_summary": "Small startup",
            "identified_requirements": [],
            "tech_stack": [],
            "culture_signals": [],
        }
        formatted = format_employer_intel(phase_2)
        
        assert "no specific" in formatted["tech_stack"].lower()
    
    def test_lists_formatted_with_bullets(self):
        """List items are formatted with bullet points for XML."""
        phase_2 = {
            "employer_summary": "Test company",
            "identified_requirements": ["Req1", "Req2"],
            "tech_stack": ["Tech1"],
            "culture_signals": ["Culture1"],
        }
        formatted = format_employer_intel(phase_2)
        
        # Should have bullet formatting
        assert "- Req1" in formatted["identified_requirements"]
        assert "- Req2" in formatted["identified_requirements"]


# =============================================================================
# Test JSON Extraction
# =============================================================================

class TestJSONExtraction:
    """Test JSON extraction from various LLM response formats."""
    
    def test_clean_json(self):
        """Direct JSON should parse correctly."""
        response = '''{
            "genuine_strengths": ["Python expertise"],
            "genuine_gaps": ["No K8s", "No AWS"],
            "risk_assessment": "medium",
            "reasoning_trace": "Analysis"
        }'''
        result = extract_json_from_response(response)
        
        assert result["genuine_strengths"] == ["Python expertise"]
        assert len(result["genuine_gaps"]) == 2
    
    def test_json_with_markdown_json_tag(self):
        """JSON in ```json code blocks should parse."""
        response = '''Here is the analysis:
```json
{
    "genuine_strengths": ["Strong background"],
    "genuine_gaps": ["Gap 1", "Gap 2"],
    "risk_assessment": "low"
}
```'''
        result = extract_json_from_response(response)
        
        assert "Strong background" in result["genuine_strengths"]
    
    def test_json_with_plain_markdown(self):
        """JSON in plain ``` code blocks should parse."""
        response = '''```
{"genuine_gaps": ["Gap 1", "Gap 2"], "risk_assessment": "high"}
```'''
        result = extract_json_from_response(response)
        
        assert result["risk_assessment"] == "high"
    
    def test_json_with_prose_wrapper(self):
        """JSON embedded in prose should be extracted."""
        response = '''Based on my analysis, here is the assessment:
        
        {"genuine_gaps": ["Gap 1", "Gap 2"], "risk_assessment": "medium"}
        
        This concludes the critical review.'''
        result = extract_json_from_response(response)
        
        assert len(result["genuine_gaps"]) == 2
    
    def test_invalid_json_raises_error(self):
        """Invalid JSON should raise ValueError."""
        response = "This is not JSON at all, just text."
        
        with pytest.raises(ValueError) as exc_info:
            extract_json_from_response(response)
        
        assert "Could not extract" in str(exc_info.value)


# =============================================================================
# Test Prompt Loading
# =============================================================================

class TestPromptLoading:
    """Test prompt template loading."""
    
    def test_fallback_prompt_has_key_elements(self):
        """Fallback prompt should have anti-sycophancy elements."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            prompt = load_phase_prompt()
        
        prompt_lower = prompt.lower()
        assert "skeptical" in prompt_lower
        assert "gap" in prompt_lower
        assert "do not" in prompt_lower


# =============================================================================
# Test Skeptical Comparison Node
# =============================================================================

class TestSkepticalComparisonNode:
    """Integration tests for the skeptical comparison node."""
    
    @pytest.fixture
    def base_state(self):
        """Create a base state with Phase 2 output."""
        state = create_initial_state("Google")
        state["phase_2_output"] = {
            "employer_summary": "Google is a tech giant using Python and ML",
            "identified_requirements": ["Python", "TensorFlow", "Kubernetes", "PhD preferred"],
            "tech_stack": ["Python", "Go", "TensorFlow", "Kubernetes"],
            "culture_signals": ["Innovation", "Scale"],
            "reasoning_trace": "Research synthesis complete",
        }
        state["step_count"] = 3
        return state
    
    @pytest.mark.asyncio
    async def test_identifies_gaps_for_strong_candidate(self, base_state):
        """Node identifies gaps even for candidates with strong alignment."""
        mock_response = MagicMock()
        mock_response.content = '''{
            "genuine_strengths": ["Python experience", "AI/ML background"],
            "genuine_gaps": ["No Kubernetes production experience", "PhD not obtained"],
            "transferable_skills": ["Docker experience applies to K8s"],
            "risk_assessment": "medium",
            "risk_justification": "Learning curve for K8s expected",
            "reasoning_trace": "Identified skill gaps in infrastructure"
        }'''
        
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await skeptical_comparison_node(base_state)
            
            assert len(result["phase_3_output"]["genuine_gaps"]) >= 2
            assert result["phase_3_output"]["risk_assessment"] in ("low", "medium", "high")
            assert result["current_phase"] == "skills_matching"
    
    @pytest.mark.asyncio
    async def test_corrects_sycophantic_llm_output(self, base_state):
        """Sycophantic LLM output with no gaps gets corrected."""
        # Simulate an LLM being overly positive
        mock_response = MagicMock()
        mock_response.content = '''{
            "genuine_strengths": ["Perfect fit!", "Ideal candidate!", "Amazing match!"],
            "genuine_gaps": [],
            "transferable_skills": [],
            "risk_assessment": "low",
            "reasoning_trace": "This candidate is a perfect match for the role"
        }'''
        
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await skeptical_comparison_node(base_state)
            
            # Validation should have added default gaps
            assert len(result["phase_3_output"]["genuine_gaps"]) >= MIN_REQUIRED_GAPS
            # Strengths should have been trimmed
            assert len(result["phase_3_output"]["genuine_strengths"]) <= MAX_ALLOWED_STRENGTHS
    
    @pytest.mark.asyncio
    async def test_callback_events_emitted(self, base_state):
        """Callback receives phase and thought events."""
        mock_callback = AsyncMock()
        mock_callback.on_phase = AsyncMock()
        mock_callback.on_thought = AsyncMock()
        mock_callback.on_phase_complete = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '''{
            "genuine_strengths": [],
            "genuine_gaps": ["Gap 1", "Gap 2"],
            "risk_assessment": "medium",
            "reasoning_trace": "Analysis done"
        }'''
        
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            await skeptical_comparison_node(base_state, callback=mock_callback)
            
            # Verify all callback methods were called
            mock_callback.on_phase.assert_called_once()
            assert mock_callback.on_thought.call_count >= 1
            mock_callback.on_phase_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_phase_event_includes_phase_name(self, base_state):
        """Phase event includes correct phase name."""
        mock_callback = AsyncMock()
        mock_callback.on_phase = AsyncMock()
        mock_callback.on_thought = AsyncMock()
        mock_callback.on_phase_complete = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '{"genuine_gaps": ["Gap 1", "Gap 2"], "risk_assessment": "medium"}'
        
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            await skeptical_comparison_node(base_state, callback=mock_callback)
            
            # Check phase name in call
            call_args = mock_callback.on_phase.call_args
            assert PHASE_NAME in str(call_args)
    
    @pytest.mark.asyncio
    async def test_error_produces_conservative_fallback(self, base_state):
        """Errors result in conservative, honest fallback output."""
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(
                side_effect=Exception("LLM service unavailable")
            )
            
            result = await skeptical_comparison_node(base_state)
            
            # Fallback should still have minimum gaps (conservative)
            assert len(result["phase_3_output"]["genuine_gaps"]) >= MIN_REQUIRED_GAPS
            # Risk should be medium (conservative, not optimistic)
            assert result["phase_3_output"]["risk_assessment"] == "medium"
            # Error should be recorded
            assert "processing_errors" in result
            assert len(result["processing_errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_error_fallback_is_not_sycophantic(self, base_state):
        """Error fallback is honest, not sycophantic."""
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(
                side_effect=Exception("Connection error")
            )
            
            result = await skeptical_comparison_node(base_state)
            
            fallback = result["phase_3_output"]
            
            # Check that fallback gaps mention the limitation
            gaps_combined = " ".join(fallback["genuine_gaps"]).lower()
            assert any(term in gaps_combined for term in [
                "verify", "unable", "further", "review", "error"
            ])
    
    @pytest.mark.asyncio
    async def test_step_count_incremented(self, base_state):
        """Step count is properly incremented."""
        initial_step = base_state["step_count"]
        
        mock_response = MagicMock()
        mock_response.content = '{"genuine_gaps": ["Gap 1", "Gap 2"], "risk_assessment": "medium"}'
        
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await skeptical_comparison_node(base_state)
            
            assert result["step_count"] > initial_step
    
    @pytest.mark.asyncio
    async def test_transitions_to_skills_matching(self, base_state):
        """Node transitions to skills_matching phase on success."""
        mock_response = MagicMock()
        mock_response.content = '{"genuine_gaps": ["Gap 1", "Gap 2"], "risk_assessment": "low"}'
        
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await skeptical_comparison_node(base_state)
            
            assert result["current_phase"] == "skills_matching"
    
    @pytest.mark.asyncio
    async def test_handles_empty_phase2_output(self):
        """Node handles empty Phase 2 output gracefully."""
        state = create_initial_state("Unknown Company")
        state["phase_2_output"] = {}
        state["step_count"] = 3
        
        mock_response = MagicMock()
        mock_response.content = '''{
            "genuine_gaps": ["Limited employer data available", "Requirements unclear"],
            "risk_assessment": "high"
        }'''
        
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await skeptical_comparison_node(state)
            
            assert result["phase_3_output"] is not None
            assert len(result["phase_3_output"]["genuine_gaps"]) >= 2


# =============================================================================
# Test Risk Assessment Logic
# =============================================================================

class TestRiskAssessmentLogic:
    """Test risk assessment validation and consistency."""
    
    def test_valid_risk_values_accepted(self):
        """All valid risk values are accepted."""
        for risk in ["low", "medium", "high"]:
            data = {
                "genuine_gaps": ["Gap 1", "Gap 2"],
                "risk_assessment": risk,
            }
            result = validate_phase3_output(data)
            assert result["risk_assessment"] == risk
    
    def test_mixed_case_risk_rejected(self):
        """Mixed case risk values are rejected."""
        data = {
            "genuine_gaps": ["Gap 1", "Gap 2"],
            "risk_assessment": "Medium",  # Wrong case
        }
        result = validate_phase3_output(data)
        assert result["risk_assessment"] == "medium"  # Defaults
    
    def test_high_risk_not_downgraded(self):
        """High risk assessment is preserved."""
        data = {
            "genuine_gaps": ["Significant gap"],
            "risk_assessment": "high",
        }
        result = validate_phase3_output(data)
        # Even with default gaps added, high risk should stay
        assert result["risk_assessment"] == "high"


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_exactly_two_gaps_no_modification(self):
        """Exactly 2 gaps should not trigger default gap addition."""
        data = {
            "genuine_gaps": ["Gap A", "Gap B"],
            "risk_assessment": "medium",
        }
        result = validate_phase3_output(data)
        
        assert len(result["genuine_gaps"]) == 2
        assert "Gap A" in result["genuine_gaps"]
        assert "Gap B" in result["genuine_gaps"]
    
    def test_exactly_max_strengths_no_trim(self):
        """Exactly MAX_ALLOWED_STRENGTHS should not be trimmed."""
        data = {
            "genuine_strengths": [f"Strength {i}" for i in range(MAX_ALLOWED_STRENGTHS)],
            "genuine_gaps": ["Gap 1", "Gap 2"],
            "risk_assessment": "medium",
        }
        result = validate_phase3_output(data)
        
        assert len(result["genuine_strengths"]) == MAX_ALLOWED_STRENGTHS
    
    def test_null_values_handled(self):
        """Null values in optional fields are handled."""
        data = {
            "genuine_strengths": None,
            "genuine_gaps": None,
            "transferable_skills": None,
            "risk_assessment": None,
            "reasoning_trace": None,
        }
        result = validate_phase3_output(data)
        
        # Should have defaults, not None
        assert result["genuine_gaps"] is not None
        assert len(result["genuine_gaps"]) >= MIN_REQUIRED_GAPS
        assert result["genuine_strengths"] == []
        assert result["transferable_skills"] == []
        assert result["risk_assessment"] == "medium"
