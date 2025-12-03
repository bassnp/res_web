# Prompt Size Optimization Strategy

> **Status**: ✅ IMPLEMENTED  
> **Priority**: Critical  
> **Last Updated**: December 3, 2025

---

## Executive Summary

The Fit Check pipeline was experiencing **timeout issues with Gemini 3 Pro** due to overly verbose XML prompts. The extensive documentation and behavioral constraints in the original prompts caused the model's native reasoning to "double-think" - performing both internal reasoning AND following verbose procedural instructions, leading to LLM call timeouts.

### Solution Implemented

Created a **dynamic prompt selection system** that loads model-appropriate prompts:
- **Reasoning models (Gemini 3 Pro)**: Concise, objective-based prompts
- **Standard models (Flash/Flash-Lite)**: Verbose, schema-focused prompts with examples

---

## Problem Analysis

### Root Cause: Gemini 3 Pro "Double-Think" Anti-Pattern

Per the Gemini prompt engineering research:

> **"For Gemini 3 Pro, the instruction 'Let's think step by step' is now considered an anti-pattern."**

The original prompts violated this by:
1. Including extensive `<behavioral_constraints>` sections
2. Providing detailed `<step_back_evaluation>` procedures
3. Including verbose XML documentation that forced procedural thinking

This caused Gemini 3 Pro to:
1. Perform internal hidden Chain-of-Thought (CoT) reasoning
2. ALSO attempt to follow verbose procedural instructions
3. Result in excessive token generation and timeouts

### Evidence

- Deep Research phase consistently timing out with Gemini 3 Pro
- `thinking_budget: 10000` being exhausted before completion
- Original prompts averaging 2000+ tokens vs. 500 tokens for concise variants

---

## Architecture: Dynamic Prompt Selection

### File Structure

```
res_backend/prompts/
├── phase_1_connecting.xml           # Verbose (Flash/Flash-Lite)
├── phase_1_connecting_concise.xml   # Concise (Gemini 3 Pro)
├── phase_2_deep_research.xml
├── phase_2_deep_research_concise.xml
├── phase_2b_research_reranker.xml
├── phase_2b_research_reranker_concise.xml
├── phase_3_skeptical_comparison.xml
├── phase_3_skeptical_comparison_concise.xml
├── phase_4_skills_matching.xml
├── phase_4_skills_matching_concise.xml
├── phase_5_generate_results.xml
├── phase_5_generate_results_concise.xml
├── phase_5b_confidence_reranker.xml
└── phase_5b_confidence_reranker_concise.xml
```

### Selection Logic

```python
# services/prompt_loader.py

def load_prompt(phase_name, config_type=None, prefer_concise=True):
    """
    Selection Logic:
    - config_type="reasoning" + prefer_concise → phase_X_concise.xml
    - config_type="standard" → phase_X.xml (verbose)
    - Fallback to verbose if concise not found
    """
```

### Integration Points

Each node passes `config_type` from the pipeline state:

```python
# Example from deep_research.py
config_type = state.get("config_type")
prompt_template = load_phase_prompt(config_type=config_type)
```

---

## Prompt Design Guidelines

### For Reasoning Models (Gemini 3 Pro)

**DO:**
- State the **objective** and **criteria** clearly
- Use `<accuracy_mandate>` for effort emphasis
- Include strict `<output_contract>` with JSON schema
- Use "Take a deep breath" for reflective pause
- Keep total prompt under 800 tokens

**DON'T:**
- Use "think step by step" or procedural instructions
- Include verbose behavioral constraint lists
- Add extensive documentation comments
- Use `<step_back_evaluation>` procedural blocks

**Example Structure:**
```xml
<agent>Role Name</agent>
<objective>What to accomplish</objective>
<criteria>Success criteria (numbered)</criteria>
<constraints>Critical DO NOT rules only</constraints>
<accuracy_mandate>Effort emphasis for quick, accurate answers</accuracy_mandate>
<input>Context data</input>
<output_contract>Strict JSON schema</output_contract>
```

### For Standard Models (Flash/Flash-Lite)

**DO:**
- Include few-shot examples
- Provide explicit XML containerization
- Use verbose `<behavioral_constraints>` sections
- Include `<success_criteria>` with priorities
- Add `<guidance>` sections for complex tasks

**DON'T:**
- Assume the model will reason internally
- Skip examples for complex output formats
- Use abstract objectives without procedures

---

## Model Configuration Reference

### From `config/llm.py`

```python
SUPPORTED_MODELS = {
    "gemini-3-pro-preview": {
        "config_type": "reasoning",        # → Uses concise prompts
        "description": "Advanced reasoning with deep analysis",
    },
    "gemini-flash-latest": {
        "config_type": "standard",         # → Uses verbose prompts
        "description": "Fast responses with balanced accuracy",
    },
}
```

### Thinking Budget Configuration

```python
if config_type == "reasoning":
    model_kwargs["thinking_config"] = {"thinking_budget": 10000}
    temp = 1.0  # Gemini 3 Pro works best with temperature 1.0
else:
    temp = temperature or DEFAULT_TEMPERATURE
    model_kwargs["top_k"] = DEFAULT_TOP_K
```

---

## Prompt Token Comparison

| Phase | Verbose Tokens | Concise Tokens | Reduction |
|-------|----------------|----------------|-----------|
| Phase 1: Connecting | ~1,800 | ~450 | 75% |
| Phase 2: Deep Research | ~2,100 | ~550 | 74% |
| Phase 2B: Research Reranker | ~3,500 | ~700 | 80% |
| Phase 3: Skeptical Comparison | ~2,800 | ~600 | 79% |
| Phase 4: Skills Matching | ~2,400 | ~650 | 73% |
| Phase 5: Generate Results | ~2,600 | ~600 | 77% |
| Phase 5B: Confidence Reranker | ~2,200 | ~550 | 75% |

**Total Pipeline Reduction: ~76% fewer prompt tokens for reasoning models**

---

## Testing Verification

### Timeout Scenarios to Test

1. **Company Query (Google, Anthropic, OpenAI)**
   - Should complete all 7 phases without timeout
   - Expected: <30 seconds total pipeline time

2. **Job Description Query**
   - Longer research phase, more synthesis
   - Expected: <45 seconds total pipeline time

3. **Obscure Company Query**
   - May trigger ENHANCE_SEARCH retry
   - Expected: <60 seconds with retry

### Validation Checklist

- [ ] Gemini 3 Pro completes Deep Research without timeout
- [ ] Research Reranker correctly routes based on quality
- [ ] Confidence scores are properly calibrated
- [ ] JSON output is always valid (no markdown wrapping)
- [ ] All 7 phases emit proper SSE events

---

## Future Maintenance

### Adding New Prompts

1. Create verbose version: `phase_X_new.xml`
2. Create concise version: `phase_X_new_concise.xml`
3. Add constant to `prompt_loader.py`: `PHASE_NEW = "phase_X_new"`
4. Use `load_prompt(PHASE_NEW, config_type)` in node

### Model Updates

When new Gemini models are released:
1. Update `SUPPORTED_MODELS` in `config/llm.py`
2. Set appropriate `config_type` based on model capabilities
3. Test prompt variants with new model
4. Adjust concise prompts if needed

---

## References

- `A Comprehensive Technical Analysis of Advanced Prompt Engineering for the Google Gemini Ecosystem.md`
- `A Prompt Engineering Research and Meta-Prompt.md`
- `TODO_DEEPER_RESEARCH.md` - Research Reranker implementation details
- `SUMMARY_INTERACTIVE_RESUME.MD` - Full pipeline documentation
