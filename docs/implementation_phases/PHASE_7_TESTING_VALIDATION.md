# Phase 7: Testing & Validation Framework

## Overview

This phase establishes a comprehensive testing framework to ensure the multi-agent workflow operates with surgical precision, validates all SSE streaming contracts, and guarantees production-ready reliability.

## Testing Architecture

```
tests/
├── unit/
│   ├── test_connecting_node.py
│   ├── test_deep_research_node.py
│   ├── test_skeptical_comparison_node.py
│   ├── test_skills_matching_node.py
│   ├── test_generate_results_node.py
│   └── test_state_management.py
├── integration/
│   ├── test_workflow_transitions.py
│   ├── test_sse_streaming.py
│   └── test_end_to_end.py
├── fixtures/
│   ├── sample_queries.py
│   ├── mock_responses.py
│   └── expected_outputs.py
└── conftest.py
```

---

## 1. Unit Test Specifications

### 1.1 CONNECTING_NODE Tests

```python
# tests/unit/test_connecting_node.py
"""
Unit tests for CONNECTING node - Query Classification & Entity Extraction
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.fit_check_agent import connecting_node
from models.fit_check import FitCheckState, QueryType

class TestConnectingNode:
    """Test suite for CONNECTING node functionality."""
    
    @pytest.fixture
    def base_state(self) -> FitCheckState:
        """Create base state for testing."""
        return {
            "messages": [],
            "query": "",
            "current_phase": "CONNECTING",
            "query_analysis": None,
            "research_results": None,
            "skeptical_analysis": None,
            "skills_analysis": None,
            "final_response": None,
            "error": None,
            "metadata": {}
        }
    
    # ============================================================
    # QUERY CLASSIFICATION TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_classifies_company_fit_query(self, base_state):
        """
        Test: Company-specific queries are correctly classified
        Input: "Would I be a good fit for Google?"
        Expected: query_type = "company_fit", company_name = "Google"
        """
        base_state["query"] = "Would I be a good fit for Google?"
        
        result = await connecting_node(base_state)
        
        assert result["query_analysis"]["query_type"] == "company_fit"
        assert result["query_analysis"]["entities"]["company_name"] == "Google"
        assert result["current_phase"] == "DEEP_RESEARCH"
    
    @pytest.mark.asyncio
    async def test_classifies_role_fit_query(self, base_state):
        """
        Test: Role-specific queries are correctly classified
        Input: "Am I suited for a senior backend engineer position?"
        Expected: query_type = "role_fit", role_title populated
        """
        base_state["query"] = "Am I suited for a senior backend engineer position?"
        
        result = await connecting_node(base_state)
        
        assert result["query_analysis"]["query_type"] == "role_fit"
        assert "backend" in result["query_analysis"]["entities"]["role_title"].lower()
    
    @pytest.mark.asyncio
    async def test_classifies_skill_assessment_query(self, base_state):
        """
        Test: Skill-focused queries are correctly classified
        Input: "How do my Python skills compare to industry standards?"
        Expected: query_type = "skill_assessment", skills list populated
        """
        base_state["query"] = "How do my Python skills compare to industry standards?"
        
        result = await connecting_node(base_state)
        
        assert result["query_analysis"]["query_type"] == "skill_assessment"
        assert "python" in [s.lower() for s in result["query_analysis"]["entities"]["skills_mentioned"]]
    
    @pytest.mark.asyncio
    async def test_classifies_industry_fit_query(self, base_state):
        """
        Test: Industry queries are correctly classified
        Input: "Would I fit well in the fintech industry?"
        Expected: query_type = "industry_fit", industry populated
        """
        base_state["query"] = "Would I fit well in the fintech industry?"
        
        result = await connecting_node(base_state)
        
        assert result["query_analysis"]["query_type"] == "industry_fit"
        assert "fintech" in result["query_analysis"]["entities"]["industry"].lower()
    
    @pytest.mark.asyncio
    async def test_classifies_general_query(self, base_state):
        """
        Test: Vague queries default to general type
        Input: "What should I know about my career?"
        Expected: query_type = "general"
        """
        base_state["query"] = "What should I know about my career?"
        
        result = await connecting_node(base_state)
        
        assert result["query_analysis"]["query_type"] == "general"
    
    # ============================================================
    # ENTITY EXTRACTION TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_extracts_multiple_companies(self, base_state):
        """
        Test: Multiple companies are extracted from query
        Input: "Should I apply to Google or Microsoft?"
        Expected: Both companies in entities
        """
        base_state["query"] = "Should I apply to Google or Microsoft?"
        
        result = await connecting_node(base_state)
        
        companies = result["query_analysis"]["entities"].get("companies", [])
        assert len(companies) >= 2
    
    @pytest.mark.asyncio
    async def test_extracts_technology_stack(self, base_state):
        """
        Test: Technology mentions are extracted
        Input: "Do I have the right React and TypeScript skills for frontend roles?"
        Expected: React and TypeScript in skills
        """
        base_state["query"] = "Do I have the right React and TypeScript skills for frontend roles?"
        
        result = await connecting_node(base_state)
        
        skills = [s.lower() for s in result["query_analysis"]["entities"]["skills_mentioned"]]
        assert "react" in skills or "typescript" in skills
    
    @pytest.mark.asyncio
    async def test_extracts_experience_level(self, base_state):
        """
        Test: Experience level is inferred
        Input: "Am I ready for a senior engineering position?"
        Expected: experience_level = "senior"
        """
        base_state["query"] = "Am I ready for a senior engineering position?"
        
        result = await connecting_node(base_state)
        
        assert result["query_analysis"]["entities"]["experience_level"] == "senior"
    
    # ============================================================
    # CONFIDENCE SCORING TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_high_confidence_for_clear_query(self, base_state):
        """
        Test: Clear queries receive high confidence scores
        Input: "Would I be a good fit for Google as a senior Python engineer?"
        Expected: confidence >= 0.8
        """
        base_state["query"] = "Would I be a good fit for Google as a senior Python engineer?"
        
        result = await connecting_node(base_state)
        
        assert result["query_analysis"]["confidence"] >= 0.8
    
    @pytest.mark.asyncio
    async def test_low_confidence_for_vague_query(self, base_state):
        """
        Test: Vague queries receive lower confidence scores
        Input: "What about jobs?"
        Expected: confidence < 0.5
        """
        base_state["query"] = "What about jobs?"
        
        result = await connecting_node(base_state)
        
        assert result["query_analysis"]["confidence"] < 0.5
    
    # ============================================================
    # SSE EMISSION TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_emits_connecting_status_event(self, base_state):
        """
        Test: Status event emitted at phase start
        """
        base_state["query"] = "Would I be a good fit for Google?"
        events_emitted = []
        
        with patch('services.fit_check_agent.emit_sse_event') as mock_emit:
            mock_emit.side_effect = lambda e: events_emitted.append(e)
            await connecting_node(base_state)
        
        status_events = [e for e in events_emitted if e["type"] == "status"]
        assert any("CONNECTING" in str(e) for e in status_events)
    
    @pytest.mark.asyncio
    async def test_emits_thought_events(self, base_state):
        """
        Test: Thought events emitted during processing
        """
        base_state["query"] = "Would I be a good fit for Google?"
        events_emitted = []
        
        with patch('services.fit_check_agent.emit_sse_event') as mock_emit:
            mock_emit.side_effect = lambda e: events_emitted.append(e)
            await connecting_node(base_state)
        
        thought_events = [e for e in events_emitted if e["type"] == "thought"]
        assert len(thought_events) >= 1
    
    # ============================================================
    # ERROR HANDLING TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_handles_empty_query(self, base_state):
        """
        Test: Empty queries are handled gracefully
        Input: ""
        Expected: error state populated, no crash
        """
        base_state["query"] = ""
        
        result = await connecting_node(base_state)
        
        assert result["error"] is not None or result["query_analysis"]["query_type"] == "invalid"
    
    @pytest.mark.asyncio
    async def test_handles_llm_failure(self, base_state):
        """
        Test: LLM failures are handled gracefully
        """
        base_state["query"] = "Would I be a good fit for Google?"
        
        with patch('services.fit_check_agent.get_llm') as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))
            result = await connecting_node(base_state)
        
        assert result["error"] is not None
```

