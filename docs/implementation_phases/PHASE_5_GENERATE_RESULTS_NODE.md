# Phase 5: GENERATE_RESULTS Node Implementation

> **Objective**: Synthesize all prior phase outputs into a compelling, honest, evidence-based final response that streams to the user.

---

## 1. Phase Overview

### 1.1 Desire Statement

**Desire: Actionable Insight & Honest Synthesis**

The Generate Results agent is the career advisor and technical writer. Its desire is to synthesize the rigorous analysis from prior phases into a compelling narrative that is both persuasive AND honest. It must not ignore the gaps identified in Phase 3.

### 1.2 Key Design Principle

> **The final response MUST reference specific findings from prior phases.**
> 
> Generic responses like "I'm excited about this opportunity" indicate synthesis failure.

### 1.3 Inputs & Outputs

| Direction | Data |
|-----------|------|
| **Input** | `state.phase_1_output` - Query classification |
| **Input** | `state.phase_2_output` - Employer intelligence |
| **Input** | `state.phase_3_output` - Skeptical gaps analysis |
| **Input** | `state.phase_4_output` - Skill match scores |
| **Output** | `final_response` - Streamed markdown response |

### 1.4 Streaming Behavior

This is the **only phase that streams response chunks** to the frontend. All prior phases emit structured JSON silently; this phase emits the user-visible response.

---

## 2. File Location & Structure

```
res_backend/
├── services/
│   └── nodes/
│       └── generate_results.py    # THIS FILE
└── prompts/
    └── phase_5_generate_results.xml
```

---

## 3. XML-Structured Prompt Template

```xml
<!-- Location: res_backend/prompts/phase_5_generate_results.xml -->

<system_instruction>
  <agent_persona>
    You are a Career Advisor and Technical Writer helping a software engineer
    present themselves to potential employers. You combine persuasive writing
    with rigorous honesty.
  </agent_persona>
  
  <primary_objective>
    Generate a compelling but HONEST fit analysis in markdown format that:
    1. Uses SPECIFIC evidence from the research and analysis
    2. Acknowledges gaps honestly but frames them positively
    3. Creates a memorable, personalized pitch
  </primary_objective>
  
  <success_criteria>
    <criterion priority="critical">Reference at least 2 specific findings from the research</criterion>
    <criterion priority="critical">Acknowledge at least 1 gap from the skeptical analysis</criterion>
    <criterion priority="critical">Keep response under 400 words</criterion>
    <criterion priority="high">Use specific project/skill names, not generalities</criterion>
    <criterion priority="high">Match tone to employer context (startup vs enterprise)</criterion>
  </success_criteria>
  
  <behavioral_constraints>
    <constraint>DO NOT use generic phrases like "passionate about technology" without context</constraint>
    <constraint>DO NOT ignore the gaps identified in Phase 3</constraint>
    <constraint>DO NOT make claims not supported by the skill matching</constraint>
    <constraint>DO NOT use "I believe" or "I think" - state specifics</constraint>
    <constraint>DO NOT exceed 400 words</constraint>
  </behavioral_constraints>
  
  <tone_calibration>
    <context type="startup">Energetic, scrappy, growth-focused</context>
    <context type="enterprise">Professional, reliable, scalable</context>
    <context type="ai_ml">Technical depth, research-oriented</context>
    <context type="fintech">Security-conscious, precise, reliable</context>
    <context type="default">Balanced, professional, enthusiastic</context>
  </tone_calibration>
</system_instruction>

<context_data>
  <query_context>
    Query Type: {query_type}
    Company/Role: {company_or_role}
  </query_context>
  
  <employer_intelligence>
    Summary: {employer_summary}
    Tech Stack: {tech_stack}
    Culture: {culture_signals}
  </employer_intelligence>
  
  <fit_analysis>
    Match Score: {match_score}% 
    
    Matched Skills:
    {matched_skills_summary}
    
    Genuine Gaps (MUST acknowledge at least one):
    {genuine_gaps}
    
    Transferable Skills:
    {transferable_skills}
    
    Risk Assessment: {risk_assessment}
  </fit_analysis>
</context_data>

<output_template>
Generate a markdown response following this structure:

### Why I'm a Great Fit for [Company/Position]

**Key Alignments:**
- [Specific match from skill analysis with evidence]
- [Specific match from experience]
- [Cultural/value alignment if identified]

**What I Bring:**
[2-3 sentences with SPECIFIC project/skill references from the analysis.
Mention at least one matched skill with its confidence level context.]

**Growth Areas:**
[Honest acknowledgment of 1-2 gaps from Phase 3, framed as opportunities.
Example: "While I haven't worked with Kubernetes in production, my Docker experience 
and quick learning curve would help me ramp up efficiently."]

**Let's Connect:**
[Personalized call to action referencing something specific about the employer.]
</output_template>
```

