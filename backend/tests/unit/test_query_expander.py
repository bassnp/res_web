import pytest
from services.utils.query_expander import expand_queries, reformulate_queries

class TestQueryExpansion:
    """Test query expansion functionality."""
    
    def test_company_focus_generates_minimum_queries(self):
        """Should generate at least 3 queries for company focus."""
        result = expand_queries(
            phase_1_output={"query_type": "company", "company_name": "Stripe"},
            original_query="Stripe",
        )
        assert len(result.queries) >= 3
        assert result.expansion_strategy == "company_focus"
    
    def test_job_focus_includes_skills(self):
        """Should incorporate extracted skills in job queries."""
        result = expand_queries(
            phase_1_output={
                "query_type": "job_description",
                "job_title": "backend engineer",
                "extracted_skills": ["Python", "Kubernetes"],
            },
            original_query="Python backend engineer",
        )
        # At least one query should contain skills
        assert any("Python" in q.query for q in result.queries)
    
    def test_cse_operators_applied(self):
        """Should apply CSE operators for precision."""
        result = expand_queries(
            phase_1_output={"query_type": "company", "company_name": "OpenAI"},
            original_query="OpenAI",
        )
        # Should have exact phrase or intitle operators
        has_operators = any(
            "intitle:" in q.query or '\"' in q.query
            for q in result.queries
        )
        assert has_operators
    
    def test_domain_exclusions_applied(self):
        """Should exclude noisy domains."""
        result = expand_queries(
            phase_1_output={"query_type": "company", "company_name": "Meta"},
            original_query="Meta",
        )
        has_exclusions = any("-site:" in q.query for q in result.queries)
        assert has_exclusions
    
    def test_iteration_2_broadens_queries(self):
        """Iteration 2 should broaden previous queries."""
        original = ['"Stripe" intitle:engineering -site:pinterest.com']
        broadened = reformulate_queries(original, iteration=2)
        # Should remove quotes and operators
        assert '"' not in broadened[0]
        assert "intitle:" not in broadened[0]


class TestQueryReformulation:
    """Test iteration-specific reformulation."""
    
    def test_broaden_removes_operators(self):
        """BROADEN strategy should remove restrictive operators."""
        queries = ['intitle:"company" -site:facebook.com']
        result = reformulate_queries(queries, iteration=2)
        assert "intitle:" not in result[0]
        assert "-site:" not in result[0]
    
    def test_synonym_replaces_terms(self):
        """SYNONYMS strategy should use alternative terms."""
        queries = ["software engineer requirements"]
        result = reformulate_queries(queries, iteration=3)
        # Should have replacement terms
        assert "developer" in result[0] or "programmer" in result[0]
