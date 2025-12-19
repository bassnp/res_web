# Phase 1: Query Intelligence & Expansion System

**Phase:** 1 of 4  
**Focus:** Enhanced Search Query Generation  
**Risk Level:** Low  
**Prerequisites:** None

---

## 1. Objective

Transform the basic 2-query system into an intelligent query expansion engine that:
- Generates 3-5 CSE-optimized queries with search operators
- Applies Fit Check-specific query strategies
- Prepares foundation for iterative reformulation

---

## 2. Current State (To Demolish)

### Location: `services/nodes/deep_research.py`

**Current `construct_search_queries()` function:**
```python
# LEGACY CODE - MAX 2 BASIC QUERIES
def construct_search_queries(phase_1, original_query) -> List[str]:
    # Only builds 2 simple concatenated queries
    # No CSE operators (intitle:, site:, -site:, quotes)
    # No optimization for search precision
```

**Problems:**
1. Only 2 queries limits coverage
2. No CSE operators reduces precision
3. No domain exclusions (Pinterest, Facebook noise)
4. No iteration-aware reformulation

---

## 3. Target State (New Architecture)

### 3.1 New Module: `services/utils/query_expander.py`

```python
"""
Query Expansion Engine for Fit Check Research.

Generates CSE-optimized queries with:
- Fit Check context awareness (company vs job description)
- CSE operators (intitle:, site:, -site:, quotes)
- Domain exclusions for noise reduction
- Iteration-specific reformulation strategies
"""
```

### 3.2 Core Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                    QUERY EXPANSION ENGINE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │ Phase1Output    │───►│ QueryExpander   │───►│ ExpandedQueries │ │
│  │ (classification)│    │ (CSE-optimized) │    │ (3-5 queries)   │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                │                                    │
│                                ▼                                    │
│                    ┌─────────────────────┐                          │
│                    │ QueryReformulator   │                          │
│                    │ (iteration-aware)   │                          │
│                    └─────────────────────┘                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Implementation Specification

### 4.1 Data Models

**Add to `models/fit_check.py`:**

```python
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class ExpandedQuery(BaseModel):
    """Single CSE-optimized search query."""
    query: str = Field(..., description="The search query string")
    purpose: str = Field(..., description="What this query targets")
    operators_used: List[str] = Field(default_factory=list)

class QueryExpansionResult(BaseModel):
    """Result of query expansion."""
    queries: List[ExpandedQuery] = Field(..., min_length=3, max_length=5)
    expansion_strategy: Literal["company_focus", "job_focus", "hybrid"]
    iteration: int = Field(default=1, ge=1, le=3)
```

### 4.2 Constants

**Add to `services/utils/query_expander.py`:**

```python
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
```

### 4.3 Core Functions

**`services/utils/query_expander.py`:**

```python
from typing import List, Optional, Dict, Any
from models.fit_check import ExpandedQuery, QueryExpansionResult

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
    
    if query_type == "company":
        return _expand_company_queries(company_name, original_query, iteration)
    else:
        return _expand_job_queries(company_name, job_title, extracted_skills, iteration)


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
    
    # Iteration-specific additions
    if iteration >= 2:
        # Broaden: Try alternative phrasings
        queries.append(ExpandedQuery(
            query=f'{company} technology company review glassdoor OR builtin',
            purpose="External reviews and company info",
            operators_used=[],
        ))
    
    if iteration >= 3:
        # Synonyms: Try related terms
        queries.append(ExpandedQuery(
            query=f'{company} developer OR programmer jobs technology 2024',
            purpose="Recent job postings with alternate terms",
            operators_used=[],
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
        import re
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
```

---

## 5. Integration Points

### 5.1 Update `deep_research.py`

**Replace `construct_search_queries()` with import:**

```python
# OLD: Local function (DELETE)
# def construct_search_queries(phase_1, original_query) -> List[str]:
#     ...

# NEW: Import from query_expander
from services.utils.query_expander import expand_queries, QueryExpansionResult

async def deep_research_node(state, callback):
    # ... existing setup ...
    
    # NEW: Use query expansion engine
    expansion_result = expand_queries(
        phase_1_output=state.get("phase_1_output", {}),
        original_query=state.get("query", ""),
        iteration=state.get("search_attempt", 1),
    )
    
    # Execute expanded queries
    search_results = []
    for expanded_query in expansion_result.queries:
        result = web_search(expanded_query.query)
        search_results.append({
            "query": expanded_query.query,
            "purpose": expanded_query.purpose,
            "result": result,
        })
    
    # ... rest of synthesis ...
```

### 5.2 Update Pipeline State

**Add to `services/pipeline_state.py`:**

```python
class FitCheckPipelineState(TypedDict):
    # ... existing fields ...
    
    # NEW: Query expansion tracking
    expanded_queries: Optional[List[Dict[str, str]]]  # Queries with purposes
    query_expansion_strategy: Optional[str]  # company_focus, job_focus, hybrid
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**`tests/unit/test_query_expander.py`:**

```python
import pytest
from services.utils.query_expander import expand_queries, reformulate_queries