---

## 4. Context Formatting Utilities

```python
"""
Context formatting utilities for Phase 5.

Transforms prior phase outputs into prompt-ready summaries.
"""

from typing import Dict, List, Optional


def format_matched_skills_summary(phase_4: Dict) -> str:
    """
    Format matched requirements into readable summary.
    
    Args:
        phase_4: Phase 4 output with matched_requirements.
    
    Returns:
        Formatted string for prompt injection.
    """
    matched = phase_4.get("matched_requirements", [])
    
    if not matched:
        return "No specific skill matches identified."
    
    lines = []
    for match in matched[:5]:  # Limit to top 5
        confidence_pct = int(match.get("confidence", 0.5) * 100)
        lines.append(
            f"- {match.get('requirement', 'Unknown')}: "
            f"Matched with {match.get('matched_skill', 'general experience')} "
            f"({confidence_pct}% confidence)"
        )
    
    return "\n".join(lines)


def format_gaps_for_prompt(phase_3: Dict) -> str:
    """
    Format genuine gaps for prompt injection.
    
    Args:
        phase_3: Phase 3 output with genuine_gaps.
    
    Returns:
        Formatted string listing gaps.
    """
    gaps = phase_3.get("genuine_gaps", [])
    
    if not gaps:
        return "No significant gaps identified (unusual - review analysis)."
    
    return "\n".join(f"- {gap}" for gap in gaps)


def detect_employer_context(phase_2: Dict, phase_1: Dict) -> str:
    """
    Detect employer context type for tone calibration.
    
    Args:
        phase_2: Phase 2 employer intelligence.
        phase_1: Phase 1 classification.
    
    Returns:
        Context type string for tone selection.
    """
    summary = (phase_2.get("employer_summary", "") or "").lower()
    culture = " ".join(phase_2.get("culture_signals", [])).lower()
    tech = " ".join(phase_2.get("tech_stack", [])).lower()
    
    combined = f"{summary} {culture} {tech}"
    
    # Priority order detection
    if any(kw in combined for kw in ["ai", "ml", "machine learning", "llm", "deep learning"]):
        return "ai_ml"
    if any(kw in combined for kw in ["fintech", "finance", "payment", "banking"]):
        return "fintech"
    if any(kw in combined for kw in ["startup", "early stage", "seed", "series a", "fast-paced"]):
        return "startup"
    if any(kw in combined for kw in ["enterprise", "fortune 500", "large scale", "global"]):
        return "enterprise"
    
    return "default"
```

---

## 5. Node Implementation

