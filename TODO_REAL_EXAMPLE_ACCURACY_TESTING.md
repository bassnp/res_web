# Accuracy Testing Framework: Semantic Matching Pipeline

> **STATUS: READY FOR RE-TESTING**  
> **Last Refactor:** December 19, 2025  
> **Architecture:** AI-Driven Semantic Matching (v2.0)

---

## Executive Summary

This document defines the accuracy testing framework for the Fit Check pipeline after the **v2.0 Semantic Matching Refactor**. The refactor removed brute-force alias dictionaries and delegated semantic interpretation to AI nodes, enabling dynamic and context-aware skill matching.

### Key Architectural Change

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    BEFORE: BRUTE-FORCE MATCHING (v1.0)                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  skill_aliases = {                                                           ║
║      "langgraph": ["langgraph", "lang graph", "agent graph"],                ║
║      "ai agents": ["agent", "agents", "agentic", "autonomous"],              ║
║      ...                                                                     ║
║  }                                                                           ║
║                                                                              ║
║  PROBLEM: Rigid keyword matching missed semantic relationships               ║
║  RESULT:  D5 "LangGraph AI Startup" scored 45% vs expected 80-95%            ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                    AFTER: SEMANTIC AI MATCHING (v2.0)                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Tools return RAW PROFILE DATA → AI performs SEMANTIC INTERPRETATION         ║
║                                                                              ║
║  Phase 1: Extract ALL technology keywords from query                         ║
║  Phase 4: LLM performs semantic matching with explicit guidance:             ║
║           - LangGraph → implies Python, AI agents, workflow automation       ║
║           - "AI agents" ≈ "agentic systems" ≈ "autonomous automation"        ║
║           - Context-aware confidence scoring                                 ║
║                                                                              ║
║  EXPECTED: Dynamic matching that adapts to any query terminology             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. Engineer Profile Ground Truth

The accuracy tests validate against this engineer's actual capabilities:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENGINEER CAPABILITY MATRIX                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ████████████████████████████████████████████████████████████████████████  │
│  █  CORE STRENGTHS (Direct Match Expected)                               █  │
│  ████████████████████████████████████████████████████████████████████████  │
│                                                                             │
│  Languages:    Python ████████████  JavaScript ███████████  TypeScript ███ │
│  Frontend:     React █████████████  Next.js ██████████████  TailwindCSS █  │
│  Backend:      FastAPI ███████████  Node.js ██████████████  REST APIs ███  │
│  AI/ML:        LangChain █████████  LangGraph █████████████  RAG ████████  │
│  Cloud:        Docker ████████████  AWS ███████████████████  PostgreSQL █  │
│                                                                             │
│  ████████████████████████████████████████████████████████████████████████  │
│  █  SEMANTIC RELATIONSHIPS (AI Should Infer)                             █  │
│  ████████████████████████████████████████████████████████████████████████  │
│                                                                             │
│  LangGraph ──────► AI Agents, Workflow Automation, Python                   │
│  Next.js ────────► React, Vercel, TypeScript, SSR                           │
│  FastAPI ────────► Python, Async APIs, Modern Backend                       │
│  RAG Systems ────► LangChain, Embeddings, Vector DBs, LLMs                  │
│  Docker ─────────► Containers, Microservices, DevOps                        │
│                                                                             │
│  ████████████████████████████████████████████████████████████████████████  │
│  █  GAPS (Should Be Identified)                                          █  │
│  ████████████████████████████████████████████████████████████████████████  │
│                                                                             │
│  Languages:    Java ░░░░░░░░░░░░░  C++ ░░░░░░░░░░░░░░░░░░  Rust ░░░░░░░░  │
│  Mobile:       iOS/Swift ░░░░░░░░  Android/Kotlin ░░░░░░░  React Native ░  │
│  Infra:        Kubernetes ░░░░░░░  Terraform ░░░░░░░░░░░░  Multi-cloud ░░  │
│  Specialized:  Embedded ░░░░░░░░░  Blockchain ░░░░░░░░░░░  Gaming/Unity ░  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Test Categories & Expected Outcomes

