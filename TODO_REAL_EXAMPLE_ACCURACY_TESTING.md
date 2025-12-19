# TODO: Real Example Accuracy Testing

> **✅ STATUS: EXECUTED** - See `backend/tests/simulation/accuracy/` for the complete testing framework.
> 
> **Last Run:** December 19, 2025 | **Model:** gemini-3-flash-preview | **Pass Rate:** 45%

**Purpose:** Systematic accuracy validation of the Fit Check pipeline using real-world queries  
**Target:** Engineer profile with Python/JavaScript full-stack + AI/ML focus  
**Method:** Visual assessment with reasoning chains, not brute-force answer matching

---

## EXECUTION RESULTS SUMMARY

### Overall Performance Dashboard

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                     ACCURACY TEST EXECUTION RESULTS                          ║
║                        December 19, 2025 @ 00:47                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  OVERALL PASS RATE                                                           ║
║  ████████████████████░░░░░░░░░░░░░░░░░░░░  45.0%                             ║
║  Passed: 2 | Partial: 14 | Failed: 4                                         ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  SCORE ACCURACY (within +/-15% of expected)                                  ║
║  █████████████████████████████████████████████████  95.0%  [EXCELLENT]       ║
║  18/20 tests within acceptable score range                                   ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  TIER ACCURACY (correct confidence classification)                           ║
║  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░  35.0%  [NEEDS WORK]               ║
║  Exact: 7 | Adjacent: 7 | Mismatch: 6                                        ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  GAP IDENTIFICATION (correct number of gaps detected)                        ║
║  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  20.0%  [OVER-DETECTING]           ║
║  Within Range: 4/20 | Outside Range: 16/20                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Category Breakdown

| Category | Description | Pass Rate | Verdict |
|----------|-------------|-----------|---------|
| **A** | HIGH FIT (70-100%) | 30.0% | Harsh scoring detected |
| **B** | MEDIUM FIT (40-69%) | 40.0% | Acceptable with caveats |
| **C** | LOW FIT (0-39%) | 70.0% | Best performing category |
| **D** | EDGE CASES | 40.0% | D5 (LangGraph) severely under-scored |

### Root Cause Analysis

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  FAILURE ROOT CAUSES                                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  HARSH_SCORING ████████████████████████████████████████  4 occurrences       ║
║    - Pipeline under-scores candidates where direct skill match exists        ║
║    - Most significant: D5 (LangGraph AI) scored 45% vs expected 80-95%       ║
║    - Recommendation: Review Phase 4 skill matching & Phase 5b calibration    ║
║                                                                              ║
║  OVER_GAP_DETECTION ██████████████████████████████████████  16 occurrences   ║
║    - Parser extracting formatting artifacts as gaps                          ║
║    - Recommendation: Refine gap extraction regex patterns                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Detailed Test Results with Visual Assessment

### CATEGORY A: HIGH FIT (Expected 70-100%)

| Test | Query | Expected | Actual | Delta | Verdict |
|------|-------|----------|--------|-------|---------|
| A1 | Vercel | 75-90% | **68%** | -7% | Slight under-score |
| A2 | OpenAI | 55-75% | **60%** | ✓ | ACCURATE |
| A3 | Stripe | 60-75% | **45%** | -15% | Under-score |
| A4 | Full-stack Python/React | 85-95% | **68%** | -17% | HARSH SCORING |
| A5 | Anthropic | 50-70% | **45%** | -5% | Close/Acceptable |

**Visual Assessment - Category A:**
```
A1 Vercel       Expected: ████████████████████░░░░  85%
                Actual:   ███████████████░░░░░░░░░  68%  [-17%]
                
A2 OpenAI       Expected: ███████████████░░░░░░░░░  70%
                Actual:   █████████████░░░░░░░░░░░  60%  [WITHIN RANGE]
                
A3 Stripe       Expected: ██████████████░░░░░░░░░░  68%
                Actual:   ██████████░░░░░░░░░░░░░░  45%  [-23%]
                
A4 Python/React Expected: █████████████████████░░░  92%
                Actual:   ███████████████░░░░░░░░░  68%  [-24%] HARSH
                
A5 Anthropic    Expected: █████████████░░░░░░░░░░░  60%
                Actual:   ██████████░░░░░░░░░░░░░░  45%  [-15%]
```

**Reasoning:** The pipeline is demonstrating **consistent under-scoring** for Category A tests. The engineer's direct stack match (Python, React, Next.js, FastAPI, LangChain) should yield higher scores for Vercel and the full-stack startup role.

---

### CATEGORY B: MEDIUM FIT (Expected 40-69%)