```python
"""
Generate Results Node - Phase 5 of the Fit Check Pipeline.

This module implements the final response generation node that:
1. Synthesizes all prior phase outputs
2. Generates streaming markdown response
3. Ensures honest acknowledgment of gaps
4. Creates compelling, personalized pitch

Gemini Optimization:
- Uses XML-structured prompt with tone calibration
- Streams response chunks via callback
- Evidence-based constraints prevent generic output
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from langchain_core.messages import HumanMessage

from config.llm import get_llm
from services.pipeline_state import FitCheckPipelineState
from services.fit_check_agent import ThoughtCallback

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "generate_results"
PROMPT_FILE = Path(__file__).parent.parent.parent / "prompts" / "phase_5_generate_results.xml"
MAX_RESPONSE_WORDS = 400


# =============================================================================
# Context Formatting
# =============================================================================

def format_matched_skills_summary(phase_4: Dict) -> str:
    """Format matched requirements into readable summary."""
    matched = phase_4.get("matched_requirements", [])
    
    if not matched:
        return "No specific skill matches identified."
    
    lines = []
    for match in matched[:5]:
        confidence_pct = int(match.get("confidence", 0.5) * 100)
        lines.append(
            f"- {match.get('requirement', 'Unknown')}: "
            f"Matched with {match.get('matched_skill', 'general experience')} "
            f"({confidence_pct}% confidence)"
        )
    
    return "\n".join(lines)


def format_gaps_for_prompt(phase_3: Dict) -> str:
    """Format genuine gaps for prompt injection."""
    gaps = phase_3.get("genuine_gaps", [])
    
    if not gaps:
        return "No significant gaps identified."
    
    return "\n".join(f"- {gap}" for gap in gaps)


def detect_employer_context(phase_2: Dict, phase_1: Dict) -> str:
    """Detect employer context type for tone calibration."""
    summary = (phase_2.get("employer_summary", "") or "").lower()
    culture = " ".join(phase_2.get("culture_signals", [])).lower()
    tech = " ".join(phase_2.get("tech_stack", [])).lower()
    
    combined = f"{summary} {culture} {tech}"
    
    if any(kw in combined for kw in ["ai", "ml", "machine learning", "llm"]):
        return "ai_ml"
    if any(kw in combined for kw in ["fintech", "finance", "payment"]):
        return "fintech"
    if any(kw in combined for kw in ["startup", "early stage", "fast-paced"]):
        return "startup"
    if any(kw in combined for kw in ["enterprise", "fortune 500", "global"]):
        return "enterprise"
    
    return "default"


def get_company_or_role(phase_1: Dict, original_query: str) -> str:
    """Extract company name or role for response personalization."""
    if phase_1.get("company_name"):
        return phase_1["company_name"]
    if phase_1.get("job_title"):
        return phase_1["job_title"]
    return original_query[:50]


# =============================================================================
# Prompt Loading
# =============================================================================

def load_phase_prompt() -> str:
    """Load the Phase 5 XML prompt template."""
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Phase 5 prompt not found at {PROMPT_FILE}, using embedded fallback")
        return get_fallback_prompt()


def get_fallback_prompt() -> str:
    """Embedded fallback prompt if file not found."""
    return """<system_instruction>
  <agent_persona>Career Advisor and Technical Writer</agent_persona>
  <primary_objective>
    Generate a compelling, honest fit analysis using SPECIFIC evidence from the analysis.
    MUST acknowledge at least one gap. Keep under 400 words.
  </primary_objective>
</system_instruction>

<context_data>
  Company/Role: {company_or_role}
  Match Score: {match_score}%
  Gaps: {genuine_gaps}
</context_data>

<output_template>
### Why I'm a Great Fit for [Company/Position]

**Key Alignments:**
- [Specific match]

**What I Bring:**
[Specific skills and projects]

**Growth Areas:**
[Honest gap acknowledgment]

**Let's Connect:**
[Call to action]
</output_template>"""


# =============================================================================
# Main Node Function
# =============================================================================

async def generate_results_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 5: GENERATE_RESULTS - Final Response Generation Node.
    
    Synthesizes all prior outputs into a streaming markdown response.
    
    Args:
        state: Current pipeline state with all prior phase outputs.
        callback: Optional callback for SSE event streaming.
    
    Returns:
        State update with final_response.
    
    Emits:
        - phase: "generate_results" at start
        - response: streaming chunks
        - phase_complete: when done
    
    NOTE: This is the only phase that streams response chunks.
    """
    logger.info("[GENERATE_RESULTS] Starting phase 5 - FINAL SYNTHESIS")
    step = state.get("step_count", 0) + 1
    
    # Gather all prior phase outputs
    phase_1 = state.get("phase_1_output", {})
    phase_2 = state.get("phase_2_output", {})
    phase_3 = state.get("phase_3_output", {})
    phase_4 = state.get("phase_4_output", {})
    
    # Emit phase start
    if callback:
        await callback.on_phase(
            PHASE_NAME,
            "Generating personalized fit analysis..."
        )
    
    try:
        # Format context data
        company_or_role = get_company_or_role(phase_1, state["query"])
        employer_context = detect_employer_context(phase_2, phase_1)
        match_score = int(phase_4.get("overall_match_score", 0.5) * 100)
        
        # Load and format prompt
        prompt_template = load_phase_prompt()
        prompt = prompt_template.format(
            query_type=phase_1.get("query_type", "unknown"),
            company_or_role=company_or_role,
            employer_summary=phase_2.get("employer_summary", "No summary available"),
            tech_stack=", ".join(phase_2.get("tech_stack", [])) or "Not identified",
            culture_signals=", ".join(phase_2.get("culture_signals", [])) or "Not identified",
            match_score=match_score,
            matched_skills_summary=format_matched_skills_summary(phase_4),
            genuine_gaps=format_gaps_for_prompt(phase_3),
            transferable_skills=", ".join(phase_3.get("transferable_skills", [])) or "None identified",
            risk_assessment=phase_3.get("risk_assessment", "medium"),
        )
        
        # Get LLM with streaming enabled
        llm = get_llm(streaming=True, temperature=0.7)  # Higher temp for creative writing
        
        # Stream response
        messages = [HumanMessage(content=prompt)]
        full_response = ""
        
        async for chunk in llm.astream(messages):
            chunk_text = chunk.content if hasattr(chunk, 'content') else str(chunk)
            
            if chunk_text:
                full_response += chunk_text
                
                # Emit response chunk
                if callback:
                    await callback.on_response_chunk(chunk_text)
        
        # Validate response quality
        validation_warnings = validate_response_quality(full_response, phase_3)
        if validation_warnings:
            logger.warning(f"[GENERATE_RESULTS] Quality warnings: {validation_warnings}")
        
        # Emit phase complete
        if callback:
            word_count = len(full_response.split())
            await callback.on_phase_complete(
                PHASE_NAME,
                f"Generated {word_count} word response"
            )
        
        logger.info(f"[GENERATE_RESULTS] Phase 5 complete: {len(full_response)} chars")
        
        return {
            "final_response": full_response,
            "step_count": step,
        }
        
    except Exception as e:
        logger.error(f"[GENERATE_RESULTS] Phase 5 failed: {e}")
        
        # Generate minimal fallback response
        company_or_role = get_company_or_role(phase_1, state["query"])
        fallback_response = f"""### Fit Analysis for {company_or_role}

I apologize, but I encountered an issue generating a complete analysis. 
Based on the research conducted, here's a brief summary:

**Key Points:**
- Technical background aligns with general software engineering requirements
- Further conversation would help identify specific alignment areas

**Next Steps:**
I'd be happy to discuss my background and how it might fit your needs in more detail.

*Note: This response was generated with limited analysis due to a processing error.*
"""
        
        if callback:
            await callback.on_response_chunk(fallback_response)
            await callback.on_phase_complete(
                PHASE_NAME,
                "Generated fallback response due to error"
            )
        
        return {
            "final_response": fallback_response,
            "step_count": step,
            "processing_errors": state.get("processing_errors", []) + [f"Phase 5 error: {str(e)}"],
        }


# =============================================================================
# Quality Validation
# =============================================================================

def validate_response_quality(response: str, phase_3: Dict) -> list[str]:
    """
    Validate that the response meets quality criteria.
    
    Returns list of warnings if quality issues detected.
    """
    warnings = []
    
    # Check word count
    word_count = len(response.split())
    if word_count > MAX_RESPONSE_WORDS:
        warnings.append(f"Response exceeds {MAX_RESPONSE_WORDS} words: {word_count}")
    
    # Check for gap acknowledgment
    gaps = phase_3.get("genuine_gaps", [])
    response_lower = response.lower()
    
    gap_acknowledged = False
    for gap in gaps:
        # Check if any significant words from gaps appear in response
        gap_words = [w for w in gap.lower().split() if len(w) > 4]
        if any(word in response_lower for word in gap_words):
            gap_acknowledged = True
            break
    
    # Also check for "growth areas" section
    if "growth" in response_lower or "learning" in response_lower or "ramp" in response_lower:
        gap_acknowledged = True
    
    if not gap_acknowledged and gaps:
        warnings.append("Response may not acknowledge gaps from Phase 3")
    
    # Check for generic phrases
    generic_phrases = [
        "passionate about technology",
        "excited about this opportunity",
        "great culture fit",
        "perfect match",
    ]
    for phrase in generic_phrases:
        if phrase in response_lower:
            warnings.append(f"Generic phrase detected: '{phrase}'")
    
    return warnings
```

