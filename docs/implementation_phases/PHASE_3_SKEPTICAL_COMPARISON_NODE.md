# Phase 3: SKEPTICAL_COMPARISON Node Implementation

> **Objective**: Perform critical, devil's advocate analysis to identify genuine fit gaps, prevent sycophantic outputs, and provide an honest risk assessment.

---

## ⚠️ CRITICAL PHASE

This is the **most important** phase of the pipeline. It is designed to counter the natural tendency of LLMs to be overly positive and agreeable. Without this phase, the fit analysis would be meaningless flattery.

---

## 1. Phase Overview

### 1.1 Desire Statement

**Desire: Veracity & Risk Assessment (Adversarial Defense)**

The Skeptical Comparison agent is the devil's advocate. It operates under the assumption that the previous phases may have overstated alignment. Its desire is to identify genuine gaps, transferable skills, and provide an honest risk assessment that prevents the final output from being sycophantic.

### 1.2 Critical Design Principle

> **This phase MUST identify at least 2 genuine gaps, even for excellent candidates.**
> 
> A "perfect fit" conclusion is almost always a sign of insufficient analysis.

### 1.3 Inputs & Outputs

| Direction | Data |
|-----------|------|
| **Input** | `state.phase_2_output` - Employer intelligence from Deep Research |
| **Input** | `ENGINEER_PROFILE` - Static engineer profile data |
| **Output** | `Phase3Output` - Strengths, gaps, transferable skills, risk assessment |

---

## 2. The Sycophancy Problem

### 2.1 Why This Phase Exists

LLMs are trained on human feedback that rewards agreeable, positive responses. This creates a systematic bias toward:

- Overstating qualifications
- Minimizing or ignoring gaps
- Using vague positive language ("great fit!", "perfect alignment!")
- Avoiding critical assessment

### 2.2 Counter-Measures Implemented

1. **Role as Skeptical Hiring Manager**: Frame the agent as someone looking for reasons to reject
2. **Mandatory Gap Requirement**: Output schema requires at least 2 gaps
3. **Negative Constraints**: Explicit prohibitions against sycophantic patterns
4. **Step-Back Prompting**: "What would a critical evaluator notice?"

---

## 3. File Location & Structure

```
res_backend/
├── services/
│   └── nodes/
│       └── skeptical_comparison.py    # THIS FILE
└── prompts/
    └── phase_3_skeptical_comparison.xml
```

---

## 4. XML-Structured Prompt Template