| Test | Query | Expected | Actual | Delta | Verdict |
|------|-------|----------|--------|-------|---------|
| B1 | Netflix | 40-55% | **45%** | ✓ | ACCURATE |
| B2 | Datadog | 45-60% | **38%** | -7% | Slight under-score |
| B3 | ML Platform Engineer | 30-45% | **35%** | ✓ | ACCURATE |
| B4 | Salesforce | 35-50% | **45%** | ✓ | ACCURATE |
| B5 | Uber | 40-55% | **45%** | ✓ | ACCURATE |

**Visual Assessment - Category B:**
```
B1 Netflix      Expected: ██████████░░░░░░░░░░░░░░  48%
                Actual:   ██████████░░░░░░░░░░░░░░  45%  [ACCURATE]
                
B2 Datadog      Expected: ███████████░░░░░░░░░░░░░  52%
                Actual:   ████████░░░░░░░░░░░░░░░░  38%  [-14%]
                
B3 ML Platform  Expected: ████████░░░░░░░░░░░░░░░░  38%
                Actual:   ███████░░░░░░░░░░░░░░░░░  35%  [ACCURATE]
                
B4 Salesforce   Expected: █████████░░░░░░░░░░░░░░░  42%
                Actual:   ██████████░░░░░░░░░░░░░░  45%  [ACCURATE]
                
B5 Uber         Expected: ██████████░░░░░░░░░░░░░░  48%
                Actual:   ██████████░░░░░░░░░░░░░░  45%  [ACCURATE]
```

**Reasoning:** Category B shows the **best calibration**. The pipeline correctly identifies partial fits where the engineer has transferable skills but notable gaps (Java at Netflix, Go/K8s at Datadog).

---

### CATEGORY C: LOW FIT (Expected 0-39%)

| Test | Query | Expected | Actual | Delta | Verdict |
|------|-------|----------|--------|-------|---------|
| C1 | Apple iOS Engineer | 10-25% | **38%** | +13% | Slight over-score |
| C2 | Embedded Systems IoT | 5-15% | **25%** | +10% | Slight over-score |
| C3 | DeFi/Solidity | 15-25% | **12%** | ✓ | ACCURATE |
| C4 | Game Dev Unity/C++ | 10-20% | **14%** | ✓ | PASS |
| C5 | Android/Kotlin | 10-25% | **12%** | ✓ | ACCURATE |

**Visual Assessment - Category C:**
```
C1 iOS Apple    Expected: █████░░░░░░░░░░░░░░░░░░░  18%
                Actual:   ████████░░░░░░░░░░░░░░░░  38%  [+20%] Over
                
C2 Embedded     Expected: ██░░░░░░░░░░░░░░░░░░░░░░  10%
                Actual:   █████░░░░░░░░░░░░░░░░░░░  25%  [PASS]
                
C3 DeFi/Solidity Expected: ████░░░░░░░░░░░░░░░░░░░░  20%
                Actual:   ██░░░░░░░░░░░░░░░░░░░░░░  12%  [ACCURATE]
                
C4 Game Dev     Expected: ███░░░░░░░░░░░░░░░░░░░░░  15%
                Actual:   ██░░░░░░░░░░░░░░░░░░░░░░  14%  [PASS]
                
C5 Android      Expected: ████░░░░░░░░░░░░░░░░░░░░  18%
                Actual:   ██░░░░░░░░░░░░░░░░░░░░░░  12%  [ACCURATE]
```

**Reasoning:** Category C is **correctly identifying low fits** for specialized domains (iOS, Embedded, Blockchain, Gaming, Android) where the engineer lacks core skills.

---

### CATEGORY D: EDGE CASES

| Test | Query | Expected | Actual | Delta | Verdict |
|------|-------|----------|--------|-------|---------|
| D1 | Obscure Company | 0-50% | **50%** | ✓ | ACCURATE |
| D2 | Ambiguous "Software" | 40-60% | **35%** | -5% | Close |
| D3 | Mixed Signal (Java+Python) | 55-70% | **68%** | ✓ | ACCURATE |
| D4 | Staff Engineer Google | 35-50% | **45%** | ✓ | ACCURATE |
| D5 | LangGraph AI Startup | 80-95% | **45%** | -35% | SEVERE UNDER-SCORE |

