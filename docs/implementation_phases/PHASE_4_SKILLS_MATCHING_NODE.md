# Phase 4: SKILLS_MATCHING Node Implementation

> **Objective**: Execute structured skill and experience alignment using dedicated tools, then synthesize a quantified match assessment.

---

## 1. Phase Overview

### 1.1 Desire Statement

**Desire: Semantic Alignment & Quantification**

The Skills Matching agent is the technical recruiter. It operates with precision, mapping each employer requirement to specific candidate skills or identifying explicit gaps. Its desire is to produce a quantified, evidence-based match score.

### 1.2 Inputs & Outputs

| Direction | Data |
|-----------|------|
| **Input** | `state.phase_2_output` - Employer requirements/tech stack |
| **Input** | `state.phase_3_output` - Skeptical gaps analysis |
| **Input** | `ENGINEER_PROFILE` - Static engineer skills data |
| **Output** | `Phase4Output` - Matched requirements, unmatched, overall score |

### 1.3 Tools Used

This node utilizes existing tools:
- `analyze_skill_match` from `services/tools/skill_matcher.py`
- `analyze_experience_relevance` from `services/tools/experience_matcher.py`

---

## 2. File Location & Structure

```
res_backend/
├── services/
│   └── nodes/
│       └── skills_matching.py    # THIS FILE
└── prompts/
    └── phase_4_skills_matching.xml
```

---

## 3. XML-Structured Prompt Template

```xml
<!-- Location: res_backend/prompts/phase_4_skills_matching.xml -->

<system_instruction>
  <agent_persona>
    You are a Technical Recruiter specializing in software engineering roles.
    Your expertise is precise skill-to-requirement mapping with quantified confidence.
  </agent_persona>
  
  <primary_objective>
    Map each employer requirement to a specific candidate skill with a confidence score,
    or explicitly identify it as unmatched. Produce an overall match percentage.
  </primary_objective>
  
  <success_criteria>
    <criterion priority="critical">Every identified_requirement from Phase 2 MUST appear in either matched_requirements or unmatched_requirements</criterion>
    <criterion priority="critical">Each match MUST have a specific skill, not just a category</criterion>
    <criterion priority="high">Confidence scores must reflect actual evidence strength</criterion>
    <criterion priority="high">Overall match score must be mathematically justified</criterion>
  </success_criteria>
  
  <behavioral_constraints>
    <constraint>DO NOT inflate confidence scores without evidence</constraint>
    <constraint>DO NOT claim 100% match unless there is explicit proof</constraint>
    <constraint>DO NOT use vague matches like "relevant experience" without specifics</constraint>
    <constraint>DO NOT ignore unmatched requirements - they must be listed</constraint>
  </behavioral_constraints>
  
  <confidence_calibration>
    <level value="0.9-1.0">Exact skill match with demonstrated production use</level>
    <level value="0.7-0.9">Skill present, some experience demonstrated</level>
    <level value="0.5-0.7">Related skill that could transfer</level>
    <level value="0.3-0.5">Tangentially related, would need training</level>
    <level value="0.0-0.3">No evidence of skill or relevance</level>
  </confidence_calibration>
</system_instruction>

<context_data>
  <employer_requirements>
    Identified Requirements: {identified_requirements}
    Tech Stack: {tech_stack}
  </employer_requirements>
  
  <skill_analysis_tool_output>
    {skill_matcher_output}
  </skill_analysis_tool_output>
  
  <experience_analysis_tool_output>
    {experience_matcher_output}
  </experience_analysis_tool_output>
  
  <skeptical_review>
    Genuine Gaps: {genuine_gaps}
    Transferable Skills: {transferable_skills}
    Risk Assessment: {risk_assessment}
  </skeptical_review>
</context_data>

<output_contract>
  Output strictly valid JSON matching this exact schema (no markdown, no code blocks):
  {{
    "matched_requirements": [
      {{
        "requirement": "string (exact requirement from employer)",
        "matched_skill": "string (specific candidate skill)",
        "confidence": 0.0-1.0,
        "evidence": "string (brief justification)"
      }}
    ],
    "unmatched_requirements": [
      "string (requirements with no match)"
    ],
    "overall_match_score": 0.0-1.0,
    "score_breakdown": "string (how score was calculated)",
    "reasoning_trace": "string (synthesis approach)"
  }}
  
  NOTE: overall_match_score = average of matched confidence scores * (matched_count / total_requirements)
</output_contract>
```

