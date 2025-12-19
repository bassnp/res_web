"""
Performance Benchmarks for Upgraded Pipeline.
"""

import pytest
import time
import asyncio
from models.fit_check import DocumentScore

class TestPerformanceBenchmarks:
    """Performance validation tests."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_parallel_scoring_performance(self):
        """Parallel scoring should complete in < 5s for 10 docs."""
        from services.utils.parallel_scorer import score_documents_parallel
        
        docs = [
            {"id": str(i), "url": f"https://site{i}.com", "title": f"Doc {i}", "snippet": "Content"}
            for i in range(10)
        ]
        
        start = time.time()
        results = await score_documents_parallel(docs, "test query")
        elapsed = time.time() - start
        
        assert elapsed < 5.0, f"Scoring took {elapsed:.2f}s, expected < 5s"
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_enrichment_performance(self):
        """Content enrichment should complete in < 10s for 5 sources."""
        from services.nodes.content_enrich import content_enrich_node
        from services.pipeline_state import create_initial_state
        
        state = create_initial_state(query="Test")
        state["top_sources"] = [
            DocumentScore(
                url=f"https://httpbin.org/html", 
                title=f"Source {i}", 
                snippet="Test",
                relevance_score=0.8,
                quality_score=0.8,
                usefulness_score=0.8,
                final_score=0.8,
                reasoning="Test"
            )
            for i in range(5)
        ]
        
        start = time.time()
        result = await content_enrich_node(state, callback=None)
        elapsed = time.time() - start
        
        assert elapsed < 10.0, f"Enrichment took {elapsed:.2f}s, expected < 10s"
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_full_iteration_loop_performance(self):
        """Full 3-iteration loop should complete in < 30s."""
        from services.fit_check_agent import FitCheckAgent
        
        agent = FitCheckAgent()
        
        start = time.time()
        result = await agent.analyze("Test Company Performance")
        elapsed = time.time() - start
        
        assert elapsed < 30.0, f"Full pipeline took {elapsed:.2f}s, expected < 30s"