class TestQueryExpansion:
    """Test query expansion functionality."""
    
    def test_company_focus_generates_minimum_queries(self):
        """Should generate at least 3 queries for company focus."""
        result = expand_queries(
            phase_1_output={"query_type": "company", "company_name": "Stripe"},
            original_query="Stripe",
        )
        assert len(result.queries) >= 3
        assert result.expansion_strategy == "company_focus"
    
    def test_job_focus_includes_skills(self):
        """Should incorporate extracted skills in job queries."""
        result = expand_queries(
            phase_1_output={
                "query_type": "job_description",
                "job_title": "backend engineer",
                "extracted_skills": ["Python", "Kubernetes"],
            },
            original_query="Python backend engineer",
        )
        # At least one query should contain skills
        assert any("Python" in q.query for q in result.queries)
    
    def test_cse_operators_applied(self):
        """Should apply CSE operators for precision."""
        result = expand_queries(
            phase_1_output={"query_type": "company", "company_name": "OpenAI"},
            original_query="OpenAI",
        )
        # Should have exact phrase or intitle operators
        has_operators = any(
            "intitle:" in q.query or '\"' in q.query
            for q in result.queries
        )
        assert has_operators
    
    def test_domain_exclusions_applied(self):
        """Should exclude noisy domains."""
        result = expand_queries(
            phase_1_output={"query_type": "company", "company_name": "Meta"},
            original_query="Meta",
        )
        has_exclusions = any("-site:" in q.query for q in result.queries)
        assert has_exclusions
    
    def test_iteration_2_broadens_queries(self):
        """Iteration 2 should broaden previous queries."""
        original = ['"Stripe" intitle:engineering -site:pinterest.com']
        broadened = reformulate_queries(original, iteration=2)
        # Should remove quotes and operators
        assert '"' not in broadened[0]
        assert "intitle:" not in broadened[0]


class TestQueryReformulation:
    """Test iteration-specific reformulation."""
    
    def test_broaden_removes_operators(self):
        """BROADEN strategy should remove restrictive operators."""
        queries = ['intitle:"company" -site:facebook.com']
        result = reformulate_queries(queries, iteration=2)
        assert "intitle:" not in result[0]
        assert "-site:" not in result[0]
    
    def test_synonym_replaces_terms(self):
        """SYNONYMS strategy should use alternative terms."""
        queries = ["software engineer requirements"]
        result = reformulate_queries(queries, iteration=3)
        # Should have replacement terms
        assert "developer" in result[0] or "programmer" in result[0]
```

### 6.2 Integration Tests

**`tests/integration/test_query_integration.py`:**

```python
import pytest
from services.nodes.deep_research import deep_research_node
from services.pipeline_state import create_initial_state

@pytest.mark.asyncio
async def test_deep_research_uses_expanded_queries():
    """Deep research should use query expansion engine."""
    state = create_initial_state(query="Stripe")
    state["phase_1_output"] = {
        "query_type": "company",
        "company_name": "Stripe",
    }
    
    result = await deep_research_node(state, callback=None)
    
    # Should have tracked expanded queries
    assert result.get("expanded_queries") is not None
    assert len(result.get("expanded_queries", [])) >= 3
```

---

## 7. Requirements Tracking

### Verification Checklist

| # | Requirement | Test | Status |
|---|-------------|------|--------|
| 1.1 | Generate 3-5 queries | `test_company_focus_generates_minimum_queries` | ⬜ |
| 1.2 | Apply CSE operators | `test_cse_operators_applied` | ⬜ |
| 1.3 | Exclude noisy domains | `test_domain_exclusions_applied` | ⬜ |
| 1.4 | Company focus strategy | `test_company_focus_generates_minimum_queries` | ⬜ |
| 1.5 | Job focus strategy | `test_job_focus_includes_skills` | ⬜ |
| 1.6 | Iteration 2 BROADEN | `test_iteration_2_broadens_queries` | ⬜ |
| 1.7 | Iteration 3 SYNONYMS | `test_synonym_replaces_terms` | ⬜ |
| 1.8 | Integration with deep_research | `test_deep_research_uses_expanded_queries` | ⬜ |

### Sign-Off

- [ ] All unit tests pass
- [ ] Integration test passes
- [ ] Code review completed
- [ ] Documentation updated

---

## 8. Files Changed Summary

| File | Action | Lines Changed (est.) |
|------|--------|---------------------|
| `services/utils/query_expander.py` | **CREATE** | ~200 |
| `models/fit_check.py` | EXTEND | ~15 |
| `services/nodes/deep_research.py` | MODIFY | ~30 |
| `services/pipeline_state.py` | EXTEND | ~5 |
| `tests/unit/test_query_expander.py` | **CREATE** | ~80 |
| `tests/integration/test_query_integration.py` | **CREATE** | ~30 |

---

## 9. Rollback Plan

If issues arise:
1. Revert `deep_research.py` to use original `construct_search_queries()`
2. New module (`query_expander.py`) can be deleted without breaking existing code
3. State field additions are optional and backward-compatible