---

## 4. Score Calculation Logic

```python
"""
Score calculation utilities for Phase 4.

Implements a transparent, reproducible scoring algorithm.
"""

from typing import List, Dict


def calculate_overall_score(
    matched: List[Dict],
    unmatched: List[str],
) -> tuple[float, str]:
    """
    Calculate overall match score with transparent breakdown.
    
    Formula:
        1. Average confidence of matched requirements
        2. Multiply by coverage ratio (matched / total)
        3. Apply gap penalty if unmatched > 30% of total
    
    Args:
        matched: List of matched requirement dicts with confidence scores.
        unmatched: List of unmatched requirement strings.
    
    Returns:
        Tuple of (score, breakdown_explanation)
    """
    total_requirements = len(matched) + len(unmatched)
    
    if total_requirements == 0:
        return 0.5, "No requirements identified; defaulting to neutral score."
    
    # Calculate average confidence of matches
    if matched:
        avg_confidence = sum(m.get("confidence", 0.5) for m in matched) / len(matched)
    else:
        avg_confidence = 0.0
    
    # Calculate coverage ratio
    coverage = len(matched) / total_requirements
    
    # Base score
    base_score = avg_confidence * coverage
    
    # Gap penalty if >30% unmatched
    gap_ratio = len(unmatched) / total_requirements
    if gap_ratio > 0.3:
        penalty = (gap_ratio - 0.3) * 0.2  # 20% penalty per 10% gap over 30%
        base_score = max(0, base_score - penalty)
    
    # Clamp to 0-1
    final_score = max(0.0, min(1.0, base_score))
    
    breakdown = (
        f"Avg confidence: {avg_confidence:.2f} × "
        f"Coverage: {coverage:.2f} ({len(matched)}/{total_requirements}) = "
        f"{base_score:.2f}"
    )
    if gap_ratio > 0.3:
        breakdown += f" (gap penalty applied: {gap_ratio:.1%} unmatched)"
    
    return round(final_score, 2), breakdown
```

---

## 5. Node Implementation

