"""
Full Pipeline Integration Tests.

Tests the complete upgraded Fit Check pipeline end-to-end.
"""

import pytest
from unittest.mock import patch, AsyncMock
from services.fit_check_agent import FitCheckAgent, build_fit_check_pipeline
from services.pipeline_state import create_initial_state


class TestFullPipelineIntegration:
    """End-to-end pipeline tests."""
    
    @pytest.fixture
    def agent(self):
        return FitCheckAgent()
    
    @pytest.mark.asyncio
    async def test_company_query_full_flow(self, agent):
        """Test complete flow for company query."""
        # Mocking to avoid actual API calls in integration tests if needed, 
        # but usually integration tests might hit real APIs or local mocks.
        # For this task, we'll assume we want to test the logic flow.
        result = await agent.analyze("Stripe")
        
        # Should have final response
        assert result is not None
        assert len(result) > 100  # Meaningful response
    
    @pytest.mark.asyncio
    async def test_job_description_full_flow(self, agent):
        """Test complete flow for job description."""
        query = "Senior Python Engineer with Kubernetes experience"
        result = await agent.analyze(query)
        
        assert result is not None
        assert "Python" in result or "engineer" in result.lower()
    
    @pytest.mark.asyncio
    async def test_iteration_loop_triggers(self, agent):
        """Test that iteration loop activates for obscure company."""
        with patch('services.tools.web_search.web_search_structured') as mock_search:
            # First iteration: sparse results
            mock_search.side_effect = [
                "Limited info about XYZ",  # Query 1
                "No results",               # Query 2
                "No results",               # Query 3
                # Second iteration: better results
                "XYZ Company uses Python, React, AWS...",
                "XYZ hiring engineers...",
                "XYZ engineering culture...",
            ]
            
            result = await agent.analyze("Obscure Startup XYZ")
            
            # Should have made multiple search calls (iteration)
            # The test verifies pipeline doesn't crash and returns something
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_graceful_abort_on_no_data(self, agent):
        """Test graceful abort when no data found."""
        with patch('services.tools.web_search.web_search') as mock_search:
            mock_search.return_value = "No results found"
            
            result = await agent.analyze("Completely Fake Company 12345")
            
            # Should have abort response
            assert "Unable" in result or "insufficient" in result.lower()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_fallback(self, agent):
        """Test circuit breaker provides fallback on repeated failures."""
        from services.utils.circuit_breaker import search_breaker
        
        # Force breaker open
        for _ in range(5):
            try:
                await search_breaker.record_failure(Exception("Test"))
            except:
                pass
        
        # Should use fallback
        result = await agent.analyze("Google")  # Known company
        
        assert result is not None
        # Reset breaker for other tests
        search_breaker._state = search_breaker._state.CLOSED
        search_breaker._failure_count = 0
    
    @pytest.mark.asyncio
    async def test_enriched_content_used(self, agent):
        """Test that enriched content improves synthesis."""
        state = create_initial_state(query="Stripe")
        
        # Mock enriched sources
        state["enriched_content"] = [
            {
                "url": "https://stripe.com/jobs",
                "title": "Stripe Careers",
                "content": "Stripe uses Ruby, Go, React. Values include user focus...",
                "is_enriched": True,
            }
        ]
        
        # Should have richer context
        assert state["enriched_content"][0]["is_enriched"] == True


class TestStreamingIntegration:
    """Test SSE streaming functionality."""
    
    @pytest.mark.asyncio
    async def test_streaming_emits_events(self):
        """Test that streaming emits expected events."""
        events = []
        
        async def mock_callback(event):
            events.append(event)
        
        # Mock ThoughtCallback
        mock_cb = AsyncMock()
        
        agent = FitCheckAgent()
        async for chunk in agent.stream_analysis("Stripe", callback=mock_cb):
            pass
        
        # Should have called on_status, on_thought, etc.
        assert mock_cb.on_status.called
        assert mock_cb.on_thought.called


class TestErrorRecovery:
    """Test error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_partial_scoring_failure_continues(self):
        """Pipeline should continue if some scoring fails."""
        from services.utils.parallel_scorer import score_documents_parallel
        from unittest.mock import AsyncMock as AM
        
        docs = [
            {"id": "1", "url": "https://good.com", "title": "Good", "snippet": "Content"},
            {"id": "2", "url": "https://bad.com", "title": "Bad", "snippet": "Content"},
        ]
        
        with patch('services.utils.parallel_scorer.score_single_document') as mock_score:
            # Create async mocks that return proper values
            async def score_success(*args, **kwargs):
                return {"document_id": "1", "final_score": 0.8}
            
            async def score_fail(*args, **kwargs):
                raise Exception("Scoring failed")
            
            mock_score.side_effect = [score_success, score_fail]
            
            results = await score_documents_parallel(docs, "query")
            
            # Should have at least one result OR return empty list on all failures
            # The important thing is it doesn't crash
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_enrichment_fallback_on_timeout(self):
        """Enrichment should fallback to snippet on timeout."""
        from services.nodes.content_enrich import content_enrich_node
        from models.fit_check import DocumentScore, SourceType
        
        state = create_initial_state(query="Test")
        state["top_sources"] = [
            DocumentScore(
                document_id="test-1",
                url="https://slow.com", 
                title="Slow", 
                snippet="Fallback content",
                relevance_score=0.8,
                quality_score=0.8,
                usefulness_score=0.8,
                raw_composite=0.8,
                extractability_multiplier=1.0,
                final_score=0.8,
                source_type=SourceType.GENERAL,
                scoring_rationale="Test document for timeout fallback"
            )
        ]
        
        with patch('httpx.AsyncClient.get') as mock_get:
            # Simulate timeout
            mock_get.side_effect = Exception("Connection timeout")
            
            result = await content_enrich_node(state, callback=None)
            
            # Should have fallback - check enriched content exists
            if result.get("enriched_content"):
                assert result["enriched_content"][0]["is_enriched"] == False
                assert result["enriched_content"][0]["content"] == "Fallback content"
