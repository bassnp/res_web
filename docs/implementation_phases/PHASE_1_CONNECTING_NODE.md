# Phase 1: CONNECTING Node Implementation

> **Objective**: Classify the user query as either "company" or "job_description" and extract structured entities for downstream processing.

---

## 1. Phase Overview

### 1.1 Desire Statement

**Desire: Data Integrity & Semantic Classification**

The Connecting node is the gatekeeper of the pipeline. Its sole purpose is to transform the unstructured user query into a pristine, structured context object that downstream agents can rely upon. If this node fails, the entire pipeline is poisoned.

### 1.2 Inputs & Outputs

| Direction | Data |
|-----------|------|
| **Input** | `state.query` - Raw user input (3-2000 chars) |
| **Output** | `Phase1Output` - Classified type, entities, extracted skills |

---

## 2. File Location & Structure

```
res_backend/
├── services/
│   └── nodes/
│       └── connecting.py     # THIS FILE
└── prompts/
    └── phase_1_connecting.xml
```

---

## 3. XML-Structured Prompt Template

```xml
<!-- Location: res_backend/prompts/phase_1_connecting.xml -->

<system_instruction>
  <agent_persona>
    You are a Query Classification Engine specializing in employment context analysis.
    Your expertise is parsing free-form text to identify employer-related entities.
  </agent_persona>
  
  <primary_objective>
    Classify the user input as either a "company" name lookup or a "job_description" analysis,
    and extract all relevant entities with high precision.
  </primary_objective>
  
  <success_criteria>
    <criterion priority="critical">Output MUST be valid JSON matching the exact schema</criterion>
    <criterion priority="critical">query_type MUST be exactly "company" or "job_description"</criterion>
    <criterion priority="high">Extract company_name if input references a known company</criterion>
    <criterion priority="high">Extract job_title if input contains a role/position</criterion>
    <criterion priority="medium">Extract any mentioned technical skills into extracted_skills array</criterion>
  </success_criteria>
  
  <behavioral_constraints>
    <constraint>DO NOT assume context not explicitly present in the query</constraint>
    <constraint>DO NOT hallucinate company names or job titles that aren't mentioned</constraint>
    <constraint>DO NOT output anything except the JSON schema - no prose, no explanation</constraint>
    <constraint>DO NOT include markdown code blocks - output raw JSON only</constraint>
  </behavioral_constraints>
  
  <classification_rules>
    <rule>If input is 1-4 words and matches a known company pattern → "company"</rule>
    <rule>If input mentions job duties, requirements, or "looking for" → "job_description"</rule>
    <rule>If input contains "engineer", "developer", "manager" with context → "job_description"</rule>
    <rule>If input is just a company name with no job context → "company"</rule>
    <rule>If ambiguous, default to "job_description" with extracted context</rule>
  </classification_rules>
</system_instruction>

<user_input>
  <query>{query}</query>
</user_input>

<output_contract>
  Output strictly valid JSON matching this exact schema (no markdown, no code blocks):
  {{
    "query_type": "company" | "job_description",
    "company_name": "string | null",
    "job_title": "string | null",
    "extracted_skills": ["string"],
    "reasoning_trace": "string (1-2 sentences explaining classification logic)"
  }}
</output_contract>
```

---

## 4. Node Implementation