```python
"""
Skills Matching Node - Phase 4 of the Fit Check Pipeline.

This module implements the skill alignment node that:
1. Invokes skill_matcher and experience_matcher tools
2. Synthesizes tool outputs into structured matches
3. Produces quantified match scores with evidence

Gemini Optimization:
- Uses XML-structured prompt for synthesis
- Tool calls emit explicit thought events
- Confidence calibration provided in prompt
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from langchain_core.messages import HumanMessage

from config.llm import get_llm
from services.pipeline_state import FitCheckPipelineState, Phase4Output, SkillMatch
from services.fit_check_agent import ThoughtCallback
from services.tools.skill_matcher import analyze_skill_match
from services.tools.experience_matcher import analyze_experience_relevance

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "skills_matching"
PROMPT_FILE = Path(__file__).parent.parent.parent / "prompts" / "phase_4_skills_matching.xml"


# =============================================================================
# Score Calculation
# =============================================================================

def calculate_overall_score(
    matched: List[Dict],
    unmatched: List[str],
) -> tuple[float, str]:
    """
    Calculate overall match score with transparent breakdown.
    """
    total_requirements = len(matched) + len(unmatched)
    
    if total_requirements == 0:
        return 0.5, "No requirements identified; defaulting to neutral score."
    
    if matched:
        avg_confidence = sum(m.get("confidence", 0.5) for m in matched) / len(matched)
    else:
        avg_confidence = 0.0
    
    coverage = len(matched) / total_requirements
    base_score = avg_confidence * coverage
    
    gap_ratio = len(unmatched) / total_requirements
    if gap_ratio > 0.3:
        penalty = (gap_ratio - 0.3) * 0.2
        base_score = max(0, base_score - penalty)
    
    final_score = max(0.0, min(1.0, base_score))
    
    breakdown = (
        f"Avg confidence: {avg_confidence:.2f} × "
        f"Coverage: {coverage:.2f} ({len(matched)}/{total_requirements}) = "
        f"{base_score:.2f}"
    )
    if gap_ratio > 0.3:
        breakdown += f" (gap penalty applied: {gap_ratio:.1%} unmatched)"
    
    return round(final_score, 2), breakdown


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt() -> str:
    """Load the Phase 4 XML prompt template."""
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Phase 4 prompt not found at {PROMPT_FILE}, using embedded fallback")
        return get_fallback_prompt()


def get_fallback_prompt() -> str:
    """Embedded fallback prompt if file not found."""
    return """<system_instruction>
  <agent_persona>Technical Recruiter</agent_persona>
  <primary_objective>
    Map each requirement to a specific skill with confidence score.
  </primary_objective>
  <behavioral_constraints>
    <constraint>DO NOT inflate confidence without evidence</constraint>
  </behavioral_constraints>
</system_instruction>

<context_data>
  <skill_analysis>{skill_output}</skill_analysis>
  <experience_analysis>{experience_output}</experience_analysis>
</context_data>

<output_contract>
{{"matched_requirements": [], "unmatched_requirements": [], 
  "overall_match_score": 0.5, "score_breakdown": "string", 
  "reasoning_trace": "string"}}
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


def validate_phase4_output(data: Dict[str, Any]) -> Phase4Output:
    """Validate and normalize Phase 4 output."""
    matched = data.get("matched_requirements") or []
    unmatched = data.get("unmatched_requirements") or []
    
    # Validate matched items
    validated_matched = []
    for item in matched:
        if isinstance(item, dict):
            validated_matched.append(SkillMatch(
                requirement=item.get("requirement", "Unknown requirement"),
                matched_skill=item.get("matched_skill", "General experience"),
                confidence=max(0.0, min(1.0, float(item.get("confidence", 0.5)))),
            ))
    
    # Recalculate score for consistency
    calculated_score, breakdown = calculate_overall_score(matched, unmatched)
    
    return Phase4Output(
        matched_requirements=validated_matched,
        unmatched_requirements=unmatched,
        overall_match_score=calculated_score,
        reasoning_trace=data.get("reasoning_trace") or f"Score breakdown: {breakdown}",
    )


# =============================================================================
# Main Node Function
# =============================================================================

async def skills_matching_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 4: SKILLS_MATCHING - Skill Alignment Node.
    
    Invokes skill/experience tools and synthesizes matches.
    
    Args:
        state: Current pipeline state with Phases 2-3 output.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update with phase_4_output and phase transition.
    
    Emits:
        - phase: "skills_matching" at start
        - thought: tool_call for each tool
        - thought: observation for each result
        - thought: reasoning for synthesis
        - phase_complete: with match score summary
    """
    logger.info("[SKILLS_MATCHING] Starting phase 4")
    step = state.get("step_count", 0)
    phase_2 = state.get("phase_2_output", {})
    phase_3 = state.get("phase_3_output", {})
    
    # Emit phase start
    if callback:
        await callback.on_phase(
            PHASE_NAME,
            "Mapping skills to requirements..."
        )
    
    try:
        # Gather requirements for tool input
        requirements = phase_2.get("identified_requirements", [])
        tech_stack = phase_2.get("tech_stack", [])
        all_requirements = list(set(requirements + tech_stack))
        requirements_str = ", ".join(all_requirements) if all_requirements else "General software engineering"
        
        # Invoke skill_matcher tool
        step += 1
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="tool_call",
                content="Analyzing skill alignment...",
                phase=PHASE_NAME,
                tool="analyze_skill_match",
                tool_input=requirements_str[:100] + "..." if len(requirements_str) > 100 else requirements_str,
            )
        
        try:
            skill_output = analyze_skill_match.invoke(requirements_str)
        except Exception as e:
            logger.warning(f"Skill matcher failed: {e}")
            skill_output = "Skill analysis unavailable."
        
        step += 1
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="observation",
                content="Skill analysis complete - identified matching skills.",
                phase=PHASE_NAME,
            )
        
        # Invoke experience_matcher tool
        employer_context = phase_2.get("employer_summary", state["query"])
        
        step += 1
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="tool_call",
                content="Analyzing experience relevance...",
                phase=PHASE_NAME,
                tool="analyze_experience_relevance",
                tool_input=employer_context[:100] + "..." if len(employer_context) > 100 else employer_context,
            )
        
        try:
            experience_output = analyze_experience_relevance.invoke(employer_context)
        except Exception as e:
            logger.warning(f"Experience matcher failed: {e}")
            experience_output = "Experience analysis unavailable."
        
        step += 1
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="observation",
                content="Experience analysis complete - identified relevant background.",
                phase=PHASE_NAME,
            )
        
        # Load and format synthesis prompt
        prompt_template = load_phase_prompt()
        prompt = prompt_template.format(
            identified_requirements=", ".join(requirements),
            tech_stack=", ".join(tech_stack),
            skill_matcher_output=skill_output,
            experience_matcher_output=experience_output,
            genuine_gaps=", ".join(phase_3.get("genuine_gaps", [])),
            transferable_skills=", ".join(phase_3.get("transferable_skills", [])),
            risk_assessment=phase_3.get("risk_assessment", "medium"),
        )
        
        step += 1
        if callback:
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content="Synthesizing skill matches with confidence scores...",
                phase=PHASE_NAME,
            )
        
        # Get LLM for synthesis
        llm = get_llm(streaming=False, temperature=0.2)  # Low temp for precision
        
        # Invoke LLM
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)
        
        # Parse response
        response_text = response.content if hasattr(response, 'content') else str(response)
        parsed_data = extract_json_from_response(response_text)
        validated_output = validate_phase4_output(parsed_data)
        
        # Emit phase complete
        if callback:
            score_pct = int(validated_output["overall_match_score"] * 100)
            matched_count = len(validated_output["matched_requirements"])
            unmatched_count = len(validated_output["unmatched_requirements"])
            summary = f"Match score: {score_pct}% ({matched_count} matched, {unmatched_count} gaps)"
            await callback.on_phase_complete(PHASE_NAME, summary)
        
        logger.info(
            f"[SKILLS_MATCHING] Phase 4 complete: "
            f"score={validated_output['overall_match_score']}"
        )
        
        return {
            "phase_4_output": validated_output,
            "current_phase": "generate_results",
            "step_count": step,
        }
        
    except Exception as e:
        logger.error(f"[SKILLS_MATCHING] Phase 4 failed: {e}")
        
        # Graceful degradation
        fallback_output = Phase4Output(
            matched_requirements=[],
            unmatched_requirements=["Unable to complete skill analysis"],
            overall_match_score=0.5,
            reasoning_trace=f"Skill matching encountered an error: {str(e)}",
        )
        
        if callback:
            await callback.on_phase_complete(
                PHASE_NAME,
                f"Skill matching completed with limited data"
            )
        
        return {
            "phase_4_output": fallback_output,
            "current_phase": "generate_results",
            "step_count": step,
            "processing_errors": state.get("processing_errors", []) + [f"Phase 4 error: {str(e)}"],
        }
```