---

## 6. Unit Tests

```python
"""
Unit tests for Phase 5: GENERATE_RESULTS node.

Location: res_backend/tests/test_generate_results_node.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, AsyncIterator

from services.nodes.generate_results import (
    generate_results_node,
    format_matched_skills_summary,
    format_gaps_for_prompt,
    detect_employer_context,
    validate_response_quality,
)
from services.pipeline_state import (
    create_initial_state,
    Phase1Output,
    Phase2Output,
    Phase3Output,
    Phase4Output,
)


class TestContextFormatting:
    """Test context formatting utilities."""
    
    def test_format_matched_skills(self):
        """Matched skills format correctly."""
        phase_4 = {
            "matched_requirements": [
                {"requirement": "Python", "matched_skill": "Python", "confidence": 0.9},
                {"requirement": "React", "matched_skill": "React", "confidence": 0.8},
            ]
        }
        result = format_matched_skills_summary(phase_4)
        
        assert "Python" in result
        assert "90%" in result
        assert "React" in result
    
    def test_format_empty_skills(self):
        """Empty skills handled gracefully."""
        result = format_matched_skills_summary({})
        assert "No specific skill" in result
    
    def test_format_gaps(self):
        """Gaps format correctly."""
        phase_3 = {
            "genuine_gaps": ["No Kubernetes experience", "Limited fintech domain"]
        }
        result = format_gaps_for_prompt(phase_3)
        
        assert "Kubernetes" in result
        assert "fintech" in result
    
    def test_detect_ai_context(self):
        """AI/ML context detected correctly."""
        phase_2 = {
            "employer_summary": "OpenAI builds cutting-edge AI and machine learning models",
            "tech_stack": ["Python", "PyTorch", "LLM"],
        }
        result = detect_employer_context(phase_2, {})
        assert result == "ai_ml"
    
    def test_detect_startup_context(self):
        """Startup context detected correctly."""
        phase_2 = {
            "employer_summary": "Fast-paced startup in Series A",
            "culture_signals": ["move fast", "startup culture"],
        }
        result = detect_employer_context(phase_2, {})
        assert result == "startup"
    
    def test_detect_default_context(self):
        """Unknown context defaults correctly."""
        result = detect_employer_context({}, {})
        assert result == "default"


class TestResponseValidation:
    """Test response quality validation."""
    
    def test_validates_word_count(self):
        """Excessive word count is flagged."""
        long_response = "word " * 500
        warnings = validate_response_quality(long_response, {})
        
        assert any("exceeds" in w.lower() for w in warnings)
    
    def test_validates_gap_acknowledgment(self):
        """Missing gap acknowledgment is flagged."""
        response = "I'm a perfect fit with no concerns whatsoever!"
        phase_3 = {"genuine_gaps": ["No Kubernetes experience"]}
        
        warnings = validate_response_quality(response, phase_3)
        
        assert any("gap" in w.lower() for w in warnings)
    
    def test_accepts_gap_acknowledgment(self):
        """Gap acknowledgment passes validation."""
        response = """
        **Growth Areas:**
        While I haven't worked with Kubernetes in production, my Docker experience
        would help me ramp up quickly.
        """
        phase_3 = {"genuine_gaps": ["No Kubernetes experience"]}
        
        warnings = validate_response_quality(response, phase_3)
        
        # Should not flag gap acknowledgment issue
        gap_warnings = [w for w in warnings if "gap" in w.lower()]
        assert len(gap_warnings) == 0
    
    def test_flags_generic_phrases(self):
        """Generic phrases are flagged."""
        response = "I'm passionate about technology and excited about this opportunity!"
        
        warnings = validate_response_quality(response, {})
        
        assert any("generic" in w.lower() for w in warnings)


class TestGenerateResultsNode:
    """Integration tests for the generate results node."""
    
    @pytest.fixture
    def full_state(self):
        """Create a complete state with all prior phase outputs."""
        state = create_initial_state("Google")
        state["phase_1_output"] = Phase1Output(
            query_type="company",
            company_name="Google",
            job_title=None,
            extracted_skills=[],
            reasoning_trace="",
        )
        state["phase_2_output"] = Phase2Output(
            employer_summary="Google is a leading tech company focused on AI",
            identified_requirements=["Python", "TensorFlow", "Distributed Systems"],
            tech_stack=["Python", "Go", "TensorFlow"],
            culture_signals=["Innovation", "Impact at scale"],
            reasoning_trace="",
        )
        state["phase_3_output"] = Phase3Output(
            genuine_strengths=["Python expertise", "AI/ML experience"],
            genuine_gaps=["No Google-scale distributed systems experience"],
            transferable_skills=["Docker experience"],
            risk_assessment="medium",
            reasoning_trace="",
        )
        state["phase_4_output"] = Phase4Output(
            matched_requirements=[
                {"requirement": "Python", "matched_skill": "Python", "confidence": 0.9},
            ],
            unmatched_requirements=["Distributed Systems at scale"],
            overall_match_score=0.72,
            reasoning_trace="",
        )
        state["step_count"] = 10
        return state
    
    @pytest.mark.asyncio
    async def test_generates_streaming_response(self, full_state):
        """Response is streamed correctly."""
        callback = AsyncMock()
        
        # Mock streaming LLM
        async def mock_stream(*args, **kwargs):
            for chunk in ["### Why", " I'm a", " Great Fit"]:
                mock_chunk = MagicMock()
                mock_chunk.content = chunk
                yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            result = await generate_results_node(full_state, callback=callback)
            
            # Verify streaming
            assert callback.on_response_chunk.called
            chunk_calls = callback.on_response_chunk.call_args_list
            assert len(chunk_calls) == 3
            
            # Verify final response assembled
            assert "Why" in result["final_response"]
    
    @pytest.mark.asyncio
    async def test_phase_events_emitted(self, full_state):
        """Phase start and complete events are emitted."""
        callback = AsyncMock()
        
        async def mock_stream(*args, **kwargs):
            mock_chunk = MagicMock()
            mock_chunk.content = "Response content"
            yield mock_chunk
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = mock_stream
            
            await generate_results_node(full_state, callback=callback)
            
            callback.on_phase.assert_called_once()
            callback.on_phase_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_produces_fallback(self, full_state):
        """Errors result in graceful fallback response."""
        callback = AsyncMock()
        
        with patch("services.nodes.generate_results.get_llm") as mock_llm:
            mock_llm.return_value.astream = AsyncMock(side_effect=Exception("LLM Error"))
            
            result = await generate_results_node(full_state, callback=callback)
            
            # Should have a fallback response
            assert "apologize" in result["final_response"].lower()
            assert "processing_errors" in result
```

