"""
Experience Matcher Tool for the Fit Check Agent.

This module provides experience analysis functionality to evaluate how the
engineer's background and projects align with employer needs.
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
    Analyze how the engineer's experience and projects relate to the employer context.
    
    Use this tool to:
    - Match past projects and experience to company/job needs
    - Identify relevant accomplishments
    - Highlight transferable experience
    - Connect background to employer's domain
    
    Args:
        context: Information about the company, role, or industry to match against.
                Include details about what the employer does, their tech stack,
                or specific project types they work on.
    
    Returns:
        str: Detailed experience relevance analysis.
    
    Example:
        analyze_experience_relevance("Fintech startup building payment APIs with focus on reliability")
    """
    logger.info(f"Experience matcher called with context: {context[:100]}...")
    
    if not context or not context.strip():
        return "Error: Context cannot be empty. Please provide company/role context to analyze."
    
    context_lower = context.lower()
    
    # Get engineer's experience data
    experience_summary = get_experience_summary()
    projects = ENGINEER_PROFILE.get("notable_projects", [])
    strengths = ENGINEER_PROFILE.get("strengths", [])
    
    # Define relevance patterns
    domain_relevance: List[Dict] = []
    project_relevance: List[Dict] = []
    
    # Domain/industry matching
    domain_patterns = {
        "ai": {
            "keywords": ["ai", "artificial intelligence", "machine learning", "ml", "llm", "gpt", "chatbot", "nlp"],
            "relevance": "Strong alignment with AI/ML engineering experience including LangChain, LangGraph, RAG systems, and prompt engineering for production AI applications.",
        },
        "fintech": {
            "keywords": ["fintech", "finance", "payment", "banking", "financial"],
            "relevance": "Experience building reliable, secure backend systems with strong API design - critical for financial applications. Familiarity with data integrity and production-ready code.",
        },
        "saas": {
            "keywords": ["saas", "b2b", "platform", "subscription", "enterprise"],
            "relevance": "Full-stack experience building web platforms with authentication, real-time features, and scalable architecture suitable for SaaS products.",
        },
        "startup": {
            "keywords": ["startup", "early stage", "fast-paced", "scrappy"],
            "relevance": "Adaptable and fast-learning engineer comfortable wearing multiple hats. Experience shipping end-to-end features quickly with modern tech stack.",
        },
        "e-commerce": {
            "keywords": ["ecommerce", "e-commerce", "retail", "shopping", "marketplace"],
            "relevance": "Experience with web applications, database design, and user-facing features relevant to e-commerce platforms.",
        },
        "cloud": {
            "keywords": ["cloud", "aws", "infrastructure", "devops", "platform"],
            "relevance": "Hands-on experience with AWS, Docker, and cloud-native development. Built and deployed containerized microservices architecture.",
        },
        "developer_tools": {
            "keywords": ["developer tools", "devtools", "api", "sdk", "developer experience"],
            "relevance": "Passion for developer experience, strong API design skills, and experience building tools that other developers use.",
        },
        "healthcare": {
            "keywords": ["healthcare", "health", "medical", "biotech"],
            "relevance": "Experience with data-sensitive applications and reliable systems. Attention to detail and quality important in healthcare contexts.",
        },
    }
    
    for domain, info in domain_patterns.items():
        if any(kw in context_lower for kw in info["keywords"]):
            domain_relevance.append({
                "domain": domain.replace("_", " ").title(),
                "relevance": info["relevance"],
            })
    
    # Project relevance matching
    project_contexts = {
        "ai_agent": {
            "keywords": ["ai", "agent", "chatbot", "llm", "automation", "intelligent"],
            "project": "AI Portfolio Assistant",
            "relevance": "Built a production AI agent using LangGraph that performs multi-step research and analysis with real-time streaming - directly applicable to intelligent automation needs.",
        },
        "web_platform": {
            "keywords": ["web", "platform", "application", "frontend", "fullstack", "full-stack"],
            "project": "Full-Stack Web Platform",
            "relevance": "Developed a complete web application with authentication, real-time features, and cloud deployment demonstrating end-to-end engineering capability.",
        },
        "rag_system": {
            "keywords": ["rag", "retrieval", "document", "knowledge", "search", "embedding"],
            "project": "RAG Document System",
            "relevance": "Created an intelligent document retrieval and Q&A system showcasing expertise in modern AI/ML application architecture.",
        },
        "api_development": {
            "keywords": ["api", "backend", "microservice", "service", "rest"],
            "project": "Backend API Development",
            "relevance": "Experience designing and building robust APIs with FastAPI, proper error handling, and production-ready patterns.",
        },
        "real_time": {
            "keywords": ["real-time", "streaming", "websocket", "sse", "live"],
            "project": "Real-Time Streaming Features",
            "relevance": "Implemented SSE and WebSocket-based real-time features for live data streaming and interactive applications.",
        },
    }
    
    for ctx_key, info in project_contexts.items():
        if any(kw in context_lower for kw in info["keywords"]):
            project_relevance.append({
                "project": info["project"],
                "relevance": info["relevance"],
            })
    
    # Build the analysis response
    response_parts = []
    
    response_parts.append("## EXPERIENCE RELEVANCE ANALYSIS\n")
    
    # Domain alignment
    if domain_relevance:
        response_parts.append("### Domain Alignment\n")
        for item in domain_relevance:
            response_parts.append(f"**{item['domain']}:**")
            response_parts.append(f"{item['relevance']}\n")
    
    # Project relevance
    if project_relevance:
        response_parts.append("### Relevant Project Experience\n")
        for item in project_relevance:
            response_parts.append(f"**{item['project']}:**")
            response_parts.append(f"{item['relevance']}\n")
    
    # Key experience highlights (always include)
    response_parts.append("### Core Experience Highlights\n")
    response_parts.append(
        "- **Full-Stack Development**: End-to-end ownership from React/Next.js frontends "
        "to FastAPI/Python backends with database design\n"
    )
    response_parts.append(
        "- **AI/ML Engineering**: Production experience with LangChain, LangGraph, "
        "RAG systems, and integrating LLMs into applications\n"
    )
    response_parts.append(
        "- **Cloud Deployment**: Containerized applications with Docker, deployed "
        "on AWS with proper CI/CD pipelines\n"
    )
    response_parts.append(
        "- **Modern Tech Stack**: Proficient with current technologies "
        "(TypeScript, React, FastAPI, PostgreSQL) and learning new ones quickly\n"
    )
    
    # Strengths alignment
    response_parts.append("### Personal Strengths\n")
    for strength in strengths[:4]:  # Top 4 strengths
        response_parts.append(f"- {strength}")
    
    # Overall assessment
    relevance_score = len(domain_relevance) + len(project_relevance)
    
    response_parts.append("\n### Fit Assessment\n")
    if relevance_score >= 3:
        response_parts.append(
            "**STRONG FIT**: Multiple areas of direct experience alignment. "
            "The candidate's background maps well to this opportunity."
        )
    elif relevance_score >= 1:
        response_parts.append(
            "**GOOD FIT**: Relevant experience in key areas with strong "
            "foundational skills that transfer to this context."
        )
    else:
        response_parts.append(
            "**POTENTIAL FIT**: While direct domain overlap may be limited, "
            "the candidate's diverse technical background and fast learning "
            "ability enable quick adaptation to new domains."
        )
    
    result = "\n".join(response_parts)
    logger.info(f"Experience analysis complete: {relevance_score} relevance areas found")
    
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
