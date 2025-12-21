"""
Unit tests for Phase 1: CONNECTING node.

Tests cover:
- JSON extraction from various LLM response formats
- Output validation and normalization
- Node function execution with mocked LLM
- Callback event emission
- Error handling and graceful degradation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.nodes.connecting import (
    connecting_node,
    extract_json_from_response,
    validate_phase1_output,
    load_phase_prompt,
    PHASE_NAME,
)
from services.pipeline_state import create_initial_state, Phase1Output


# =============================================================================
# Test JSON Extraction
# =============================================================================

class TestJSONExtraction:
    """Test JSON extraction from various LLM response formats."""
    
    def test_clean_json(self):
        """Direct JSON should parse correctly."""
        response = '{"query_type": "company", "company_name": "Google", "job_title": null, "extracted_skills": [], "reasoning_trace": "Single company name"}'
        result = extract_json_from_response(response)
        assert result["query_type"] == "company"
        assert result["company_name"] == "Google"
        assert result["job_title"] is None
    
    def test_json_with_markdown_json_tag(self):
        """JSON in ```json code blocks should parse."""
        response = '```json\n{"query_type": "company", "company_name": "Stripe", "extracted_skills": []}\n```'
        result = extract_json_from_response(response)
        assert result["company_name"] == "Stripe"
    
    def test_json_with_plain_markdown(self):
        """JSON in plain ``` code blocks should parse."""
        response = '```\n{"query_type": "job_description", "job_title": "Engineer"}\n```'
        result = extract_json_from_response(response)
        assert result["query_type"] == "job_description"
    
    def test_json_with_surrounding_text(self):
        """JSON with surrounding prose should be extracted."""
        response = 'Here is my analysis:\n{"query_type": "job_description", "company_name": null}\nDone!'
        result = extract_json_from_response(response)
        assert result["query_type"] == "job_description"
    
    def test_json_with_whitespace(self):
        """JSON with extra whitespace should parse."""
        response = '''
        
        {"query_type": "company", "company_name": "Meta"}
        
        '''
        result = extract_json_from_response(response)
        assert result["company_name"] == "Meta"
    
    def test_nested_json(self):
        """Complex nested JSON should parse correctly."""
        response = '{"query_type": "job_description", "extracted_skills": ["Python", "AWS", "Docker"]}'
        result = extract_json_from_response(response)
        assert result["extracted_skills"] == ["Python", "AWS", "Docker"]
    
    def test_invalid_json_raises(self):
        """Invalid JSON should raise ValueError."""
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            extract_json_from_response("This is not JSON at all")
    
    def test_empty_response_raises(self):
        """Empty response should raise ValueError."""
        with pytest.raises(ValueError):
            extract_json_from_response("")
    
    def test_malformed_json_raises(self):
        """Malformed JSON should raise ValueError."""
        with pytest.raises(ValueError):
            extract_json_from_response('{"query_type": "company", "company_name":}')


# =============================================================================
# Test Output Validation
# =============================================================================

class TestOutputValidation:
    """Test Phase 1 output validation and normalization."""
    
    def test_valid_company_output(self):
        """Valid company query should validate correctly."""
        data = {
            "query_type": "company",
            "company_name": "OpenAI",
            "job_title": None,
            "extracted_skills": ["Python", "ML"],
            "reasoning_trace": "Single company name detected.",
        }
        result = validate_phase1_output(data)
        
        assert result["query_type"] == "company"
        assert result["company_name"] == "OpenAI"
        assert result["job_title"] is None
        assert result["extracted_skills"] == ["Python", "ML"]
        assert result["reasoning_trace"] == "Single company name detected."
    
    def test_valid_job_description_output(self):
        """Valid job description should validate correctly."""
        data = {
            "query_type": "job_description",
            "company_name": "Netflix",
            "job_title": "Senior Engineer",
            "extracted_skills": ["Java", "Spring", "AWS"],
            "reasoning_trace": "Job title with requirements detected.",
        }
        result = validate_phase1_output(data)
        
        assert result["query_type"] == "job_description"
        assert result["company_name"] == "Netflix"
        assert result["job_title"] == "Senior Engineer"
    
    def test_invalid_query_type_recovery_company(self):
        """Invalid query_type should recover to 'company' if company_name only."""
        data = {
            "query_type": "invalid",
            "company_name": "Meta",
            "job_title": None,
        }
        result = validate_phase1_output(data)
        assert result["query_type"] == "company"
    
    def test_invalid_query_type_recovery_job_description(self):
        """Invalid query_type should recover to 'job_description' by default."""
        data = {
            "query_type": "invalid",
            "company_name": None,
            "job_title": "Engineer",
        }
        result = validate_phase1_output(data)
        assert result["query_type"] == "job_description"
    
    def test_empty_string_normalization(self):
        """Empty strings should normalize to None."""
        data = {
            "query_type": "company",
            "company_name": "",
            "job_title": "",
        }
        result = validate_phase1_output(data)
        assert result["company_name"] is None
        assert result["job_title"] is None
    
    def test_null_string_normalization(self):
        """String 'null' should normalize to None."""
        data = {
            "query_type": "company",
            "company_name": "null",
            "job_title": "None",
        }
        result = validate_phase1_output(data)
        assert result["company_name"] is None
        assert result["job_title"] is None
    
    def test_missing_fields_default(self):
        """Missing optional fields should default correctly."""
        data = {"query_type": "job_description"}
        result = validate_phase1_output(data)
        
        assert result["company_name"] is None
        assert result["job_title"] is None
        assert result["extracted_skills"] == []
        assert result["reasoning_trace"] == "Classification completed."
    
    def test_skills_normalization(self):
        """Skills should filter empty strings and non-strings."""
        data = {
            "query_type": "job_description",
            "extracted_skills": ["Python", "", "  ", "AWS", 123, None],
        }
        result = validate_phase1_output(data)
        assert result["extracted_skills"] == ["Python", "AWS"]
    
    def test_skills_not_list(self):
        """Non-list skills should default to empty list."""
        data = {
            "query_type": "company",
            "extracted_skills": "Python",  # String instead of list
        }
        result = validate_phase1_output(data)
        assert result["extracted_skills"] == []
    
    def test_skills_whitespace_trimmed(self):
        """Skill names should have whitespace trimmed."""
        data = {
            "query_type": "job_description",
            "extracted_skills": ["  Python  ", "AWS ", " Docker"],
        }
        result = validate_phase1_output(data)
        assert result["extracted_skills"] == ["Python", "AWS", "Docker"]


# =============================================================================
# Test Prompt Loading
# =============================================================================

class TestPromptLoading:
    """Test prompt file loading."""
    
    def test_prompt_loads(self):
        """Phase 1 prompt should load from file."""
        prompt = load_phase_prompt()
        assert "<system_instruction>" in prompt
        assert "<agent_persona>" in prompt
        assert "{query}" in prompt
    
    def test_prompt_contains_required_elements(self):
        """Prompt should contain all required XML elements."""
        prompt = load_phase_prompt()
        
        required_elements = [
            "<primary_objective>",
            "<success_criteria>",
            "<behavioral_constraints>",
            "<output_contract>",
        ]
        for element in required_elements:
            assert element in prompt, f"Missing required element: {element}"


# =============================================================================
# Test Connecting Node
# =============================================================================

class TestConnectingNode:
    """Integration tests for the connecting node."""
    
    @pytest.mark.asyncio
    async def test_company_classification(self):
        """Company name query should classify correctly."""
        state = create_initial_state("Google")
        
        mock_response = MagicMock()
        mock_response.content = '{"query_type": "company", "company_name": "Google", "job_title": null, "extracted_skills": [], "reasoning_trace": "Single company name"}'
        
        with patch("services.nodes.connecting.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            
            result = await connecting_node(state)
            
            assert result["phase_1_output"]["query_type"] == "company"
            assert result["phase_1_output"]["company_name"] == "Google"
            assert result["current_phase"] == "deep_research"
            assert result["step_count"] == 1
    
    @pytest.mark.asyncio
    async def test_job_description_classification(self):
        """Job description should classify with skills extraction."""
        state = create_initial_state("Senior Python developer with AWS experience at a startup")
        
        mock_response = MagicMock()
        mock_response.content = '''
        {"query_type": "job_description", 
         "company_name": null,
         "job_title": "Senior Python developer",
         "extracted_skills": ["Python", "AWS"],
         "reasoning_trace": "Job requirements detected with role and skills"}
        '''
        
        with patch("services.nodes.connecting.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            
            result = await connecting_node(state)
            
            assert result["phase_1_output"]["query_type"] == "job_description"
            assert result["phase_1_output"]["job_title"] == "Senior Python developer"
            assert "Python" in result["phase_1_output"]["extracted_skills"]
            assert "AWS" in result["phase_1_output"]["extracted_skills"]
    
    @pytest.mark.asyncio
    async def test_callback_status_event(self):
        """Callback should receive status event when on_phase not available."""
        state = create_initial_state("Stripe")
        
        # Create a callback without on_phase method to test backward compatibility
        class LegacyCallback:
            def __init__(self):
                self.status_calls = []
                self.thought_calls = []
            
            async def on_status(self, status: str, message: str):
                self.status_calls.append((status, message))
            
            async def on_thought(self, step: int, thought_type: str, content: str, 
                                 tool=None, tool_input=None, phase=None):
                self.thought_calls.append((step, thought_type, content))
        
        callback = LegacyCallback()
        
        mock_response = MagicMock()
        mock_response.content = '{"query_type": "company", "company_name": "Stripe"}'
        
        with patch("services.nodes.connecting.get_llm") as mock_get_llm, \
             patch("services.nodes.connecting.llm_breaker") as mock_breaker:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            mock_breaker.call.return_value.__aenter__ = AsyncMock()
            mock_breaker.call.return_value.__aexit__ = AsyncMock()
            
            await connecting_node(state, callback=callback)
            
            # Should have called callback.on_thought at least once
            assert len(callback.thought_calls) >= 1
    
    @pytest.mark.asyncio
    async def test_callback_phase_events(self):
        """Callback should receive phase-specific events when available."""
        state = create_initial_state("Netflix")
        callback = AsyncMock()
        callback.on_phase = AsyncMock()
        callback.on_phase_complete = AsyncMock()
        callback.on_thought = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '{"query_type": "company", "company_name": "Netflix"}'
        
        with patch("services.nodes.connecting.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            
            await connecting_node(state, callback=callback)
            
            # Verify phase events were called
            callback.on_phase.assert_called_once_with(
                PHASE_NAME,
                "Classifying query and extracting entities..."
            )
            callback.on_phase_complete.assert_called_once()
            callback.on_thought.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_graceful_degradation(self):
        """Errors should result in graceful fallback."""
        state = create_initial_state("test query")
        
        with patch("services.nodes.connecting.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))
            mock_get_llm.return_value = mock_llm
            
            result = await connecting_node(state)
            
            # Should still return valid output with fallback
            assert result["phase_1_output"]["query_type"] == "job_description"
            assert result["current_phase"] == "deep_research"
            assert "processing_errors" in result
            assert len(result["processing_errors"]) > 0
            assert "Phase 1 error" in result["processing_errors"][0]
    
    @pytest.mark.asyncio
    async def test_json_in_markdown_handled(self):
        """LLM response with markdown code blocks should be handled."""
        state = create_initial_state("Amazon")
        
        mock_response = MagicMock()
        mock_response.content = '''Here is the classification:
```json
{"query_type": "company", "company_name": "Amazon", "extracted_skills": ["AWS"]}
```
'''
        
        with patch("services.nodes.connecting.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            
            result = await connecting_node(state)
            
            assert result["phase_1_output"]["query_type"] == "company"
            assert result["phase_1_output"]["company_name"] == "Amazon"
    
    @pytest.mark.asyncio
    async def test_step_count_incremented(self):
        """Step count should increment from initial state."""
        state = create_initial_state("Test")
        state["step_count"] = 5
        
        mock_response = MagicMock()
        mock_response.content = '{"query_type": "company", "company_name": "Test"}'
        
        with patch("services.nodes.connecting.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            
            result = await connecting_node(state)
            
            assert result["step_count"] == 6
    
    @pytest.mark.asyncio
    async def test_temperature_setting(self):
        """LLM should be called with low temperature for classification."""
        state = create_initial_state("Stripe")
        
        mock_response = MagicMock()
        mock_response.content = '{"query_type": "company", "company_name": "Stripe"}'
        
        with patch("services.nodes.connecting.get_llm") as mock_get_llm, \
             patch("services.nodes.connecting.llm_breaker") as mock_breaker:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            mock_breaker.call.return_value.__aenter__ = AsyncMock()
            mock_breaker.call.return_value.__aexit__ = AsyncMock()
            
            await connecting_node(state)
            
            # Verify get_llm was called with low temperature (0.1 for classification)
            mock_get_llm.assert_called_once()
            call_kwargs = mock_get_llm.call_args.kwargs
            assert call_kwargs.get("streaming") == False
            assert call_kwargs.get("temperature") == 0.1


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_very_short_query(self):
        """Very short query (just company name) should work."""
        state = create_initial_state("IBM")
        
        mock_response = MagicMock()
        mock_response.content = '{"query_type": "company", "company_name": "IBM"}'
        
        with patch("services.nodes.connecting.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            
            result = await connecting_node(state)
            assert result["phase_1_output"]["query_type"] == "company"
    
    @pytest.mark.asyncio
    async def test_long_job_description(self):
        """Long job description with many skills should work."""
        long_query = """
        We are looking for a Senior Software Engineer with 5+ years of experience in
        Python, JavaScript, TypeScript, React, Node.js, FastAPI, PostgreSQL, Redis,
        Docker, Kubernetes, AWS, GCP, CI/CD, and machine learning frameworks like
        TensorFlow and PyTorch. Experience with LangChain and LLM applications preferred.
        """
        state = create_initial_state(long_query)
        
        mock_response = MagicMock()
        mock_response.content = '''{
            "query_type": "job_description",
            "job_title": "Senior Software Engineer",
            "extracted_skills": ["Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI"],
            "reasoning_trace": "Long job description with multiple requirements"
        }'''
        
        with patch("services.nodes.connecting.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            
            result = await connecting_node(state)
            assert result["phase_1_output"]["query_type"] == "job_description"
            assert len(result["phase_1_output"]["extracted_skills"]) > 0
    
    @pytest.mark.asyncio  
    async def test_ambiguous_input(self):
        """Ambiguous input should default to job_description."""
        state = create_initial_state("Python developer")
        
        mock_response = MagicMock()
        mock_response.content = '{"query_type": "job_description", "job_title": "Python developer", "extracted_skills": ["Python"]}'
        
        with patch("services.nodes.connecting.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            
            result = await connecting_node(state)
            assert result["phase_1_output"]["query_type"] == "job_description"
