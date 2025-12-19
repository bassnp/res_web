"""
Query Expansion Engine for Fit Check Research.

Generates CSE-optimized queries with:
- Fit Check context awareness (company vs job description)
- CSE operators (intitle:, site:, -site:, quotes)
- Domain exclusions for noise reduction
- Iteration-specific reformulation strategies
"""

import re
from typing import List, Optional, Dict, Any
from models.fit_check import ExpandedQuery, QueryExpansionResult

# =============================================================================
# Constants
# =============================================================================

# Domain exclusions for noise reduction
EXCLUDED_DOMAINS = [
    "pinterest.com",
    "facebook.com", 
    "instagram.com",
    "tiktok.com",
    "twitter.com",
    "linkedin.com",  # Often paywalled
]

# Preferred domains for tech/job info
PREFERRED_DOMAINS = [
    "glassdoor.com",
    "levels.fyi",
    "builtin.com",
    "stackshare.io",
    "github.com",
]

# CSE operators mapping
CSE_OPERATORS = {
    "exact_phrase": lambda s: f'"{s}"',
    "in_title": lambda s: f"intitle:{s}",
    "exclude_site": lambda d: f"-site:{d}",
    "include_site": lambda d: f"site:{d}",
}

# Query templates by context
COMPANY_QUERY_TEMPLATES = [
    "{company} software engineer tech stack engineering",
    'intitle:"{company}" careers engineering jobs',
    "{company} engineering culture values -site:pinterest.com -site:facebook.com",
    "{company} technology blog OR engineering OR developers",
    '"{company}" software developer requirements 2024',
]

JOB_DESCRIPTION_TEMPLATES = [
    "{title} {skills} requirements tech stack",
    'intitle:"{title}" {company} engineering',
    "{skills} engineer job requirements -site:pinterest.com",
    "{company} {title} interview OR culture OR team",
]


# =============================================================================
# Core Functions
# =============================================================================

def expand_queries(
    phase_1_output: Dict[str, Any],
    original_query: str,
    iteration: int = 1,
    max_queries: int = 5,
) -> QueryExpansionResult:
    """
    Generate CSE-optimized queries from Phase 1 classification.
    
    Args:
        phase_1_output: Classification result with query_type, company_name, etc.
        original_query: Raw user input for fallback.
        iteration: Current search iteration (1-3).
        max_queries: Maximum queries to generate.
    
    Returns:
        QueryExpansionResult with 3-5 optimized queries.
    """
    query_type = phase_1_output.get("query_type", "job_description")
    company_name = phase_1_output.get("company_name")
    job_title = phase_1_output.get("job_title") or "software engineer"
    extracted_skills = phase_1_output.get("extracted_skills") or []
    
    # 1. Generate base queries for iteration 1
    if query_type == "company":
        result = _expand_company_queries(company_name, original_query, 1)
    else:
        result = _expand_job_queries(company_name, job_title, extracted_skills, 1)
    
    # 2. Apply reformulation if iteration > 1
    if iteration > 1:
        query_strings = [q.query for q in result.queries]
        reformulated_strings = reformulate_queries(query_strings, iteration)
        
        # Update queries in result
        for i, q_str in enumerate(reformulated_strings):
            if i < len(result.queries):
                result.queries[i].query = q_str
                result.queries[i].operators_used = [] # Operators are removed in BROADEN
        
        result.iteration = iteration
    
    return result