```xml
<!-- Location: res_backend/prompts/phase_3_skeptical_comparison.xml -->

<system_instruction>
  <agent_persona>
    You are a Skeptical Hiring Manager with 15 years of experience evaluating
    software engineering candidates. You are known for your rigorous, fair, but 
    CRITICAL evaluation style. You do NOT rubber-stamp candidates.
    
    Your role is to find GENUINE GAPS, not to validate the candidate.
  </agent_persona>
  
  <primary_objective>
    Evaluate candidate-employer fit with CRITICAL HONESTY. Your job is to identify
    what could go wrong, what's missing, and what the real risks are.
    
    A good evaluation finds both strengths AND meaningful gaps.
  </primary_objective>
  
  <success_criteria>
    <criterion priority="critical">Identify AT LEAST 2 genuine alignment gaps</criterion>
    <criterion priority="critical">Avoid sycophantic "perfect fit" conclusions</criterion>
    <criterion priority="critical">Distinguish between hard skill gaps and transferable skills</criterion>
    <criterion priority="high">Provide honest risk_assessment (low/medium/high)</criterion>
    <criterion priority="high">Be specific - no vague "could improve communication"</criterion>
  </success_criteria>
  
  <behavioral_constraints>
    <constraint>DO NOT assume perfect alignment where evidence is weak or missing</constraint>
    <constraint>DO NOT ignore missing requirements from the employer's tech stack</constraint>
    <constraint>DO NOT be overly positive without concrete justification</constraint>
    <constraint>DO NOT use phrases like "excellent fit", "perfect match", "ideal candidate"</constraint>
    <constraint>DO NOT list the same strength in multiple ways to pad the list</constraint>
    <constraint>DO NOT frame every gap as "just needs a little learning"</constraint>
  </behavioral_constraints>
  
  <analysis_framework>
    <step>1. List explicit requirements from employer intel</step>
    <step>2. For each requirement, check: Does candidate have direct evidence? Partial? None?</step>
    <step>3. Identify requirements where candidate has NO evidence - these are gaps</step>
    <step>4. For gaps, determine: Is this learnable in &lt;3 months? Or a fundamental mismatch?</step>
    <step>5. Assign risk: low (minor gaps), medium (some learning needed), high (significant gaps)</step>
  </analysis_framework>
  
  <step_back_question>
    Before concluding, ask yourself: "If I were the hiring manager defending this hire 
    to my VP, what concerns would they raise? What would make me hesitate?"
  </step_back_question>
</system_instruction>

<context_data>
  <employer_intel>
    Summary: {employer_summary}
    
    Required Skills/Tech: {identified_requirements}
    
    Tech Stack: {tech_stack}
    
    Culture Signals: {culture_signals}
  </employer_intel>
  
  <candidate_profile>
    {engineer_profile}
  </candidate_profile>
</context_data>

<output_contract>
  Output strictly valid JSON matching this exact schema (no markdown, no code blocks):
  {{
    "genuine_strengths": [
      "string (specific strength with evidence, max 4)"
    ],
    "genuine_gaps": [
      "string (specific gap that is a real concern, MINIMUM 2 REQUIRED)"
    ],
    "transferable_skills": [
      "string (skills that partially address gaps)"
    ],
    "risk_assessment": "low" | "medium" | "high",
    "risk_justification": "string (1-2 sentences explaining risk level)",
    "reasoning_trace": "string (summary of critical analysis process)"
  }}
  
  REMINDER: genuine_gaps MUST have at least 2 items. 
  If you cannot identify gaps, you are not being critical enough.
</output_contract>
```

---

## 5. Node Implementation