---

## 7. Response Quality Checklist

The generated response MUST include:

| Element | Requirement | Validation |
|---------|-------------|------------|
| **Company/Role Name** | Personalized header | Check for `phase_1.company_name` or `job_title` |
| **Specific Matches** | At least 2 skill references | Check for items from `phase_4.matched_requirements` |
| **Gap Acknowledgment** | At least 1 gap mentioned | Check for items from `phase_3.genuine_gaps` |
| **Growth Framing** | Gaps framed positively | Look for "learning", "ramp up", "opportunity" |
| **Call to Action** | Personalized closing | Check for employer-specific reference |
| **Word Count** | Under 400 words | Count words in final response |

---

## 8. Validation Checklist

Before proceeding to Phase 6:

- [ ] `services/nodes/generate_results.py` created and importable
- [ ] `prompts/phase_5_generate_results.xml` created
- [ ] Response streams via `callback.on_response_chunk()`
- [ ] All prior phase outputs are used in prompt
- [ ] Gap acknowledgment is validated
- [ ] Generic phrase detection is active
- [ ] Graceful fallback on errors
- [ ] Unit tests pass

---

## 9. Performance Considerations

- **Temperature**: 0.7 (creative but controlled)
- **Streaming**: Chunks emitted as generated
- **Max Tokens**: ~800 (for 400 word limit with formatting)
- **Timeout**: 20s maximum for this phase

