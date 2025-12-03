"""
Prompts module for the Portfolio Backend API.

Contains XML-based system prompts for each phase of the AI pipeline.
The prompts are loaded by the prompt_loader service and formatted
with engineer profile data before being passed to the LLM.

Prompt Files:
    - phase_1_connecting.xml          - Query classification
    - phase_2_deep_research.xml       - Web research
    - phase_2b_research_reranker.xml  - Research quality validation
    - phase_3_skeptical_comparison.xml - Critical gap analysis
    - phase_4_skills_matching.xml     - Skill-to-requirement mapping
    - phase_5b_confidence_reranker.xml - LLM-as-Judge calibration
    - phase_5_generate_results.xml    - Response synthesis
    
Concise Variants (for reduced token usage):
    - *_concise.xml versions of each phase prompt
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

__all__ = ["PROMPTS_DIR"]