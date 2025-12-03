# Requirements Tracking Document

## Overview

This document tracks all implementation requirements across all phases of the Multi-Agent Fit Check System upgrade. Each requirement must be verified, tested, and marked complete before proceeding.

**CRITICAL**: This document is the single source of truth for implementation progress. Update this document immediately after completing each requirement.

---

## Status Legend

| Symbol | Status | Description |
|--------|--------|-------------|
| ⬜ | Not Started | Requirement not yet begun |
| 🔄 | In Progress | Currently being implemented |
| ✅ | Complete | Implemented, tested, and verified |
| ❌ | Blocked | Cannot proceed due to dependency |
| ⚠️ | Needs Review | Implementation complete, needs verification |

---

## Phase 0: Architecture Overview

### Requirements

| ID | Requirement | Status | Verified By | Date |
|----|-------------|--------|-------------|------|
| P0-001 | FitCheckState TypedDict defined with all fields | ⬜ | | |
| P0-002 | State schema includes messages, query, current_phase | ⬜ | | |
| P0-003 | State schema includes query_analysis field | ⬜ | | |
| P0-004 | State schema includes research_results field | ⬜ | | |
| P0-005 | State schema includes skeptical_analysis field | ⬜ | | |
| P0-006 | State schema includes skills_analysis field | ⬜ | | |
| P0-007 | State schema includes final_response field | ⬜ | | |
| P0-008 | State schema includes error field | ⬜ | | |
| P0-009 | State schema includes metadata field | ⬜ | | |
| P0-010 | Graph structure defined with 5 nodes | ⬜ | | |
| P0-011 | SSE event types defined (status, thought, response, complete, error) | ⬜ | | |
| P0-012 | Phase enum defined with all phases | ⬜ | | |

### Build Verification
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `python -c "from models.fit_check import FitCheckState"` succeeds
- [ ] No import errors in fit_check_agent.py

---

## Phase 1: CONNECTING Node

### Requirements

| ID | Requirement | Status | Verified By | Date |
|----|-------------|--------|-------------|------|
| P1-001 | connecting_node function implemented | ⬜ | | |
| P1-002 | Query classification logic (5 types) | ⬜ | | |
| P1-003 | Entity extraction (company, role, skills, industry) | ⬜ | | |
| P1-004 | Confidence scoring (0.0-1.0) | ⬜ | | |
| P1-005 | Research priorities generation | ⬜ | | |
| P1-006 | QueryAnalysis Pydantic model defined | ⬜ | | |
| P1-007 | SSE status event emitted at phase start | ⬜ | | |
| P1-008 | SSE thought events emitted during processing | ⬜ | | |
| P1-009 | State transition to DEEP_RESEARCH on success | ⬜ | | |
| P1-010 | Error handling for empty query | ⬜ | | |
| P1-011 | Error handling for LLM failure | ⬜ | | |
| P1-012 | System prompt loaded from file | ⬜ | | |

### Build Verification
- [ ] `pytest tests/unit/test_connecting_node.py` passes
- [ ] No syntax errors in connecting_node function
- [ ] Import statement works: `from services.fit_check_agent import connecting_node`

---

## Phase 2: DEEP_RESEARCH Node

### Requirements

| ID | Requirement | Status | Verified By | Date |
|----|-------------|--------|-------------|------|
| P2-001 | deep_research_node function implemented | ⬜ | | |
| P2-002 | Search query generation based on query_analysis | ⬜ | | |
| P2-003 | web_search tool integration | ⬜ | | |
| P2-004 | Result synthesis logic | ⬜ | | |
| P2-005 | Source credibility scoring | ⬜ | | |
| P2-006 | ResearchResults Pydantic model defined | ⬜ | | |
| P2-007 | SSE status event emitted at phase start | ⬜ | | |
| P2-008 | SSE thought events for each search | ⬜ | | |
| P2-009 | State transition to SKEPTICAL_COMPARISON | ⬜ | | |
| P2-010 | Graceful handling of no search results | ⬜ | | |
| P2-011 | Profile-only fallback when search fails | ⬜ | | |
| P2-012 | Research priorities respected in search order | ⬜ | | |

### Build Verification
- [ ] `pytest tests/unit/test_deep_research_node.py` passes
- [ ] web_search tool callable without errors
- [ ] Import statement works: `from services.fit_check_agent import deep_research_node`

---

## Phase 3: SKEPTICAL_COMPARISON Node

### Requirements

