# Fit Check Pipeline Upgrade: Agentic Workflow Specification

> **Directive**: Transform the Fit Check into a **5-phase LangGraph pipeline** optimized for Gemini 2.5 Flash using **XML containerization**, **criteria-based prompting**, and **explicit phase orchestration**.

---

## 1. Architecture Overview

### Current Problem
Single ReAct agent with uncontrolled tool invocation order. Frontend guesses phase completion from tool calls.

### Target Solution
**5-node sequential pipeline** where each phase:
1. Has a dedicated LLM invocation with **XML-structured prompts**
2. Emits explicit `phase` SSE events (not inferred from tools)
3. Passes structured JSON context to the next node
4. Uses **Criteria-Based Prompting** (not "think step-by-step")

```
[START] → CONNECTING → DEEP_RESEARCH → SKEPTICAL_COMPARISON → SKILLS_MATCHING → GENERATE_RESULTS → [END]
```

---

## 2. Gemini-Optimized Prompt Architecture

### 2.1 The Anti-Pattern to Avoid
**DO NOT** use: `"Let's think step by step..."`

Per Gemini 3.x/2.5 research, this causes **redundant double-thinking** that degrades output quality.

### 2.2 The Correct Pattern: Criteria-Based + XML Containerization

Each phase prompt follows this structure:

```xml
<system_instruction>
  <agent_persona>You are a [ROLE] specializing in [DOMAIN].</agent_persona>
  <primary_objective>[SINGLE CLEAR GOAL]</primary_objective>
  <success_criteria>
    <criterion priority="critical">[MUST-HAVE OUTPUT]</criterion>
    <criterion priority="high">[QUALITY REQUIREMENT]</criterion>
  </success_criteria>
  <behavioral_constraints>
    <constraint>DO NOT [ANTI-PATTERN]</constraint>
    <constraint>DO NOT [ANTI-PATTERN]</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <prior_phase_output>[STRUCTURED JSON FROM PREVIOUS NODE]</prior_phase_output>
  <reference_profile>[ENGINEER PROFILE]</reference_profile>
</context_data>

<output_contract>
  Output strictly valid JSON matching this schema:
  {
    "key_findings": [...],
    "reasoning_trace": "...",
    "confidence": 0.0-1.0
  }
</output_contract>
```

### 2.3 Reasoning Trace Pattern
Instead of CoT in generation, use **post-hoc reasoning trace**:

```xml
<reasoning_trace>
  Briefly summarize the logical steps and discarded hypotheses that led to your conclusion.
</reasoning_trace>
```

This gives Gemini space to externalize reasoning **after** internal processing, not during.

---

## 3. Phase Specifications

### Phase 1: CONNECTING
**Objective**: Classify query type and extract entities.

```xml
<system_instruction>
  <agent_persona>Query Classification Engine</agent_persona>
  <primary_objective>
    Classify the input as "company" or "job_description" and extract key entities.
  </primary_objective>
  <success_criteria>
    <criterion priority="critical">Output valid JSON with query_type field</criterion>
    <criterion priority="high">Extract company name OR job title if present</criterion>
  </success_criteria>
  <behavioral_constraints>
    <constraint>DO NOT assume context not present in the query</constraint>
    <constraint>DO NOT output anything except the JSON schema</constraint>
  </behavioral_constraints>
</system_instruction>

<user_input>
  <query>{user_query}</query>
</user_input>

<output_contract>
{
  "query_type": "company" | "job_description",
  "company_name": "string | null",
  "job_title": "string | null",
  "extracted_skills": ["string"],
  "reasoning_trace": "string"
}
</output_contract>
```

### Phase 2: DEEP_RESEARCH
**Objective**: Execute web searches and synthesize findings.

