"""
Skill Matcher Tool for the Fit Check Agent.

This module provides the engineer's skill profile for AI-driven semantic matching.

Design Philosophy:
    The tool provides RAW DATA (engineer skills) to the AI synthesis node.
    Semantic interpretation and matching is delegated to the LLM in Phase 4,
    NOT performed via brute-force alias dictionaries.
    
    This ensures:
    - Contextual understanding of technology relationships
    - Recognition of semantic equivalence (e.g., "AI agents" ≈ "agentic systems")
    - Adaptation to novel terminology without code changes
    - Robust matching for edge cases like D5 (LangGraph AI startup)
"""

import logging
from typing import List, Dict, Any

from langchain_core.tools import tool

# Import engineer profile for skill data
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.engineer_profile import get_skills_by_category, get_skills_list, ENGINEER_PROFILE

logger = logging.getLogger(__name__)


# =============================================================================
# Skill Matcher Tool
# =============================================================================

@tool
def analyze_skill_match(requirements: str) -> str:
    """
    Provide the engineer's skill profile for semantic matching against requirements.
    
    This tool returns the candidate's COMPLETE skill inventory organized by category,
    along with the requirements context. The AI synthesis node performs semantic
    matching - this tool does NOT hardcode alias relationships.
    
    Use this tool to:
    - Retrieve the candidate's full technical skill profile
    - Provide structured data for AI-driven skill-to-requirement mapping
    - Enable semantic matching (not just keyword matching)
    
    Args:
        requirements: Description of required skills, technologies, or qualifications
                     extracted from job description or company research.
    
    Returns:
        str: Structured skill profile with requirements context for AI synthesis.
    
    Example:
        analyze_skill_match("AI agents, LangGraph, Python, enterprise automation")
    """
    logger.info(f"Skill matcher called with requirements: {requirements[:100]}...")
    
    if not requirements or not requirements.strip():
        return "Error: Requirements cannot be empty. Please provide job requirements to analyze."
    
    # Get engineer's complete skill profile
    skills_by_category = get_skills_by_category()
    
    # Build structured output for AI synthesis
    response_parts = []
    
    # Section 1: Requirements Context (for AI to match against)
    response_parts.append("## REQUIREMENTS TO MATCH AGAINST")
    response_parts.append(f"{requirements}")
    response_parts.append("")
    
    # Section 2: Complete Candidate Skill Profile
    response_parts.append("## CANDIDATE SKILL PROFILE")
    response_parts.append("")
    
    for category, skills in skills_by_category.items():
        category_name = category.replace("_", " ").title()
        skills_str = ", ".join(skills)
        response_parts.append(f"**{category_name}:** {skills_str}")
    
    response_parts.append("")
    
    # Section 3: Notable Projects (for experience context)
    response_parts.append("## RELEVANT PROJECT EXPERIENCE")
    projects = ENGINEER_PROFILE.get("notable_projects", [])
    for project in projects:
        tech_str = ", ".join(project.get("tech", []))
        response_parts.append(f"- **{project['name']}**: {project['description']}")
        response_parts.append(f"  Technologies: {tech_str}")
    
    response_parts.append("")
    
    # Section 4: Candidate Strengths
    response_parts.append("## CANDIDATE STRENGTHS")
    strengths = ENGINEER_PROFILE.get("strengths", [])
    for strength in strengths:
        response_parts.append(f"- {strength}")
    
    response_parts.append("")
    
    # Section 5: Guidance for AI Synthesis
    response_parts.append("## MATCHING INSTRUCTIONS FOR AI SYNTHESIS")
    response_parts.append("Perform SEMANTIC matching between requirements and candidate skills:")
    response_parts.append("- Consider technology relationships (e.g., LangGraph implies Python, AI agents)")
    response_parts.append("- Recognize framework ecosystems (e.g., Next.js implies React, Vercel)")
    response_parts.append("- Identify transferable skills across domains")
    response_parts.append("- Note BOTH direct matches AND semantic alignments")
    response_parts.append("- Flag genuine gaps where no reasonable skill transfer exists")
    
    result = "\n".join(response_parts)
    logger.info(f"Skill profile returned for AI synthesis")
    
    return result


# =============================================================================
# Utility Functions
# =============================================================================

def get_skill_summary() -> str:
    """
    Get a quick summary of the engineer's skills.
    
    Returns:
        str: Formatted skill summary.
    """
    skills_by_category = get_skills_by_category()
    
    summary_parts = ["Engineer Skill Summary:"]
    for category, skills in skills_by_category.items():
        category_name = category.replace("_", " ").title()
        summary_parts.append(f"  {category_name}: {', '.join(skills)}")
    
    return "\n".join(summary_parts)