```python
"""
Connecting Node - Phase 1 of the Fit Check Pipeline.

This module implements the query classification node that:
1. Classifies input as "company" or "job_description"
2. Extracts entities (company name, job title, skills)
3. Provides structured output for downstream phases

Gemini Optimization:
- Uses XML-structured prompt with criteria-based constraints
- No "think step-by-step" instructions (anti-pattern)
- Reasoning trace as post-hoc field, not inline CoT
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from config.llm import get_llm
from services.pipeline_state import FitCheckPipelineState, Phase1Output
from services.fit_check_agent import ThoughtCallback

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "connecting"
PROMPT_FILE = Path(__file__).parent.parent.parent / "prompts" / "phase_1_connecting.xml"


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt() -> str:
    """
    Load the Phase 1 XML prompt template.
    
    Returns:
        str: XML-structured prompt template.
    
    Raises:
        FileNotFoundError: If prompt file doesn't exist.
    """
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Phase 1 prompt not found at {PROMPT_FILE}, using embedded fallback")
        return get_fallback_prompt()


def get_fallback_prompt() -> str:
    """Embedded fallback prompt if file not found."""
    return """<system_instruction>
  <agent_persona>Query Classification Engine</agent_persona>
  <primary_objective>
    Classify input as "company" or "job_description" and extract entities.
  </primary_objective>
  <behavioral_constraints>
    <constraint>Output only valid JSON, no markdown</constraint>
  </behavioral_constraints>
</system_instruction>

<user_input><query>{query}</query></user_input>

<output_contract>
{{"query_type": "company" | "job_description", "company_name": "string|null", 
  "job_title": "string|null", "extracted_skills": [], "reasoning_trace": "string"}}
</output_contract>"""


# =============================================================================
# JSON Parsing Utilities
# =============================================================================

def extract_json_from_response(response: str) -> Dict[str, Any]:
    """
    Extract JSON from LLM response, handling various formats.
    
    Args:
        response: Raw LLM response text.
    
    Returns:
        Parsed JSON dictionary.
    
    Raises:
        ValueError: If JSON cannot be extracted or parsed.
    """
    # Strip whitespace
    text = response.strip()
    
    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from markdown code blocks
    json_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    matches = re.findall(json_pattern, text)
    if matches:
        try:
            return json.loads(matches[0])
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object in text
    brace_pattern = r'\{[\s\S]*\}'
    matches = re.findall(brace_pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")


def validate_phase1_output(data: Dict[str, Any]) -> Phase1Output:
    """
    Validate and normalize Phase 1 output.
    
    Args:
        data: Raw parsed JSON from LLM.
    
    Returns:
        Validated Phase1Output TypedDict.
    
    Raises:
        ValueError: If required fields are missing or invalid.
    """
    # Validate query_type
    query_type = data.get("query_type")
    if query_type not in ("company", "job_description"):
        # Attempt recovery based on content
        if data.get("company_name") and not data.get("job_title"):
            query_type = "company"
        else:
            query_type = "job_description"
    
    # Normalize fields
    return Phase1Output(
        query_type=query_type,
        company_name=data.get("company_name") or None,
        job_title=data.get("job_title") or None,
        extracted_skills=data.get("extracted_skills") or [],
        reasoning_trace=data.get("reasoning_trace") or "Classification completed.",
    )


# =============================================================================
# Main Node Function
# =============================================================================

async def connecting_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 1: CONNECTING - Query Classification Node.
    
    Classifies the user query and extracts structured entities.
    
    Args:
        state: Current pipeline state with user query.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update with phase_1_output and phase transition.
    
    Emits:
        - phase: "connecting" at start
        - thought: reasoning step
        - phase_complete: with classification summary
    """
    logger.info(f"[CONNECTING] Starting phase 1 for query: {state['query'][:50]}...")
    step = state.get("step_count", 0) + 1
    
    # Emit phase start
    if callback:
        await callback.on_phase(
            PHASE_NAME,
            "Classifying query and extracting entities..."
        )
    
    try:
        # Load and format prompt
        prompt_template = load_phase_prompt()
        prompt = prompt_template.format(query=state["query"])
        
        # Get LLM (non-streaming for structured output)
        llm = get_llm(streaming=False, temperature=0.1)  # Low temp for classification
        
        # Emit reasoning thought
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content="Analyzing query structure to determine classification...",
                phase=PHASE_NAME,
            )
        
        # Invoke LLM
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)
        
        # Parse response
        response_text = response.content if hasattr(response, 'content') else str(response)
        parsed_data = extract_json_from_response(response_text)
        validated_output = validate_phase1_output(parsed_data)
        
        # Emit phase complete
        if callback:
            summary = f"Query classified as '{validated_output['query_type']}'"
            if validated_output["company_name"]:
                summary += f", company: {validated_output['company_name']}"
            if validated_output["job_title"]:
                summary += f", role: {validated_output['job_title']}"
            if validated_output["extracted_skills"]:
                summary += f", skills: {len(validated_output['extracted_skills'])} extracted"
            
            await callback.on_phase_complete(PHASE_NAME, summary)
        
        logger.info(f"[CONNECTING] Phase 1 complete: {validated_output['query_type']}")
        
        return {
            "phase_1_output": validated_output,
            "current_phase": "deep_research",
            "step_count": step,
        }
        
    except Exception as e:
        logger.error(f"[CONNECTING] Phase 1 failed: {e}")
        
        # Attempt graceful degradation
        fallback_output = Phase1Output(
            query_type="job_description",  # Default to broader analysis
            company_name=None,
            job_title=None,
            extracted_skills=[],
            reasoning_trace=f"Classification failed, defaulting to job_description: {str(e)}",
        )
        
        if callback:
            await callback.on_phase_complete(
                PHASE_NAME,
                f"Classification defaulted (error: {str(e)[:50]})"
            )
        
        return {
            "phase_1_output": fallback_output,
            "current_phase": "deep_research",
            "step_count": step,
            "processing_errors": state.get("processing_errors", []) + [f"Phase 1 error: {str(e)}"],
        }
```

