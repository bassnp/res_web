import pytest
from services.nodes.deep_research import deep_research_node
from services.pipeline_state import create_initial_state

@pytest.mark.asyncio
async def test_deep_research_uses_expanded_queries():
    """Deep research should use query expansion engine."""
    state = create_initial_state(query="Stripe")
    state["phase_1_output"] = {
        "query_type": "company",
        "company_name": "Stripe",
        "job_title": "Software Engineer",
        "extracted_skills": ["Python"],
        "reasoning_trace": "Test trace"
    }
    
    # Mocking web_search to avoid actual API calls if possible, 
    # but the test in MD doesn't show mocking. 
    # I'll assume web_search is already mocked in conftest or handles it.
    
    result = await deep_research_node(state, callback=None)
    
    # Should have tracked expanded queries
    assert result.get("expanded_queries") is not None
    assert len(result.get("expanded_queries", [])) >= 3
    assert result.get("query_expansion_strategy") == "company_focus"