**Visual Assessment - Category D:**
```
D1 Obscure Co   Expected: █████████░░░░░░░░░░░░░░░  35% (uncertain)
                Actual:   ███████████░░░░░░░░░░░░░  50%  [OK for edge case]
                
D2 "Software"   Expected: ███████████░░░░░░░░░░░░░  50%
                Actual:   ███████░░░░░░░░░░░░░░░░░  35%  [-15%]
                
D3 Mixed Signal Expected: ██████████████░░░░░░░░░░  62%
                Actual:   ███████████████░░░░░░░░░  68%  [ACCURATE]
                
D4 Staff Google Expected: ██████████░░░░░░░░░░░░░░  42%
                Actual:   ██████████░░░░░░░░░░░░░░  45%  [ACCURATE]
                
D5 LangGraph AI Expected: █████████████████████░░░  88%  <-- CRITICAL
                Actual:   ██████████░░░░░░░░░░░░░░  45%  [-43%] SEVERE
```

**Reasoning:** D5 is the **most significant failure**. The query "Startup using AI agents with LangGraph for enterprise automation" directly matches the engineer's core expertise (LangGraph, AI agents, Python, FastAPI). Expected 80-95%, got 45%. This indicates the pipeline isn't recognizing direct technology matches in the query text.

---

## Recommendations for Pipeline Improvement

### Priority 1: Fix Harsh Scoring in High-Fit Cases
- **Issue:** A1, A4, D5 all show significant under-scoring
- **Action:** Review Phase 4 skill matching logic for direct technology name matches
- **Action:** Check Phase 5b confidence calibration formula

### Priority 2: Improve Technology Name Recognition
- **Issue:** D5 "LangGraph" wasn't recognized as a direct skill match
- **Action:** Enhance query classification to detect technology names from job descriptions
- **Action:** Add technology name extraction to Phase 1 connecting

### Priority 3: Tier Calibration
- **Issue:** 35% tier accuracy (many MEDIUM assigned when HIGH expected)
- **Action:** Adjust tier thresholds based on score ranges
- **Action:** Consider tier inference from score rather than separate calculation

### Priority 4: Gap Detection Refinement
- **Issue:** 16/20 tests over-detected gaps
- **Action:** Refine regex patterns to exclude formatting artifacts
- **Action:** Focus on "Areas to Address" section only for gap extraction

---

## Implementation Summary

The accuracy testing framework has been fully implemented with the following components:

### Files Created

| File | Description |
|------|-------------|
| `accuracy/__init__.py` | Module exports and public API |
| `accuracy/test_definitions.py` | 20 test cases across 4 categories |
| `accuracy/accuracy_validator.py` | Score/tier/gap validation utilities |
| `accuracy/failure_analyzer.py` | Root cause analysis for failures |
| `accuracy/run_accuracy_tests.py` | Standalone CLI test runner |
| `accuracy/test_accuracy.py` | Pytest-compatible test suite |
| `accuracy/README.md` | Comprehensive documentation |

### Quick Start

```bash
# Run all accuracy tests (standalone)
cd backend
python -m tests.simulation.accuracy.run_accuracy_tests

# Run specific category
python -m tests.simulation.accuracy.run_accuracy_tests --category A

# Run via pytest
pytest tests/simulation/accuracy/test_accuracy.py -v -m accuracy_category_a
```

---

## 1. Engineer Profile Summary (Baseline)

Before testing, we establish the engineer's ground truth capabilities:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENGINEER CAPABILITY MATRIX                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ████████████████████████████████████████████████████████████████████████  │
│  █  STRONG FIT (Direct Match)                                            █  │
│  ████████████████████████████████████████████████████████████████████████  │
│                                                                             │
│  Languages:    Python ████████████  JavaScript ███████████  TypeScript ███ │
│  Frontend:     React █████████████  Next.js ██████████████  TailwindCSS █  │
│  Backend:      FastAPI ███████████  Node.js ██████████████  REST APIs ███  │
│  AI/ML:        LangChain █████████  LangGraph █████████████  RAG ████████  │
│  Cloud:        Docker ████████████  AWS (basic) ███████████  PostgreSQL █  │
│                                                                             │
│  ████████████████████████████████████████████████████████████████████████  │
│  █  WEAK FIT (Limited/No Experience)                                     █  │
│  ████████████████████████████████████████████████████████████████████████  │
│                                                                             │
│  Languages:    Java ░░░░░░░░░░░░░  C++ ░░░░░░░░░░░░░░░░░░  Rust ░░░░░░░░  │
│  Mobile:       iOS/Swift ░░░░░░░░  Android/Kotlin ░░░░░░░  React Native ░  │
│  Infra:        Kubernetes ░░░░░░░  Terraform ░░░░░░░░░░░░  Multi-cloud ░░  │
│  Specialized:  Embedded ░░░░░░░░░  Blockchain ░░░░░░░░░░░  Gaming/Unity ░  │
│  Data Eng:     Spark ░░░░░░░░░░░░  Hadoop ░░░░░░░░░░░░░░░  Airflow ░░░░░░  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Test Categories