---

## 6. Unit Tests

```python
"""
Unit tests for Phase 4: SKILLS_MATCHING node.

Location: res_backend/tests/test_skills_matching_node.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.nodes.skills_matching import (
    skills_matching_node,
    calculate_overall_score,
    validate_phase4_output,
)
from services.pipeline_state import create_initial_state, Phase2Output, Phase3Output


class TestScoreCalculation:
    """Test the transparent scoring algorithm."""
    
    def test_perfect_matches(self):
        """All requirements matched with high confidence."""
        matched = [
            {"confidence": 0.9},
            {"confidence": 0.85},
            {"confidence": 0.95},
        ]
        unmatched = []
        
        score, breakdown = calculate_overall_score(matched, unmatched)
        
        assert score >= 0.85
        assert "3/3" in breakdown
    
    def test_partial_matches(self):
        """Some requirements matched, some not."""
        matched = [
            {"confidence": 0.8},
            {"confidence": 0.7},
        ]
        unmatched = ["Kubernetes", "GraphQL"]
        
        score, breakdown = calculate_overall_score(matched, unmatched)
        
        assert 0.3 <= score <= 0.6  # Should be moderate
        assert "2/4" in breakdown
    
    def test_gap_penalty(self):
        """Heavy gaps should apply penalty."""
        matched = [{"confidence": 0.9}]
        unmatched = ["Skill 1", "Skill 2", "Skill 3", "Skill 4"]  # 80% unmatched
        
        score, breakdown = calculate_overall_score(matched, unmatched)
        
        assert "gap penalty" in breakdown.lower()
        assert score < 0.3
    
    def test_no_requirements(self):
        """No requirements defaults to neutral."""
        score, breakdown = calculate_overall_score([], [])
        
        assert score == 0.5
        assert "defaulting" in breakdown.lower()


class TestOutputValidation:
    """Test Phase 4 output validation."""
    
    def test_valid_output(self):
        """Valid skill matching output validates correctly."""
        data = {
            "matched_requirements": [
                {"requirement": "Python", "matched_skill": "Python", "confidence": 0.9},
                {"requirement": "React", "matched_skill": "React", "confidence": 0.85},
            ],
            "unmatched_requirements": ["Kubernetes"],
            "overall_match_score": 0.7,
            "reasoning_trace": "Analysis complete",
        }
        result = validate_phase4_output(data)
        
        assert len(result["matched_requirements"]) == 2
        assert len(result["unmatched_requirements"]) == 1
    
    def test_confidence_clamping(self):
        """Confidence scores outside 0-1 get clamped."""
        data = {
            "matched_requirements": [
                {"requirement": "X", "matched_skill": "Y", "confidence": 1.5},
            ],
            "unmatched_requirements": [],
        }
        result = validate_phase4_output(data)
        
        assert result["matched_requirements"][0]["confidence"] == 1.0
    
    def test_score_recalculation(self):
        """Score gets recalculated for consistency."""
        data = {
            "matched_requirements": [
                {"requirement": "A", "matched_skill": "B", "confidence": 0.8},
            ],
            "unmatched_requirements": ["C", "D", "E"],
            "overall_match_score": 0.9,  # Suspiciously high
        }
        result = validate_phase4_output(data)
        
        # Score should be recalculated lower
        assert result["overall_match_score"] < 0.5


class TestSkillsMatchingNode:
    """Integration tests for the skills matching node."""
    
    @pytest.mark.asyncio
    async def test_successful_matching(self):
        """Successful skill matching produces quantified output."""
        state = create_initial_state("Google")
        state["phase_2_output"] = Phase2Output(
            employer_summary="Google needs Python and ML engineers",
            identified_requirements=["Python", "TensorFlow", "Kubernetes"],
            tech_stack=["Python", "TensorFlow"],
            culture_signals=[],
            reasoning_trace="",
        )
        state["phase_3_output"] = Phase3Output(
            genuine_strengths=["Python"],
            genuine_gaps=["Kubernetes"],
            transferable_skills=["Docker"],
            risk_assessment="medium",
            reasoning_trace="",
        )
        state["step_count"] = 5
        
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "matched_requirements": [
                {"requirement": "Python", "matched_skill": "Python", "confidence": 0.9},
                {"requirement": "TensorFlow", "matched_skill": "AI/ML experience", "confidence": 0.7}
            ],
            "unmatched_requirements": ["Kubernetes"],
            "overall_match_score": 0.65,
            "reasoning_trace": "Good Python match, learning curve for K8s"
        }
        '''
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.return_value = "Python: Strong match"
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.return_value = "AI domain experience"
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    result = await skills_matching_node(state)
                    
                    assert len(result["phase_4_output"]["matched_requirements"]) == 2
                    assert result["phase_4_output"]["overall_match_score"] > 0
                    assert result["current_phase"] == "generate_results"
    
    @pytest.mark.asyncio
    async def test_callback_events(self):
        """Callback receives tool and reasoning events."""
        state = create_initial_state("Company")
        state["phase_2_output"] = Phase2Output(
            employer_summary="Company",
            identified_requirements=["Python"],
            tech_stack=[],
            culture_signals=[],
            reasoning_trace="",
        )
        state["phase_3_output"] = Phase3Output(
            genuine_strengths=[],
            genuine_gaps=["Gap"],
            transferable_skills=[],
            risk_assessment="medium",
            reasoning_trace="",
        )
        state["step_count"] = 5
        
        callback = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.content = '''
        {"matched_requirements": [], "unmatched_requirements": [], 
         "overall_match_score": 0.5, "reasoning_trace": "Done"}
        '''
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.return_value = "Skill output"
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.return_value = "Experience output"
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    await skills_matching_node(state, callback=callback)
                    
                    # Should have multiple tool_call events
                    call_args_list = callback.on_thought.call_args_list
                    tool_calls = [c for c in call_args_list 
                                  if c.kwargs.get("thought_type") == "tool_call"]
                    assert len(tool_calls) >= 2  # skill + experience tools
    
    @pytest.mark.asyncio
    async def test_tool_failure_recovery(self):
        """Tool failures result in graceful degradation."""
        state = create_initial_state("Company")
        state["phase_2_output"] = Phase2Output(
            employer_summary="Company",
            identified_requirements=[],
            tech_stack=[],
            culture_signals=[],
            reasoning_trace="",
        )
        state["phase_3_output"] = {}
        state["step_count"] = 5
        
        with patch("services.nodes.skills_matching.analyze_skill_match") as mock_skill:
            mock_skill.invoke.side_effect = Exception("Tool error")
            
            with patch("services.nodes.skills_matching.analyze_experience_relevance") as mock_exp:
                mock_exp.invoke.side_effect = Exception("Tool error")
                
                mock_response = MagicMock()
                mock_response.content = '''
                {"matched_requirements": [], "unmatched_requirements": [], 
                 "overall_match_score": 0.5, "reasoning_trace": "Limited data"}
                '''
                
                with patch("services.nodes.skills_matching.get_llm") as mock_llm:
                    mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
                    
                    result = await skills_matching_node(state)
                    
                    # Should still produce output
                    assert result["current_phase"] == "generate_results"
```

