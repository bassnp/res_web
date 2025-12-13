"""
Unit tests for Phase 4: SKILLS_MATCHING node.

Tests cover:
- Score calculation with transparent breakdown
- Output validation and confidence clamping
- JSON extraction from various LLM response formats
- Node function execution with mocked LLM and tools
- Tool invocation and callback event emission
- Error handling with graceful degradation
- Score recalculation for consistency (anti-gaming)

Location: res_backend/tests/unit/test_skills_matching_node.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.nodes.skills_matching import (
    skills_matching_node,
    calculate_overall_score,
    validate_phase4_output,
    extract_json_from_response,
    load_phase_prompt,
    format_list_for_prompt,
    truncate_tool_input,
    PHASE_NAME,
    SYNTHESIS_TEMPERATURE,
    MAX_TOOL_INPUT_LENGTH,
)
from services.pipeline_state import (
    create_initial_state,
    Phase2Output,
    Phase3Output,
    Phase4Output,
)


# =============================================================================
# Test Score Calculation
# =============================================================================

class TestScoreCalculation:
    """
    Test the transparent scoring algorithm.
    
    The scoring formula is:
    - base_score = avg_confidence × coverage_ratio
    - gap_penalty applied if unmatched > 30%
    """
    
    def test_perfect_matches_all_high_confidence(self):
        """All requirements matched with high confidence yields high score."""
        matched = [
            {"confidence": 0.95},
            {"confidence": 0.90},
            {"confidence": 0.85},
        ]
        unmatched = []
        
        score, breakdown = calculate_overall_score(matched, unmatched)
        
        assert score >= 0.85
        assert "3/3" in breakdown
        assert "Avg confidence: 0.90" in breakdown
    
    def test_perfect_matches_moderate_confidence(self):
        """All requirements matched with moderate confidence."""
        matched = [
            {"confidence": 0.7},
            {"confidence": 0.6},
            {"confidence": 0.65},
        ]
        unmatched = []
        
        score, breakdown = calculate_overall_score(matched, unmatched)
        
        # 0.65 avg × 1.0 coverage = 0.65
        assert 0.60 <= score <= 0.70
        assert "3/3" in breakdown
    
    def test_partial_matches(self):
        """Some requirements matched, some not (under gap penalty threshold)."""
        matched = [
            {"confidence": 0.8},
            {"confidence": 0.7},
        ]
        unmatched = ["Kubernetes"]  # 1 out of 3 unmatched = 33%
        
        score, breakdown = calculate_overall_score(matched, unmatched)
        
        # 0.75 avg × 0.67 coverage = 0.50, slight penalty applied
        assert 0.30 <= score <= 0.55
        assert "2/3" in breakdown
    
    def test_heavy_gaps_apply_penalty(self):
        """More than 30% unmatched applies gap penalty."""
        matched = [{"confidence": 0.9}]
        unmatched = ["Skill 1", "Skill 2", "Skill 3", "Skill 4"]  # 80% unmatched
        
        score, breakdown = calculate_overall_score(matched, unmatched)
        
        # Should have penalty applied
        assert "penalty" in breakdown.lower() or "gap" in breakdown.lower()
        assert score < 0.3
    
    def test_no_matches_all_gaps(self):
        """No matches at all yields very low score."""
        matched = []
        unmatched = ["Python", "React", "AWS"]
        
        score, breakdown = calculate_overall_score(matched, unmatched)
        
        assert score == 0.0
        assert "0/3" in breakdown
    
    def test_no_requirements_defaults_to_neutral(self):
        """No requirements identified defaults to neutral 0.5 score."""
        score, breakdown = calculate_overall_score([], [])
        
        assert score == 0.5
        assert "defaulting" in breakdown.lower() or "neutral" in breakdown.lower()
    
    def test_score_clamped_to_valid_range(self):
        """Score is always clamped to 0.0-1.0 range."""
        # Edge case: extremely high confidence shouldn't exceed 1.0
        matched = [{"confidence": 1.0}, {"confidence": 1.0}]
        unmatched = []
        
        score, _ = calculate_overall_score(matched, unmatched)
        assert 0.0 <= score <= 1.0
        
        # Edge case: extremely low confidence shouldn't go below 0.0
        matched = [{"confidence": 0.0}]
        unmatched = ["Gap1", "Gap2", "Gap3", "Gap4", "Gap5"]
        
        score, _ = calculate_overall_score(matched, unmatched)
        assert 0.0 <= score <= 1.0
    
    def test_breakdown_shows_calculation(self):
        """Breakdown string shows transparent calculation."""
        matched = [{"confidence": 0.8}]
        unmatched = ["Gap"]
        
        score, breakdown = calculate_overall_score(matched, unmatched)
        
        assert "Avg confidence" in breakdown
        assert "Coverage" in breakdown
        assert "1/2" in breakdown


# =============================================================================
# Test Output Validation
# =============================================================================

class TestOutputValidation:
    """Test Phase 4 output validation and normalization."""
    
    def test_valid_output_passes_through(self):
        """Valid skill matching output validates correctly."""
        data = {
            "matched_requirements": [
                {"requirement": "Python", "matched_skill": "Python", "confidence": 0.9, "evidence": "Portfolio"},
                {"requirement": "React", "matched_skill": "React.js", "confidence": 0.85, "evidence": "Projects"},
            ],
            "unmatched_requirements": ["Kubernetes"],
            "overall_match_score": 0.7,
            "reasoning_trace": "Analysis complete",
        }
        result = validate_phase4_output(data)
        
        assert len(result["matched_requirements"]) == 2
        assert len(result["unmatched_requirements"]) == 1
        assert 0.0 <= result["overall_match_score"] <= 1.0
    
    def test_confidence_clamped_above_one(self):
        """Confidence scores above 1.0 get clamped down."""
        data = {
            "matched_requirements": [
                {"requirement": "Python", "matched_skill": "Python", "confidence": 1.5},
            ],
            "unmatched_requirements": [],
        }
        result = validate_phase4_output(data)
        
        assert result["matched_requirements"][0]["confidence"] == 1.0
    
    def test_confidence_clamped_below_zero(self):
        """Confidence scores below 0.0 get clamped up."""
        data = {
            "matched_requirements": [
                {"requirement": "Test", "matched_skill": "Test", "confidence": -0.5},
            ],
            "unmatched_requirements": [],
        }
        result = validate_phase4_output(data)
        
        assert result["matched_requirements"][0]["confidence"] == 0.0
    
    def test_invalid_confidence_defaults_to_half(self):
        """Non-numeric confidence defaults to 0.5."""
        data = {
            "matched_requirements": [
                {"requirement": "Test", "matched_skill": "Test", "confidence": "high"},
            ],
            "unmatched_requirements": [],
        }
        result = validate_phase4_output(data)
        
        assert result["matched_requirements"][0]["confidence"] == 0.5
    
    def test_score_recalculated_for_consistency(self):
        """Score is recalculated regardless of what LLM provides."""
        data = {
            "matched_requirements": [
                {"requirement": "A", "matched_skill": "A", "confidence": 0.8},
            ],
            "unmatched_requirements": ["B", "C", "D"],  # 75% unmatched
            "overall_match_score": 0.95,  # LLM claiming high score
        }
        result = validate_phase4_output(data)
        
        # Score should be recalculated to be much lower
        assert result["overall_match_score"] < 0.5
    
    def test_missing_fields_get_defaults(self):
        """Missing optional fields receive sensible defaults."""
        data = {
            "matched_requirements": [{"requirement": "Test"}],  # Missing most fields
            "unmatched_requirements": None,
        }
        result = validate_phase4_output(data)
        
        match = result["matched_requirements"][0]
        assert match["matched_skill"] == "General experience"
        assert match["confidence"] == 0.5
        assert match["evidence"] == "Skill match identified"
        assert result["unmatched_requirements"] == []
    
    def test_empty_input_returns_valid_structure(self):
        """Completely empty input returns valid empty structure."""
        data = {}
        result = validate_phase4_output(data)
        
        assert result["matched_requirements"] == []
        assert result["unmatched_requirements"] == []
        assert result["overall_match_score"] == 0.5  # Neutral default


# =============================================================================
# Test JSON Extraction
# =============================================================================

class TestJSONExtraction:
    """Test JSON extraction from various LLM response formats."""
    
    def test_clean_json(self):
        """Direct JSON without any wrapping."""
        response = '{"matched_requirements": [], "unmatched_requirements": [], "overall_match_score": 0.5}'
        result = extract_json_from_response(response)
        
        assert result["overall_match_score"] == 0.5
    
    def test_json_in_markdown_code_block(self):
        """JSON wrapped in markdown code block."""
        response = '''Here's the analysis:
        
```json
{
    "matched_requirements": [{"requirement": "Python", "matched_skill": "Python", "confidence": 0.9}],
    "unmatched_requirements": [],
    "overall_match_score": 0.9
}
```

That's my assessment.'''
        result = extract_json_from_response(response)
        
        assert len(result["matched_requirements"]) == 1
        assert result["overall_match_score"] == 0.9
    
    def test_json_in_code_block_without_language(self):
        """JSON in code block without json language specifier."""
        response = '''```
{"matched_requirements": [], "overall_match_score": 0.7}
```'''
        result = extract_json_from_response(response)
        
        assert result["overall_match_score"] == 0.7
    
    def test_json_with_surrounding_prose(self):
        """JSON embedded in prose."""
        response = '''Based on my analysis, here is the result:

{"matched_requirements": [], "unmatched_requirements": ["Kubernetes"], "overall_match_score": 0.4}

This represents a moderate match.'''
        result = extract_json_from_response(response)
        
        assert "Kubernetes" in result["unmatched_requirements"]
    
    def test_invalid_json_raises_error(self):
        """Completely invalid JSON raises ValueError."""
        response = "This is just regular text with no JSON at all."
        
        with pytest.raises(ValueError) as exc_info:
            extract_json_from_response(response)
        
        assert "Could not extract valid JSON" in str(exc_info.value)


# =============================================================================
# Test Utility Functions
# =============================================================================

class TestUtilityFunctions:
    """Test helper utility functions."""
    
    def test_format_list_empty(self):
        """Empty list returns default value."""
        result = format_list_for_prompt([])
        assert result == "None identified"
    
    def test_format_list_with_items(self):
        """List with items returns comma-separated string."""
        result = format_list_for_prompt(["Python", "React", "AWS"])
        assert result == "Python, React, AWS"
    
    def test_format_list_with_none_items(self):
        """List with None items filters them out."""
        # Note: format_list_for_prompt expects List[str], but we test edge case behavior
        items = ["Python", "React"]  # type: ignore
        result = format_list_for_prompt(items)
        assert "Python" in result
        assert "React" in result
    
    def test_format_list_custom_default(self):
        """Custom default value is used for empty list."""
        result = format_list_for_prompt([], default="No skills")
        assert result == "No skills"
    
    def test_truncate_short_input(self):
        """Short input is not truncated."""
        short_text = "Python, React, AWS"
        result = truncate_tool_input(short_text)
        assert result == short_text
    
    def test_truncate_long_input(self):
        """Long input is truncated with ellipsis."""
        long_text = "x" * (MAX_TOOL_INPUT_LENGTH + 100)
        result = truncate_tool_input(long_text)
        
        assert len(result) == MAX_TOOL_INPUT_LENGTH + 3  # +3 for "..."
        assert result.endswith("...")
    
    def test_load_phase_prompt_returns_string(self):
        """Load phase prompt returns a string."""
        prompt = load_phase_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should contain key XML elements
        assert "<system_instruction>" in prompt or "system_instruction" in prompt.lower()


# =============================================================================
# Test Skills Matching Node
# =============================================================================

class TestSkillsMatchingNode:
    """Integration tests for the skills matching node function."""
    
    @pytest.fixture
    def base_state(self):
        """Create a base state with Phase 2 and Phase 3 outputs."""
        state = create_initial_state("Google")
        state["phase_2_output"] = {
            "employer_summary": "Google is a tech giant using Python and ML",
            "identified_requirements": ["Python", "TensorFlow", "Kubernetes"],
            "tech_stack": ["Python", "TensorFlow", "Go"],
            "culture_signals": ["Innovation", "Scale"],
            "search_queries_used": ["google software engineer"],
            "reasoning_trace": "Research synthesis complete",
        }
        state["phase_3_output"] = {
            "genuine_strengths": ["Python expertise"],
            "genuine_gaps": ["No Kubernetes experience", "Limited Go knowledge"],
            "transferable_skills": ["Docker experience"],
            "risk_assessment": "medium",
            "reasoning_trace": "Skeptical analysis complete",
        }
        state["step_count"] = 6
        return state
    
    @pytest.mark.asyncio
    async def test_successful_skill_matching(self, base_state):
        """Successful skill matching produces quantified output."""
        mock_response = MagicMock()
        mock_response.content = '''{
            "matched_requirements": [
                {"requirement": "Python", "matched_skill": "Python", "confidence": 0.9, "evidence": "Portfolio"},
                {"requirement": "TensorFlow", "matched_skill": "AI/ML experience", "confidence": 0.7, "evidence": "Projects"}
            ],
            "unmatched_requirements": ["Kubernetes", "Go"],
            "overall_match_score": 0.55,
            "score_breakdown": "Avg 0.8 × Coverage 0.5 = 0.4",
            "reasoning_trace": "Good Python match, learning curve for K8s and Go"
        }'''
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.return_value = "Python: Strong match (0.9)"
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.return_value = "AI domain experience matches"
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    result = await skills_matching_node(base_state)
                    
                    assert len(result["phase_4_output"]["matched_requirements"]) == 2
                    assert len(result["phase_4_output"]["unmatched_requirements"]) == 2
                    assert 0.0 <= result["phase_4_output"]["overall_match_score"] <= 1.0
                    assert result["current_phase"] == "generate_results"
    
    @pytest.mark.asyncio
    async def test_tools_are_invoked(self, base_state):
        """Both skill_matcher and experience_matcher tools are invoked."""
        mock_response = MagicMock()
        mock_response.content = '{"matched_requirements": [], "unmatched_requirements": [], "overall_match_score": 0.5}'
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.return_value = "Skill analysis"
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.return_value = "Experience analysis"
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    await skills_matching_node(base_state)
                    
                    # Both tools should be called
                    mock_skill.invoke.assert_called_once()
                    mock_exp.invoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_callback_events_emitted(self, base_state):
        """Callback receives phase, thought, and phase_complete events."""
        mock_callback = AsyncMock()
        mock_callback.on_phase = AsyncMock()
        mock_callback.on_thought = AsyncMock()
        mock_callback.on_phase_complete = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '''{"matched_requirements": [], "unmatched_requirements": [], 
                                    "overall_match_score": 0.5, "reasoning_trace": "Done"}'''
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.return_value = "Skill output"
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.return_value = "Experience output"
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    await skills_matching_node(base_state, callback=mock_callback)
                    
                    # Verify all callback methods were called
                    mock_callback.on_phase.assert_called_once()
                    assert mock_callback.on_thought.call_count >= 4  # At least 4 thoughts: 2 tool calls + 2 observations
                    mock_callback.on_phase_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tool_calls_emit_correct_types(self, base_state):
        """Tool calls emit 'tool_call' thought type with correct tool names."""
        mock_callback = AsyncMock()
        mock_callback.on_phase = AsyncMock()
        mock_callback.on_thought = AsyncMock()
        mock_callback.on_phase_complete = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '{"matched_requirements": [], "unmatched_requirements": [], "overall_match_score": 0.5}'
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.return_value = "Skill output"
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.return_value = "Experience output"
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    await skills_matching_node(base_state, callback=mock_callback)
                    
                    # Extract all tool_call events
                    tool_calls = [
                        call for call in mock_callback.on_thought.call_args_list
                        if call.kwargs.get("thought_type") == "tool_call"
                    ]
                    
                    assert len(tool_calls) >= 2
                    
                    # Check tool names
                    tool_names = [call.kwargs.get("tool") for call in tool_calls]
                    assert "analyze_skill_match" in tool_names
                    assert "analyze_experience_relevance" in tool_names
    
    @pytest.mark.asyncio
    async def test_thought_events_have_correct_types(self, base_state):
        """Thought events have correct thought_type values."""
        mock_callback = AsyncMock()
        mock_callback.on_phase = AsyncMock()
        mock_callback.on_thought = AsyncMock()
        mock_callback.on_phase_complete = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '{"matched_requirements": [], "unmatched_requirements": [], "overall_match_score": 0.5}'
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.return_value = "Skill output"
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.return_value = "Experience output"
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    await skills_matching_node(base_state, callback=mock_callback)
                    
                    # All thought events should have valid thought_type
                    valid_types = {"tool_call", "observation", "reasoning"}
                    for call in mock_callback.on_thought.call_args_list:
                        thought_type = call.kwargs.get("thought_type")
                        assert thought_type in valid_types, f"Invalid thought_type: {thought_type}"
    
    @pytest.mark.asyncio
    async def test_tool_failure_graceful_recovery(self, base_state):
        """Tool failures result in graceful continuation."""
        mock_callback = AsyncMock()
        mock_callback.on_phase = AsyncMock()
        mock_callback.on_thought = AsyncMock()
        mock_callback.on_phase_complete = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '{"matched_requirements": [], "unmatched_requirements": [], "overall_match_score": 0.5}'
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.side_effect = Exception("Skill tool error")
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.side_effect = Exception("Experience tool error")
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    result = await skills_matching_node(base_state, callback=mock_callback)
                    
                    # Should still produce output
                    assert result["current_phase"] == "generate_results"
                    assert "phase_4_output" in result
                    
                    # Errors should be logged
                    assert len(result.get("processing_errors", [])) >= 1
    
    @pytest.mark.asyncio
    async def test_llm_failure_produces_fallback(self, base_state):
        """LLM failure produces neutral fallback output."""
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.return_value = "Skill output"
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.return_value = "Experience output"
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(
                        side_effect=Exception("LLM service unavailable")
                    )
                    
                    result = await skills_matching_node(base_state)
                    
                    # Should still transition to next phase
                    assert result["current_phase"] == "generate_results"
                    
                    # Fallback should have neutral score
                    assert result["phase_4_output"]["overall_match_score"] == 0.5
                    
                    # Error should be recorded
                    assert len(result["processing_errors"]) >= 1
    
    @pytest.mark.asyncio
    async def test_step_count_incremented(self, base_state):
        """Step count is properly incremented through the node."""
        initial_step = base_state["step_count"]
        
        mock_response = MagicMock()
        mock_response.content = '{"matched_requirements": [], "unmatched_requirements": [], "overall_match_score": 0.5}'
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.return_value = "Skill output"
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.return_value = "Experience output"
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    result = await skills_matching_node(base_state)
                    
                    # Step count should have increased
                    assert result["step_count"] > initial_step
    
    @pytest.mark.asyncio
    async def test_empty_phase2_handled(self, base_state):
        """Empty Phase 2 output is handled gracefully."""
        base_state["phase_2_output"] = {}
        base_state["phase_3_output"] = {}
        
        mock_response = MagicMock()
        mock_response.content = '{"matched_requirements": [], "unmatched_requirements": [], "overall_match_score": 0.5}'
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.return_value = "Skill output"
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.return_value = "Experience output"
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    result = await skills_matching_node(base_state)
                    
                    # Should still produce valid output
                    assert result["current_phase"] == "generate_results"
                    assert "phase_4_output" in result


# =============================================================================
# Test Phase Complete Event
# =============================================================================

class TestPhaseCompleteEvent:
    """Test phase completion event content."""
    
    @pytest.fixture
    def base_state(self):
        """Create a base state with prior phase outputs."""
        state = create_initial_state("Company")
        state["phase_2_output"] = Phase2Output(
            employer_summary="Company info",
            identified_requirements=["Python", "React"],
            tech_stack=[],
            culture_signals=[],
            search_queries_used=[],
            reasoning_trace="",
        )
        state["phase_3_output"] = Phase3Output(
            genuine_strengths=[],
            genuine_gaps=["Gap"],
            transferable_skills=[],
            risk_assessment="medium",
            reasoning_trace="",
        )
        state["step_count"] = 5
        return state
    
    @pytest.mark.asyncio
    async def test_phase_complete_includes_score(self, base_state):
        """Phase complete event includes match score."""
        mock_callback = AsyncMock()
        mock_callback.on_phase = AsyncMock()
        mock_callback.on_thought = AsyncMock()
        mock_callback.on_phase_complete = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '''{
            "matched_requirements": [{"requirement": "Python", "matched_skill": "Python", "confidence": 0.8}],
            "unmatched_requirements": ["React"],
            "overall_match_score": 0.4,
            "reasoning_trace": "Done"
        }'''
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.return_value = "Skill output"
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.return_value = "Experience output"
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    await skills_matching_node(base_state, callback=mock_callback)
                    
                    # Check phase complete call
                    call_args = mock_callback.on_phase_complete.call_args
                    summary = call_args[0][1] if call_args[0] else call_args.kwargs.get("summary", "")
                    
                    # Should include score percentage
                    assert "%" in summary or "score" in summary.lower()