---

## 5. Unit Tests

```python
"""
Unit tests for Phase 1: CONNECTING node.

Location: res_backend/tests/test_connecting_node.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.nodes.connecting import (
    connecting_node,
    extract_json_from_response,
    validate_phase1_output,
)
from services.pipeline_state import create_initial_state


class TestJSONExtraction:
    """Test JSON extraction from various LLM response formats."""
    
    def test_clean_json(self):
        """Direct JSON should parse correctly."""
        response = '{"query_type": "company", "company_name": "Google"}'
        result = extract_json_from_response(response)
        assert result["query_type"] == "company"
        assert result["company_name"] == "Google"
    
    def test_json_with_markdown(self):
        """JSON in markdown code blocks should parse."""
        response = '```json\n{"query_type": "company", "company_name": "Stripe"}\n```'
        result = extract_json_from_response(response)
        assert result["company_name"] == "Stripe"
    
    def test_json_with_surrounding_text(self):
        """JSON with surrounding prose should be extracted."""
        response = 'Here is my analysis:\n{"query_type": "job_description"}\nDone!'
        result = extract_json_from_response(response)
        assert result["query_type"] == "job_description"
    
    def test_invalid_json_raises(self):
        """Invalid JSON should raise ValueError."""
        with pytest.raises(ValueError):
            extract_json_from_response("This is not JSON at all")


class TestOutputValidation:
    """Test Phase 1 output validation and normalization."""
    
    def test_valid_company_output(self):
        """Valid company query should validate correctly."""
        data = {
            "query_type": "company",
            "company_name": "OpenAI",
            "job_title": None,
            "extracted_skills": ["Python", "ML"],
            "reasoning_trace": "Single company name detected.",
        }
        result = validate_phase1_output(data)
        assert result["query_type"] == "company"
        assert result["company_name"] == "OpenAI"
    
    def test_invalid_query_type_recovery(self):
        """Invalid query_type should recover based on content."""
        data = {
            "query_type": "invalid",
            "company_name": "Meta",
            "job_title": None,
        }
        result = validate_phase1_output(data)
        assert result["query_type"] == "company"  # Recovered
    
    def test_missing_fields_default(self):
        """Missing optional fields should default correctly."""
        data = {"query_type": "job_description"}
        result = validate_phase1_output(data)
        assert result["company_name"] is None
        assert result["extracted_skills"] == []


class TestConnectingNode:
    """Integration tests for the connecting node."""
    
    @pytest.mark.asyncio
    async def test_company_classification(self):
        """Company name query should classify correctly."""
        state = create_initial_state("Google")
        
        mock_response = MagicMock()
        mock_response.content = '{"query_type": "company", "company_name": "Google", "reasoning_trace": "Single company name"}'
        
        with patch("services.nodes.connecting.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await connecting_node(state)
            
            assert result["phase_1_output"]["query_type"] == "company"
            assert result["phase_1_output"]["company_name"] == "Google"
            assert result["current_phase"] == "deep_research"
    
    @pytest.mark.asyncio
    async def test_job_description_classification(self):
        """Job description should classify with skills extraction."""
        state = create_initial_state("Senior Python developer with AWS experience at a startup")
        
        mock_response = MagicMock()
        mock_response.content = '''
        {"query_type": "job_description", 
         "job_title": "Senior Python developer",
         "extracted_skills": ["Python", "AWS"],
         "reasoning_trace": "Job requirements detected"}
        '''
        
        with patch("services.nodes.connecting.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await connecting_node(state)
            
            assert result["phase_1_output"]["query_type"] == "job_description"
            assert "Python" in result["phase_1_output"]["extracted_skills"]
    
    @pytest.mark.asyncio
    async def test_callback_events_emitted(self):
        """Callback should receive phase and thought events."""
        state = create_initial_state("Stripe")
        callback = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '{"query_type": "company", "company_name": "Stripe"}'
        
        with patch("services.nodes.connecting.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            await connecting_node(state, callback=callback)
            
            # Verify callback methods were called
            callback.on_phase.assert_called_once()
            callback.on_thought.assert_called()
            callback.on_phase_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_graceful_degradation(self):
        """Errors should result in graceful fallback."""
        state = create_initial_state("test query")
        
        with patch("services.nodes.connecting.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))
            
            result = await connecting_node(state)
            
            # Should still return valid output with fallback
            assert result["phase_1_output"]["query_type"] == "job_description"
            assert "processing_errors" in result
            assert len(result["processing_errors"]) > 0
```

