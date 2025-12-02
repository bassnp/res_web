"""
Skill Matcher Tool for the Fit Check Agent.

This module provides skill analysis functionality to match the engineer's
skills against job requirements and identify alignment areas.
"""

import logging
from typing import List, Dict, Any

from langchain_core.tools import tool

# Import engineer profile for skill data
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.engineer_profile import get_skills_by_category, get_skills_list

logger = logging.getLogger(__name__)


# =============================================================================
# Skill Matcher Tool
# =============================================================================

@tool
def analyze_skill_match(requirements: str) -> str:
    """
    Analyze how the engineer's skills match against job/company requirements.
    
    Use this tool to:
    - Compare candidate skills against extracted requirements
    - Identify strong matches and alignment areas
    - Highlight transferable skills
    - Note any skill gaps (framed constructively)
    
    Args:
        requirements: Description of required skills, technologies, or qualifications
                     extracted from job description or company research.
    
    Returns:
        str: Detailed skill match analysis with strengths and gaps.
    
    Example:
        analyze_skill_match("Python, React, AWS, machine learning, agile methodology")
    """
    logger.info(f"Skill matcher called with requirements: {requirements[:100]}...")
    
    if not requirements or not requirements.strip():
        return "Error: Requirements cannot be empty. Please provide job requirements to analyze."
    
    requirements_lower = requirements.lower()
    
    # Get engineer's skills
    skills_by_category = get_skills_by_category()
    all_skills = get_skills_list()
    
    # Analyze matches
    matched_skills: List[Dict[str, Any]] = []
    partial_matches: List[Dict[str, Any]] = []
    
    # Skill mapping for flexible matching
    skill_aliases = {
        "python": ["python", "py", "django", "flask", "fastapi"],
        "javascript": ["javascript", "js", "node", "nodejs", "express"],
        "typescript": ["typescript", "ts"],
        "react": ["react", "reactjs", "react.js", "next.js", "nextjs"],
        "sql": ["sql", "postgresql", "postgres", "mysql", "database"],
        "docker": ["docker", "containers", "containerization", "kubernetes", "k8s"],
        "aws": ["aws", "amazon web services", "cloud", "ec2", "s3", "lambda"],
        "git": ["git", "github", "gitlab", "version control"],
        "ai": ["ai", "artificial intelligence", "machine learning", "ml", "llm", "gpt", "gemini"],
        "langchain": ["langchain", "langgraph", "rag", "agents", "llm framework"],
        "api": ["api", "rest", "restful", "graphql", "fastapi", "express"],
        "frontend": ["frontend", "front-end", "ui", "ux", "css", "tailwind"],
        "backend": ["backend", "back-end", "server", "microservices"],
        "fullstack": ["fullstack", "full-stack", "full stack"],
    }
    
    # Check each skill category
    for category, skills in skills_by_category.items():
        for skill in skills:
            skill_lower = skill.lower()
            
            # Direct match
            if skill_lower in requirements_lower:
                matched_skills.append({
                    "skill": skill,
                    "category": category.replace("_", " ").title(),
                    "match_type": "direct",
                })
                continue
            
            # Check aliases for this skill
            for base_skill, aliases in skill_aliases.items():
                if skill_lower in [a.lower() for a in aliases]:
                    if any(alias in requirements_lower for alias in aliases):
                        matched_skills.append({
                            "skill": skill,
                            "category": category.replace("_", " ").title(),
                            "match_type": "related",
                        })
                        break
    
    # Look for requirements we might partially match
    common_requirements = [
        ("agile", "Experience with agile development methodologies through project work"),
        ("scrum", "Familiar with scrum/agile practices from team projects"),
        ("ci/cd", "Experience with CI/CD pipelines and automated deployments"),
        ("testing", "Experience writing tests and following TDD practices"),
        ("communication", "Strong communication skills demonstrated through collaboration"),
        ("problem solving", "Strong analytical and problem-solving abilities"),
        ("team", "Collaborative team player with experience in group projects"),
    ]
    
    for req_keyword, description in common_requirements:
        if req_keyword in requirements_lower:
            partial_matches.append({
                "requirement": req_keyword,
                "coverage": description,
            })
    
    # Build the analysis response
    response_parts = []
    
    # Strong matches
    if matched_skills:
        response_parts.append("## STRONG SKILL MATCHES\n")
        
        # Group by category
        by_category: Dict[str, List[str]] = {}
        for match in matched_skills:
            cat = match["category"]
            if cat not in by_category:
                by_category[cat] = []
            match_indicator = "✓" if match["match_type"] == "direct" else "≈"
            by_category[cat].append(f"{match_indicator} {match['skill']}")
        
        for category, skills in by_category.items():
            response_parts.append(f"**{category}:**")
            response_parts.append("  " + ", ".join(skills))
        
        response_parts.append(f"\nTotal matched skills: {len(matched_skills)}")
    else:
        response_parts.append("## SKILL ANALYSIS\n")
        response_parts.append("No direct skill matches found in requirements.")
    
    # Additional coverage
    if partial_matches:
        response_parts.append("\n## ADDITIONAL QUALIFICATIONS MET\n")
        for match in partial_matches:
            response_parts.append(f"- **{match['requirement'].title()}**: {match['coverage']}")
    
    # Highlight key strengths regardless of matches
    response_parts.append("\n## KEY TECHNICAL STRENGTHS\n")
    response_parts.append("The candidate brings expertise in:")
    response_parts.append("- **Full-Stack Development**: React/Next.js frontend + FastAPI/Python backend")
    response_parts.append("- **AI/ML Integration**: LangChain, LangGraph, RAG systems, prompt engineering")
    response_parts.append("- **Cloud & DevOps**: Docker, AWS, PostgreSQL, CI/CD pipelines")
    response_parts.append("- **Modern Development**: TypeScript, REST APIs, real-time features (SSE/WebSockets)")
    
    # Determine match quality
    match_count = len(matched_skills)
    if match_count >= 5:
        response_parts.append(f"\n**Overall Match Quality: STRONG** ({match_count} skill alignments)")
    elif match_count >= 3:
        response_parts.append(f"\n**Overall Match Quality: GOOD** ({match_count} skill alignments)")
    elif match_count >= 1:
        response_parts.append(f"\n**Overall Match Quality: MODERATE** ({match_count} skill alignments)")
    else:
        response_parts.append("\n**Note:** While direct skill matches are limited, the candidate's strong foundation enables quick adaptation to new technologies.")
    
    result = "\n".join(response_parts)
    logger.info(f"Skill analysis complete: {match_count} matches found")
    
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