```python
"""
Skeptical Comparison Node - Phase 3 of the Fit Check Pipeline.

This module implements the CRITICAL devil's advocate node that:
1. Analyzes fit with intentional skepticism
2. Identifies genuine gaps (minimum 2 required)
3. Prevents sycophantic "perfect fit" outputs
4. Provides honest risk assessment

Gemini Optimization:
- Uses Step-Back prompting ("What would a critical evaluator notice?")
- Negative constraints to prevent agreeable patterns
- Mandatory gap requirements in output schema
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from langchain_core.messages import HumanMessage

from config.llm import get_llm
from config.engineer_profile import get_formatted_profile
from services.pipeline_state import FitCheckPipelineState, Phase3Output
from services.fit_check_agent import ThoughtCallback

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "skeptical_comparison"
PROMPT_FILE = Path(__file__).parent.parent.parent / "prompts" / "phase_3_skeptical_comparison.xml"

# Minimum gaps required for valid output
MIN_REQUIRED_GAPS = 2


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt() -> str:
    """Load the Phase 3 XML prompt template."""
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Phase 3 prompt not found at {PROMPT_FILE}, using embedded fallback")
        return get_fallback_prompt()


def get_fallback_prompt() -> str:
    """Embedded fallback prompt if file not found."""
    return """<system_instruction>
  <agent_persona>Skeptical Hiring Manager</agent_persona>
  <primary_objective>
    Evaluate fit with CRITICAL HONESTY. Find genuine gaps, not just strengths.
  </primary_objective>
  <behavioral_constraints>
    <constraint>DO NOT be overly positive</constraint>
    <constraint>MUST identify at least 2 genuine gaps</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <employer_intel>{employer_intel}</employer_intel>
  <candidate_profile>{engineer_profile}</candidate_profile>
</context_data>

<output_contract>
{{"genuine_strengths": [], "genuine_gaps": ["gap1", "gap2"], 
  "transferable_skills": [], "risk_assessment": "medium", 
  "risk_justification": "string", "reasoning_trace": "string"}}
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


def validate_phase3_output(data: Dict[str, Any]) -> Phase3Output:
    """
    Validate and normalize Phase 3 output.
    
    Enforces the minimum gap requirement.
    """
    genuine_gaps = data.get("genuine_gaps") or []
    
    # CRITICAL: Enforce minimum gaps
    if len(genuine_gaps) < MIN_REQUIRED_GAPS:
        logger.warning(f"Phase 3 output had only {len(genuine_gaps)} gaps, adding defaults")
        default_gaps = [
            "Limited direct experience with employer's specific domain",
            "Some required technologies may need ramping up time",
        ]
        while len(genuine_gaps) < MIN_REQUIRED_GAPS:
            genuine_gaps.append(default_gaps[len(genuine_gaps)])
    
    # Validate risk_assessment
    risk = data.get("risk_assessment", "medium")
    if risk not in ("low", "medium", "high"):
        risk = "medium"
    
    return Phase3Output(
        genuine_strengths=data.get("genuine_strengths") or [],
        genuine_gaps=genuine_gaps,
        transferable_skills=data.get("transferable_skills") or [],
        risk_assessment=risk,
        reasoning_trace=data.get("reasoning_trace") or "Critical analysis completed.",
    )


def format_employer_intel(phase_2: Dict) -> str:
    """Format Phase 2 output for prompt injection."""
    return f"""Summary: {phase_2.get('employer_summary', 'No summary available')}

Required Skills/Tech: {', '.join(phase_2.get('identified_requirements', []))}

Tech Stack: {', '.join(phase_2.get('tech_stack', []))}

Culture Signals: {', '.join(phase_2.get('culture_signals', []))}"""


# =============================================================================
# Main Node Function
# =============================================================================

async def skeptical_comparison_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 3: SKEPTICAL_COMPARISON - Critical Gap Analysis Node.
    
    Performs devil's advocate analysis to identify genuine fit gaps.
    
    Args:
        state: Current pipeline state with Phase 2 output.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update with phase_3_output and phase transition.
    
    Emits:
        - phase: "skeptical_comparison" at start
        - thought: reasoning for critical analysis
        - phase_complete: with gap/strength summary
    
    CRITICAL: This phase MUST identify at least 2 gaps.
    """
    logger.info("[SKEPTICAL_COMPARISON] Starting phase 3 - CRITICAL ANALYSIS")
    step = state.get("step_count", 0) + 1
    phase_2 = state.get("phase_2_output", {})
    
    # Emit phase start
    if callback:
        await callback.on_phase(
            PHASE_NAME,
            "Performing critical fit analysis (devil's advocate)..."
        )
    
    try:
        # Format context data
        employer_intel = format_employer_intel(phase_2)
        engineer_profile = get_formatted_profile()
        
        # Load and format prompt
        prompt_template = load_phase_prompt()
        prompt = prompt_template.format(
            employer_summary=phase_2.get("employer_summary", "No summary"),
            identified_requirements=", ".join(phase_2.get("identified_requirements", [])),
            tech_stack=", ".join(phase_2.get("tech_stack", [])),
            culture_signals=", ".join(phase_2.get("culture_signals", [])),
            engineer_profile=engineer_profile,
        )
        
        # Emit reasoning thought
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content="Analyzing fit from a skeptical perspective - identifying genuine gaps and concerns...",
                phase=PHASE_NAME,
            )
        
        # Get LLM (slightly higher temp for creative critical thinking)
        llm = get_llm(streaming=False, temperature=0.4)
        
        # Invoke LLM
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)
        
        # Parse response
        response_text = response.content if hasattr(response, 'content') else str(response)
        parsed_data = extract_json_from_response(response_text)
        validated_output = validate_phase3_output(parsed_data)
        
        step += 1
        # Emit step-back reasoning
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content=f"Critical review complete: Found {len(validated_output['genuine_strengths'])} strengths, "
                        f"{len(validated_output['genuine_gaps'])} gaps. "
                        f"Risk assessment: {validated_output['risk_assessment']}",
                phase=PHASE_NAME,
            )
        
        # Emit phase complete
        if callback:
            summary = (
                f"Identified {len(validated_output['genuine_gaps'])} gaps, "
                f"{len(validated_output['genuine_strengths'])} strengths. "
                f"Risk: {validated_output['risk_assessment']}"
            )
            await callback.on_phase_complete(PHASE_NAME, summary)
        
        logger.info(
            f"[SKEPTICAL_COMPARISON] Phase 3 complete: "
            f"gaps={len(validated_output['genuine_gaps'])}, "
            f"risk={validated_output['risk_assessment']}"
        )
        
        return {
            "phase_3_output": validated_output,
            "current_phase": "skills_matching",
            "step_count": step,
        }
        
    except Exception as e:
        logger.error(f"[SKEPTICAL_COMPARISON] Phase 3 failed: {e}")
        
        # Graceful degradation with HONEST defaults
        fallback_output = Phase3Output(
            genuine_strengths=["Technical background shows relevant experience"],
            genuine_gaps=[
                "Unable to verify specific alignment with employer requirements",
                "Further analysis needed to assess complete fit",
            ],
            transferable_skills=[],
            risk_assessment="medium",
            reasoning_trace=f"Analysis encountered an error, providing conservative assessment: {str(e)}",
        )
        
        if callback:
            await callback.on_phase_complete(
                PHASE_NAME,
                f"Critical analysis completed with conservative defaults"
            )
        
        return {
            "phase_3_output": fallback_output,
            "current_phase": "skills_matching",
            "step_count": step,
            "processing_errors": state.get("processing_errors", []) + [f"Phase 3 error: {str(e)}"],
        }
```