### 1.2 DEEP_RESEARCH_NODE Tests

```python
# tests/unit/test_deep_research_node.py
"""
Unit tests for DEEP_RESEARCH node - Web Intelligence Gathering
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.fit_check_agent import deep_research_node
from services.tools.web_search import web_search

class TestDeepResearchNode:
    """Test suite for DEEP_RESEARCH node functionality."""
    
    @pytest.fixture
    def research_ready_state(self) -> dict:
        """State ready for research phase."""
        return {
            "messages": [],
            "query": "Would I be a good fit for Google?",
            "current_phase": "DEEP_RESEARCH",
            "query_analysis": {
                "query_type": "company_fit",
                "entities": {
                    "company_name": "Google",
                    "role_title": "Software Engineer"
                },
                "confidence": 0.9,
                "research_priorities": ["company culture", "tech stack", "hiring requirements"]
            },
            "research_results": None,
            "skeptical_analysis": None,
            "skills_analysis": None,
            "final_response": None,
            "error": None,
            "metadata": {}
        }
    
    # ============================================================
    # SEARCH GENERATION TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_generates_relevant_search_queries(self, research_ready_state):
        """
        Test: Search queries are relevant to query analysis
        """
        with patch('services.tools.web_search.web_search') as mock_search:
            mock_search.return_value = {"results": []}
            await deep_research_node(research_ready_state)
            
            # Verify search was called with relevant terms
            call_args = [str(call) for call in mock_search.call_args_list]
            assert any("Google" in arg for arg in call_args)
    
    @pytest.mark.asyncio
    async def test_prioritizes_searches_by_query_type(self, research_ready_state):
        """
        Test: Company queries prioritize company-specific searches
        """
        search_queries_executed = []
        
        with patch('services.tools.web_search.web_search') as mock_search:
            mock_search.side_effect = lambda q: search_queries_executed.append(q) or {"results": []}
            await deep_research_node(research_ready_state)
        
        # First searches should be company-focused
        assert any("hiring" in q.lower() or "culture" in q.lower() for q in search_queries_executed[:3])
    
    # ============================================================
    # RESULT SYNTHESIS TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_synthesizes_search_results(self, research_ready_state):
        """
        Test: Multiple search results are synthesized into coherent intelligence
        """
        mock_results = {
            "results": [
                {"title": "Google Hiring", "snippet": "Google seeks Python experts"},
                {"title": "Google Culture", "snippet": "Innovation-focused environment"}
            ]
        }
        
        with patch('services.tools.web_search.web_search', return_value=mock_results):
            result = await deep_research_node(research_ready_state)
        
        assert result["research_results"] is not None
        assert "synthesis" in result["research_results"]
    
    @pytest.mark.asyncio
    async def test_handles_no_search_results(self, research_ready_state):
        """
        Test: Empty search results are handled gracefully
        """
        with patch('services.tools.web_search.web_search', return_value={"results": []}):
            result = await deep_research_node(research_ready_state)
        
        # Should still proceed with available engineer profile data
        assert result["current_phase"] == "SKEPTICAL_COMPARISON"
        assert result["research_results"]["source"] == "profile_only"
    
    # ============================================================
    # CREDIBILITY SCORING TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_scores_source_credibility(self, research_ready_state):
        """
        Test: Sources are scored for credibility
        """
        mock_results = {
            "results": [
                {"title": "Official Google Careers", "url": "https://careers.google.com", "snippet": "..."},
                {"title": "Random Blog", "url": "https://random-blog.com", "snippet": "..."}
            ]
        }
        
        with patch('services.tools.web_search.web_search', return_value=mock_results):
            result = await deep_research_node(research_ready_state)
        
        sources = result["research_results"]["sources"]
        official_source = next(s for s in sources if "google.com" in s["url"])
        blog_source = next(s for s in sources if "random-blog" in s["url"])
        
        assert official_source["credibility_score"] > blog_source["credibility_score"]
```

