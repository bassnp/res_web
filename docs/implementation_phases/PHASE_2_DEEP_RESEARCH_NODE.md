# Phase 2: DEEP_RESEARCH Node Implementation

> **Objective**: Execute web searches to gather employer intelligence, synthesize findings into structured context, and verify external data sources.

---

## 1. Phase Overview

### 1.1 Desire Statement

**Desire: Totality of Evidence (Digital Truth)**

The Deep Research agent is the investigator. It operates under the assumption that the user's query is merely a starting point, and the truth lies in external data. Its desire is to gather comprehensive, verified intelligence about the employer.

### 1.2 Inputs & Outputs

| Direction | Data |
|-----------|------|
| **Input** | `state.phase_1_output` - Classification + entities from Connecting |
| **Input** | `state.query` - Original user query |
| **Output** | `Phase2Output` - Employer summary, requirements, tech stack, culture signals |

### 1.3 Tools Available

This node utilizes the existing `web_search` tool from `services/tools/web_search.py`.

---

## 2. File Location & Structure

```
res_backend/
├── services/
│   └── nodes/
│       └── deep_research.py    # THIS FILE
└── prompts/
    └── phase_2_deep_research.xml
```

---

## 3. XML-Structured Prompt Template

```xml
<!-- Location: res_backend/prompts/phase_2_deep_research.xml -->

<system_instruction>
  <agent_persona>
    You are an Intelligence Gathering Agent specializing in employer research.
    Your expertise is synthesizing web search results into actionable employer intelligence
    for evaluating job fit.
  </agent_persona>
  
  <primary_objective>
    Synthesize the provided web search results into a structured employer profile
    focusing on tech stack, culture, and requirements relevant to a software engineer.
  </primary_objective>
  
  <success_criteria>
    <criterion priority="critical">Identify concrete tech stack components mentioned</criterion>
    <criterion priority="critical">Extract explicit job requirements or qualifications if found</criterion>
    <criterion priority="high">Capture culture signals (values, work style, company stage)</criterion>
    <criterion priority="high">Note any red flags or concerns from search results</criterion>
    <criterion priority="medium">Distinguish between verified facts and speculation</criterion>
  </success_criteria>
  
  <behavioral_constraints>
    <constraint>DO NOT fabricate information not present in search results</constraint>
    <constraint>DO NOT speculate beyond what the evidence supports</constraint>
    <constraint>DO NOT include generic tech industry platitudes without evidence</constraint>
    <constraint>DO NOT output markdown or prose - output only valid JSON</constraint>
    <constraint>DO NOT include "I think" or "probably" - state only observed facts</constraint>
  </behavioral_constraints>
  
  <synthesis_guidelines>
    <guideline>If search results are sparse, acknowledge limited data</guideline>
    <guideline>Prioritize recent information over dated content</guideline>
    <guideline>Distinguish between job postings and company culture pages</guideline>
    <guideline>Extract specific technologies, not vague "modern stack" claims</guideline>
  </synthesis_guidelines>
</system_instruction>

<context_data>
  <prior_phase_output>
    Query Type: {query_type}
    Company Name: {company_name}
    Job Title: {job_title}
    Extracted Skills: {extracted_skills}
  </prior_phase_output>
  
  <search_results>
    {search_results}
  </search_results>
</context_data>

<output_contract>
  Output strictly valid JSON matching this exact schema (no markdown, no code blocks):
  {{
    "employer_summary": "string (2-4 sentences describing the company/role)",
    "identified_requirements": ["string (specific requirements found)"],
    "tech_stack": ["string (specific technologies mentioned)"],
    "culture_signals": ["string (observed culture indicators)"],
    "data_quality": "high" | "medium" | "low",
    "reasoning_trace": "string (1-2 sentences on synthesis approach)"
  }}
</output_contract>
```

---

## 4. Search Query Construction Logic