---

## 6. Unit Tests

```python
"""
Unit tests for Phase 3: SKEPTICAL_COMPARISON node.

Location: res_backend/tests/test_skeptical_comparison_node.py

CRITICAL: These tests verify the anti-sycophancy measures.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.nodes.skeptical_comparison import (
    skeptical_comparison_node,
    validate_phase3_output,
    format_employer_intel,
    MIN_REQUIRED_GAPS,
)
from services.pipeline_state import create_initial_state, Phase2Output


class TestOutputValidation:
    """Test Phase 3 output validation, especially gap requirements."""
    
    def test_valid_output_with_gaps(self):
        """Output with sufficient gaps validates correctly."""
        data = {
            "genuine_strengths": ["Python expertise", "AI experience"],
            "genuine_gaps": ["No Kubernetes experience", "Limited fintech domain"],
            "transferable_skills": ["Docker knowledge applies to K8s"],
            "risk_assessment": "medium",
            "reasoning_trace": "Analysis complete",
        }
        result = validate_phase3_output(data)
        
        assert len(result["genuine_gaps"]) >= MIN_REQUIRED_GAPS
        assert result["risk_assessment"] == "medium"
    
    def test_insufficient_gaps_gets_defaults(self):
        """Output with too few gaps receives default gaps."""
        data = {
            "genuine_strengths": ["Great fit!"],
            "genuine_gaps": ["Minor issue"],  # Only 1 gap
            "risk_assessment": "low",
        }
        result = validate_phase3_output(data)
        
        # Should have at least MIN_REQUIRED_GAPS
        assert len(result["genuine_gaps"]) >= MIN_REQUIRED_GAPS
    
    def test_zero_gaps_gets_defaults(self):
        """Output with zero gaps receives multiple default gaps."""
        data = {
            "genuine_strengths": ["Perfect match!"],
            "genuine_gaps": [],  # Sycophantic output
            "risk_assessment": "low",
        }
        result = validate_phase3_output(data)
        
        assert len(result["genuine_gaps"]) >= MIN_REQUIRED_GAPS
        # Default gaps should be meaningful
        assert any("experience" in gap.lower() or "technology" in gap.lower() 
                   for gap in result["genuine_gaps"])
    
    def test_invalid_risk_defaults_to_medium(self):
        """Invalid risk assessment defaults to medium."""
        data = {
            "genuine_gaps": ["Gap 1", "Gap 2"],
            "risk_assessment": "perfect",  # Invalid
        }
        result = validate_phase3_output(data)
        
        assert result["risk_assessment"] == "medium"


class TestEmployerIntelFormatting:
    """Test employer intelligence formatting for prompts."""
    
    def test_complete_formatting(self):
        """Complete Phase 2 output formats correctly."""
        phase_2 = {
            "employer_summary": "Google is a tech giant",
            "identified_requirements": ["Python", "ML", "Distributed Systems"],
            "tech_stack": ["Python", "TensorFlow", "GCP"],
            "culture_signals": ["Innovation", "Scale"],
        }
        formatted = format_employer_intel(phase_2)
        
        assert "Google" in formatted
        assert "Python" in formatted
        assert "TensorFlow" in formatted
    
    def test_empty_fields_handled(self):
        """Empty Phase 2 fields handled gracefully."""
        phase_2 = {}
        formatted = format_employer_intel(phase_2)
        
        assert "No summary" in formatted


class TestSkepticalComparisonNode:
    """Integration tests for the skeptical comparison node."""
    
    @pytest.mark.asyncio
    async def test_identifies_gaps(self):
        """Node identifies gaps even for strong candidates."""
        state = create_initial_state("Google")
        state["phase_2_output"] = Phase2Output(
            employer_summary="Google is a tech giant using Python and ML",
            identified_requirements=["Python", "TensorFlow", "Kubernetes", "PhD preferred"],
            tech_stack=["Python", "Go", "TensorFlow", "Kubernetes"],
            culture_signals=["Innovation", "Scale"],
            reasoning_trace="",
        )
        state["step_count"] = 3
        
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "genuine_strengths": ["Python experience", "AI/ML background"],
            "genuine_gaps": ["No Kubernetes production experience", "PhD not obtained"],
            "transferable_skills": ["Docker experience applies to K8s"],
            "risk_assessment": "medium",
            "reasoning_trace": "Identified skill gaps in infrastructure"
        }
        '''
        
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await skeptical_comparison_node(state)
            
            assert len(result["phase_3_output"]["genuine_gaps"]) >= 2
            assert result["phase_3_output"]["risk_assessment"] in ("low", "medium", "high")
            assert result["current_phase"] == "skills_matching"
    
    @pytest.mark.asyncio
    async def test_prevents_sycophantic_output(self):
        """Sycophantic LLM output gets corrected."""
        state = create_initial_state("Startup")
        state["phase_2_output"] = Phase2Output(
            employer_summary="Cool startup",
            identified_requirements=["React", "Node.js"],
            tech_stack=["React", "Node.js"],
            culture_signals=["Fast-paced"],
            reasoning_trace="",
        )
        state["step_count"] = 3
        
        # Simulate sycophantic LLM response
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "genuine_strengths": ["Perfect fit!", "Ideal candidate!", "Amazing match!"],
            "genuine_gaps": [],
            "risk_assessment": "low",
            "reasoning_trace": "This candidate is perfect"
        }
        '''
        
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await skeptical_comparison_node(state)
            
            # Validation should have added default gaps
            assert len(result["phase_3_output"]["genuine_gaps"]) >= MIN_REQUIRED_GAPS
    
    @pytest.mark.asyncio
    async def test_callback_events(self):
        """Callback receives phase and thought events."""
        state = create_initial_state("Company")
        state["phase_2_output"] = Phase2Output(
            employer_summary="Company info",
            identified_requirements=[],
            tech_stack=[],
            culture_signals=[],
            reasoning_trace="",
        )
        state["step_count"] = 3
        
        callback = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '''
        {"genuine_strengths": [], "genuine_gaps": ["Gap 1", "Gap 2"], 
         "risk_assessment": "medium", "reasoning_trace": "Analysis done"}
        '''
        
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            await skeptical_comparison_node(state, callback=callback)
            
            callback.on_phase.assert_called_once()
            callback.on_thought.assert_called()
            callback.on_phase_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_produces_conservative_output(self):
        """Errors result in conservative, honest fallback."""
        state = create_initial_state("Company")
        state["phase_2_output"] = {}
        state["step_count"] = 3
        
        with patch("services.nodes.skeptical_comparison.get_llm") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))
            
            result = await skeptical_comparison_node(state)
            
            # Fallback should still have gaps
            assert len(result["phase_3_output"]["genuine_gaps"]) >= MIN_REQUIRED_GAPS
            assert result["phase_3_output"]["risk_assessment"] == "medium"
            assert "processing_errors" in result
```

