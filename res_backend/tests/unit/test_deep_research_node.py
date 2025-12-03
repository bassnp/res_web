"""
Unit tests for Phase 2: DEEP_RESEARCH node.

Tests cover:
- Search query construction for company and job_description types
- Search result formatting
- JSON extraction from various LLM response formats
- Output validation and normalization
- Node function execution with mocked LLM and search
- Callback event emission
- Error handling and graceful degradation

Location: res_backend/tests/unit/test_deep_research_node.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.nodes.deep_research import (
    deep_research_node,
    construct_search_queries,
    format_search_results,
    extract_json_from_response,
    validate_phase2_output,
    load_phase_prompt,
    PHASE_NAME,
    MAX_RESULT_LENGTH,
)
from services.pipeline_state import create_initial_state, Phase1Output, Phase2Output


# =============================================================================
# Test Search Query Construction
# =============================================================================

class TestSearchQueryConstruction:
    """Test search query construction logic for different query types."""
    
    def test_company_query_generates_two_queries(self):
        """Company classification generates appropriate search queries."""
        phase_1 = {
            "query_type": "company",
            "company_name": "Google",
            "job_title": None,
            "extracted_skills": [],
            "reasoning_trace": "Company name identified",
        }
        queries = construct_search_queries(phase_1, "Google")
        
        assert len(queries) == 2
        assert "Google" in queries[0]
        assert any(term in queries[0].lower() for term in ["tech stack", "culture", "engineer"])
        assert any(term in queries[1].lower() for term in ["careers", "jobs", "requirements"])
    
    def test_company_query_uses_original_query_as_fallback(self):
        """When company_name is None, uses original query."""
        phase_1 = {
            "query_type": "company",
            "company_name": None,
            "job_title": None,
            "extracted_skills": [],
            "reasoning_trace": "",
        }
        queries = construct_search_queries(phase_1, "Stripe")
        
        assert len(queries) == 2
        assert "Stripe" in queries[0]
    
    def test_job_description_with_company_and_skills(self):
        """Job description with company generates company-specific queries."""
        phase_1 = {
            "query_type": "job_description",
            "company_name": "Stripe",
            "job_title": "Senior Python Developer",
            "extracted_skills": ["Python", "AWS", "PostgreSQL"],
            "reasoning_trace": "",
        }
        queries = construct_search_queries(phase_1, "original query")
        
        assert len(queries) == 2
        # Primary query should include title and skills
        assert "Senior Python Developer" in queries[0] or "Python" in queries[0]
        # Secondary should be company culture
        assert "Stripe" in queries[1]
    
    def test_job_description_without_company(self):
        """Job description without company generates industry-focused queries."""
        phase_1 = {
            "query_type": "job_description",
            "company_name": None,
            "job_title": "Backend Engineer",
            "extracted_skills": ["Python", "Django"],
            "reasoning_trace": "",
        }
        queries = construct_search_queries(phase_1, "original")
        
        assert len(queries) == 2
        assert "Backend Engineer" in queries[0]
        # Should have skill-focused secondary query
        assert "Python" in queries[1] or "Django" in queries[1]
    
    def test_query_limit_enforced(self):
        """Queries are limited to MAX_SEARCH_QUERIES."""
        phase_1 = {
            "query_type": "company",
            "company_name": "Meta",
            "job_title": None,
            "extracted_skills": ["Python", "React", "GraphQL", "Kubernetes"],
            "reasoning_trace": "",
        }
        queries = construct_search_queries(phase_1, "Meta")
        
        assert len(queries) <= 2
    
    def test_skills_truncated_to_three(self):
        """Only first 3 skills are used in queries to avoid over-specification."""
        phase_1 = {
            "query_type": "job_description",
            "company_name": None,
            "job_title": "Engineer",
            "extracted_skills": ["Python", "Go", "Rust", "Java", "TypeScript"],
            "reasoning_trace": "",
        }
        queries = construct_search_queries(phase_1, "original")
        
        # Should only use first 3 skills max
        combined = " ".join(queries)
        skill_count = sum(1 for skill in ["Python", "Go", "Rust", "Java", "TypeScript"] if skill in combined)
        assert skill_count <= 3


# =============================================================================
# Test Result Formatting
# =============================================================================

class TestResultFormatting:
    """Test search result formatting for prompt injection."""
    
    def test_format_multiple_results(self):
        """Multiple results format correctly with numbered sections."""
        results = [
            {"query": "Google engineering", "result": "Google uses Python..."},
            {"query": "Google careers", "result": "Looking for engineers..."},
        ]
        formatted = format_search_results(results)
        
        assert "Search Result 1" in formatted
        assert "Search Result 2" in formatted
        assert "Google engineering" in formatted
        assert "Google uses Python" in formatted
    
    def test_empty_results_returns_message(self):
        """Empty results return informative default message."""
        formatted = format_search_results([])
        assert "No search results" in formatted or "Limited data" in formatted
    
    def test_long_results_truncated(self):
        """Long results are truncated to prevent context overflow."""
        long_content = "x" * (MAX_RESULT_LENGTH + 500)
        results = [{"query": "test", "result": long_content}]
        formatted = format_search_results(results)
        
        assert len(formatted) < len(long_content)
        assert "[truncated]" in formatted
    
    def test_result_includes_query(self):
        """Formatted result includes the query for attribution."""
        results = [{"query": "Stripe tech stack", "result": "Uses Ruby on Rails"}]
        formatted = format_search_results(results)
        
        assert "Stripe tech stack" in formatted
        assert "Query:" in formatted


# =============================================================================
# Test JSON Extraction
# =============================================================================

class TestJSONExtraction:
    """Test JSON extraction from various LLM response formats."""
    
    def test_clean_json(self):
        """Direct JSON should parse correctly."""
        response = '{"employer_summary": "Google is a tech giant", "tech_stack": ["Python"]}'
        result = extract_json_from_response(response)
        
        assert result["employer_summary"] == "Google is a tech giant"
        assert result["tech_stack"] == ["Python"]
    
    def test_json_with_markdown_tag(self):
        """JSON in ```json code blocks should parse."""
        response = '```json\n{"employer_summary": "Stripe uses Ruby", "tech_stack": ["Ruby"]}\n```'
        result = extract_json_from_response(response)
        
        assert "Stripe" in result["employer_summary"]
    
    def test_json_with_plain_markdown(self):
        """JSON in plain ``` code blocks should parse."""
        response = '```\n{"employer_summary": "Test", "identified_requirements": ["Python"]}\n```'
        result = extract_json_from_response(response)
        
        assert result["employer_summary"] == "Test"
    
    def test_json_with_surrounding_prose(self):
        """JSON with surrounding prose should be extracted."""
        response = 'Here is my analysis:\n{"employer_summary": "Meta focuses on AI"}\nDone!'
        result = extract_json_from_response(response)
        
        assert "Meta" in result["employer_summary"]
    
    def test_complex_nested_json(self):
        """Complex JSON with arrays should parse correctly."""
        response = '''
        {
            "employer_summary": "Tech company",
            "identified_requirements": ["5 years Python", "AWS experience"],
            "tech_stack": ["Python", "AWS", "Docker"],
            "culture_signals": ["Remote-first", "Startup culture"],
            "data_quality": "high",
            "reasoning_trace": "Synthesized from job posting"
        }
        '''
        result = extract_json_from_response(response)
        
        assert len(result["tech_stack"]) == 3
        assert result["data_quality"] == "high"
    
    def test_invalid_json_raises_error(self):
        """Invalid JSON should raise ValueError."""
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            extract_json_from_response("This is not JSON at all")
    
    def test_malformed_json_raises_error(self):
        """Malformed JSON should raise ValueError."""
        with pytest.raises(ValueError):
            extract_json_from_response('{"employer_summary": "incomplete')


# =============================================================================
# Test Output Validation
# =============================================================================

class TestOutputValidation:
    """Test Phase 2 output validation and normalization."""
    
    def test_valid_full_output(self):
        """Valid complete research output validates correctly."""
        data = {
            "employer_summary": "Google is a leading technology company...",
            "identified_requirements": ["Python expertise", "Distributed systems"],
            "tech_stack": ["Python", "Go", "Kubernetes"],
            "culture_signals": ["Innovation-focused", "Data-driven"],
            "data_quality": "high",
            "reasoning_trace": "Synthesized from official job postings.",
        }
        queries = ["google engineer", "google careers"]
        result = validate_phase2_output(data, queries)
        
        assert result["employer_summary"] == "Google is a leading technology company..."
        assert len(result["tech_stack"]) == 3
        assert result["search_queries_used"] == queries
    
    def test_missing_fields_default_correctly(self):
        """Missing fields default to appropriate values."""
        data = {"employer_summary": "Basic summary"}
        result = validate_phase2_output(data, [])
        
        assert result["employer_summary"] == "Basic summary"
        assert result["tech_stack"] == []
        assert result["identified_requirements"] == []
        assert result["culture_signals"] == []
        assert result["search_queries_used"] == []
    
    def test_empty_employer_summary_defaults(self):
        """Empty employer_summary gets default value."""
        data = {"employer_summary": "", "tech_stack": ["Python"]}
        result = validate_phase2_output(data, [])
        
        assert "Limited" in result["employer_summary"] or "available" in result["employer_summary"]
    
    def test_non_string_items_filtered(self):
        """Non-string items in arrays are filtered or converted."""
        data = {
            "employer_summary": "Test",
            "tech_stack": ["Python", None, "", "   ", "AWS", 123],
            "identified_requirements": ["Valid", None, ""],
        }
        result = validate_phase2_output(data, [])
        
        # Should have filtered out empty/null values
        assert "Python" in result["tech_stack"]
        assert "AWS" in result["tech_stack"]
        assert None not in result["tech_stack"]
        assert "" not in result["tech_stack"]
    
    def test_queries_preserved(self):
        """Search queries used are preserved in output."""
        data = {"employer_summary": "Test"}
        queries = ["query 1", "query 2"]
        result = validate_phase2_output(data, queries)
        
        assert result["search_queries_used"] == queries


# =============================================================================
# Test Deep Research Node
# =============================================================================

class TestDeepResearchNode:
    """Integration tests for the deep research node execution."""
    
    @pytest.mark.asyncio
    async def test_successful_research_company_query(self):
        """Successful research for company query type."""
        state = create_initial_state("Google")
        state["phase_1_output"] = {
            "query_type": "company",
            "company_name": "Google",
            "job_title": None,
            "extracted_skills": [],
            "reasoning_trace": "Company name identified",
        }
        state["step_count"] = 1
        
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "employer_summary": "Google is a leading tech company known for innovation",
            "identified_requirements": ["Python", "Machine Learning"],
            "tech_stack": ["Python", "TensorFlow", "Kubernetes"],
            "culture_signals": ["Innovation-focused", "20% time"],
            "data_quality": "high",
            "reasoning_trace": "Synthesized from search results."
        }
        '''
        
        with patch("services.nodes.deep_research.web_search") as mock_search:
            mock_search.invoke.return_value = "Google uses Python and TensorFlow for ML..."
            
            with patch("services.nodes.deep_research.get_llm") as mock_llm:
                mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                
                result = await deep_research_node(state)
                
                assert result["phase_2_output"]["employer_summary"] == "Google is a leading tech company known for innovation"
                assert result["current_phase"] == "skeptical_comparison"
                assert len(result["phase_2_output"]["tech_stack"]) == 3
                assert "Python" in result["phase_2_output"]["tech_stack"]
    
    @pytest.mark.asyncio
    async def test_successful_research_job_description(self):
        """Successful research for job description query type."""
        state = create_initial_state("Looking for Python developer with AWS experience")
        state["phase_1_output"] = {
            "query_type": "job_description",
            "company_name": "Acme Corp",
            "job_title": "Python Developer",
            "extracted_skills": ["Python", "AWS"],
            "reasoning_trace": "Job description with requirements",
        }
        state["step_count"] = 1
        
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "employer_summary": "Acme Corp is a growing startup",
            "identified_requirements": ["Python 3+", "AWS experience"],
            "tech_stack": ["Python", "AWS", "Docker"],
            "culture_signals": ["Startup culture"],
            "data_quality": "medium",
            "reasoning_trace": "Limited public information available."
        }
        '''
        
        with patch("services.nodes.deep_research.web_search") as mock_search:
            mock_search.invoke.return_value = "Acme Corp hiring Python developers..."
            
            with patch("services.nodes.deep_research.get_llm") as mock_llm:
                mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                
                result = await deep_research_node(state)
                
                assert result["current_phase"] == "skeptical_comparison"
                assert "AWS" in result["phase_2_output"]["tech_stack"]
    
    @pytest.mark.asyncio
    async def test_callback_events_emitted(self):
        """Callback receives appropriate phase and thought events."""
        state = create_initial_state("Stripe")
        state["phase_1_output"] = {
            "query_type": "company",
            "company_name": "Stripe",
            "job_title": None,
            "extracted_skills": [],
            "reasoning_trace": "",
        }
        state["step_count"] = 1
        
        callback = AsyncMock()
        callback.on_phase = AsyncMock()
        callback.on_thought = AsyncMock()
        callback.on_phase_complete = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '{"employer_summary": "Stripe", "tech_stack": ["Ruby"]}'
        
        with patch("services.nodes.deep_research.web_search") as mock_search:
            mock_search.invoke.return_value = "Stripe info..."
            
            with patch("services.nodes.deep_research.get_llm") as mock_llm:
                mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                
                await deep_research_node(state, callback=callback)
                
                # Verify phase events
                callback.on_phase.assert_called_once()
                phase_call = callback.on_phase.call_args
                # on_phase is called with positional args (phase_name, message)
                assert phase_call[0][0] == PHASE_NAME
                
                # Verify thought events were called (tool_call, observation, reasoning)
                assert callback.on_thought.call_count >= 3
                
                # Verify phase complete
                callback.on_phase_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_failure_graceful_degradation(self):
        """Search failures result in graceful degradation, not crash."""
        state = create_initial_state("Unknown Company XYZ")
        state["phase_1_output"] = {
            "query_type": "company",
            "company_name": "Unknown Company XYZ",
            "job_title": None,
            "extracted_skills": [],
            "reasoning_trace": "",
        }
        state["step_count"] = 1
        
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "employer_summary": "Limited information available",
            "identified_requirements": [],
            "tech_stack": [],
            "culture_signals": [],
            "data_quality": "low",
            "reasoning_trace": "Sparse search results."
        }
        '''
        
        with patch("services.nodes.deep_research.web_search") as mock_search:
            # First search fails, second succeeds
            mock_search.invoke.side_effect = [
                Exception("Network timeout"),
                "Some partial results...",
            ]
            
            with patch("services.nodes.deep_research.get_llm") as mock_llm:
                mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                
                result = await deep_research_node(state)
                
                # Should still transition to next phase
                assert result["current_phase"] == "skeptical_comparison"
                assert result["phase_2_output"] is not None
    
    @pytest.mark.asyncio
    async def test_llm_failure_returns_fallback(self):
        """LLM failure returns fallback output and continues pipeline."""
        state = create_initial_state("Test Company")
        state["phase_1_output"] = {
            "query_type": "company",
            "company_name": "Test Company",
            "job_title": None,
            "extracted_skills": [],
            "reasoning_trace": "",
        }
        state["step_count"] = 1
        
        with patch("services.nodes.deep_research.web_search") as mock_search:
            mock_search.invoke.return_value = "Search results..."
            
            with patch("services.nodes.deep_research.get_llm") as mock_llm:
                mock_llm.return_value.ainvoke = AsyncMock(
                    side_effect=Exception("LLM API error")
                )
                
                result = await deep_research_node(state)
                
                # Should return fallback and continue
                assert result["current_phase"] == "skeptical_comparison"
                assert "Unable to gather" in result["phase_2_output"]["employer_summary"] or \
                       "error" in result["phase_2_output"]["reasoning_trace"].lower()
                assert "processing_errors" in result
                assert len(result["processing_errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_step_count_incremented(self):
        """Step count is properly incremented through the phase."""
        state = create_initial_state("Google")
        state["phase_1_output"] = {
            "query_type": "company",
            "company_name": "Google",
            "job_title": None,
            "extracted_skills": [],
            "reasoning_trace": "",
        }
        state["step_count"] = 5  # Start from previous phase count
        
        mock_response = MagicMock()
        mock_response.content = '{"employer_summary": "Test", "tech_stack": []}'
        
        with patch("services.nodes.deep_research.web_search") as mock_search:
            mock_search.invoke.return_value = "Results..."
            
            with patch("services.nodes.deep_research.get_llm") as mock_llm:
                mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                
                result = await deep_research_node(state)
                
                # Step count should have increased
                assert result["step_count"] > 5


# =============================================================================
# Test Prompt Loading
# =============================================================================

class TestPromptLoading:
    """Test prompt template loading."""
    
    def test_load_phase_prompt_returns_string(self):
        """load_phase_prompt returns a non-empty string."""
        prompt = load_phase_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_prompt_contains_required_placeholders(self):
        """Prompt template contains required format placeholders."""
        prompt = load_phase_prompt()
        
        assert "{query_type}" in prompt or "{" in prompt
        assert "{company_name}" in prompt or "company" in prompt.lower()
        assert "{search_results}" in prompt or "search" in prompt.lower()
    
    def test_prompt_contains_xml_structure(self):
        """Prompt uses XML structure for Gemini optimization."""
        prompt = load_phase_prompt()
        
        assert "<system_instruction>" in prompt or "<agent_persona>" in prompt
        assert "<output_contract>" in prompt or "output" in prompt.lower()


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_phase1_output_handled(self):
        """Empty Phase 1 output is handled gracefully."""
        phase_1 = {}
        queries = construct_search_queries(phase_1, "fallback query")
        
        # Should not raise, should return valid queries
        assert len(queries) > 0
    
    def test_none_skills_handled(self):
        """None skills list is handled gracefully."""
        phase_1 = {
            "query_type": "job_description",
            "company_name": None,
            "job_title": "Engineer",
            "extracted_skills": None,
            "reasoning_trace": "",
        }
        queries = construct_search_queries(phase_1, "test")
        
        assert len(queries) > 0
    
    def test_whitespace_in_query_cleaned(self):
        """Extra whitespace in constructed queries is cleaned."""
        phase_1 = {
            "query_type": "job_description",
            "company_name": None,
            "job_title": "  Software Engineer  ",
            "extracted_skills": [],
            "reasoning_trace": "",
        }
        queries = construct_search_queries(phase_1, "test")
        
        # Should not have double spaces
        for query in queries:
            assert "  " not in query
