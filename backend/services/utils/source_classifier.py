"""
Source Type Classifier for Extractability Scoring.

Classifies URLs into source types and applies extractability multipliers.
"""

from typing import Tuple
from urllib.parse import urlparse
from models.fit_check import SourceType

# Domain sets for classification
VIDEO_DOMAINS = {"youtube.com", "vimeo.com", "dailymotion.com", "twitch.tv"}
SOCIAL_MEDIA_DOMAINS = {"twitter.com", "x.com", "facebook.com", "instagram.com", 
                        "linkedin.com", "tiktok.com", "pinterest.com", "reddit.com"}
WIKI_DOMAINS = {"wikipedia.org", "wikimedia.org", "fandom.com"}
ACADEMIC_DOMAINS = {"arxiv.org", "scholar.google.com", "researchgate.net", 
                    "academia.edu", "sciencedirect.com", "ieee.org"}
NEWS_DOMAINS = {"nytimes.com", "wsj.com", "bloomberg.com", "techcrunch.com",
                "theverge.com", "wired.com", "arstechnica.com", "bbc.com"}
FORUM_DOMAINS = {"stackoverflow.com", "stackexchange.com", "quora.com",
                 "news.ycombinator.com", "dev.to"}

# Extractability multipliers by source type
EXTRACTABILITY_MULTIPLIERS = {
    SourceType.VIDEO: 0.20,        # Cannot extract video content
    SourceType.SOCIAL_MEDIA: 0.50, # Limited text, noisy
    SourceType.WIKI: 1.10,         # Excellent extractability
    SourceType.ACADEMIC: 1.08,     # High-quality content
    SourceType.FORUM: 1.00,        # Good technical content
    SourceType.NEWS: 0.85,         # Paywalls, bias concerns
    SourceType.GENERAL: 1.00,      # Baseline
}


def classify_source(url: str) -> Tuple[SourceType, float]:
    """
    Classify a URL into a source type and return extractability multiplier.
    
    Args:
        url: The source URL to classify.
    
    Returns:
        Tuple of (SourceType, extractability_multiplier).
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception:
        return SourceType.GENERAL, 1.0
    
    # Check each domain set
    for video_domain in VIDEO_DOMAINS:
        if video_domain in domain:
            return SourceType.VIDEO, EXTRACTABILITY_MULTIPLIERS[SourceType.VIDEO]
    
    for social_domain in SOCIAL_MEDIA_DOMAINS:
        if social_domain in domain:
            return SourceType.SOCIAL_MEDIA, EXTRACTABILITY_MULTIPLIERS[SourceType.SOCIAL_MEDIA]
    
    for wiki_domain in WIKI_DOMAINS:
        if wiki_domain in domain:
            return SourceType.WIKI, EXTRACTABILITY_MULTIPLIERS[SourceType.WIKI]
    
    for academic_domain in ACADEMIC_DOMAINS:
        if academic_domain in domain:
            return SourceType.ACADEMIC, EXTRACTABILITY_MULTIPLIERS[SourceType.ACADEMIC]
    
    for news_domain in NEWS_DOMAINS:
        if news_domain in domain:
            return SourceType.NEWS, EXTRACTABILITY_MULTIPLIERS[SourceType.NEWS]
    
    for forum_domain in FORUM_DOMAINS:
        if forum_domain in domain:
            return SourceType.FORUM, EXTRACTABILITY_MULTIPLIERS[SourceType.FORUM]
    
    return SourceType.GENERAL, EXTRACTABILITY_MULTIPLIERS[SourceType.GENERAL]


def get_extractability_multiplier(source_type: SourceType) -> float:
    """Get the extractability multiplier for a source type."""
    return EXTRACTABILITY_MULTIPLIERS.get(source_type, 1.0)
