"""
Experience Matcher Tool for the Fit Check Agent.

This module provides the engineer's experience profile for AI-driven relevance analysis.

Design Philosophy:
    The tool provides RAW DATA (engineer experience, projects, strengths) to the 
    AI synthesis node. Semantic interpretation and domain matching is delegated 
    to the LLM in Phase 4, NOT performed via hardcoded domain pattern dictionaries.
    
    This ensures:
    - Contextual understanding of experience relevance
    - Recognition of transferable skills across domains
    - Adaptation to novel industries without code changes
    - Nuanced assessment for edge cases
"""

import logging
from typing import List, Dict

from langchain_core.tools import tool

# Import engineer profile for experience data
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.engineer_profile import ENGINEER_PROFILE, get_experience_summary

logger = logging.getLogger(__name__)


# =============================================================================
# Experience Matcher Tool
# =============================================================================

@tool
def analyze_experience_relevance(context: str) -> str:
    """
    Provide the engineer's experience profile for semantic relevance analysis.
    
    This tool returns the candidate's COMPLETE experience inventory including
    projects, accomplishments, and strengths. The AI synthesis node performs 
    semantic matching - this tool does NOT hardcode domain pattern dictionaries.
    
    Use this tool to:
    - Retrieve the candidate's full experience profile
    - Provide structured data for AI-driven relevance assessment
    - Enable semantic matching of experience to employer context
    
    Args:
        context: Information about the company, role, or industry to match against.
                Include details about what the employer does, their tech stack,
                or specific project types they work on.
    
    Returns:
        str: Structured experience profile with context for AI synthesis.
    
    Example:
        analyze_experience_relevance("AI startup building enterprise automation agents")
    """
    logger.info(f"Experience matcher called with context: {context[:100]}...")
    
    if not context or not context.strip():
        return "Error: Context cannot be empty. Please provide company/role context to analyze."
    
    # Get engineer's experience data
    experience_summary = get_experience_summary()
    projects = ENGINEER_PROFILE.get("notable_projects", [])
    strengths = ENGINEER_PROFILE.get("strengths", [])
    career_interests = ENGINEER_PROFILE.get("career_interests", [])
    education = ENGINEER_PROFILE.get("education", "")
    
    # Build structured output for AI synthesis
    response_parts = []
    
    # Section 1: Employer Context (for AI to match against)
    response_parts.append("## EMPLOYER CONTEXT TO MATCH AGAINST")
    response_parts.append(f"{context}")
    response_parts.append("")
    
    # Section 2: Experience Summary
    response_parts.append("## CANDIDATE EXPERIENCE SUMMARY")
    response_parts.append(experience_summary.strip())
    response_parts.append("")
    
    # Section 3: Education
    response_parts.append("## EDUCATION")
    response_parts.append(f"{education}")
    response_parts.append("")
    
    # Section 4: Notable Projects (detailed for context)
    response_parts.append("## NOTABLE PROJECTS")
    for project in projects:
        tech_str = ", ".join(project.get("tech", []))
        response_parts.append(f"### {project['name']}")
        response_parts.append(f"**Description:** {project['description']}")
        response_parts.append(f"**Technologies:** {tech_str}")
        response_parts.append("")
    
    # Section 5: Personal Strengths
    response_parts.append("## PERSONAL STRENGTHS")
    for strength in strengths:
        response_parts.append(f"- {strength}")
    response_parts.append("")
    
    # Section 6: Career Interests
    response_parts.append("## CAREER INTERESTS")
    response_parts.append(", ".join(career_interests))
    response_parts.append("")
    
    # Section 7: Guidance for AI Synthesis
    response_parts.append("## MATCHING INSTRUCTIONS FOR AI SYNTHESIS")
    response_parts.append("Perform SEMANTIC experience-to-context matching:")
    response_parts.append("- Identify projects directly relevant to the employer's domain")
    response_parts.append("- Recognize transferable experience across industries")
    response_parts.append("- Note alignment between candidate interests and employer focus")
    response_parts.append("- Assess how project complexity relates to role requirements")
    response_parts.append("- Flag genuine experience gaps where no transfer applies")
    
    result = "\n".join(response_parts)
    logger.info(f"Experience profile returned for AI synthesis")
    
    return result


# =============================================================================
# Utility Functions
# =============================================================================

def get_project_highlights() -> str:
    """
    Get a summary of notable projects.
    
    Returns:
        str: Formatted project highlights.
    """
    projects = ENGINEER_PROFILE.get("notable_projects", [])
    
    highlights = ["Notable Projects:"]
    for project in projects:
        tech_str = ", ".join(project.get("tech", []))
        highlights.append(f"  - {project['name']}: {project['description']}")
        highlights.append(f"    Tech: {tech_str}")
    
    return "\n".join(highlights)