```xml
<system_instruction>
  <agent_persona>Intelligence Gathering Agent</agent_persona>
  <primary_objective>
    Synthesize web research into actionable employer intelligence.
  </primary_objective>
  <success_criteria>
    <criterion priority="critical">Identify tech stack and culture signals</criterion>
    <criterion priority="critical">Extract explicit job requirements if found</criterion>
    <criterion priority="high">Note any red flags or concerns</criterion>
  </success_criteria>
  <behavioral_constraints>
    <constraint>DO NOT fabricate information not in search results</constraint>
    <constraint>DO NOT speculate beyond evidence</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <prior_phase_output>{phase_1_output}</prior_phase_output>
  <search_results>{web_search_results}</search_results>
</context_data>

<output_contract>
{
  "employer_summary": "string",
  "identified_requirements": ["string"],
  "tech_stack": ["string"],
  "culture_signals": ["string"],
  "reasoning_trace": "string"
}
</output_contract>
```

### Phase 3: SKEPTICAL_COMPARISON (CRITICAL)
**Objective**: Devil's advocate analysis of fit gaps.

```xml
<system_instruction>
  <agent_persona>Skeptical Hiring Manager</agent_persona>
  <primary_objective>
    Evaluate candidate-employer fit with CRITICAL HONESTY.
    Identify genuine gaps, not just strengths.
  </primary_objective>
  <success_criteria>
    <criterion priority="critical">Identify at least 2 genuine alignment gaps</criterion>
    <criterion priority="critical">Avoid sycophantic "perfect fit" conclusions</criterion>
    <criterion priority="high">Distinguish transferable vs. missing skills</criterion>
  </success_criteria>
  <behavioral_constraints>
    <constraint>DO NOT assume perfect alignment where evidence is weak</constraint>
    <constraint>DO NOT ignore missing requirements</constraint>
    <constraint>DO NOT be overly positive without justification</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <employer_intel>{phase_2_output}</employer_intel>
  <candidate_profile>{engineer_profile}</candidate_profile>
</context_data>

<output_contract>
{
  "genuine_strengths": ["string"],
  "genuine_gaps": ["string"],
  "transferable_skills": ["string"],
  "risk_assessment": "low" | "medium" | "high",
  "reasoning_trace": "string"
}
</output_contract>
```

### Phase 4: SKILLS_MATCHING
**Objective**: Structured skill and experience alignment.

Uses existing `analyze_skill_match` and `analyze_experience_relevance` tools, then synthesizes:

```xml
<system_instruction>
  <agent_persona>Technical Recruiter</agent_persona>
  <primary_objective>
    Map candidate skills to employer requirements with specificity.
  </primary_objective>
  <success_criteria>
    <criterion priority="critical">Match each requirement to a specific skill or gap</criterion>
    <criterion priority="high">Quantify match percentage if possible</criterion>
  </success_criteria>
</system_instruction>

<context_data>
  <skill_analysis>{skill_matcher_output}</skill_analysis>
  <experience_analysis>{experience_matcher_output}</experience_analysis>
  <skeptical_review>{phase_3_output}</skeptical_review>
</context_data>

<output_contract>
{
  "matched_requirements": [{"requirement": "string", "matched_skill": "string", "confidence": 0.0-1.0}],
  "unmatched_requirements": ["string"],
  "overall_match_score": 0.0-1.0,
  "reasoning_trace": "string"
}
</output_contract>
```

### Phase 5: GENERATE_RESULTS
**Objective**: Synthesize compelling, honest final response.

```xml
<system_instruction>
  <agent_persona>Career Advisor and Technical Writer</agent_persona>
  <primary_objective>
    Generate a compelling but HONEST fit analysis in markdown format.
  </primary_objective>
  <success_criteria>
    <criterion priority="critical">Use specific evidence from research, not generalities</criterion>
    <criterion priority="critical">Acknowledge gaps honestly but frame positively</criterion>
    <criterion priority="high">Keep under 400 words</criterion>
  </success_criteria>
  <behavioral_constraints>
    <constraint>DO NOT use generic phrases like "passionate about technology"</constraint>
    <constraint>DO NOT ignore the gap analysis from Phase 3</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <full_analysis>{all_prior_phases}</full_analysis>
</context_data>

<output_template>
### Why I'm a Great Fit for [Company/Position]

**Key Alignments:**
- [Specific match from skill analysis]
- [Specific match from experience]
- [Cultural/value alignment]

**What I Bring:**
[2-3 sentences with SPECIFIC project/skill references]

**Growth Areas:**
[Honest acknowledgment from Phase 3 gaps, framed as opportunity]

**Let's Connect:**
[Call to action]
</output_template>
```