```python
"""
Search query construction utilities for Phase 2.

Different query strategies based on Phase 1 classification.
"""

from typing import List
from services.pipeline_state import Phase1Output


def construct_search_queries(phase_1: Phase1Output, original_query: str) -> List[str]:
    """
    Construct optimized search queries based on Phase 1 classification.
    
    Args:
        phase_1: Output from the Connecting phase.
        original_query: Raw user input.
    
    Returns:
        List of search queries to execute (max 2).
    """
    queries = []
    
    if phase_1["query_type"] == "company":
        company = phase_1["company_name"] or original_query
        
        # Primary: Company + engineering culture/tech
        queries.append(f"{company} software engineer tech stack engineering culture")
        
        # Secondary: Company + career/jobs
        queries.append(f"{company} careers jobs software developer requirements")
        
    else:  # job_description
        # Extract key terms from the job description
        job_title = phase_1["job_title"] or "software engineer"
        skills = phase_1["extracted_skills"][:3] if phase_1["extracted_skills"] else []
        company = phase_1["company_name"]
        
        # Primary: Role + skills + company (if known)
        skill_str = " ".join(skills) if skills else ""
        company_str = company if company else ""
        queries.append(f"{job_title} {skill_str} {company_str} requirements tech stack".strip())
        
        # Secondary: Industry context if company unknown
        if not company and skills:
            queries.append(f"{skills[0]} engineer job requirements culture startup")
    
    return queries[:2]  # Max 2 queries to avoid latency


def format_search_results(results: List[str]) -> str:
    """
    Format multiple search results for prompt injection.
    
    Args:
        results: List of search result strings.
    
    Returns:
        Formatted string for XML prompt.
    """
    if not results:
        return "No search results available."
    
    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(f"--- Search Result {i} ---\n{result}")
    
    return "\n\n".join(formatted)
```

---

## 5. Node Implementation