### Category A: HIGH FIT (Expected 70-100%)

Queries where the engineer's skills DIRECTLY ALIGN with requirements.

| ID | Query | Key Signals | Expected Score | Semantic Reasoning |
|----|-------|-------------|----------------|-------------------|
| A1 | `Vercel` | Next.js, React, TypeScript | **78-92%** | Next.js is Vercel's core product; direct ecosystem match |
| A2 | `OpenAI` | Python, LLM APIs, Prompt Engineering | **60-78%** | Strong applied AI, weaker research/PhD background |
| A3 | `Stripe` | APIs, Backend, PostgreSQL | **62-78%** | API design excellence transfers; Ruby gap expected |
| A4 | `Full-stack engineer position using Python, React, and PostgreSQL for a SaaS startup` | Python, React, PostgreSQL, Full-stack | **85-95%** | Near-perfect stack alignment |
| A5 | `Anthropic` | Python, LLM, Prompt Engineering | **55-72%** | Applied AI strong; research depth gap |

### Category B: MEDIUM FIT (Expected 40-69%)

Queries with partial alignment requiring skill transfer assessment.

| ID | Query | Key Signals | Expected Score | Semantic Reasoning |
|----|-------|-------------|----------------|-------------------|
| B1 | `Netflix` | Java (gap), React (match), Scale | **42-58%** | Frontend transfers; Java/scale gaps |
| B2 | `Datadog` | Go (gap), Python (match), K8s (gap) | **40-55%** | Python transfers; Go/K8s significant gaps |
| B3 | `ML Engineer building training pipelines with PyTorch and distributed GPU computing` | PyTorch (gap), Python (match) | **32-48%** | Python base; no PyTorch/GPU experience |
| B4 | `Salesforce` | Java/Apex (gap), Enterprise | **38-52%** | Web skills transfer; platform gap |
| B5 | `Uber` | Java/Go (gaps), Scale, Backend | **40-55%** | Backend patterns transfer; language gaps |

### Category C: LOW FIT (Expected 0-39%)

Queries where the engineer lacks core requirements.

| ID | Query | Key Signals | Expected Score | Semantic Reasoning |
|----|-------|-------------|----------------|-------------------|
| C1 | `iOS Engineer at Apple` | Swift (gap), iOS SDK (gap) | **10-25%** | Complete platform mismatch |
| C2 | `Embedded software engineer for IoT devices using C and RTOS` | C (gap), RTOS (gap), Hardware (gap) | **5-18%** | Fundamentally different domain |
| C3 | `Solidity developer for DeFi protocols on Ethereum` | Solidity (gap), Blockchain (gap) | **12-25%** | JS knowledge irrelevant to smart contracts |
| C4 | `Game developer using Unity and C++ for AAA games` | C++ (gap), Unity (gap) | **8-20%** | No game dev experience |
| C5 | `Android developer with Kotlin expertise` | Kotlin (gap), Android SDK (gap) | **10-25%** | No mobile development experience |

### Category D: EDGE CASES

Critical tests for semantic matching robustness.

| ID | Query | Expected Behavior | Expected Score |
|----|-------|-------------------|----------------|
| D1 | `TechVenture Innovations LLC 2024` | Graceful degradation with INSUFFICIENT_DATA flag | **30-50%** (uncertain) |
| D2 | `Software` | Flag as ambiguous; generic assessment | **35-55%** |
| D3 | `Full-stack developer with Java, Python, and React experience for fintech` | Partial match (Python + React); Java gap | **55-72%** |
| D4 | `Staff Software Engineer at Google` | Flag seniority/scale gaps; technical partial match | **35-52%** |
| D5 | `Startup using AI agents with LangGraph for enterprise automation` | **CRITICAL TEST** - Must recognize LangGraph + AI agents as STRONG match | **80-95%** |

---

## 3. D5 Critical Test Case: Semantic Matching Validation