### 1.3 SKEPTICAL_COMPARISON_NODE Tests

```python
# tests/unit/test_skeptical_comparison_node.py
"""
Unit tests for SKEPTICAL_COMPARISON node - Devil's Advocate Analysis
"""
import pytest
from unittest.mock import patch, AsyncMock
from services.fit_check_agent import skeptical_comparison_node

class TestSkepticalComparisonNode:
    """Test suite for SKEPTICAL_COMPARISON node functionality."""
    
    @pytest.fixture
    def comparison_ready_state(self) -> dict:
        """State ready for skeptical comparison phase."""
        return {
            "messages": [],
            "query": "Would I be a good fit for Google?",
            "current_phase": "SKEPTICAL_COMPARISON",
            "query_analysis": {
                "query_type": "company_fit",
                "entities": {"company_name": "Google"},
                "confidence": 0.9
            },
            "research_results": {
                "synthesis": "Google requires strong distributed systems experience...",
                "key_requirements": ["distributed systems", "system design", "Python"],
                "culture_notes": "Fast-paced, innovation-driven",
                "sources": []
            },
            "skeptical_analysis": None,
            "skills_analysis": None,
            "final_response": None,
            "error": None,
            "metadata": {}
        }
    
    # ============================================================
    # GAP ANALYSIS TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_identifies_skill_gaps(self, comparison_ready_state):
        """
        Test: Skill gaps are identified between profile and requirements
        """
        result = await skeptical_comparison_node(comparison_ready_state)
        
        assert "gaps" in result["skeptical_analysis"]
        assert isinstance(result["skeptical_analysis"]["gaps"], list)
    
    @pytest.mark.asyncio
    async def test_provides_gap_severity_ratings(self, comparison_ready_state):
        """
        Test: Each gap has a severity rating
        """
        result = await skeptical_comparison_node(comparison_ready_state)
        
        for gap in result["skeptical_analysis"]["gaps"]:
            assert "severity" in gap
            assert gap["severity"] in ["critical", "moderate", "minor"]
    
    @pytest.mark.asyncio
    async def test_provides_mitigation_strategies(self, comparison_ready_state):
        """
        Test: Each gap has mitigation strategies
        """
        result = await skeptical_comparison_node(comparison_ready_state)
        
        for gap in result["skeptical_analysis"]["gaps"]:
            assert "mitigation" in gap
            assert len(gap["mitigation"]) > 0
    
    # ============================================================
    # HONEST ASSESSMENT TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_provides_honest_fit_assessment(self, comparison_ready_state):
        """
        Test: Fit assessment is honest and not always positive
        """
        result = await skeptical_comparison_node(comparison_ready_state)
        
        assert "fit_assessment" in result["skeptical_analysis"]
        assert result["skeptical_analysis"]["fit_assessment"]["score"] <= 100
        assert result["skeptical_analysis"]["fit_assessment"]["score"] >= 0
    
    @pytest.mark.asyncio
    async def test_includes_dealbreaker_flags(self, comparison_ready_state):
        """
        Test: Critical mismatches are flagged as potential dealbreakers
        """
        result = await skeptical_comparison_node(comparison_ready_state)
        
        assert "dealbreakers" in result["skeptical_analysis"]
    
    # ============================================================
    # COUNTERARGUMENT TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_generates_counterarguments(self, comparison_ready_state):
        """
        Test: Counterarguments to weaknesses are provided
        """
        result = await skeptical_comparison_node(comparison_ready_state)
        
        assert "counterarguments" in result["skeptical_analysis"]
```

### 1.4 SKILLS_MATCHING_NODE Tests