### Category A: Expected HIGH Fit (70-100%)
Queries where the engineer SHOULD score well based on direct skill alignment.

### Category B: Expected MEDIUM Fit (40-69%)
Queries with partial alignment - transferable skills but notable gaps.

### Category C: Expected LOW Fit (0-39%)
Queries where the engineer lacks core requirements.

### Category D: Edge Cases
Ambiguous queries, obscure companies, malformed inputs.

---

## 3. Test Cases with Visual Reasoning

### ═══════════════════════════════════════════════════════════════════════════
### CATEGORY A: EXPECTED HIGH FIT (70-100%)
### ═══════════════════════════════════════════════════════════════════════════

---

#### A1. Vercel (Frontend-Focused Company)

**Query:** `Vercel`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ EMPLOYER REQUIREMENTS (Inferred)          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ Next.js expertise          ─────────────► Next.js ████████████  │
│ React/Frontend             ─────────────► React █████████████   │
│ TypeScript                 ─────────────► TypeScript ██████████ │
│ Edge/Serverless            ─ ─ ─ ─ ─ ─ ─► AWS (partial) ████░░░ │
│ Performance optimization   ─ ─ ─ ─ ─ ─ ─► Inferred from exp ███ │
│ Developer tools mindset    ─────────────► Portfolio project ███ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 75-90% | Direct alignment with Next.js, React, TypeScript |
| Confidence Tier | HIGH | Core stack matches exactly |
| Gaps Identified | 1-2 | Possibly edge computing, deep serverless exp |

**Visual Assessment:**
```
ALIGNMENT GAUGE: ████████████████████░░░░ 85%
                 └─ Strong │ Gap ─┘
```

---

#### A2. OpenAI (AI Engineering Company)

**Query:** `OpenAI`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ EMPLOYER REQUIREMENTS (Inferred)          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ Python proficiency         ─────────────► Python ██████████████ │
│ LLM/Prompt Engineering     ─────────────► LangChain/Gemini ████ │
│ API Development            ─────────────► FastAPI/REST ████████ │
│ ML Research Background     ─ ─ ─ ─ ─ ─ ─► Applied AI only ██░░░ │
│ Distributed Systems        ─ ─ ─ ─ ─ ─ ─► Docker (basic) ███░░░ │
│ PhD/Research Papers        ─ ─ ✗ ─ ─ ─ ─► B.S. only ░░░░░░░░░░ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 55-75% | Strong applied AI, weak research depth |
| Confidence Tier | MEDIUM-HIGH | Technical fit good, experience gap |
| Gaps Identified | 2-3 | Research background, scale, education |

**Visual Assessment:**
```
ALIGNMENT GAUGE: ███████████████░░░░░░░░░ 70%
                 └─ Applied AI  │ Research Gap ─┘
```

---

#### A3. Stripe (Backend/API Company)

**Query:** `Stripe`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ EMPLOYER REQUIREMENTS (Inferred)          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ API Design Excellence      ─────────────► REST/FastAPI ████████ │
│ Backend Systems            ─────────────► Python/Node ██████████ │
│ Database Experience        ─────────────► PostgreSQL ██████████ │
│ Ruby (primary lang)        ─ ─ ✗ ─ ─ ─ ─► No Ruby ░░░░░░░░░░░░░ │
│ Payment/Fintech Domain     ─ ─ ─ ─ ─ ─ ─► No fintech exp ░░░░░░ │
│ Scale (millions of txns)   ─ ─ ─ ─ ─ ─ ─► Project scale ███░░░░ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 60-75% | API skills transfer, but Ruby/domain gap |
| Confidence Tier | MEDIUM-HIGH | Transferable skills present |
| Gaps Identified | 2-3 | Ruby, fintech domain, scale |

**Visual Assessment:**
```
ALIGNMENT GAUGE: ██████████████░░░░░░░░░░ 68%
                 └─ API/Backend │ Domain Gap ─┘
```

---

#### A4. Startup - Full-Stack Python/React Role

