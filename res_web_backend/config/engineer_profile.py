"""
Engineer Profile Configuration for the Fit Check Agent.

This module contains the engineer's skills, experience, and background
information used by the AI agent to match against employer requirements.

Edit this file to customize the engineer's information for personalized
fit analysis responses.
"""

from typing import Dict, List, Any


# =============================================================================
# Engineer Profile Data
# =============================================================================

ENGINEER_PROFILE: Dict[str, Any] = {
    "name": "Software Engineer",
    
    "education": "B.S. in Computer Science",
    
    "skills": {
        "languages": [
            "Python",
            "JavaScript",
            "TypeScript",
            "SQL",
            "HTML/CSS",
        ],
        "frameworks": [
            "React",
            "Next.js",
            "FastAPI",
            "Node.js",
            "TailwindCSS",
        ],
        "cloud_devops": [
            "Docker",
            "AWS",
            "PostgreSQL",
            "Redis",
            "CI/CD",
        ],
        "ai_ml": [
            "LangChain",
            "LangGraph",
            "OpenAI API",
            "Google Gemini",
            "RAG Systems",
            "Prompt Engineering",
        ],
        "tools": [
            "Git",
            "VS Code",
            "Linux",
            "REST APIs",
            "GraphQL",
        ],
    },
    
    "experience_summary": """
    Full-stack software engineer with experience building modern web applications
    and AI-powered systems. Proficient in developing scalable backend services,
    responsive frontend interfaces, and integrating cutting-edge AI/ML capabilities.
    
    Key accomplishments:
    - Built production AI agents using LangChain and LangGraph
    - Developed full-stack applications with React/Next.js and FastAPI
    - Implemented real-time streaming features using SSE and WebSockets
    - Designed and deployed containerized microservices architecture
    - Created RAG systems for intelligent document processing
    """,
    
    "notable_projects": [
        {
            "name": "AI Portfolio Assistant",
            "description": "Real-time AI agent that analyzes employer fit using web research and skill matching",
            "tech": ["Python", "FastAPI", "LangGraph", "React", "SSE Streaming"],
        },
        {
            "name": "Full-Stack Web Platform",
            "description": "Production web application with authentication, real-time features, and cloud deployment",
            "tech": ["Next.js", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        },
        {
            "name": "RAG Document System",
            "description": "Intelligent document retrieval and question-answering system",
            "tech": ["LangChain", "Vector Databases", "OpenAI", "Python"],
        },
    ],
    
    "strengths": [
        "Fast learner who quickly adapts to new technologies",
        "Strong problem-solving and debugging skills",
        "Experience with end-to-end software development lifecycle",
        "Excellent communication and collaboration abilities",
        "Passionate about building AI-powered applications",
    ],
    
    "career_interests": [
        "Full-Stack Development",
        "AI/ML Engineering",
        "Backend Systems",
        "Cloud Architecture",
        "Developer Tools",
    ],
}


# =============================================================================
# Profile Formatting Functions
# =============================================================================

def get_formatted_profile() -> str:
    """
    Format engineer profile for system prompt injection.
    
    Returns:
        str: Formatted string representation of the engineer profile
             suitable for inclusion in AI system prompts.
    """
    profile = ENGINEER_PROFILE
    
    # Format skills by category
    skills_formatted = []
    for category, skill_list in profile["skills"].items():
        category_name = category.replace("_", " ").title()
        skills_str = ", ".join(skill_list)
        skills_formatted.append(f"  {category_name}: {skills_str}")
    
    # Format projects
    projects_formatted = []
    for project in profile["notable_projects"]:
        tech_str = ", ".join(project["tech"])
        projects_formatted.append(
            f"  - {project['name']}: {project['description']} "
            f"(Tech: {tech_str})"
        )
    
    # Build the formatted profile string
    return f"""
Name: {profile['name']}
Education: {profile['education']}

Technical Skills:
{chr(10).join(skills_formatted)}

Experience Summary:
{profile['experience_summary'].strip()}

Notable Projects:
{chr(10).join(projects_formatted)}

Key Strengths:
{chr(10).join(f'  - {s}' for s in profile['strengths'])}

Career Interests:
{chr(10).join(f'  - {i}' for i in profile['career_interests'])}
"""


def get_skills_list() -> List[str]:
    """
    Get a flat list of all skills.
    
    Returns:
        List[str]: All skills across all categories.
    """
    skills = []
    for category_skills in ENGINEER_PROFILE["skills"].values():
        skills.extend(category_skills)
    return skills


def get_skills_by_category() -> Dict[str, List[str]]:
    """
    Get skills organized by category.
    
    Returns:
        Dict[str, List[str]]: Skills dictionary with category names as keys.
    """
    return ENGINEER_PROFILE["skills"].copy()


def get_experience_summary() -> str:
    """
    Get the experience summary.
    
    Returns:
        str: The engineer's experience summary.
    """
    return ENGINEER_PROFILE["experience_summary"].strip()