```python
# tests/unit/test_skills_matching_node.py
"""
Unit tests for SKILLS_MATCHING node - Tool-Based Analysis
"""
import pytest
from unittest.mock import patch, AsyncMock
from services.fit_check_agent import skills_matching_node

class TestSkillsMatchingNode:
    """Test suite for SKILLS_MATCHING node functionality."""
    
    @pytest.fixture
    def matching_ready_state(self) -> dict:
        """State ready for skills matching phase."""
        return {
            "messages": [],
            "query": "Would I be a good fit for Google?",
            "current_phase": "SKILLS_MATCHING",
            "query_analysis": {
                "query_type": "company_fit",
                "entities": {"company_name": "Google"},
                "confidence": 0.9
            },
            "research_results": {
                "key_requirements": ["Python", "distributed systems", "API design"]
            },
            "skeptical_analysis": {
                "gaps": [{"skill": "distributed systems", "severity": "moderate"}],
                "fit_assessment": {"score": 75}
            },
            "skills_analysis": None,
            "final_response": None,
            "error": None,
            "metadata": {}
        }
    
    # ============================================================
    # TOOL INVOCATION TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_invokes_skill_matcher_tool(self, matching_ready_state):
        """
        Test: analyze_skill_match tool is invoked
        """
        with patch('services.fit_check_agent.analyze_skill_match') as mock_tool:
            mock_tool.return_value = {"matches": [], "score": 80}
            await skills_matching_node(matching_ready_state)
            
            mock_tool.assert_called()
    
    @pytest.mark.asyncio
    async def test_invokes_experience_matcher_tool(self, matching_ready_state):
        """
        Test: analyze_experience_relevance tool is invoked
        """
        with patch('services.fit_check_agent.analyze_experience_relevance') as mock_tool:
            mock_tool.return_value = {"relevance_score": 85, "highlights": []}
            await skills_matching_node(matching_ready_state)
            
            mock_tool.assert_called()
    
    # ============================================================
    # MATCH SCORING TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_produces_skill_match_scores(self, matching_ready_state):
        """
        Test: Individual skill match scores are produced
        """
        result = await skills_matching_node(matching_ready_state)
        
        assert "skill_scores" in result["skills_analysis"]
        for skill_score in result["skills_analysis"]["skill_scores"]:
            assert "skill" in skill_score
            assert "score" in skill_score
            assert 0 <= skill_score["score"] <= 100
    
    @pytest.mark.asyncio
    async def test_produces_experience_relevance_scores(self, matching_ready_state):
        """
        Test: Experience relevance scores are produced
        """
        result = await skills_matching_node(matching_ready_state)
        
        assert "experience_scores" in result["skills_analysis"]
    
    @pytest.mark.asyncio
    async def test_produces_aggregate_match_score(self, matching_ready_state):
        """
        Test: Aggregate match score is calculated
        """
        result = await skills_matching_node(matching_ready_state)
        
        assert "aggregate_score" in result["skills_analysis"]
        assert 0 <= result["skills_analysis"]["aggregate_score"] <= 100
    
    # ============================================================
    # EVIDENCE LINKING TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_links_evidence_to_scores(self, matching_ready_state):
        """
        Test: Scores are backed by specific evidence from profile
        """
        result = await skills_matching_node(matching_ready_state)
        
        for skill_score in result["skills_analysis"]["skill_scores"]:
            assert "evidence" in skill_score
            assert len(skill_score["evidence"]) > 0
```

### 1.5 GENERATE_RESULTS_NODE Tests