| ID | Requirement | Status | Verified By | Date |
|----|-------------|--------|-------------|------|
| P3-001 | skeptical_comparison_node function implemented | ⬜ | | |
| P3-002 | Gap analysis logic (profile vs requirements) | ⬜ | | |
| P3-003 | Gap severity classification (critical, moderate, minor) | ⬜ | | |
| P3-004 | Mitigation strategy generation per gap | ⬜ | | |
| P3-005 | Honest fit assessment scoring | ⬜ | | |
| P3-006 | Dealbreaker flagging logic | ⬜ | | |
| P3-007 | Counterargument generation | ⬜ | | |
| P3-008 | SkepticalAnalysis Pydantic model defined | ⬜ | | |
| P3-009 | SSE status event emitted at phase start | ⬜ | | |
| P3-010 | SSE thought events for analysis steps | ⬜ | | |
| P3-011 | State transition to SKILLS_MATCHING | ⬜ | | |
| P3-012 | Devil's advocate prompt engineering | ⬜ | | |

### Build Verification
- [ ] `pytest tests/unit/test_skeptical_comparison_node.py` passes
- [ ] No syntax errors in skeptical_comparison_node function
- [ ] Import statement works: `from services.fit_check_agent import skeptical_comparison_node`

---

## Phase 4: SKILLS_MATCHING Node

### Requirements

| ID | Requirement | Status | Verified By | Date |
|----|-------------|--------|-------------|------|
| P4-001 | skills_matching_node function implemented | ⬜ | | |
| P4-002 | analyze_skill_match tool invocation | ⬜ | | |
| P4-003 | analyze_experience_relevance tool invocation | ⬜ | | |
| P4-004 | Individual skill scoring (0-100) | ⬜ | | |
| P4-005 | Experience relevance scoring | ⬜ | | |
| P4-006 | Aggregate match score calculation | ⬜ | | |
| P4-007 | Evidence linking to scores | ⬜ | | |
| P4-008 | SkillsAnalysis Pydantic model defined | ⬜ | | |
| P4-009 | SSE status event emitted at phase start | ⬜ | | |
| P4-010 | SSE thought events for tool results | ⬜ | | |
| P4-011 | State transition to GENERATE_RESULTS | ⬜ | | |
| P4-012 | Tool error handling | ⬜ | | |

### Build Verification
- [ ] `pytest tests/unit/test_skills_matching_node.py` passes
- [ ] analyze_skill_match tool callable
- [ ] analyze_experience_relevance tool callable
- [ ] Import statement works: `from services.fit_check_agent import skills_matching_node`

---

## Phase 5: GENERATE_RESULTS Node

### Requirements

| ID | Requirement | Status | Verified By | Date |
|----|-------------|--------|-------------|------|
| P5-001 | generate_results_node function implemented | ⬜ | | |
| P5-002 | Response structure (summary, strengths, growth_areas, recommendations) | ⬜ | | |
| P5-003 | Fit score calculation and inclusion | ⬜ | | |
| P5-004 | Token-by-token streaming implementation | ⬜ | | |
| P5-005 | SSE response events for each token | ⬜ | | |
| P5-006 | SSE complete event with full response | ⬜ | | |
| P5-007 | Complete event includes metadata | ⬜ | | |
| P5-008 | FinalResponse Pydantic model defined | ⬜ | | |
| P5-009 | State transition to COMPLETE | ⬜ | | |
| P5-010 | Synthesis of all phase analyses | ⬜ | | |
| P5-011 | Actionable recommendations generation | ⬜ | | |
| P5-012 | Response addresses original query | ⬜ | | |

### Build Verification
- [ ] `pytest tests/unit/test_generate_results_node.py` passes
- [ ] Streaming works without buffering issues
- [ ] Import statement works: `from services.fit_check_agent import generate_results_node`

---

## Phase 6: Frontend Integration

### Requirements

| ID | Requirement | Status | Verified By | Date |
|----|-------------|--------|-------------|------|
| P6-001 | useFitCheck hook updated for 5-phase workflow | ⬜ | | |
| P6-002 | Phase state tracking in hook | ⬜ | | |
| P6-003 | Status event handling updated | ⬜ | | |
| P6-004 | Thought event handling per phase | ⬜ | | |
| P6-005 | Response streaming accumulation | ⬜ | | |
| P6-006 | Complete event handling with metadata | ⬜ | | |
| P6-007 | Error event handling | ⬜ | | |
| P6-008 | ThinkingPanel component updated | ⬜ | | |
| P6-009 | ComparisonChain component updated | ⬜ | | |
| P6-010 | Phase completion visual indicators | ⬜ | | |
| P6-011 | Thought timeline per phase | ⬜ | | |
| P6-012 | Loading states for each phase | ⬜ | | |

