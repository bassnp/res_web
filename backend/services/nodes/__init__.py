"""
Node implementations for the Fit Check Pipeline.

This package contains the phase nodes that make up the
agentic workflow for employer fit analysis:

    1.  connecting          - Query classification and entity extraction
    2.  deep_research       - Web research and intelligence gathering
    2b. research_reranker   - Research quality validation and data pruning
    3.  skeptical_comparison - Critical gap analysis (ANTI-SYCOPHANCY)
    4.  skills_matching     - Skill-to-requirement mapping with quantification
    5b. confidence_reranker - LLM-as-a-Judge confidence calibration
    5.  generate_results    - Final response synthesis

Each node follows the pattern:
    async def {phase}_node(state, callback) -> Dict[str, Any]
"""

from services.nodes.connecting import connecting_node
from services.nodes.deep_research import deep_research_node
from services.nodes.research_reranker import research_reranker_node
from services.nodes.content_enrich import content_enrich_node
from services.nodes.skeptical_comparison import skeptical_comparison_node
from services.nodes.skills_matching import skills_matching_node
from services.nodes.confidence_reranker import confidence_reranker_node
from services.nodes.generate_results import generate_results_node

__all__ = [
    "connecting_node",
    "deep_research_node",
    "research_reranker_node",
    "content_enrich_node",
    "skeptical_comparison_node",
    "skills_matching_node",
    "confidence_reranker_node",
    "generate_results_node",
]