---

## 7. Anti-Sycophancy Validation Rules

### 7.1 Runtime Validation

```python
def validate_anti_sycophancy(output: Phase3Output) -> List[str]:
    """
    Validate that output is not sycophantic.
    
    Returns list of warnings if output seems too positive.
    """
    warnings = []
    
    # Check gap count
    if len(output["genuine_gaps"]) < MIN_REQUIRED_GAPS:
        warnings.append(f"Insufficient gaps: only {len(output['genuine_gaps'])}")
    
    # Check for sycophantic phrases in strengths
    sycophantic_phrases = [
        "perfect fit", "ideal candidate", "excellent match",
        "amazing", "outstanding", "exceptional", "flawless"
    ]
    for strength in output["genuine_strengths"]:
        for phrase in sycophantic_phrases:
            if phrase in strength.lower():
                warnings.append(f"Sycophantic phrase detected: '{phrase}' in strength")
    
    # Check risk assessment
    if output["risk_assessment"] == "low" and len(output["genuine_gaps"]) > 2:
        warnings.append("Risk 'low' with multiple gaps is inconsistent")
    
    return warnings
```

### 7.2 Logging for Review

```python
# In the node function, after validation:
warnings = validate_anti_sycophancy(validated_output)
if warnings:
    logger.warning(f"[SKEPTICAL_COMPARISON] Anti-sycophancy warnings: {warnings}")
    # Consider re-invoking with stricter prompt
```

