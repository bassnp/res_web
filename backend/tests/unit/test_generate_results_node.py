"""
Unit tests for Phase 5: GENERATE_RESULTS node.

Tests cover:
- Context formatting utilities
- Employer context detection for tone calibration
- Response quality validation
- Streaming response generation
- Phase event emission (phase start, response chunks, phase complete)
- Error handling with graceful fallback response
- Integration with prior phase outputs

Location: res_backend/tests/unit/test_generate_results_node.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.nodes.generate_results import (
    generate_results_node,
    format_matched_skills_summary,
    format_gaps_for_prompt,
    format_strengths_for_prompt,
    format_transferable_skills,
    detect_employer_context,
    get_company_or_role,
    validate_response_quality,
    generate_fallback_response,
    load_phase_prompt,
    PHASE_NAME,
    GENERATION_TEMPERATURE,
    MAX_RESPONSE_WORDS,
)
from services.pipeline_state import (
    create_initial_state,
    Phase1Output,
    Phase2Output,
    Phase3Output,
    Phase4Output,
)


# =============================================================================
# Test Context Formatting Utilities
# =============================================================================

class TestFormatMatchedSkillsSummary:
    """Test matched skills formatting for prompt injection."""
    
    def test_formats_multiple_skills(self):
        """Multiple matched skills format correctly with confidence."""
        phase_4 = {
            "matched_requirements": [
                {"requirement": "Python", "matched_skill": "Python expertise", "confidence": 0.9},
                {"requirement": "React", "matched_skill": "React/Next.js", "confidence": 0.85},
                {"requirement": "Docker", "matched_skill": "Container experience", "confidence": 0.7},
            ]
        }
        result = format_matched_skills_summary(phase_4)
        
        assert "Python" in result
        assert "90%" in result
        assert "React" in result
        assert "85%" in result
        assert "Docker" in result
        assert "70%" in result
    
    def test_limits_to_five_skills(self):
        """Only top 5 skills are shown."""
        phase_4 = {
            "matched_requirements": [
                {"requirement": f"Skill{i}", "matched_skill": f"Match{i}", "confidence": 0.8}
                for i in range(8)
            ]
        }
        result = format_matched_skills_summary(phase_4)
        
        # Should have 5 specific skills plus "... and 3 additional matches"
        assert "Skill0" in result
        assert "Skill4" in result
        assert "Skill5" not in result
        assert "3 additional matches" in result
    
    def test_handles_empty_matches(self):
        """Empty matches returns appropriate message."""
        result = format_matched_skills_summary({})
        assert "No specific skill" in result
        
        result = format_matched_skills_summary({"matched_requirements": []})
        assert "No specific skill" in result
    
    def test_handles_missing_confidence(self):
        """Missing confidence defaults to 0.5 (50%)."""
        phase_4 = {
            "matched_requirements": [
                {"requirement": "Python", "matched_skill": "Python"}
            ]
        }
        result = format_matched_skills_summary(phase_4)
        assert "50%" in result


class TestFormatGapsForPrompt:
    """Test gap formatting for prompt injection."""
    
    def test_formats_multiple_gaps(self):
        """Multiple gaps format as bullet list."""
        phase_3 = {
            "genuine_gaps": [
                "No Kubernetes experience",
                "Limited fintech domain knowledge"
            ]
        }
        result = format_gaps_for_prompt(phase_3)
        
        assert "- No Kubernetes experience" in result
        assert "- Limited fintech" in result
    
    def test_handles_empty_gaps(self):
        """Empty gaps returns unusual message for review."""
        result = format_gaps_for_prompt({})
        assert "No significant gaps" in result
        assert "unusual" in result.lower()


class TestFormatStrengthsForPrompt:
    """Test strengths formatting for prompt injection."""
    
    def test_formats_multiple_strengths(self):
        """Multiple strengths format as bullet list."""
        phase_3 = {
            "genuine_strengths": [
                "Strong Python expertise",
                "AI/ML experience"
            ]
        }
        result = format_strengths_for_prompt(phase_3)
        
        assert "- Strong Python" in result
        assert "- AI/ML" in result
    
    def test_handles_empty_strengths(self):
        """Empty strengths returns default message."""
        result = format_strengths_for_prompt({})
        assert "Strengths to be highlighted" in result


class TestFormatTransferableSkills:
    """Test transferable skills formatting."""
    
    def test_formats_as_comma_list(self):
        """Transferable skills format as comma-separated list."""
        phase_3 = {
            "transferable_skills": ["Docker", "FastAPI", "SQL"]
        }
        result = format_transferable_skills(phase_3)
        
        assert result == "Docker, FastAPI, SQL"
    
    def test_handles_empty(self):
        """Empty returns appropriate message."""
        result = format_transferable_skills({})
        assert "None specifically identified" in result


# =============================================================================
# Test Employer Context Detection
# =============================================================================

class TestDetectEmployerContext:
    """Test employer context type detection for tone calibration."""
    
    def test_detects_ai_ml_context(self):
        """AI/ML keywords trigger ai_ml context."""
        phase_2 = {
            "employer_summary": "OpenAI builds cutting-edge AI and machine learning models",
            "tech_stack": ["Python", "PyTorch", "LLM"],
            "culture_signals": ["Innovation"]
        }
        result = detect_employer_context(phase_2, {})
        assert result == "ai_ml"
    
    def test_detects_fintech_context(self):
        """Financial keywords trigger fintech context."""
        phase_2 = {
            "employer_summary": "Stripe is a fintech company handling payments",
            "tech_stack": ["Go", "Ruby"],
            "culture_signals": ["Security"]
        }
        result = detect_employer_context(phase_2, {})
        assert result == "fintech"
    
    def test_detects_startup_context(self):
        """Startup keywords trigger startup context."""
        phase_2 = {
            "employer_summary": "Fast-paced startup in Series A",
            "culture_signals": ["move fast", "startup culture"],
            "tech_stack": []
        }
        result = detect_employer_context(phase_2, {})
        assert result == "startup"
    
    def test_detects_enterprise_context(self):
        """Enterprise keywords trigger enterprise context."""
        phase_2 = {
            "employer_summary": "Fortune 500 global enterprise",
            "culture_signals": ["established processes"],
            "tech_stack": ["Java", "Oracle"]
        }
        result = detect_employer_context(phase_2, {})
        assert result == "enterprise"
    
    def test_defaults_to_default_context(self):
        """Unknown context defaults to 'default'."""
        result = detect_employer_context({}, {})
        assert result == "default"
    
    def test_ai_ml_takes_priority(self):
        """AI/ML context takes priority over other signals."""
        phase_2 = {
            "employer_summary": "AI startup in fintech space",
            "tech_stack": ["Python", "TensorFlow"],
            "culture_signals": ["fast-paced"]
        }
        result = detect_employer_context(phase_2, {})
        # AI/ML should win because it's checked first
        assert result == "ai_ml"


class TestGetCompanyOrRole:
    """Test company/role extraction for personalization."""
    
    def test_returns_company_name(self):
        """Returns company name when present."""
        phase_1 = {"company_name": "Google", "job_title": None}
        result = get_company_or_role(phase_1, "google software engineer")
        assert result == "Google"
    
    def test_returns_job_title_when_no_company(self):
        """Returns job title when company is None."""
        phase_1 = {"company_name": None, "job_title": "Senior Software Engineer"}
        result = get_company_or_role(phase_1, "software engineer at startup")
        assert result == "Senior Software Engineer"
    
    def test_falls_back_to_query(self):
        """Falls back to query when neither present."""
        phase_1 = {"company_name": None, "job_title": None}
        result = get_company_or_role(phase_1, "looking for python developer role")
        assert result == "looking for python developer role"
    
    def test_truncates_long_query(self):
        """Long queries are truncated to 50 chars."""
        phase_1 = {}
        long_query = "x" * 100
        result = get_company_or_role(phase_1, long_query)
        assert len(result) == 50


# =============================================================================
# Test Response Quality Validation
# =============================================================================

class TestValidateResponseQuality:
    """Test response quality validation."""
    
    def test_validates_word_count(self):
        """Excessive word count is flagged."""
        long_response = "word " * 500
        warnings = validate_response_quality(long_response, {})
        
        assert any("exceeds" in w.lower() for w in warnings)
        assert any(str(MAX_RESPONSE_WORDS) in w for w in warnings)
    
    def test_validates_gap_acknowledgment(self):
        """Missing gap acknowledgment is flagged."""
        response = "I'm a perfect fit with amazing skills and no issues whatsoever!"
        phase_3 = {"genuine_gaps": ["No Kubernetes experience"]}
        
        warnings = validate_response_quality(response, phase_3)
        
        assert any("gap" in w.lower() for w in warnings)
    
    def test_accepts_gap_acknowledgment_by_keyword(self):
        """Gap acknowledgment via keywords passes validation."""
        response = """
        **The Learning Curve:**
        While I haven't worked with Kubernetes in production, my Docker experience
        would help me ramp up quickly.
        """
        phase_3 = {"genuine_gaps": ["No Kubernetes experience"]}
        
        warnings = validate_response_quality(response, phase_3)
        
        # Should not flag gap acknowledgment issue
        gap_warnings = [w for w in warnings if "gap" in w.lower()]
        assert len(gap_warnings) == 0
    
    def test_accepts_gap_via_section_keywords(self):
        """Learning/growth section keywords satisfy gap requirement."""
        response = """
        **Growth Areas:**
        I see this as an opportunity to develop new skills.
        """
        phase_3 = {"genuine_gaps": ["Something unrelated"]}
        
        warnings = validate_response_quality(response, phase_3)
        
        # Learning/growth keywords should satisfy gap acknowledgment
        gap_warnings = [w for w in warnings if "gap" in w.lower()]
        assert len(gap_warnings) == 0
    
    def test_flags_generic_phrases(self):
        """Generic phrases are flagged."""
        response = "I'm passionate about technology and excited about this opportunity!"
        
        warnings = validate_response_quality(response, {})
        
        assert any("generic" in w.lower() for w in warnings)
        assert len([w for w in warnings if "generic" in w.lower()]) >= 2
    
    def test_no_warnings_for_good_response(self):
        """Good response with gaps acknowledged has no warnings."""
        response = """
        ### Why I'm a Great Fit for Google

        **At a Glance:** 75% match with strong Python and AI/ML alignment.

        **Where I Align:**
        - Python expertise (90% confidence)
        - LangChain experience (85% confidence)

        **The Learning Curve:**
        While I haven't worked with large-scale distributed systems at Google scale,
        my Docker and microservices experience provides a foundation.

        **Let's Connect:**
        I'd love to discuss how my AI agent experience aligns with Google's LLM initiatives.
        """
        phase_3 = {"genuine_gaps": ["Large-scale distributed systems"]}
        
        warnings = validate_response_quality(response, phase_3)
        
        # Should have no warnings
        assert len(warnings) == 0


class TestGenerateFallbackResponse:
    """Test fallback response generation."""
    
    def test_generates_minimal_response(self):
        """Fallback response includes key elements."""
        phase_4 = {"overall_match_score": 0.65}
        result = generate_fallback_response(
            company_or_role="Google",
            phase_4=phase_4,
            error_message="LLM timeout"
        )
        
        assert "Google" in result
        assert "65%" in result
        assert "apologize" in result.lower()
        assert "processing error" in result.lower()
    
    def test_handles_missing_phase4(self):
        """Fallback works when phase_4 is None."""
        result = generate_fallback_response(
            company_or_role="Unknown Company",
            phase_4=None,
            error_message="Error"
        )
        
        assert "50%" in result  # Default score
        assert "Unknown Company" in result


# =============================================================================
# Test Prompt Loading
# =============================================================================

class TestPromptLoading:
    """Test prompt template loading."""
    
    def test_load_prompt_returns_string(self):
        """Prompt loading returns non-empty string."""
        prompt = load_phase_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "<system_instruction>" in prompt or "agent_persona" in prompt
    
    def test_fallback_prompt_has_required_placeholders(self):
        """Fallback prompt has required format placeholders."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            prompt = load_phase_prompt()
        
        # Should have key placeholders
        assert "{company_or_role}" in prompt or "{match_score}" in prompt