```python
# tests/unit/test_generate_results_node.py
"""
Unit tests for GENERATE_RESULTS node - Response Synthesis
"""
import pytest
from unittest.mock import patch, AsyncMock
from services.fit_check_agent import generate_results_node

class TestGenerateResultsNode:
    """Test suite for GENERATE_RESULTS node functionality."""
    
    @pytest.fixture
    def generation_ready_state(self) -> dict:
        """State ready for results generation phase."""
        return {
            "messages": [],
            "query": "Would I be a good fit for Google?",
            "current_phase": "GENERATE_RESULTS",
            "query_analysis": {
                "query_type": "company_fit",
                "entities": {"company_name": "Google"},
                "confidence": 0.9
            },
            "research_results": {
                "synthesis": "Google requires distributed systems expertise...",
                "key_requirements": ["Python", "distributed systems"]
            },
            "skeptical_analysis": {
                "gaps": [{"skill": "distributed systems", "severity": "moderate", "mitigation": ["..."]}],
                "fit_assessment": {"score": 75, "reasoning": "..."},
                "counterarguments": ["Strong Python experience..."]
            },
            "skills_analysis": {
                "skill_scores": [{"skill": "Python", "score": 95, "evidence": ["..."]}],
                "experience_scores": [{"area": "Backend", "score": 88}],
                "aggregate_score": 82
            },
            "final_response": None,
            "error": None,
            "metadata": {}
        }
    
    # ============================================================
    # RESPONSE STRUCTURE TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_generates_structured_response(self, generation_ready_state):
        """
        Test: Response follows expected structure
        """
        result = await generate_results_node(generation_ready_state)
        
        response = result["final_response"]
        assert "summary" in response
        assert "strengths" in response
        assert "growth_areas" in response
        assert "recommendations" in response
    
    @pytest.mark.asyncio
    async def test_includes_fit_score(self, generation_ready_state):
        """
        Test: Overall fit score is included
        """
        result = await generate_results_node(generation_ready_state)
        
        assert "fit_score" in result["final_response"]
        assert 0 <= result["final_response"]["fit_score"] <= 100
    
    # ============================================================
    # STREAMING TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_streams_response_tokens(self, generation_ready_state):
        """
        Test: Response is streamed token by token
        """
        tokens_streamed = []
        
        with patch('services.fit_check_agent.stream_response') as mock_stream:
            async def mock_stream_fn(text):
                for token in text.split():
                    tokens_streamed.append(token)
                    yield token
            
            mock_stream.side_effect = mock_stream_fn
            await generate_results_node(generation_ready_state)
        
        assert len(tokens_streamed) > 0
    
    @pytest.mark.asyncio
    async def test_emits_response_sse_events(self, generation_ready_state):
        """
        Test: SSE response events are emitted during streaming
        """
        events_emitted = []
        
        with patch('services.fit_check_agent.emit_sse_event') as mock_emit:
            mock_emit.side_effect = lambda e: events_emitted.append(e)
            await generate_results_node(generation_ready_state)
        
        response_events = [e for e in events_emitted if e["type"] == "response"]
        assert len(response_events) > 0
    
    # ============================================================
    # COMPLETE EVENT TESTS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_emits_complete_event(self, generation_ready_state):
        """
        Test: Complete event is emitted after response
        """
        events_emitted = []
        
        with patch('services.fit_check_agent.emit_sse_event') as mock_emit:
            mock_emit.side_effect = lambda e: events_emitted.append(e)
            await generate_results_node(generation_ready_state)
        
        complete_events = [e for e in events_emitted if e["type"] == "complete"]
        assert len(complete_events) == 1
    
    @pytest.mark.asyncio
    async def test_complete_event_includes_metadata(self, generation_ready_state):
        """
        Test: Complete event includes processing metadata
        """
        events_emitted = []
        
        with patch('services.fit_check_agent.emit_sse_event') as mock_emit:
            mock_emit.side_effect = lambda e: events_emitted.append(e)
            await generate_results_node(generation_ready_state)
        
        complete_event = next(e for e in events_emitted if e["type"] == "complete")
        assert "total_duration_ms" in complete_event["data"]
        assert "phases_completed" in complete_event["data"]
```

---

## 2. Integration Test Specifications

### 2.1 Workflow Transition Tests

```python
# tests/integration/test_workflow_transitions.py
"""
Integration tests for workflow state transitions
"""
import pytest
from services.fit_check_agent import create_fit_check_graph, FitCheckState

class TestWorkflowTransitions:
    """Test suite for workflow state machine transitions."""
    
    @pytest.fixture
    def graph(self):
        """Create the workflow graph."""
        return create_fit_check_graph()
    
    # ============================================================
    # HAPPY PATH TRANSITIONS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_full_workflow_execution(self, graph):
        """
        Test: Complete workflow executes all phases in order
        """
        initial_state: FitCheckState = {
            "messages": [],
            "query": "Would I be a good fit for Google as a Python developer?",
            "current_phase": "CONNECTING",
            # ... other initial state
        }
        
        phases_visited = []
        
        async for state in graph.astream(initial_state):
            phases_visited.append(state.get("current_phase"))
        
        expected_order = [
            "CONNECTING",
            "DEEP_RESEARCH",
            "SKEPTICAL_COMPARISON",
            "SKILLS_MATCHING",
            "GENERATE_RESULTS",
            "COMPLETE"
        ]
        
        assert phases_visited == expected_order
    
    @pytest.mark.asyncio
    async def test_state_accumulation_through_phases(self, graph):
        """
        Test: State accumulates correctly through workflow
        """
        initial_state: FitCheckState = {
            "messages": [],
            "query": "Would I be a good fit for Google?",
            "current_phase": "CONNECTING",
        }
        
        final_state = None
        async for state in graph.astream(initial_state):
            final_state = state
        
        # Verify all analysis components are populated
        assert final_state["query_analysis"] is not None
        assert final_state["research_results"] is not None
        assert final_state["skeptical_analysis"] is not None
        assert final_state["skills_analysis"] is not None
        assert final_state["final_response"] is not None
    
    # ============================================================
    # ERROR RECOVERY TRANSITIONS
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_error_transitions_to_error_handler(self, graph):
        """
        Test: Errors transition to error handling state
        """
        initial_state: FitCheckState = {
            "messages": [],
            "query": "",  # Invalid query
            "current_phase": "CONNECTING",
        }
        
        final_state = None
        async for state in graph.astream(initial_state):
            final_state = state
        
        assert final_state["error"] is not None
        assert final_state["current_phase"] == "ERROR"
    
    @pytest.mark.asyncio
    async def test_recovers_from_research_failure(self, graph):
        """
        Test: Workflow continues even if research fails
        """
        initial_state: FitCheckState = {
            "messages": [],
            "query": "Would I be a good fit for NonExistentCompany123?",
            "current_phase": "CONNECTING",
        }
        
        with patch('services.tools.web_search.web_search', return_value={"results": []}):
            final_state = None
            async for state in graph.astream(initial_state):
                final_state = state
        
        # Should still complete with profile-only analysis
        assert final_state["final_response"] is not None
```