---

## 7. Validation Checklist

Before proceeding to Phase 5:

- [ ] `services/nodes/skills_matching.py` created and importable
- [ ] `prompts/phase_4_skills_matching.xml` created
- [ ] Both `analyze_skill_match` and `analyze_experience_relevance` tools are invoked
- [ ] Tool calls and observations emit separate thought events
- [ ] Score calculation is transparent and reproducible
- [ ] Confidence scores are validated (clamped to 0-1)
- [ ] Graceful degradation on tool/LLM failures
- [ ] Unit tests pass

---

## 8. Performance Considerations

- **Temperature**: 0.2 (precision for quantified output)
- **Tool Parallelization**: Consider running skill + experience tools in parallel
- **Timeout**: 15s maximum for this phase
- **Caching**: Tool outputs could be cached for repeated queries

---

## 9. Next Steps

After implementing this phase:
1. Proceed to **PHASE_5_GENERATE_RESULTS_NODE.md**
2. Phase 5 synthesizes all prior outputs into the final response
3. The final response will reference specific skill matches and gaps

---

## 10. Build Verification Gate

> ⛔ **STOP**: Do NOT proceed to the next phase until this phase compiles and builds successfully.

### Backend Build Verification

```powershell
# Navigate to backend directory
cd res_backend

# Verify Python syntax
python -m py_compile services/nodes/skills_matching.py

# Verify imports work
python -c "from services.nodes.skills_matching import skills_matching_node; print('Phase 4 imports OK')"

# Verify tool integrations
python -c "from services.tools.skill_matcher import analyze_skill_match; print('skill_matcher OK')"
python -c "from services.tools.experience_matcher import analyze_experience_relevance; print('experience_matcher OK')"

# Run Phase 4 unit tests
pytest tests/unit/test_skills_matching_node.py -v

# Run all tests (ensure no regressions)
pytest --tb=short
```

### Verification Checklist

- [ ] `services/nodes/skills_matching.py` created and has no syntax errors
- [ ] `prompts/phase_4_skills_matching.xml` created
- [ ] analyze_skill_match tool integration works
- [ ] analyze_experience_relevance tool integration works
- [ ] Import verification succeeds
- [ ] Phase 4 unit tests pass
- [ ] All existing tests still pass

---

## 11. Requirements Tracking

> 📋 **IMPORTANT**: Refer to **[TRACK_ALL_REQUIREMENTS.md](./TRACK_ALL_REQUIREMENTS.md)** for the complete requirements checklist.

### After Completing This Phase:

1. Open `TRACK_ALL_REQUIREMENTS.md`
2. Locate the **Phase 4: SKILLS_MATCHING Node** section
3. Mark each completed requirement with ✅
4. Fill in the "Verified By" and "Date" columns
5. Complete the **Build Verification** checkboxes
6. Update the **Completion Summary** table at the bottom

### Phase 4 Requirement IDs to Update:

- P4-001 through P4-012

---

*Document Version: 1.1 | Phase 4 of 7 | Quantified Skill Alignment*