# =============================================================================
# Test Generate Results Node
# =============================================================================

class TestGenerateResultsNode:
    """Integration tests for the generate results node."""
    
    @pytest.fixture
    def full_state(self):
        """Create a complete state with all prior phase outputs."""
        state = create_initial_state("Google")
        state["phase_1_output"] = Phase1Output(
            query_type="company",
            company_name="Google",
            job_title=None,
            extracted_skills=["Python", "AI"],
            reasoning_trace="Identified as company query",
        )
        state["phase_2_output"] = Phase2Output(
            employer_summary="Google is a leading tech company focused on AI and cloud computing",
            identified_requirements=["Python", "TensorFlow", "Distributed Systems"],
            tech_stack=["Python", "Go", "TensorFlow", "Kubernetes"],
            culture_signals=["Innovation", "Impact at scale", "AI-first"],
            search_queries_used=["Google engineering jobs"],
            reasoning_trace="Research complete",
        )
        state["phase_3_output"] = Phase3Output(
            genuine_strengths=["Strong Python expertise", "AI/ML experience with LangChain"],
            genuine_gaps=["No Google-scale distributed systems experience", "Limited Go knowledge"],
            transferable_skills=["Docker experience", "FastAPI backend development"],
            risk_assessment="medium",
            reasoning_trace="Skeptical analysis complete",
        )
        state["phase_4_output"] = Phase4Output(
            matched_requirements=[
                {"requirement": "Python", "matched_skill": "Python expertise", "confidence": 0.9},
                {"requirement": "TensorFlow", "matched_skill": "AI/ML experience", "confidence": 0.7},
            ],
            unmatched_requirements=["Distributed Systems at scale", "Go"],
            overall_match_score=0.72,
            reasoning_trace="Skill matching complete",
        )
        state["step_count"] = 15
        return state
    
    @pytest.mark.asyncio
    async def test_generates_streaming_response(self, full_state):
        """Response is streamed correctly via callback."""
        callback = AsyncMock()
        callback.on_phase = AsyncMock()
        callback.on_phase_complete = AsyncMock()
        callback.on_thought = AsyncMock()
        callback.on_response_chunk = AsyncMock()
        
        # Mock streaming LLM
        async def mock_stream(*args, **kwargs):
            chunks = [
                "### Why I'm a Great Fit for ",
                "Google\n\n**At a Glance:** ",
                "72% match with strong Python",
            ]
            for chunk_text in chunks:
                mock_chunk = MagicMock()
                mock_chunk.content = chunk_text
                yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            result = await generate_results_node(full_state, callback=callback)
            
            # Verify streaming occurred
            assert callback.on_response_chunk.called
            chunk_calls = callback.on_response_chunk.call_args_list
            assert len(chunk_calls) == 3
            
            # Verify final response assembled
            assert "Why I'm a Great Fit" in result["final_response"]
            assert "Google" in result["final_response"]
    
    @pytest.mark.asyncio
    async def test_phase_events_emitted(self, full_state):
        """Phase start and complete events are emitted."""
        callback = AsyncMock()
        callback.on_phase = AsyncMock()
        callback.on_phase_complete = AsyncMock()
        callback.on_thought = AsyncMock()
        callback.on_response_chunk = AsyncMock()
        
        async def mock_stream(*args, **kwargs):
            mock_chunk = MagicMock()
            mock_chunk.content = "Response content"
            yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            await generate_results_node(full_state, callback=callback)
            
            # Phase start emitted
            callback.on_phase.assert_called_once()
            phase_call = callback.on_phase.call_args
            assert phase_call[0][0] == PHASE_NAME
            
            # Phase complete emitted
            callback.on_phase_complete.assert_called_once()
            complete_call = callback.on_phase_complete.call_args
            assert complete_call[0][0] == PHASE_NAME
            assert "word" in complete_call[0][1].lower()
    
    @pytest.mark.asyncio
    async def test_thought_event_emitted(self, full_state):
        """Reasoning thought is emitted before generation."""
        callback = AsyncMock()
        callback.on_phase = AsyncMock()
        callback.on_phase_complete = AsyncMock()
        callback.on_thought = AsyncMock()
        callback.on_response_chunk = AsyncMock()
        
        async def mock_stream(*args, **kwargs):
            mock_chunk = MagicMock()
            mock_chunk.content = "Response"
            yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            await generate_results_node(full_state, callback=callback)
            
            # Reasoning thought emitted
            callback.on_thought.assert_called()
            thought_call = callback.on_thought.call_args
            assert thought_call.kwargs.get("thought_type") == "reasoning"
            assert "72%" in thought_call.kwargs.get("content", "")
    
    @pytest.mark.asyncio
    async def test_error_produces_fallback_response(self, full_state):
        """Errors result in graceful fallback response."""
        callback = AsyncMock()
        callback.on_phase = AsyncMock()
        callback.on_phase_complete = AsyncMock()
        callback.on_thought = AsyncMock()
        callback.on_response_chunk = AsyncMock()
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            # Make LLM fail
            mock_llm.return_value.astream = AsyncMock(
                side_effect=Exception("LLM Error")
            )
            
            result = await generate_results_node(full_state, callback=callback)
            
            # Should have a fallback response
            assert "apologize" in result["final_response"].lower()
            assert "processing error" in result["final_response"].lower()
            
            # Should have error logged
            assert "processing_errors" in result
            assert any("Phase 5 error" in e for e in result["processing_errors"])
            
            # Fallback should be streamed
            callback.on_response_chunk.assert_called()
    
    @pytest.mark.asyncio
    async def test_returns_correct_state_keys(self, full_state):
        """Node returns correct state update keys."""
        async def mock_stream(*args, **kwargs):
            mock_chunk = MagicMock()
            mock_chunk.content = "Test response"
            yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            result = await generate_results_node(full_state)
            
            # Must have these keys
            assert "final_response" in result
            assert "step_count" in result
            
            # Step count should be incremented
            assert result["step_count"] > full_state["step_count"]
    
    @pytest.mark.asyncio
    async def test_uses_correct_temperature(self, full_state):
        """LLM is called with creative temperature."""
        async def mock_stream(*args, **kwargs):
            mock_chunk = MagicMock()
            mock_chunk.content = "Response"
            yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            await generate_results_node(full_state)
            
            # Verify temperature
            mock_llm.assert_called_once()
            call_kwargs = mock_llm.call_args.kwargs
            assert call_kwargs.get("streaming") is True
            assert call_kwargs.get("temperature") == GENERATION_TEMPERATURE
    
    @pytest.mark.asyncio
    async def test_detects_employer_context_for_tone(self, full_state):
        """Employer context is detected and used in prompt."""
        async def mock_stream(*args, **kwargs):
            mock_chunk = MagicMock()
            mock_chunk.content = "Response"
            yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            # The state has AI-related signals in phase_2
            await generate_results_node(full_state)
            
            # Verify LLM was called (we can't easily check prompt content
            # without more complex mocking, but we verify no error)
            mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handles_minimal_state(self):
        """Node handles state with minimal data gracefully."""
        state = create_initial_state("Unknown Company")
        state["phase_1_output"] = None
        state["phase_2_output"] = None
        state["phase_3_output"] = None
        state["phase_4_output"] = None
        state["step_count"] = 0
        
        async def mock_stream(*args, **kwargs):
            mock_chunk = MagicMock()
            mock_chunk.content = "Basic response"
            yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            result = await generate_results_node(state)
            
            # Should still produce output
            assert "final_response" in result
            assert len(result["final_response"]) > 0
    
    @pytest.mark.asyncio
    async def test_quality_warnings_added_to_errors(self, full_state):
        """Quality validation warnings are added to processing_errors."""
        async def mock_stream(*args, **kwargs):
            # Return a response with generic phrases
            mock_chunk = MagicMock()
            mock_chunk.content = "I'm passionate about technology and excited about this opportunity!"
            yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            result = await generate_results_node(full_state)
            
            # Should have quality warnings in processing_errors
            errors = result.get("processing_errors", [])
            quality_errors = [e for e in errors if "Quality:" in e]
            assert len(quality_errors) > 0
    
    @pytest.mark.asyncio
    async def test_callback_methods_optional(self, full_state):
        """Works with callback that doesn't have on_phase method."""
        callback = MagicMock()
        # Explicitly delete on_phase and on_phase_complete to test fallback
        del callback.on_phase
        del callback.on_phase_complete
        callback.on_status = AsyncMock()
        callback.on_thought = AsyncMock()
        callback.on_response_chunk = AsyncMock()
        
        async def mock_stream(*args, **kwargs):
            mock_chunk = MagicMock()
            mock_chunk.content = "Response"
            yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            # Should not raise AttributeError
            result = await generate_results_node(full_state, callback=callback)
            
            assert "final_response" in result
            # Falls back to on_status
            callback.on_status.assert_called()


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_handles_none_values_in_phase_outputs(self):
        """Handles None values in phase outputs gracefully."""
        state = create_initial_state("Test Company")
        state["phase_1_output"] = {"query_type": "company", "company_name": None, "job_title": None}
        state["phase_2_output"] = {"employer_summary": None, "tech_stack": None, "culture_signals": None}
        state["phase_3_output"] = {"genuine_gaps": None, "genuine_strengths": None}
        state["phase_4_output"] = {"matched_requirements": None, "overall_match_score": None}
        
        async def mock_stream(*args, **kwargs):
            mock_chunk = MagicMock()
            mock_chunk.content = "Response"
            yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            # Should not raise any exceptions
            result = await generate_results_node(state)
            assert "final_response" in result
    
    def test_format_functions_handle_empty_dicts(self):
        """Format functions handle empty dicts without crashing."""
        assert format_matched_skills_summary({}) == "No specific skill matches identified."
        assert "No significant gaps" in format_gaps_for_prompt({})
        assert "Strengths to be highlighted" in format_strengths_for_prompt({})
        assert "None specifically identified" in format_transferable_skills({})
        assert detect_employer_context({}, {}) == "default"
    
    def test_validate_response_quality_empty_inputs(self):
        """Validation handles empty inputs."""
        warnings = validate_response_quality("", {})
        # Empty response should pass word count but might have other issues
        assert isinstance(warnings, list)
        
        warnings = validate_response_quality("Short response", {"genuine_gaps": []})
        # No gaps means no gap warning
        gap_warnings = [w for w in warnings if "gap" in w.lower()]
        assert len(gap_warnings) == 0