### 2.2 SSE Streaming Integration Tests

```python
# tests/integration/test_sse_streaming.py
"""
Integration tests for SSE event streaming
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from server import app

class TestSSEStreaming:
    """Test suite for SSE streaming functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    # ============================================================
    # EVENT FORMAT TESTS
    # ============================================================
    
    def test_sse_event_format(self, client):
        """
        Test: SSE events follow correct format
        """
        response = client.post(
            "/api/fit-check/stream",
            json={"query": "Would I be a good fit for Google?"},
            stream=True
        )
        
        events = list(response.iter_lines())
        
        for event in events:
            if event.startswith(b"data:"):
                data = json.loads(event[5:])
                assert "type" in data
                assert data["type"] in ["status", "thought", "response", "complete", "error"]
    
    def test_status_events_include_phase(self, client):
        """
        Test: Status events include current phase
        """
        response = client.post(
            "/api/fit-check/stream",
            json={"query": "Would I be a good fit for Google?"},
            stream=True
        )
        
        status_events = []
        for event in response.iter_lines():
            if event.startswith(b"data:"):
                data = json.loads(event[5:])
                if data["type"] == "status":
                    status_events.append(data)
        
        phases_seen = [e["phase"] for e in status_events]
        assert "CONNECTING" in phases_seen
        assert "DEEP_RESEARCH" in phases_seen
    
    # ============================================================
    # THOUGHT EVENT TESTS
    # ============================================================
    
    def test_thought_events_have_content(self, client):
        """
        Test: Thought events contain meaningful content
        """
        response = client.post(
            "/api/fit-check/stream",
            json={"query": "Would I be a good fit for Google?"},
            stream=True
        )
        
        for event in response.iter_lines():
            if event.startswith(b"data:"):
                data = json.loads(event[5:])
                if data["type"] == "thought":
                    assert "content" in data
                    assert len(data["content"]) > 0
    
    # ============================================================
    # COMPLETE EVENT TESTS
    # ============================================================
    
    def test_complete_event_is_last(self, client):
        """
        Test: Complete event is the last event
        """
        response = client.post(
            "/api/fit-check/stream",
            json={"query": "Would I be a good fit for Google?"},
            stream=True
        )
        
        events = []
        for event in response.iter_lines():
            if event.startswith(b"data:"):
                events.append(json.loads(event[5:]))
        
        assert events[-1]["type"] == "complete"
    
    def test_complete_event_has_full_response(self, client):
        """
        Test: Complete event contains full response
        """
        response = client.post(
            "/api/fit-check/stream",
            json={"query": "Would I be a good fit for Google?"},
            stream=True
        )
        
        complete_event = None
        for event in response.iter_lines():
            if event.startswith(b"data:"):
                data = json.loads(event[5:])
                if data["type"] == "complete":
                    complete_event = data
        
        assert "full_response" in complete_event
        assert "strengths" in complete_event["full_response"]
        assert "growth_areas" in complete_event["full_response"]
```

### 2.3 End-to-End Tests

```python
# tests/integration/test_end_to_end.py
"""
End-to-end tests for the complete fit check workflow
"""
import pytest
from fastapi.testclient import TestClient
from server import app

class TestEndToEnd:
    """End-to-end test suite."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    # ============================================================
    # QUERY TYPE SCENARIOS
    # ============================================================
    
    @pytest.mark.parametrize("query,expected_type", [
        ("Would I be a good fit for Google?", "company_fit"),
        ("Am I suited for a senior backend role?", "role_fit"),
        ("How do my Python skills compare?", "skill_assessment"),
        ("Would I fit in the fintech industry?", "industry_fit"),
    ])
    def test_handles_different_query_types(self, client, query, expected_type):
        """
        Test: Different query types are handled correctly
        """
        response = client.post(
            "/api/fit-check/stream",
            json={"query": query},
            stream=True
        )
        
        events = [json.loads(e[5:]) for e in response.iter_lines() if e.startswith(b"data:")]
        complete = events[-1]
        
        assert complete["type"] == "complete"
        assert complete["metadata"]["query_type"] == expected_type
    
    # ============================================================
    # RESPONSE QUALITY TESTS
    # ============================================================
    
    def test_response_addresses_query(self, client):
        """
        Test: Response directly addresses the user's query
        """
        query = "Would I be a good fit for Microsoft as a cloud engineer?"
        
        response = client.post(
            "/api/fit-check/stream",
            json={"query": query},
            stream=True
        )
        
        events = [json.loads(e[5:]) for e in response.iter_lines() if e.startswith(b"data:")]
        complete = events[-1]
        
        full_response = complete["full_response"]["summary"]
        assert "Microsoft" in full_response or "cloud" in full_response.lower()
    
    def test_response_includes_actionable_recommendations(self, client):
        """
        Test: Response includes actionable recommendations
        """
        response = client.post(
            "/api/fit-check/stream",
            json={"query": "Would I be a good fit for Google?"},
            stream=True
        )
        
        events = [json.loads(e[5:]) for e in response.iter_lines() if e.startswith(b"data:")]
        complete = events[-1]
        
        recommendations = complete["full_response"]["recommendations"]
        assert len(recommendations) >= 2
        for rec in recommendations:
            assert "action" in rec or len(rec) > 20  # Substantive recommendations
    
    # ============================================================
    # PERFORMANCE TESTS
    # ============================================================
    
    def test_completes_within_timeout(self, client):
        """
        Test: Workflow completes within acceptable time
        """
        import time
        
        start = time.time()
        response = client.post(
            "/api/fit-check/stream",
            json={"query": "Would I be a good fit for Google?"},
            stream=True
        )
        
        # Consume all events
        list(response.iter_lines())
        
        duration = time.time() - start
        assert duration < 60  # Should complete within 60 seconds
    
    def test_first_event_arrives_quickly(self, client):
        """
        Test: First SSE event arrives within 2 seconds
        """
        import time
        
        start = time.time()
        response = client.post(
            "/api/fit-check/stream",
            json={"query": "Would I be a good fit for Google?"},
            stream=True
        )
        
        # Get first event
        for _ in response.iter_lines():
            break
        
        time_to_first = time.time() - start
        assert time_to_first < 2.0
```