### Build Verification
- [ ] `npm run build` succeeds without errors
- [ ] `npm run lint` passes
- [ ] No TypeScript/ESLint errors in modified files
- [ ] Application loads in browser without console errors

---

## Phase 7: Testing & Validation

### Requirements

| ID | Requirement | Status | Verified By | Date |
|----|-------------|--------|-------------|------|
| P7-001 | Unit tests for CONNECTING node | ⬜ | | |
| P7-002 | Unit tests for DEEP_RESEARCH node | ⬜ | | |
| P7-003 | Unit tests for SKEPTICAL_COMPARISON node | ⬜ | | |
| P7-004 | Unit tests for SKILLS_MATCHING node | ⬜ | | |
| P7-005 | Unit tests for GENERATE_RESULTS node | ⬜ | | |
| P7-006 | Integration tests for workflow transitions | ⬜ | | |
| P7-007 | Integration tests for SSE streaming | ⬜ | | |
| P7-008 | End-to-end tests for all query types | ⬜ | | |
| P7-009 | Test fixtures created | ⬜ | | |
| P7-010 | conftest.py updated with mocks | ⬜ | | |
| P7-011 | pytest.ini configured | ⬜ | | |
| P7-012 | Code coverage ≥ 85% | ⬜ | | |

### Build Verification
- [ ] `pytest` runs all tests successfully
- [ ] `pytest --cov` shows ≥ 85% coverage
- [ ] No flaky tests (run 3x consistently)

---

## Cross-Phase Requirements

### SSE Contract Compliance

| ID | Requirement | Status | Verified By | Date |
|----|-------------|--------|-------------|------|
| SSE-001 | All events include "type" field | ⬜ | | |
| SSE-002 | Status events include "phase" field | ⬜ | | |
| SSE-003 | Thought events include "content" field | ⬜ | | |
| SSE-004 | Response events include "token" field | ⬜ | | |
| SSE-005 | Complete event is always last | ⬜ | | |
| SSE-006 | Error events include "message" field | ⬜ | | |
| SSE-007 | All events are valid JSON | ⬜ | | |

### Performance Requirements

| ID | Requirement | Status | Verified By | Date |
|----|-------------|--------|-------------|------|
| PERF-001 | Time to first event < 2 seconds | ⬜ | | |
| PERF-002 | Total workflow time < 60 seconds | ⬜ | | |
| PERF-003 | No memory leaks during streaming | ⬜ | | |
| PERF-004 | Concurrent request handling | ⬜ | | |

### Error Handling Requirements

| ID | Requirement | Status | Verified By | Date |
|----|-------------|--------|-------------|------|
| ERR-001 | Empty query handled gracefully | ⬜ | | |
| ERR-002 | LLM timeout handled | ⬜ | | |
| ERR-003 | Search API failure handled | ⬜ | | |
| ERR-004 | Tool execution failure handled | ⬜ | | |
| ERR-005 | Network disconnection handled | ⬜ | | |

---

## Completion Summary

| Phase | Total Requirements | Completed | Percentage |
|-------|-------------------|-----------|------------|
| Phase 0 | 12 | 0 | 0% |
| Phase 1 | 12 | 0 | 0% |
| Phase 2 | 12 | 0 | 0% |
| Phase 3 | 12 | 0 | 0% |
| Phase 4 | 12 | 0 | 0% |
| Phase 5 | 12 | 0 | 0% |
| Phase 6 | 12 | 0 | 0% |
| Phase 7 | 12 | 0 | 0% |
| SSE Contract | 7 | 0 | 0% |
| Performance | 4 | 0 | 0% |
| Error Handling | 5 | 0 | 0% |
| **TOTAL** | **102** | **0** | **0%** |

---

## Change Log

| Date | Phase | Requirement IDs | Change Description | Changed By |
|------|-------|-----------------|-------------------|------------|
| | | | | |

---

## Notes

- **DO NOT** proceed to the next phase until all requirements in the current phase are marked ✅
- **ALWAYS** run build verification before marking a phase complete
- **UPDATE** this document immediately after completing each requirement
- **VERIFY** with tests before marking any requirement complete