---

## 10. Next Steps

After implementing this phase:
1. Proceed to **PHASE_6_FRONTEND_INTEGRATION.md**
2. Frontend updates handle new phase events
3. ComparisonChain uses explicit phase props

---

## 11. Build Verification Gate

> ⛔ **STOP**: Do NOT proceed to the next phase until this phase compiles and builds successfully.

### Backend Build Verification

```powershell
# Navigate to backend directory
cd res_backend

# Verify Python syntax
python -m py_compile services/nodes/generate_results.py

# Verify imports work
python -c "from services.nodes.generate_results import generate_results_node; print('Phase 5 imports OK')"

# Run Phase 5 unit tests
pytest tests/unit/test_generate_results_node.py -v

# Run integration tests (workflow should complete)
pytest tests/integration/test_workflow_transitions.py -v

# Run all tests (ensure no regressions)
pytest --tb=short
```

### Verification Checklist

- [ ] `services/nodes/generate_results.py` created and has no syntax errors
- [ ] `prompts/phase_5_generate_results.xml` created
- [ ] Streaming response works correctly
- [ ] Complete event includes all metadata
- [ ] Import verification succeeds
- [ ] Phase 5 unit tests pass
- [ ] Integration tests pass (full workflow)
- [ ] All existing tests still pass

---

## 12. Requirements Tracking

> 📋 **IMPORTANT**: Refer to **[TRACK_ALL_REQUIREMENTS.md](./TRACK_ALL_REQUIREMENTS.md)** for the complete requirements checklist.

### After Completing This Phase:

1. Open `TRACK_ALL_REQUIREMENTS.md`
2. Locate the **Phase 5: GENERATE_RESULTS Node** section
3. Mark each completed requirement with ✅
4. Fill in the "Verified By" and "Date" columns
5. Complete the **Build Verification** checkboxes
6. Update the **Completion Summary** table at the bottom

### Phase 5 Requirement IDs to Update:

- P5-001 through P5-012

---

*Document Version: 1.1 | Phase 5 of 7 | Final Response Synthesis*