This is the primary validation test for the v2.0 refactor.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  TEST D5: LangGraph AI Startup                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  QUERY: "Startup using AI agents with LangGraph for enterprise automation"  ║
║                                                                              ║
║  EXTRACTED TECHNOLOGIES (Phase 1 should capture):                            ║
║    • "AI agents"                                                             ║
║    • "LangGraph"                                                             ║
║    • "enterprise automation"                                                 ║
║    • "Startup"                                                               ║
║                                                                              ║
║  SEMANTIC MATCHING (Phase 4 should recognize):                               ║
║                                                                              ║
║    Query Term              Candidate Skill        Match Type                 ║
║    ─────────────────────────────────────────────────────────────────────    ║
║    "LangGraph"         →   LangGraph              EXACT (0.95)               ║
║    "AI agents"         →   LangGraph, RAG         SEMANTIC (0.90)            ║
║    "enterprise auto"   →   AI Portfolio Project   SEMANTIC (0.85)            ║
║    "Startup"           →   Fast learner, agile    CONTEXTUAL (0.80)          ║
║    "Python" (implied)  →   Python                 INFERRED (0.90)            ║
║                                                                              ║
║  EXPECTED OUTCOME:                                                           ║
║    • Score: 80-95%                                                           ║
║    • Tier: HIGH                                                              ║
║    • Gaps: 0-1 (possibly "enterprise scale" if flagged)                      ║
║                                                                              ║
║  v1.0 RESULT: 45% (FAILURE - brute-force aliases missed semantic match)      ║
║  v2.0 TARGET: 80-95% (SUCCESS - AI semantic interpretation)                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 4. Accuracy Validation Criteria

### Score Accuracy Thresholds

```
If |Actual Score - Expected Score| ≤ 10%  →  EXCELLENT
If |Actual Score - Expected Score| ≤ 15%  →  ACCURATE  
If |Actual Score - Expected Score| ≤ 20%  →  ACCEPTABLE
If |Actual Score - Expected Score| > 20%  →  NEEDS INVESTIGATION
```

### Tier Accuracy

| Tier | Score Range | Description |
|------|-------------|-------------|
| HIGH | 70-100% | Strong candidate; direct skill alignment |
| MEDIUM | 40-69% | Partial fit; transferable skills with gaps |
| LOW | 20-39% | Weak fit; significant skill gaps |
| INSUFFICIENT | 0-19% | Poor fit; fundamental misalignment |

### Semantic Matching Quality Indicators

The v2.0 pipeline should demonstrate:

1. **Technology Relationship Recognition**
   - LangGraph query → matches LangGraph skill AND infers AI agents relevance
   - Next.js query → matches Next.js AND infers React/Vercel ecosystem

2. **Contextual Confidence Calibration**
   - Direct skill match: 0.85-1.0 confidence
   - Semantic relationship: 0.70-0.85 confidence
   - Transferable skill: 0.50-0.70 confidence
   - Weak/no match: 0.0-0.50 confidence

3. **Gap Identification Precision**
   - Only flag GENUINE gaps (e.g., Java for Netflix, not formatting artifacts)
   - Minimum 2 gaps for anti-sycophancy (preserve existing constraint)

---

## 5. Pass/Fail Criteria

| Metric | Target | Priority |
|--------|--------|----------|
| Category A Accuracy | ≥ 75% within expected range | P0 |
| Category D5 Score | ≥ 80% (was 45%) | P0 - Critical Validation |
| Category B Accuracy | ≥ 70% within expected range | P1 |
| Category C Accuracy | ≥ 75% within expected range | P1 |
| Tier Accuracy | ≥ 65% exact match | P2 |
| Score Accuracy (±15%) | ≥ 85% | P2 |
| No Data Fabrication | 100% | P0 |

---

## 6. Test Execution Protocol

### Step 1: Run Critical D5 Test First

```bash
cd backend
python -m tests.simulation.test_frontend_pipeline --query "Startup using AI agents with LangGraph for enterprise automation"
```

**Expected D5 Result:**
- Score: 80-95%
- Tier: HIGH
- Matched: LangGraph, AI agents, Python, automation experience
- Gaps: 0-1

### Step 2: Run Full Test Suite