**Query:** `Full-stack engineer position using Python, React, and PostgreSQL for a SaaS startup`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ JOB REQUIREMENTS                          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ Python                     ─────────────► Python ██████████████ │
│ React                      ─────────────► React █████████████   │
│ PostgreSQL                 ─────────────► PostgreSQL ██████████ │
│ Full-stack ownership       ─────────────► End-to-end exp ██████ │
│ Startup mentality          ─────────────► Fast learner █████████ │
│ SaaS experience            ─ ─ ─ ─ ─ ─ ─► Web platform exp ████ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 85-95% | Near-perfect stack alignment |
| Confidence Tier | HIGH | Direct match to all requirements |
| Gaps Identified | 0-1 | Possibly SaaS-specific patterns |

**Visual Assessment:**
```
ALIGNMENT GAUGE: █████████████████████████ 92%
                 └─ Excellent Fit ───────┘
```

---

### ═══════════════════════════════════════════════════════════════════════════
### CATEGORY B: EXPECTED MEDIUM FIT (40-69%)
### ═══════════════════════════════════════════════════════════════════════════

---

#### B1. Netflix (Streaming/Scale Company)

**Query:** `Netflix`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ EMPLOYER REQUIREMENTS (Inferred)          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ Java (primary language)    ─ ─ ✗ ─ ─ ─ ─► No Java ░░░░░░░░░░░░░ │
│ Microservices at scale     ─ ─ ─ ─ ─ ─ ─► Docker (basic) ███░░░ │
│ Distributed systems        ─ ─ ─ ─ ─ ─ ─► Limited exp ███░░░░░░ │
│ React/Frontend             ─────────────► React █████████████   │
│ AWS (deep expertise)       ─ ─ ─ ─ ─ ─ ─► AWS (basic) █████░░░░ │
│ Chaos engineering mindset  ─ ─ ─ ─ ─ ─ ─► Unknown ░░░░░░░░░░░░░ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 40-55% | Frontend aligns, backend stack misaligned |
| Confidence Tier | MEDIUM | Significant language gap |
| Gaps Identified | 3-4 | Java, distributed systems, scale |

**Visual Assessment:**
```
ALIGNMENT GAUGE: ██████████░░░░░░░░░░░░░░ 48%
                 └─ Frontend │ Backend Gap ─┘
```

---

#### B2. Datadog (Observability/Go Company)

**Query:** `Datadog`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ EMPLOYER REQUIREMENTS (Inferred)          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ Go (primary language)      ─ ─ ✗ ─ ─ ─ ─► No Go ░░░░░░░░░░░░░░░ │
│ Python                     ─────────────► Python ██████████████ │
│ Kubernetes expertise       ─ ─ ✗ ─ ─ ─ ─► No K8s ░░░░░░░░░░░░░ │
│ Distributed tracing        ─ ─ ─ ─ ─ ─ ─► Limited exp ██░░░░░░░ │
│ React/Frontend             ─────────────► React █████████████   │
│ Cloud infrastructure       ─ ─ ─ ─ ─ ─ ─► Docker/AWS ██████░░░░ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 45-60% | Python transfers, but Go/K8s gaps |
| Confidence Tier | MEDIUM | Core language mismatch |
| Gaps Identified | 2-3 | Go, Kubernetes, observability domain |

**Visual Assessment:**
```
ALIGNMENT GAUGE: ███████████░░░░░░░░░░░░░ 52%
                 └─ Python/React │ Go/K8s Gap ─┘
```

---

#### B3. Machine Learning Platform Role

**Query:** `ML Engineer building training pipelines with PyTorch and distributed GPU computing`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ JOB REQUIREMENTS                          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ PyTorch expertise          ─ ─ ✗ ─ ─ ─ ─► No PyTorch ░░░░░░░░░░ │
│ GPU/CUDA programming       ─ ─ ✗ ─ ─ ─ ─► No GPU exp ░░░░░░░░░░ │
│ Python                     ─────────────► Python ██████████████ │
│ ML training pipelines      ─ ─ ─ ─ ─ ─ ─► RAG only (applied) ██ │
│ Distributed computing      ─ ─ ─ ─ ─ ─ ─► Limited ██░░░░░░░░░░░ │
│ Model optimization         ─ ─ ✗ ─ ─ ─ ─► No exp ░░░░░░░░░░░░░ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 30-45% | Python base, but core ML stack missing |
| Confidence Tier | LOW-MEDIUM | Fundamental tooling gap |
| Gaps Identified | 4-5 | PyTorch, GPU, training pipelines, dist sys |

**Visual Assessment:**
```
ALIGNMENT GAUGE: ████████░░░░░░░░░░░░░░░░ 38%
                 └─ Python │ ML Infrastructure Gap ─┘
```

---

#### B4. Salesforce (Enterprise Java/Apex)