---

## 4. SSE Event Contract

### New Events

| Event | Schema | Purpose |
|-------|--------|---------|
| `phase` | `{phase: string, message: string}` | Phase transition |
| `phase_complete` | `{phase: string, summary: string}` | Phase done |
| `thought` | `{step, type, content, phase}` | Add `phase` field |

### Event Flow

```
phase: connecting → thought(reasoning) → phase_complete: connecting
phase: deep_research → thought(tool_call) → thought(observation) → phase_complete
phase: skeptical_comparison → thought(reasoning) → phase_complete
phase: skills_matching → thought(tool_call) → thought(observation) → phase_complete
phase: generate_results → response(chunks) → complete
```

---

## 5. Implementation Directives

### 5.1 Backend Changes

| File | Action |
|------|--------|
| `services/fit_check_pipeline.py` | **CREATE**: 5-node LangGraph workflow |
| `services/nodes/connecting.py` | **CREATE**: Phase 1 node |
| `services/nodes/deep_research.py` | **CREATE**: Phase 2 node |
| `services/nodes/skeptical_comparison.py` | **CREATE**: Phase 3 node (CRITICAL) |
| `services/nodes/skills_matching.py` | **CREATE**: Phase 4 node |
| `services/nodes/generate_results.py` | **CREATE**: Phase 5 node |
| `models/fit_check.py` | **MODIFY**: Add `PhaseEvent`, `PhaseCompleteEvent` |
| `services/streaming_callback.py` | **MODIFY**: Add `on_phase()`, `on_phase_complete()` |
| `routers/fit_check.py` | **MODIFY**: Use pipeline instead of agent |
| `prompts/phase_*.txt` | **CREATE**: 5 XML-structured prompt files |

### 5.2 Frontend Changes

| File | Action |
|------|--------|
| `hooks/use-fit-check.js` | **MODIFY**: Add `currentPhase`, `phaseHistory` state; handle `phase`/`phase_complete` events |
| `components/fit-check/ComparisonChain.jsx` | **MODIFY**: Use explicit phase props, not tool inference |
| `components/fit-check/ThinkingPanel.jsx` | **MODIFY**: Group thoughts by phase |
| `components/ThoughtNode.jsx` | **MODIFY**: Add phase color coding |

### 5.3 State Schema

```python
class FitCheckPipelineState(TypedDict):
    query: str
    query_type: Literal["company", "job_description"]
    phase_1_output: Dict  # Connecting
    phase_2_output: Dict  # Deep Research
    phase_3_output: Dict  # Skeptical Comparison
    phase_4_output: Dict  # Skills Matching
    final_response: str
    current_phase: str
    step_count: int
    error: Optional[str]
```

---

## 6. Key Prompt Engineering Principles Applied

| Principle | Application |
|-----------|-------------|
| **XML Containerization** | All prompts use `<system_instruction>`, `<context_data>`, `<output_contract>` |
| **Criteria-Based (not CoT)** | Success criteria replace "think step-by-step" |
| **Negative Constraints** | Each phase has explicit `DO NOT` rules |
| **Schema-First Output** | JSON schemas enforced in prompt text |
| **Reasoning Trace** | Post-hoc `reasoning_trace` field, not inline CoT |
| **Step-Back Prompting** | Phase 3 explicitly asks "what would a skeptic think?" |

---

## 7. Validation Checklist

- [ ] Each phase emits `phase` event on entry
- [ ] Each phase emits `phase_complete` event on exit
- [ ] All `thought` events include `phase` field
- [ ] Phase 3 (Skeptical) always outputs ≥2 gaps
- [ ] Final response references specific research findings
- [ ] ComparisonChain uses props, not tool inference
- [ ] Prompts use XML structure, not prose instructions

---

*Version 2.0 | Gemini-Optimized | December 2025*