---

## 3. Test Fixtures & Mocks

### 3.1 Sample Queries Fixture

```python
# tests/fixtures/sample_queries.py
"""
Sample queries for testing various scenarios
"""

COMPANY_FIT_QUERIES = [
    "Would I be a good fit for Google?",
    "Am I suited for a position at Microsoft?",
    "How well would I fit at Amazon Web Services?",
    "Would Netflix hire someone like me?",
    "Do I match Meta's engineering requirements?",
]

ROLE_FIT_QUERIES = [
    "Am I ready for a senior backend engineer position?",
    "Would I succeed as a tech lead?",
    "Do I have what it takes to be a principal engineer?",
    "Am I suited for a full-stack developer role?",
    "Would I be a good fit for a DevOps engineer position?",
]

SKILL_ASSESSMENT_QUERIES = [
    "How do my Python skills compare to industry standards?",
    "Is my experience with React sufficient for modern frontend roles?",
    "Do I have enough cloud experience for senior positions?",
    "How does my system design knowledge stack up?",
    "Are my API design skills competitive?",
]

INDUSTRY_FIT_QUERIES = [
    "Would I fit well in the fintech industry?",
    "Am I suited for healthcare technology companies?",
    "Do my skills align with the gaming industry?",
    "Would I be a good match for cybersecurity companies?",
    "How well would I fit in the AI/ML industry?",
]

EDGE_CASE_QUERIES = [
    "",  # Empty query
    "?",  # Single character
    "What" * 500,  # Very long query
    "Would I fit at 会社名?",  # Unicode characters
    "Am I good for $COMPANY?",  # Template-like query
]
```

### 3.2 Mock Responses Fixture

```python
# tests/fixtures/mock_responses.py
"""
Mock responses for testing
"""

MOCK_WEB_SEARCH_RESULTS = {
    "google": {
        "results": [
            {
                "title": "Google Careers - Software Engineering",
                "url": "https://careers.google.com/",
                "snippet": "Google seeks passionate engineers with strong CS fundamentals..."
            },
            {
                "title": "Google's Engineering Culture",
                "url": "https://engineering.google.com/",
                "snippet": "Innovation-driven environment with emphasis on collaboration..."
            }
        ]
    },
    "empty": {
        "results": []
    }
}

MOCK_SKILL_MATCH_RESULTS = {
    "high_match": {
        "matches": [
            {"skill": "Python", "score": 95, "evidence": ["5+ years experience"]},
            {"skill": "API Design", "score": 90, "evidence": ["RESTful API projects"]},
        ],
        "overall_score": 92
    },
    "low_match": {
        "matches": [
            {"skill": "Python", "score": 40, "evidence": ["Limited experience"]},
        ],
        "overall_score": 40
    }
}

MOCK_EXPERIENCE_RESULTS = {
    "relevant": {
        "relevance_score": 85,
        "highlights": [
            "Backend development at scale",
            "Distributed systems experience"
        ]
    },
    "not_relevant": {
        "relevance_score": 30,
        "highlights": []
    }
}
```

---

## 4. Test Configuration

### 4.1 pytest.ini Updates

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests (> 10s)
filterwarnings =
    ignore::DeprecationWarning