**Query:** `Salesforce`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ EMPLOYER REQUIREMENTS (Inferred)          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ Java                       ─ ─ ✗ ─ ─ ─ ─► No Java ░░░░░░░░░░░░░ │
│ Apex (Salesforce lang)     ─ ─ ✗ ─ ─ ─ ─► No Apex ░░░░░░░░░░░░░ │
│ CRM/Enterprise domain      ─ ─ ─ ─ ─ ─ ─► No domain exp ░░░░░░░ │
│ React/Lightning            ─ ─ ─ ─ ─ ─ ─► React (general) ████░ │
│ Cloud (Salesforce platform)─ ─ ─ ─ ─ ─ ─► AWS (different) ██░░░ │
│ Enterprise architecture    ─ ─ ─ ─ ─ ─ ─► Startup scale ███░░░░ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 35-50% | React transfers, but ecosystem mismatch |
| Confidence Tier | LOW-MEDIUM | Platform-specific gaps |
| Gaps Identified | 3-4 | Java/Apex, CRM domain, enterprise |

**Visual Assessment:**
```
ALIGNMENT GAUGE: ██████████░░░░░░░░░░░░░░ 42%
                 └─ Web Skills │ Salesforce Ecosystem Gap ─┘
```

---

### ═══════════════════════════════════════════════════════════════════════════
### CATEGORY C: EXPECTED LOW FIT (0-39%)
### ═══════════════════════════════════════════════════════════════════════════

---

#### C1. Apple (iOS/Swift Focus)

**Query:** `iOS Engineer at Apple`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ EMPLOYER REQUIREMENTS                     ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ Swift (required)           ─ ─ ✗ ─ ─ ─ ─► No Swift ░░░░░░░░░░░░ │
│ iOS SDK                    ─ ─ ✗ ─ ─ ─ ─► No iOS ░░░░░░░░░░░░░░ │
│ Objective-C                ─ ─ ✗ ─ ─ ─ ─► No Obj-C ░░░░░░░░░░░░ │
│ UIKit/SwiftUI              ─ ─ ✗ ─ ─ ─ ─► No experience ░░░░░░░ │
│ App Store publishing       ─ ─ ✗ ─ ─ ─ ─► No experience ░░░░░░░ │
│ Performance optimization   ─ ─ ─ ─ ─ ─ ─► Web-focused ██░░░░░░░ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 10-25% | Complete platform mismatch |
| Confidence Tier | LOW/INSUFFICIENT | Core skills missing |
| Gaps Identified | 5+ | Swift, iOS SDK, mobile platform |

**Visual Assessment:**
```
ALIGNMENT GAUGE: ████░░░░░░░░░░░░░░░░░░░░ 18%
                 └─ General │ iOS Stack Completely Missing ─┘
```

---

#### C2. Embedded Systems Role

**Query:** `Embedded software engineer for IoT devices using C and RTOS`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ JOB REQUIREMENTS                          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ C programming              ─ ─ ✗ ─ ─ ─ ─► No C ░░░░░░░░░░░░░░░░ │
│ RTOS (FreeRTOS, etc.)      ─ ─ ✗ ─ ─ ─ ─► No RTOS ░░░░░░░░░░░░░ │
│ Hardware interfaces        ─ ─ ✗ ─ ─ ─ ─► No hardware ░░░░░░░░░ │
│ Memory management          ─ ─ ✗ ─ ─ ─ ─► GC languages ░░░░░░░░ │
│ Low-level debugging        ─ ─ ✗ ─ ─ ─ ─► Web debugging ░░░░░░░ │
│ IoT protocols              ─ ─ ✗ ─ ─ ─ ─► HTTP/REST only ░░░░░░ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 5-15% | Fundamentally different domain |
| Confidence Tier | INSUFFICIENT | No transferable skills |
| Gaps Identified | 5+ | Entire embedded stack missing |

**Visual Assessment:**
```
ALIGNMENT GAUGE: ██░░░░░░░░░░░░░░░░░░░░░░ 10%
                 └─ Wrong Domain Entirely ─────────────────┘
```

---

#### C3. Blockchain/Web3 Company

**Query:** `Solidity developer for DeFi protocols on Ethereum`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ JOB REQUIREMENTS                          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ Solidity                   ─ ─ ✗ ─ ─ ─ ─► No Solidity ░░░░░░░░░ │
│ Smart contracts            ─ ─ ✗ ─ ─ ─ ─► No blockchain ░░░░░░░ │
│ Ethereum/EVM               ─ ─ ✗ ─ ─ ─ ─► No EVM ░░░░░░░░░░░░░░ │
│ DeFi protocols             ─ ─ ✗ ─ ─ ─ ─► No domain exp ░░░░░░░ │
│ Web3.js/Ethers.js          ─ ─ ✗ ─ ─ ─ ─► No exp ░░░░░░░░░░░░░░ │
│ JavaScript                 ─────────────► JavaScript ██████████ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 15-25% | JS knowledge, but domain is foreign |
| Confidence Tier | LOW | Core blockchain skills missing |
| Gaps Identified | 5+ | Solidity, smart contracts, DeFi domain |