```python
"""
Deep Research Node - Phase 2 of the Fit Check Pipeline.

This module implements the intelligence gathering node that:
1. Executes web searches based on Phase 1 classification
2. Synthesizes findings into structured employer intelligence
3. Identifies tech stack, requirements, and culture signals

Gemini Optimization:
- Uses XML-structured prompt for synthesis
- Tool calls emit explicit thought events
- Post-hoc reasoning trace, not inline CoT
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from langchain_core.messages import HumanMessage

from config.llm import get_llm
from services.pipeline_state import FitCheckPipelineState, Phase2Output
from services.fit_check_agent import ThoughtCallback
from services.tools.web_search import web_search

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "deep_research"
PROMPT_FILE = Path(__file__).parent.parent.parent / "prompts" / "phase_2_deep_research.xml"


# =============================================================================
# Search Query Construction
# =============================================================================

def construct_search_queries(phase_1: Dict, original_query: str) -> List[str]:
    """
    Construct optimized search queries based on Phase 1 classification.
    
    Args:
        phase_1: Output from the Connecting phase.
        original_query: Raw user input.
    
    Returns:
        List of search queries to execute (max 2).
    """
    queries = []
    
    if phase_1.get("query_type") == "company":
        company = phase_1.get("company_name") or original_query
        queries.append(f"{company} software engineer tech stack engineering culture")
        queries.append(f"{company} careers jobs software developer requirements")
    else:
        job_title = phase_1.get("job_title") or "software engineer"
        skills = (phase_1.get("extracted_skills") or [])[:3]
        company = phase_1.get("company_name")
        
        skill_str = " ".join(skills) if skills else ""
        company_str = company if company else ""
        queries.append(f"{job_title} {skill_str} {company_str} requirements tech stack".strip())
        
        if not company and skills:
            queries.append(f"{skills[0]} engineer job requirements culture")
    
    return queries[:2]


def format_search_results(results: List[str]) -> str:
    """Format multiple search results for prompt injection."""
    if not results:
        return "No search results available."
    
    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(f"--- Search Result {i} ---\n{result}")
    
    return "\n\n".join(formatted)


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt() -> str:
    """Load the Phase 2 XML prompt template."""
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Phase 2 prompt not found at {PROMPT_FILE}, using embedded fallback")
        return get_fallback_prompt()


def get_fallback_prompt() -> str:
    """Embedded fallback prompt if file not found."""
    return """<system_instruction>
  <agent_persona>Intelligence Gathering Agent</agent_persona>
  <primary_objective>
    Synthesize search results into structured employer intelligence.
  </primary_objective>
  <behavioral_constraints>
    <constraint>DO NOT fabricate information not in search results</constraint>
    <constraint>Output only valid JSON</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <prior_phase_output>{prior_phase}</prior_phase_output>
  <search_results>{search_results}</search_results>
</context_data>

<output_contract>
{{"employer_summary": "string", "identified_requirements": [], "tech_stack": [],
  "culture_signals": [], "data_quality": "medium", "reasoning_trace": "string"}}
</output_contract>"""


# =============================================================================
# JSON Parsing
# =============================================================================

def extract_json_from_response(response: str) -> Dict[str, Any]:
    """Extract JSON from LLM response, handling various formats."""
    text = response.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    json_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    matches = re.findall(json_pattern, text)
    if matches:
        try:
            return json.loads(matches[0])
        except json.JSONDecodeError:
            pass
    
    brace_pattern = r'\{[\s\S]*\}'
    matches = re.findall(brace_pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")


def validate_phase2_output(data: Dict[str, Any]) -> Phase2Output:
    """Validate and normalize Phase 2 output."""
    return Phase2Output(
        employer_summary=data.get("employer_summary") or "No employer summary available.",
        identified_requirements=data.get("identified_requirements") or [],
        tech_stack=data.get("tech_stack") or [],
        culture_signals=data.get("culture_signals") or [],
        reasoning_trace=data.get("reasoning_trace") or "Research synthesis completed.",
    )


# =============================================================================
# Main Node Function
# =============================================================================

async def deep_research_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 2: DEEP_RESEARCH - Intelligence Gathering Node.
    
    Executes web searches and synthesizes employer intelligence.
    
    Args:
        state: Current pipeline state with Phase 1 output.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update with phase_2_output and phase transition.
    
    Emits:
        - phase: "deep_research" at start
        - thought: tool_call for each search
        - thought: observation for each result
        - thought: reasoning for synthesis
        - phase_complete: with research summary
    """
    logger.info("[DEEP_RESEARCH] Starting phase 2")
    step = state.get("step_count", 0)
    phase_1 = state.get("phase_1_output", {})
    
    # Emit phase start
    if callback:
        await callback.on_phase(
            PHASE_NAME,
            "Researching employer intelligence..."
        )
    
    try:
        # Construct search queries
        queries = construct_search_queries(phase_1, state["query"])
        search_results = []
        
        # Execute searches
        for query in queries:
            step += 1
            
            # Emit tool call
            if callback:
                await callback.on_thought(
                    step=step,
                    thought_type="tool_call",
                    content=f"Searching for: {query}",
                    phase=PHASE_NAME,
                    tool="web_search",
                    tool_input=query,
                )
            
            # Execute search
            try:
                result = web_search.invoke(query)
                search_results.append(result)
                
                step += 1
                # Emit observation
                if callback:
                    # Truncate for display
                    preview = result[:200] + "..." if len(result) > 200 else result
                    await callback.on_thought(
                        step=step,
                        thought_type="observation",
                        content=f"Found relevant information about employer context.",
                        phase=PHASE_NAME,
                    )
                    
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                search_results.append(f"Search unavailable: {str(e)}")
        
        # Format results for synthesis
        formatted_results = format_search_results(search_results)
        
        # Load and format synthesis prompt
        prompt_template = load_phase_prompt()
        prompt = prompt_template.format(
            query_type=phase_1.get("query_type", "unknown"),
            company_name=phase_1.get("company_name") or "Unknown",
            job_title=phase_1.get("job_title") or "Not specified",
            extracted_skills=", ".join(phase_1.get("extracted_skills", [])) or "None",
            search_results=formatted_results,
        )
        
        step += 1
        # Emit reasoning thought
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content="Synthesizing search results into structured employer profile...",
                phase=PHASE_NAME,
            )
        
        # Get LLM for synthesis
        llm = get_llm(streaming=False, temperature=0.3)
        
        # Invoke LLM
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)
        
        # Parse response
        response_text = response.content if hasattr(response, 'content') else str(response)
        parsed_data = extract_json_from_response(response_text)
        validated_output = validate_phase2_output(parsed_data)
        
        # Emit phase complete
        if callback:
            tech_count = len(validated_output["tech_stack"])
            req_count = len(validated_output["identified_requirements"])
            summary = f"Identified {tech_count} technologies, {req_count} requirements"
            await callback.on_phase_complete(PHASE_NAME, summary)
        
        logger.info(f"[DEEP_RESEARCH] Phase 2 complete: {len(search_results)} searches")
        
        return {
            "phase_2_output": validated_output,
            "current_phase": "skeptical_comparison",
            "step_count": step,
        }
        
    except Exception as e:
        logger.error(f"[DEEP_RESEARCH] Phase 2 failed: {e}")
        
        # Graceful degradation
        fallback_output = Phase2Output(
            employer_summary="Unable to gather complete employer information.",
            identified_requirements=[],
            tech_stack=[],
            culture_signals=[],
            reasoning_trace=f"Research phase encountered an error: {str(e)}",
        )
        
        if callback:
            await callback.on_phase_complete(
                PHASE_NAME,
                f"Research completed with limited data (error: {str(e)[:50]})"
            )
        
        return {
            "phase_2_output": fallback_output,
            "current_phase": "skeptical_comparison",
            "step_count": step,
            "processing_errors": state.get("processing_errors", []) + [f"Phase 2 error: {str(e)}"],
        }
```

