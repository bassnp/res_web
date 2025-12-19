import pytest
from services.utils.source_classifier import classify_source, SourceType

class TestSourceClassifier:
    """Test source type classification."""
    
    def test_video_classification(self):
        source_type, multiplier = classify_source("https://youtube.com/watch?v=123")
        assert source_type == SourceType.VIDEO
        assert multiplier == 0.20
    
    def test_social_media_classification(self):
        source_type, _ = classify_source("https://twitter.com/company/status/123")
        assert source_type == SourceType.SOCIAL_MEDIA
    
    def test_wiki_classification(self):
        source_type, multiplier = classify_source("https://en.wikipedia.org/wiki/Company")
        assert source_type == SourceType.WIKI
        assert multiplier > 1.0  # Bonus multiplier
    
    def test_academic_classification(self):
        source_type, _ = classify_source("https://arxiv.org/abs/2301.00000")
        assert source_type == SourceType.ACADEMIC
    
    def test_general_classification(self):
        source_type, multiplier = classify_source("https://company.com/careers")
        assert source_type == SourceType.GENERAL
        assert multiplier == 1.0
    
    def test_www_prefix_handling(self):
        source_type, _ = classify_source("https://www.youtube.com/watch")
        assert source_type == SourceType.VIDEO


class TestAdaptiveThreshold:
    """Test adaptive threshold calculation."""
    
    def test_low_results_lenient_threshold(self):
        from services.utils.parallel_scorer import calculate_adaptive_threshold
        threshold = calculate_adaptive_threshold(total_results=5, social_media_ratio=0.2)
        assert threshold <= 0.50
    
    def test_high_results_strict_threshold(self):
        from services.utils.parallel_scorer import calculate_adaptive_threshold
        threshold = calculate_adaptive_threshold(total_results=40, social_media_ratio=0.1)
        assert threshold >= 0.55
    
    def test_high_social_ratio_lenient(self):
        from services.utils.parallel_scorer import calculate_adaptive_threshold
        threshold = calculate_adaptive_threshold(total_results=20, social_media_ratio=0.6)
        assert threshold <= 0.50