**Visual Assessment:**
```
ALIGNMENT GAUGE: █████░░░░░░░░░░░░░░░░░░░ 20%
                 └─ JS │ Blockchain Stack Missing ──────────┘
```

---

#### C4. Gaming Company (Unity/C++)

**Query:** `Game developer using Unity and C++ for AAA games`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ JOB REQUIREMENTS                          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ C++                        ─ ─ ✗ ─ ─ ─ ─► No C++ ░░░░░░░░░░░░░░ │
│ Unity/C#                   ─ ─ ✗ ─ ─ ─ ─► No Unity ░░░░░░░░░░░░ │
│ Game physics engines       ─ ─ ✗ ─ ─ ─ ─► No experience ░░░░░░░ │
│ 3D graphics/shaders        ─ ─ ✗ ─ ─ ─ ─► No experience ░░░░░░░ │
│ Performance optimization   ─ ─ ─ ─ ─ ─ ─► Web-focused ██░░░░░░░ │
│ Multiplayer networking     ─ ─ ─ ─ ─ ─ ─► WebSockets (diff) ░░░ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 10-20% | Different programming paradigm |
| Confidence Tier | INSUFFICIENT | No game dev experience |
| Gaps Identified | 5+ | C++, Unity, graphics, game design |

**Visual Assessment:**
```
ALIGNMENT GAUGE: ███░░░░░░░░░░░░░░░░░░░░░ 15%
                 └─ Web Dev │ Game Dev Stack Missing ───────┘
```

---

### ═══════════════════════════════════════════════════════════════════════════
### CATEGORY D: EDGE CASES
### ═══════════════════════════════════════════════════════════════════════════

---

#### D1. Obscure/Unknown Company

**Query:** `TechVenture Innovations LLC 2024`

**Expected Behavior:**
- Pipeline should attempt iteration loop (up to 3 searches)
- Should gracefully degrade with INSUFFICIENT_DATA flag
- Should NOT fabricate information about unknown company

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | N/A or 30-50% | Based on inferred generic tech role |
| Confidence Tier | INSUFFICIENT_DATA | Cannot verify company |
| Data Quality | SPARSE or UNVERIFIED | Limited research available |

---

#### D2. Ambiguous Query

**Query:** `Software`

**Expected Behavior:**
- Too vague for accurate matching
- Should flag low confidence due to ambiguity
- May classify as job_description with generic analysis

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 40-60% | Generic software → generic match |
| Confidence Tier | LOW | Cannot determine specific requirements |
| Quality Flags | AMBIGUOUS_QUERY | Input too vague |

---

#### D3. Mixed Signal Query

**Query:** `Full-stack developer with Java, Python, and React experience for fintech`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ JOB REQUIREMENTS                          ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ Java                       ─ ─ ✗ ─ ─ ─ ─► No Java ░░░░░░░░░░░░░ │
│ Python                     ─────────────► Python ██████████████ │
│ React                      ─────────────► React █████████████   │
│ Fintech domain             ─ ─ ─ ─ ─ ─ ─► No fintech exp ░░░░░░ │
│ Full-stack ownership       ─────────────► End-to-end exp ██████ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 55-70% | 2/3 languages match, domain gap |
| Confidence Tier | MEDIUM | Partial match with clear gap |
| Gaps Identified | 2 | Java, fintech domain knowledge |

---

#### D4. Senior/Staff Level Implicit Requirements

**Query:** `Staff Software Engineer at Google`

**Reasoning Chain:**
```
┌──────────────────────────────────────────────────────────────────┐
│ INFERRED REQUIREMENTS                     ENGINEER CAPABILITIES  │
├──────────────────────────────────────────────────────────────────┤
│ 10+ years experience       ─ ─ ─ ─ ─ ─ ─► Junior/Mid level ░░░░ │
│ System design at scale     ─ ─ ─ ─ ─ ─ ─► Project scale ███░░░░ │
│ Technical leadership       ─ ─ ─ ─ ─ ─ ─► IC experience ███░░░░ │
│ Python/Go/C++              ─ ─ ─ ─ ─ ─ ─► Python only █████░░░░ │
│ PhD or equivalent          ─ ─ ─ ─ ─ ─ ─► B.S. only ██░░░░░░░░░ │
│ Published work             ─ ─ ✗ ─ ─ ─ ─► No publications ░░░░░ │
└──────────────────────────────────────────────────────────────────┘
```