---

## 6. Unit Tests

```python
"""
Unit tests for Phase 2: DEEP_RESEARCH node.

Location: res_backend/tests/test_deep_research_node.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.nodes.deep_research import (
    deep_research_node,
    construct_search_queries,
    format_search_results,
    validate_phase2_output,
)
from services.pipeline_state import create_initial_state, Phase1Output


class TestSearchQueryConstruction:
    """Test search query construction logic."""
    
    def test_company_query(self):
        """Company classification generates appropriate queries."""
        phase_1 = Phase1Output(
            query_type="company",
            company_name="Google",
            job_title=None,
            extracted_skills=[],
            reasoning_trace="",
        )
        queries = construct_search_queries(phase_1, "Google")
        
        assert len(queries) == 2
        assert "Google" in queries[0]
        assert "tech stack" in queries[0].lower() or "culture" in queries[0].lower()
    
    def test_job_description_query(self):
        """Job description generates skill-focused queries."""
        phase_1 = Phase1Output(
            query_type="job_description",
            company_name="Stripe",
            job_title="Senior Python Developer",
            extracted_skills=["Python", "AWS", "PostgreSQL"],
            reasoning_trace="",
        )
        queries = construct_search_queries(phase_1, "original query")
        
        assert len(queries) >= 1
        assert "Python" in queries[0] or "Senior" in queries[0]
    
    def test_query_limit(self):
        """Queries are limited to max 2."""
        phase_1 = Phase1Output(
            query_type="company",
            company_name="Meta",
            job_title=None,
            extracted_skills=["Python", "React", "GraphQL", "Kubernetes"],
            reasoning_trace="",
        )
        queries = construct_search_queries(phase_1, "Meta")
        assert len(queries) <= 2


class TestResultFormatting:
    """Test search result formatting."""
    
    def test_format_multiple_results(self):
        """Multiple results format correctly."""
        results = ["Result 1 content", "Result 2 content"]
        formatted = format_search_results(results)
        
        assert "Search Result 1" in formatted
        assert "Search Result 2" in formatted
        assert "Result 1 content" in formatted
    
    def test_empty_results(self):
        """Empty results return default message."""
        formatted = format_search_results([])
        assert "No search results" in formatted


class TestOutputValidation:
    """Test Phase 2 output validation."""
    
    def test_valid_output(self):
        """Valid research output validates correctly."""
        data = {
            "employer_summary": "Google is a tech company...",
            "identified_requirements": ["Python", "Distributed systems"],
            "tech_stack": ["Python", "Go", "Kubernetes"],
            "culture_signals": ["Innovation-focused"],
            "reasoning_trace": "Synthesized from search results.",
        }
        result = validate_phase2_output(data)
        
        assert result["employer_summary"] == "Google is a tech company..."
        assert len(result["tech_stack"]) == 3
    
    def test_missing_fields_default(self):
        """Missing fields default correctly."""
        data = {"employer_summary": "Basic summary"}
        result = validate_phase2_output(data)
        
        assert result["tech_stack"] == []
        assert result["culture_signals"] == []


class TestDeepResearchNode:
    """Integration tests for the deep research node."""
    
    @pytest.mark.asyncio
    async def test_successful_research(self):
        """Successful research synthesizes results."""
        state = create_initial_state("Google")
        state["phase_1_output"] = Phase1Output(
            query_type="company",
            company_name="Google",
            job_title=None,
            extracted_skills=[],
            reasoning_trace="",
        )
        state["step_count"] = 1
        
        mock_response = MagicMock()
        mock_response.content = '''
        {"employer_summary": "Google is a leading tech company",
         "identified_requirements": ["Python", "ML"],
         "tech_stack": ["Python", "TensorFlow"],
         "culture_signals": ["Innovation"],
         "reasoning_trace": "Synthesized from search."}
        '''
        
        with patch("services.nodes.deep_research.web_search") as mock_search:
            mock_search.invoke.return_value = "Google uses Python and TensorFlow..."
            
            with patch("services.nodes.deep_research.get_llm") as mock_llm:
                mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                
                result = await deep_research_node(state)
                
                assert result["phase_2_output"]["employer_summary"] == "Google is a leading tech company"
                assert result["current_phase"] == "skeptical_comparison"
    
    @pytest.mark.asyncio
    async def test_callback_events(self):
        """Callback receives appropriate events."""
        state = create_initial_state("Stripe")
        state["phase_1_output"] = Phase1Output(
            query_type="company",
            company_name="Stripe",
            job_title=None,
            extracted_skills=[],
            reasoning_trace="",
        )
        state["step_count"] = 1
        
        callback = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '{"employer_summary": "Stripe", "tech_stack": []}'
        
        with patch("services.nodes.deep_research.web_search") as mock_search:
            mock_search.invoke.return_value = "Stripe info..."
            
            with patch("services.nodes.deep_research.get_llm") as mock_llm:
                mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                
                await deep_research_node(state, callback=callback)
                
                # Verify events
                callback.on_phase.assert_called_once()
                callback.on_thought.assert_called()  # Multiple times
                callback.on_phase_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_failure_recovery(self):
        """Search failures result in graceful degradation."""
        state = create_initial_state("Unknown Company")
        state["phase_1_output"] = Phase1Output(
            query_type="company",
            company_name="Unknown Company",
            job_title=None,
            extracted_skills=[],
            reasoning_trace="",
        )
        state["step_count"] = 1
        
        with patch("services.nodes.deep_research.web_search") as mock_search:
            mock_search.invoke.side_effect = Exception("Network error")
            
            # Should still produce output (degraded)
            mock_response = MagicMock()
            mock_response.content = '{"employer_summary": "Limited info", "tech_stack": []}'
            
            with patch("services.nodes.deep_research.get_llm") as mock_llm:
                mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                
                result = await deep_research_node(state)
                
                # Should still transition to next phase
                assert result["current_phase"] == "skeptical_comparison"
```