addopts = -v --tb=short --strict-markers
```

### 4.2 conftest.py Updates

```python
# tests/conftest.py
"""
Pytest configuration and shared fixtures
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Generator

# ============================================================
# ASYNC FIXTURES
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# ============================================================
# MOCK FIXTURES
# ============================================================

@pytest.fixture
def mock_llm():
    """Mock LLM for testing without API calls."""
    with patch('config.llm.get_llm') as mock:
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(return_value="Mock response")
        mock.return_value = mock_llm
        yield mock_llm

@pytest.fixture
def mock_web_search():
    """Mock web search for testing without external calls."""
    with patch('services.tools.web_search.web_search') as mock:
        mock.return_value = MOCK_WEB_SEARCH_RESULTS["google"]
        yield mock

@pytest.fixture
def mock_skill_matcher():
    """Mock skill matcher tool."""
    with patch('services.tools.skill_matcher.analyze_skill_match') as mock:
        mock.return_value = MOCK_SKILL_MATCH_RESULTS["high_match"]
        yield mock

@pytest.fixture
def mock_experience_matcher():
    """Mock experience matcher tool."""
    with patch('services.tools.experience_matcher.analyze_experience_relevance') as mock:
        mock.return_value = MOCK_EXPERIENCE_RESULTS["relevant"]
        yield mock

# ============================================================
# STATE FIXTURES
# ============================================================

@pytest.fixture
def empty_state() -> dict:
    """Create empty initial state."""
    return {
        "messages": [],
        "query": "",
        "current_phase": "CONNECTING",
        "query_analysis": None,
        "research_results": None,
        "skeptical_analysis": None,
        "skills_analysis": None,
        "final_response": None,
        "error": None,
        "metadata": {}
    }

@pytest.fixture
def populated_state() -> dict:
    """Create fully populated state for testing late phases."""
    return {
        "messages": [],
        "query": "Would I be a good fit for Google?",
        "current_phase": "GENERATE_RESULTS",
        "query_analysis": {
            "query_type": "company_fit",
            "entities": {"company_name": "Google"},
            "confidence": 0.9
        },
        "research_results": {
            "synthesis": "Google requires...",
            "key_requirements": ["Python", "distributed systems"]
        },
        "skeptical_analysis": {
            "gaps": [],
            "fit_assessment": {"score": 80}
        },
        "skills_analysis": {
            "skill_scores": [{"skill": "Python", "score": 95}],
            "aggregate_score": 85
        },
        "final_response": None,
        "error": None,
        "metadata": {}
    }
```

---

## 5. Validation Checklist

### 5.1 Pre-Deployment Validation

```markdown
## Pre-Deployment Validation Checklist

### Unit Tests
- [ ] All CONNECTING node tests pass
- [ ] All DEEP_RESEARCH node tests pass
- [ ] All SKEPTICAL_COMPARISON node tests pass
- [ ] All SKILLS_MATCHING node tests pass
- [ ] All GENERATE_RESULTS node tests pass
- [ ] State management tests pass
- [ ] Error handling tests pass

### Integration Tests
- [ ] Workflow transitions complete successfully
- [ ] SSE events are properly formatted
- [ ] All event types are emitted correctly
- [ ] State accumulates through phases
- [ ] Error recovery works as expected

### End-to-End Tests
- [ ] Company fit queries work correctly
- [ ] Role fit queries work correctly
- [ ] Skill assessment queries work correctly
- [ ] Industry fit queries work correctly
- [ ] Edge cases are handled gracefully
- [ ] Performance requirements met

### SSE Contract Validation
- [ ] Status events include phase information
- [ ] Thought events have meaningful content
- [ ] Response events stream correctly
- [ ] Complete event is last event
- [ ] Error events provide useful information

### Manual Validation
- [ ] Test with real Google API key
- [ ] Verify response quality with human review
- [ ] Check frontend displays all phases correctly
- [ ] Verify thinking timeline updates properly
- [ ] Confirm comparison chain shows completion
```

### 5.2 Running the Test Suite

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov=routers --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_connecting_node.py

# Run tests matching pattern
pytest -k "test_classifies"
```

---

## 6. Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Unit Test Coverage | ≥ 85% | pytest-cov |
| Integration Test Pass Rate | 100% | pytest |
| E2E Test Pass Rate | ≥ 95% | pytest |
| Time to First Event | < 2s | Performance test |
| Total Workflow Time | < 60s | Performance test |
| Error Recovery Success | 100% | Error handling tests |

---

## 7. Build Verification Gate

> ⛔ **STOP**: The system is NOT ready for deployment until all tests pass.

### Full Test Suite Verification

```powershell
# Navigate to backend directory
cd res_backend

# Run all unit tests
pytest tests/unit/ -v

# Run all integration tests
pytest tests/integration/ -v

# Run with coverage
pytest --cov=services --cov=routers --cov-report=html --cov-report=term

# Run tests multiple times to check for flakiness
pytest --count=3
```

### Frontend Verification

```powershell
# Navigate to frontend directory
cd res_web

# Full build
npm run build

# Run frontend tests (if any)
npm test
```

### Verification Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Code coverage ≥ 85%
- [ ] No flaky tests (pass 3x consistently)
- [ ] Backend builds without errors
- [ ] Frontend builds without errors
- [ ] Docker container builds successfully

---

## 8. Requirements Tracking

> 📋 **IMPORTANT**: Refer to **[TRACK_ALL_REQUIREMENTS.md](./TRACK_ALL_REQUIREMENTS.md)** for the complete requirements checklist.

### After Completing This Phase:

1. Open `TRACK_ALL_REQUIREMENTS.md`
2. Locate the **Phase 7: Testing & Validation** section
3. Mark each completed requirement with ✅
4. Fill in the "Verified By" and "Date" columns
5. Complete the **Build Verification** checkboxes
6. Update the **Completion Summary** table at the bottom
7. Verify **Cross-Phase Requirements** (SSE, Performance, Error Handling)

### Phase 7 Requirement IDs to Update:

- P7-001 through P7-012
- SSE-001 through SSE-007
- PERF-001 through PERF-004
- ERR-001 through ERR-005

---

## Next Phase

Proceed to **production deployment** after all tests pass and the validation checklist in `TRACK_ALL_REQUIREMENTS.md` shows 100% completion.

---

*Document Version: 1.1 | Phase 7 of 7 | Testing & Validation*