---

## 6. Prompt File Creation

Create the actual prompt file at `res_backend/prompts/phase_1_connecting.xml` with the XML content from Section 3.

---

## 7. Validation Checklist

Before proceeding to Phase 2:

- [ ] `services/nodes/connecting.py` created and importable
- [ ] `prompts/phase_1_connecting.xml` created
- [ ] Node function accepts `FitCheckPipelineState` and returns state update
- [ ] Callback events emit `phase`, `thought`, `phase_complete`
- [ ] JSON extraction handles various LLM response formats
- [ ] Graceful degradation on errors (no hard failures)
- [ ] Unit tests pass

---

## 8. Edge Cases Handled

| Edge Case | Handling |
|-----------|----------|
| Single word company name | Classify as "company" |
| Long job description | Parse and extract entities |
| Ambiguous input | Default to "job_description" |
| LLM returns markdown | Strip code blocks, extract JSON |
| LLM error | Return fallback classification, log error |
| Empty/null fields | Normalize to None or empty list |

---

## 9. Performance Considerations

- **Temperature**: 0.1 (low) for deterministic classification
- **Max Tokens**: Limited output (JSON schema is small)
- **Caching**: Consider caching for identical queries
- **Timeout**: 10s maximum for this phase

---

## 10. Next Steps

After implementing this phase:
1. Proceed to **PHASE_2_DEEP_RESEARCH_NODE.md**
2. The Deep Research node will use `phase_1_output` to construct appropriate search queries
3. Company name vs job description determines search strategy

---

## 11. Build Verification Gate

> ⛔ **STOP**: Do NOT proceed to the next phase until this phase compiles and builds successfully.

### Backend Build Verification

```powershell
# Navigate to backend directory
cd res_backend

# Verify Python syntax
python -m py_compile services/nodes/connecting.py

# Verify imports work
python -c "from services.nodes.connecting import connecting_node; print('Phase 1 imports OK')"

# Run Phase 1 unit tests
pytest tests/unit/test_connecting_node.py -v

# Run all tests (ensure no regressions)
pytest --tb=short
```

### Verification Checklist

- [ ] `services/nodes/connecting.py` created and has no syntax errors
- [ ] `prompts/phase_1_connecting.xml` created
- [ ] Import verification succeeds
- [ ] Phase 1 unit tests pass
- [ ] All existing tests still pass
- [ ] No import or circular dependency errors

---

## 12. Requirements Tracking

> 📋 **IMPORTANT**: Refer to **[TRACK_ALL_REQUIREMENTS.md](./TRACK_ALL_REQUIREMENTS.md)** for the complete requirements checklist.

### After Completing This Phase:

1. Open `TRACK_ALL_REQUIREMENTS.md`
2. Locate the **Phase 1: CONNECTING Node** section
3. Mark each completed requirement with ✅
4. Fill in the "Verified By" and "Date" columns
5. Complete the **Build Verification** checkboxes
6. Update the **Completion Summary** table at the bottom

### Phase 1 Requirement IDs to Update:

- P1-001 through P1-012

---

*Document Version: 1.1 | Phase 1 of 7 | Query Classification*