---

## 8. Validation Checklist

Before proceeding to Phase 4:

- [ ] `services/nodes/skeptical_comparison.py` created and importable
- [ ] `prompts/phase_3_skeptical_comparison.xml` created
- [ ] Output validation enforces minimum 2 gaps
- [ ] Sycophantic LLM output gets corrected with defaults
- [ ] Risk assessment is validated (low/medium/high only)
- [ ] Step-back prompting is included in XML template
- [ ] Unit tests verify anti-sycophancy measures
- [ ] Fallback output is conservative, not optimistic

---

## 9. Performance Considerations

- **Temperature**: 0.4 (allow creative critical thinking)
- **Retries**: Consider 1 retry if output is too sycophantic
- **Timeout**: 12s maximum for this phase
- **Logging**: Log all anti-sycophancy warnings for review

---

## 10. Next Steps

After implementing this phase:
1. Proceed to **PHASE_4_SKILLS_MATCHING_NODE.md**
2. Phase 4 uses the gaps from Phase 3 to contextualize skill matching
3. The final response will acknowledge the gaps honestly

---

## 11. Build Verification Gate

> ⛔ **STOP**: Do NOT proceed to the next phase until this phase compiles and builds successfully.

### Backend Build Verification

```powershell
# Navigate to backend directory
cd res_backend

# Verify Python syntax
python -m py_compile services/nodes/skeptical_comparison.py

# Verify imports work
python -c "from services.nodes.skeptical_comparison import skeptical_comparison_node; print('Phase 3 imports OK')"

# Run Phase 3 unit tests
pytest tests/unit/test_skeptical_comparison_node.py -v

# Run all tests (ensure no regressions)
pytest --tb=short
```

### Verification Checklist

- [ ] `services/nodes/skeptical_comparison.py` created and has no syntax errors
- [ ] `prompts/phase_3_skeptical_comparison.xml` created
- [ ] Anti-sycophancy validation logic implemented
- [ ] Import verification succeeds
- [ ] Phase 3 unit tests pass (including anti-sycophancy tests)
- [ ] All existing tests still pass

---

## 12. Requirements Tracking

> 📋 **IMPORTANT**: Refer to **[TRACK_ALL_REQUIREMENTS.md](./TRACK_ALL_REQUIREMENTS.md)** for the complete requirements checklist.

### After Completing This Phase:

1. Open `TRACK_ALL_REQUIREMENTS.md`
2. Locate the **Phase 3: SKEPTICAL_COMPARISON Node** section
3. Mark each completed requirement with ✅
4. Fill in the "Verified By" and "Date" columns
5. Complete the **Build Verification** checkboxes
6. Update the **Completion Summary** table at the bottom

### Phase 3 Requirement IDs to Update:

- P3-001 through P3-012

---

*Document Version: 1.1 | Phase 3 of 7 | CRITICAL - Anti-Sycophancy Defense*