def _expand_company_queries(
    company_name: Optional[str],
    original_query: str,
    iteration: int,
) -> QueryExpansionResult:
    """Generate queries for company-focused research."""
    company = company_name or original_query.strip()
    queries = []
    exclusions = " ".join(f"-site:{d}" for d in EXCLUDED_DOMAINS[:3])
    
    # Primary: Exact company + tech stack
    queries.append(ExpandedQuery(
        query=f'"{company}" software engineer tech stack engineering {exclusions}',
        purpose="Core tech stack and engineering culture",
        operators_used=["exact_phrase", "exclude_site"],
    ))
    
    # Secondary: Company careers with title operator
    queries.append(ExpandedQuery(
        query=f'intitle:"{company}" careers jobs software developer requirements',
        purpose="Job requirements from careers page",
        operators_used=["in_title", "exact_phrase"],
    ))
    
    # Tertiary: Engineering blog/culture
    queries.append(ExpandedQuery(
        query=f'{company} engineering blog OR tech OR culture values {exclusions}',
        purpose="Engineering culture and values",
        operators_used=["exclude_site"],
    ))
    
    return QueryExpansionResult(
        queries=queries[:5],
        expansion_strategy="company_focus",
        iteration=iteration,
    )


def _expand_job_queries(
    company_name: Optional[str],
    job_title: str,
    skills: List[str],
    iteration: int,
) -> QueryExpansionResult:
    """Generate queries for job description research."""
    queries = []
    exclusions = " ".join(f"-site:{d}" for d in EXCLUDED_DOMAINS[:3])
    skill_str = " ".join(skills[:3]) if skills else ""
    
    # Primary: Role + skills + company
    base_query = f'{job_title} {skill_str}'.strip()
    if company_name:
        base_query += f' "{company_name}"'
    queries.append(ExpandedQuery(
        query=f'{base_query} requirements tech stack {exclusions}',
        purpose="Core job requirements and tech stack",
        operators_used=["exact_phrase", "exclude_site"] if company_name else ["exclude_site"],
    ))
    
    # Secondary: Title in title
    queries.append(ExpandedQuery(
        query=f'intitle:"{job_title}" {skill_str} requirements',
        purpose="Job listings with title match",
        operators_used=["in_title", "exact_phrase"],
    ))
    
    # Tertiary: Company-specific if known
    if company_name:
        queries.append(ExpandedQuery(
            query=f'"{company_name}" engineering team culture {job_title} {exclusions}',
            purpose="Company culture for the role",
            operators_used=["exact_phrase", "exclude_site"],
        ))
    else:
        # Industry context
        primary_skill = skills[0] if skills else "software"
        queries.append(ExpandedQuery(
            query=f'{primary_skill} engineer career requirements industry 2024',
            purpose="Industry context for skill area",
            operators_used=[],
        ))
    
    return QueryExpansionResult(
        queries=queries[:5],
        expansion_strategy="job_focus",
        iteration=iteration,
    )


def reformulate_queries(
    previous_queries: List[str],
    iteration: int,
    low_result_count: bool = False,
) -> List[str]:
    """
    Reformulate queries for subsequent iterations.
    
    Strategies by iteration:
        - Iteration 2: BROADEN (remove restrictive operators)
        - Iteration 3: SYNONYMS (alternative phrasings)
    
    Args:
        previous_queries: Queries from previous iteration.
        iteration: Current iteration number (2 or 3).
        low_result_count: True if previous iteration had few results.
    
    Returns:
        List of reformulated query strings.
    """
    if iteration == 2:
        return _broaden_queries(previous_queries)
    elif iteration == 3:
        return _synonym_queries(previous_queries)
    return previous_queries


def _broaden_queries(queries: List[str]) -> List[str]:
    """Remove restrictive operators for broader search."""
    broadened = []
    for q in queries:
        # Remove exact phrase quotes
        q = q.replace('"', '')
        # Remove intitle:
        q = q.replace('intitle:', '')
        # Remove site exclusions
        q = re.sub(r'-site:\S+', '', q)
        broadened.append(q.strip())
    return broadened


def _synonym_queries(queries: List[str]) -> List[str]:
    """Replace terms with synonyms for fresh results."""
    synonyms = {
        "software engineer": "developer programmer",
        "tech stack": "technology tools",
        "engineering culture": "developer experience",
        "requirements": "qualifications skills",
    }
    result = []
    for q in queries:
        for term, replacement in synonyms.items():
            q = q.replace(term, replacement)
        result.append(q)
    return result