```bash
# All categories
python -m tests.simulation.accuracy.run_accuracy_tests

# By category
python -m tests.simulation.accuracy.run_accuracy_tests --category A
python -m tests.simulation.accuracy.run_accuracy_tests --category B
python -m tests.simulation.accuracy.run_accuracy_tests --category C
python -m tests.simulation.accuracy.run_accuracy_tests --category D
```

### Step 3: Validate Semantic Matching Quality

For each test, verify:

1. **Phase 1 Output**: Are ALL technology terms extracted from the query?
2. **Phase 4 Output**: Does the LLM recognize semantic relationships?
3. **Confidence Scores**: Are they calibrated correctly per evidence?
4. **Gap Detection**: Are gaps genuine or formatting artifacts?

---

## 7. Failure Analysis Template

For any test outside expected range:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  TEST FAILURE ANALYSIS                                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Test ID:        [X#]                                                        ║
║  Query:          [...]                                                       ║
║  Expected:       [Score%, Tier]                                              ║
║  Actual:         [Score%, Tier]                                              ║
║  Delta:          [±%]                                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ROOT CAUSE HYPOTHESIS:                                                      ║
║  [ ] Phase 1: Technology extraction incomplete                               ║
║  [ ] Phase 4: Semantic matching failed to recognize relationship             ║
║  [ ] Phase 4: Confidence miscalibration (too high/low)                       ║
║  [ ] Phase 5B: Reranker over-penalized/under-penalized                       ║
║  [ ] Research: Insufficient/incorrect data from web search                   ║
║  [ ] Prompt: Missing semantic guidance for this case                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  RECOMMENDED FIX:                                                            ║
║  [Specific action to address root cause]                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. Refactoring Changelog (v2.0)

### Files Modified

| File | Change | Rationale |
|------|--------|-----------|
| `services/tools/skill_matcher.py` | Removed `skill_aliases` dictionary (40+ lines); returns raw profile data | Delegate semantic matching to AI |
| `services/tools/experience_matcher.py` | Removed `domain_patterns` and `project_contexts` dictionaries | Delegate domain relevance to AI |
| `prompts/phase_1_connecting_concise.xml` | Added comprehensive technology extraction rules | Capture ALL tech terms from queries |
| `prompts/phase_4_skills_matching_concise.xml` | Added `<semantic_matching>` guidance section | Guide LLM on technology relationships |

### Design Principles Applied

1. **AI-Driven Interpretation**: Move semantic understanding from rigid Python dictionaries to flexible LLM prompts
2. **Raw Data Provision**: Tools provide complete profile data; AI performs contextual matching
3. **Explicit Semantic Guidance**: Prompts include technology relationship examples for consistent behavior
4. **Dynamic Adaptation**: Pipeline can handle novel terminology without code changes

---

## 9. Next Steps

1. **Execute D5 Critical Test** - Validate semantic matching works for LangGraph/AI agents
2. **Run Full Test Suite** - Gather baseline metrics for v2.0 architecture
3. **Analyze Failures** - Identify any remaining prompt or logic issues
4. **Iterate on Prompts** - Refine semantic guidance based on test results
5. **Document Final Accuracy** - Update this document with v2.0 results

---

## 10. Success Criteria Summary

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         v2.0 SUCCESS CRITERIA                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PRIMARY VALIDATION (P0):                                                    ║
║  ✓ D5 "LangGraph AI Startup" scores 80-95% (was 45%)                         ║
║  ✓ No data fabrication in any test                                           ║
║  ✓ Category A (HIGH FIT) accuracy ≥ 75%                                      ║
║                                                                              ║
║  SECONDARY VALIDATION (P1):                                                  ║
║  ✓ Category B/C accuracy ≥ 70%                                               ║
║  ✓ Score accuracy within ±15% for 85%+ of tests                              ║
║                                                                              ║
║  QUALITATIVE VALIDATION:                                                     ║
║  ✓ Semantic relationships recognized (LangGraph → AI agents)                 ║
║  ✓ Confidence calibration reflects evidence strength                         ║
║  ✓ Gaps are genuine, not formatting artifacts                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

*Document Version: 2.0*  
*Architecture: AI-Driven Semantic Matching*  
*Last Updated: December 19, 2025*  
*Status: Ready for Re-Testing*