---

## 7. The Research Loop (Future Enhancement)

For advanced implementations, consider a **cyclic research loop**:

```python
async def research_loop(state, callback, max_iterations=3):
    """
    Iterative research loop for comprehensive intelligence gathering.
    
    If initial search is insufficient, generate follow-up queries.
    """
    iteration = 0
    data_quality = "low"
    
    while data_quality != "high" and iteration < max_iterations:
        # Execute research
        result = await gather_intelligence(state, callback)
        data_quality = result.get("data_quality", "low")
        
        if data_quality == "low":
            # Generate follow-up queries
            follow_up = generate_follow_up_queries(result)
            state = update_state_with_queries(state, follow_up)
        
        iteration += 1
    
    return result
```

---

## 8. Validation Checklist

Before proceeding to Phase 3:

- [ ] `services/nodes/deep_research.py` created and importable
- [ ] `prompts/phase_2_deep_research.xml` created
- [ ] Web search tool is invoked with appropriate queries
- [ ] Tool calls and observations emit separate thought events
- [ ] Search results are synthesized into structured output
- [ ] Graceful degradation on search/LLM failures
- [ ] Unit tests pass

---

## 9. Performance Considerations

- **Search Queries**: Limited to 2 to avoid latency
- **Result Truncation**: Search results truncated to 1500 chars each
- **Temperature**: 0.3 for synthesis (balanced creativity/accuracy)
- **Parallel Execution**: Consider running searches in parallel
- **Timeout**: 15s maximum for this phase (includes network calls)