**Expected Outcome:**
| Metric | Expected Value | Reasoning |
|--------|---------------|-----------|
| Match Score | 35-50% | Technical skills partial, seniority gap |
| Confidence Tier | MEDIUM | Level mismatch should be flagged |
| Gaps Identified | 3+ | Seniority, scale, leadership |

---

## 4. Accuracy Validation Matrix

### Expected Results Summary

| Test ID | Query | Expected Score | Expected Tier | Key Validation Point |
|---------|-------|---------------|---------------|---------------------|
| A1 | Vercel | 75-90% | HIGH | Next.js/React direct match |
| A2 | OpenAI | 55-75% | MEDIUM-HIGH | AI skills, research gap |
| A3 | Stripe | 60-75% | MEDIUM-HIGH | API skills, Ruby gap |
| A4 | Full-stack startup | 85-95% | HIGH | Perfect stack match |
| B1 | Netflix | 40-55% | MEDIUM | Java/scale gap |
| B2 | Datadog | 45-60% | MEDIUM | Go/K8s gap |
| B3 | ML Platform | 30-45% | LOW-MEDIUM | PyTorch/GPU gap |
| B4 | Salesforce | 35-50% | LOW-MEDIUM | Apex/enterprise gap |
| C1 | iOS at Apple | 10-25% | LOW/INSUFF | Swift/iOS missing |
| C2 | Embedded IoT | 5-15% | INSUFFICIENT | C/RTOS missing |
| C3 | DeFi Solidity | 15-25% | LOW | Blockchain missing |
| C4 | Game Dev Unity | 10-20% | INSUFFICIENT | C++/Unity missing |
| D1 | Unknown Company | N/A | INSUFFICIENT_DATA | Data quality check |
| D2 | "Software" | 40-60% | LOW | Ambiguity handling |
| D3 | Mixed (Java+Python) | 55-70% | MEDIUM | Partial match handling |
| D4 | Staff @ Google | 35-50% | MEDIUM | Seniority inference |

---

## 5. Test Execution Protocol

### Step 1: Run Individual Tests
```bash
python -m tests.simulation.test_frontend_pipeline --query "Vercel"
python -m tests.simulation.test_frontend_pipeline --query "iOS Engineer at Apple"
# ... etc
```

### Step 2: Record Results
For each test, record:
1. Actual match score
2. Actual confidence tier
3. Gaps identified
4. Quality flags raised

### Step 3: Calculate Accuracy Metrics

**Scoring Accuracy:**
```
If |Actual Score - Expected Score| ≤ 15%  →  ACCURATE
If |Actual Score - Expected Score| ≤ 25%  →  ACCEPTABLE
If |Actual Score - Expected Score| > 25%  →  INACCURATE
```

**Tier Accuracy:**
```
If Actual Tier == Expected Tier  →  ACCURATE
If Actual Tier adjacent to Expected  →  ACCEPTABLE
Otherwise  →  INACCURATE
```

### Step 4: Identify Systematic Errors

Look for patterns:
- Are HIGH fit queries consistently underscored?
- Are LOW fit queries being overscored (sycophancy)?
- Are gaps being properly identified?
- Is the system appropriately flagging data quality issues?

---

## 6. Pass/Fail Criteria

| Metric | Pass Threshold |
|--------|---------------|
| Category A Accuracy | ≥ 80% within expected range |
| Category B Accuracy | ≥ 75% within expected range |
| Category C Accuracy | ≥ 80% within expected range |
| Tier Accuracy | ≥ 75% exact match |
| Gap Identification | ≥ 2 genuine gaps on B/C queries |
| Edge Case Handling | No fabrication, graceful degradation |

---

## 7. Failure Analysis Template

For any test that fails accuracy criteria, document:

```
TEST FAILURE ANALYSIS
─────────────────────
Test ID: [X#]
Query: [...]
Expected: [Score%, Tier]
Actual: [Score%, Tier]
Delta: [±%]

Root Cause Hypothesis:
[ ] Insufficient research data
[ ] Incorrect skill mapping
[ ] Sycophancy (over-scoring)
[ ] Missing gap detection
[ ] Domain knowledge gap in prompts
[ ] Query classification error

Recommended Fix:
[...]
```

---

*Document Version: 1.0*  
*Created: December 2025*  
*Purpose: Systematic accuracy validation with visual reasoning*
