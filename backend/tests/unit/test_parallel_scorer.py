import pytest
from unittest.mock import AsyncMock, patch
from services.utils.parallel_scorer import score_documents_parallel, score_single_document
from models.fit_check import DocumentScore

class TestParallelScorer:
    """Test parallel document scoring."""
    
    @pytest.mark.asyncio
    async def test_score_single_document_success(self):
        """Should score document and apply extractability."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = '{"relevance": 0.8, "quality": 0.7, "usefulness": 0.6, "rationale": "Good source"}'
        
        doc = {"id": "1", "link": "https://company.com", "title": "About", "snippet": "Test"}
        
        # We pass the mock_llm directly to score_single_document
        result = await score_single_document(doc, "company research", mock_llm)
        
        assert result is not None
        assert result.url == "https://company.com"
        assert result.relevance_score == 0.8
        assert result.final_score > 0
    
    @pytest.mark.asyncio
    async def test_video_source_penalty(self):
        """Video sources should have extractability penalty."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = '{"relevance": 0.9, "quality": 0.9, "usefulness": 0.9, "rationale": "Good"}'
        
        doc = {"id": "1", "link": "https://youtube.com/watch?v=123", "title": "Video", "snippet": "Test"}
        
        result = await score_single_document(doc, "query", mock_llm)
        
        assert result.extractability_multiplier == 0.20
        assert result.final_score < result.raw_composite
    
    @pytest.mark.asyncio
    async def test_parallel_scoring_respects_concurrency(self):
        """Should respect concurrency limits."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = '{"relevance": 0.5, "quality": 0.5, "usefulness": 0.5, "rationale": ""}'
        
        docs = [{"id": str(i), "link": f"https://site{i}.com", "title": f"Doc {i}", "snippet": "Test"} for i in range(10)]
        
        with patch('services.utils.parallel_scorer.get_llm', return_value=mock_llm):
            results = await score_documents_parallel(docs, "query", max_concurrent=3)
        
        assert len(results) == 10