---

## 10. Next Steps

After implementing this phase:
1. Proceed to **PHASE_3_SKEPTICAL_COMPARISON_NODE.md**
2. The Skeptical Comparison node will critique the research findings
3. This is the **CRITICAL** phase that prevents sycophantic outputs

---

## 11. Build Verification Gate

> ⛔ **STOP**: Do NOT proceed to the next phase until this phase compiles and builds successfully.

### Backend Build Verification

```powershell
# Navigate to backend directory
cd res_backend

# Verify Python syntax
python -m py_compile services/nodes/deep_research.py

# Verify imports work
python -c "from services.nodes.deep_research import deep_research_node; print('Phase 2 imports OK')"

# Verify web_search tool integration
python -c "from services.tools.web_search import web_search; print('web_search tool OK')"

# Run Phase 2 unit tests
pytest tests/unit/test_deep_research_node.py -v

# Run all tests (ensure no regressions)
pytest --tb=short
```

### Verification Checklist

- [ ] `services/nodes/deep_research.py` created and has no syntax errors
- [ ] `prompts/phase_2_deep_research.xml` created
- [ ] web_search tool integration works
- [ ] Import verification succeeds
- [ ] Phase 2 unit tests pass
- [ ] All existing tests still pass

---

## 12. Requirements Tracking

> 📋 **IMPORTANT**: Refer to **[TRACK_ALL_REQUIREMENTS.md](./TRACK_ALL_REQUIREMENTS.md)** for the complete requirements checklist.

### After Completing This Phase:

1. Open `TRACK_ALL_REQUIREMENTS.md`
2. Locate the **Phase 2: DEEP_RESEARCH Node** section
3. Mark each completed requirement with ✅
4. Fill in the "Verified By" and "Date" columns
5. Complete the **Build Verification** checkboxes
6. Update the **Completion Summary** table at the bottom

### Phase 2 Requirement IDs to Update:

- P2-001 through P2-012

---

*Document Version: 1.1 | Phase 2 of 7 | Intelligence Gathering*
