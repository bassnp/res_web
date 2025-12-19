#!/usr/bin/env python3
"""
SSE Event Flow Tests

Tests for validating the SSE event sequence matches the expected contract.

Run with:
    pytest tests/simulation/test_sse_event_flow.py -v
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# Expected Event Sequence
# =============================================================================

EXPECTED_PHASE_ORDER = [
    "connecting",
    "deep_research",
    "research_reranker",
    "content_enrich",
    "skeptical_comparison",
    "skills_matching",
    "confidence_reranker",
    "generate_results",
]

EXPECTED_EVENT_TYPES = {
    "phase",           # Phase transition
    "phase_complete",  # Phase finished
    "status",          # Status update (legacy)
    "thought",         # Agent thought
    "response",        # Response chunk
    "complete",        # Stream complete
    "error",           # Error occurred
}

VALID_THOUGHT_TYPES = {
    "tool_call",
    "observation", 
    "reasoning",
}

VALID_STATUS_VALUES = {
    "connecting",
    "researching",
    "analyzing",
    "generating",
}


# =============================================================================
# Event Validation
# =============================================================================

@dataclass
class EventSequenceValidator:
    """Validates SSE event sequences against expected patterns."""
    
    events: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    phases_started: List[str] = field(default_factory=list)
    phases_completed: List[str] = field(default_factory=list)
    current_phase: str = None
    
    def add_event(self, event_type: str, data: Dict) -> None:
        """Add and validate a single event."""
        self.events.append({"type": event_type, "data": data})
        
        # Validate event type
        if event_type not in EXPECTED_EVENT_TYPES:
            self.errors.append(f"Unknown event type: {event_type}")
            return
        
        # Dispatch to type-specific validator
        validator = getattr(self, f"_validate_{event_type}", None)
        if validator:
            validator(data)
    
    def _validate_phase(self, data: Dict) -> None:
        """Validate phase transition event."""
        phase = data.get("phase")
        message = data.get("message")
        
        if not phase:
            self.errors.append("phase event missing 'phase' field")
            return
        
        if phase not in EXPECTED_PHASE_ORDER:
            self.errors.append(f"Unknown phase: {phase}")
            return
        
        if not message:
            self.warnings.append(f"phase '{phase}' has no message")
        
        # Check phase order
        if self.phases_started:
            expected_idx = EXPECTED_PHASE_ORDER.index(self.phases_started[-1]) + 1
            actual_idx = EXPECTED_PHASE_ORDER.index(phase)
            
            if actual_idx != expected_idx:
                self.errors.append(
                    f"Phase order violation: expected {EXPECTED_PHASE_ORDER[expected_idx]}, "
                    f"got {phase}"
                )
        else:
            # First phase should be 'connecting'
            if phase != "connecting":
                self.errors.append(f"First phase should be 'connecting', got '{phase}'")
        
        self.phases_started.append(phase)
        self.current_phase = phase
    
    def _validate_phase_complete(self, data: Dict) -> None:
        """Validate phase completion event."""
        phase = data.get("phase")
        summary = data.get("summary")
        
        if not phase:
            self.errors.append("phase_complete event missing 'phase' field")
            return
        
        if phase not in self.phases_started:
            self.errors.append(f"phase_complete for phase that wasn't started: {phase}")
            return
        
        if phase in self.phases_completed:
            self.errors.append(f"Duplicate phase_complete for: {phase}")
            return
        
        if not summary:
            self.warnings.append(f"phase_complete '{phase}' has empty summary")
        
        self.phases_completed.append(phase)
    
    def _validate_status(self, data: Dict) -> None:
        """Validate status event."""
        status = data.get("status")
        message = data.get("message")
        
        if not status:
            self.errors.append("status event missing 'status' field")
            return
        
        if status not in VALID_STATUS_VALUES:
            self.warnings.append(f"Non-standard status value: {status}")
    
    def _validate_thought(self, data: Dict) -> None:
        """Validate thought event."""
        step = data.get("step")
        thought_type = data.get("type")
        content = data.get("content")
        phase = data.get("phase")
        
        if step is None:
            self.errors.append("thought event missing 'step' field")
        
        if not thought_type:
            self.errors.append("thought event missing 'type' field")
        elif thought_type not in VALID_THOUGHT_TYPES:
            self.warnings.append(f"Non-standard thought type: {thought_type}")
        
        if thought_type == "tool_call":
            tool = data.get("tool")
            if not tool:
                self.errors.append("tool_call thought missing 'tool' field")
        
        if not phase and not self.current_phase:
            self.warnings.append("thought event has no phase context")
    
    def _validate_response(self, data: Dict) -> None:
        """Validate response chunk event."""
        chunk = data.get("chunk")
        
        if chunk is None:
            self.errors.append("response event missing 'chunk' field")
        elif not isinstance(chunk, str):
            self.errors.append(f"response chunk must be string, got {type(chunk)}")
    
    def _validate_complete(self, data: Dict) -> None:
        """Validate completion event."""
        duration_ms = data.get("duration_ms")
        
        if duration_ms is None:
            self.warnings.append("complete event missing 'duration_ms'")
        elif not isinstance(duration_ms, (int, float)) or duration_ms < 0:
            self.errors.append(f"Invalid duration_ms: {duration_ms}")
        
        # All phases should be completed
        for phase in EXPECTED_PHASE_ORDER:
            if phase not in self.phases_completed:
                self.errors.append(f"Phase not completed before 'complete': {phase}")
    
    def _validate_error(self, data: Dict) -> None:
        """Validate error event."""
        code = data.get("code")
        message = data.get("message")
        
        if not code:
            self.errors.append("error event missing 'code' field")
        if not message:
            self.errors.append("error event missing 'message' field")
    
    def get_summary(self) -> Dict:
        """Get validation summary."""
        return {
            "total_events": len(self.events),
            "phases_started": self.phases_started,
            "phases_completed": self.phases_completed,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "valid": len(self.errors) == 0,
        }


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def validator():
    """Create a fresh validator instance."""
    return EventSequenceValidator()


@pytest.fixture
def valid_event_sequence():
    """Create a valid complete event sequence."""
    return [
        # Phase 1: Connecting
        {"type": "phase", "data": {"phase": "connecting", "message": "Classifying query..."}},
        {"type": "thought", "data": {"step": 1, "type": "reasoning", "phase": "connecting", "content": "Analyzing input..."}},
        {"type": "phase_complete", "data": {"phase": "connecting", "summary": "Classified as company"}},
        
        # Phase 2: Deep Research
        {"type": "phase", "data": {"phase": "deep_research", "message": "Gathering intelligence..."}},
        {"type": "thought", "data": {"step": 2, "type": "tool_call", "tool": "web_search", "phase": "deep_research", "input": "Google careers"}},
        {"type": "thought", "data": {"step": 3, "type": "observation", "phase": "deep_research", "content": "Found tech stack info..."}},
        {"type": "phase_complete", "data": {"phase": "deep_research", "summary": "Found Python, Go, TensorFlow"}},
        
        # Phase 3: Skeptical Comparison
        {"type": "phase", "data": {"phase": "skeptical_comparison", "message": "Critical analysis..."}},
        {"type": "thought", "data": {"step": 4, "type": "reasoning", "phase": "skeptical_comparison", "content": "Evaluating gaps..."}},
        {"type": "phase_complete", "data": {"phase": "skeptical_comparison", "summary": "Identified 2 gaps"}},
        
        # Phase 4: Skills Matching
        {"type": "phase", "data": {"phase": "skills_matching", "message": "Mapping skills..."}},
        {"type": "thought", "data": {"step": 5, "type": "tool_call", "tool": "analyze_skill_match", "phase": "skills_matching"}},
        {"type": "thought", "data": {"step": 6, "type": "observation", "phase": "skills_matching", "content": "Matched 5/7 requirements"}},
        {"type": "phase_complete", "data": {"phase": "skills_matching", "summary": "Match score: 0.72"}},
        
        # Phase 5: Generate Results
        {"type": "phase", "data": {"phase": "generate_results", "message": "Synthesizing response..."}},
        {"type": "response", "data": {"chunk": "### Why I'm a Great Fit\n\n"}},
        {"type": "response", "data": {"chunk": "**Key Alignments:**\n- Python expertise\n"}},
        {"type": "phase_complete", "data": {"phase": "generate_results", "summary": "Response generated"}},
        
        # Completion
        {"type": "complete", "data": {"duration_ms": 12500}},
    ]


# =============================================================================
# Test Cases
# =============================================================================

class TestEventSequenceValidation:
    """Tests for event sequence validation."""
    
    def test_valid_sequence(self, validator, valid_event_sequence):
        """Test that valid sequence passes validation."""
        for event in valid_event_sequence:
            validator.add_event(event["type"], event["data"])
        
        summary = validator.get_summary()
        assert summary["valid"], f"Errors: {summary['errors']}"
        assert len(summary["phases_completed"]) == 5
    
    def test_unknown_event_type(self, validator):
        """Test detection of unknown event type."""
        validator.add_event("unknown_type", {"data": "test"})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("Unknown event type" in e for e in summary["errors"])
    
    def test_phase_order_violation(self, validator):
        """Test detection of phase order violation."""
        validator.add_event("phase", {"phase": "connecting", "message": "..."})
        validator.add_event("phase_complete", {"phase": "connecting", "summary": "..."})
        # Skip deep_research and go straight to skeptical_comparison
        validator.add_event("phase", {"phase": "skeptical_comparison", "message": "..."})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("Phase order violation" in e for e in summary["errors"])
    
    def test_first_phase_not_connecting(self, validator):
        """Test detection of wrong first phase."""
        validator.add_event("phase", {"phase": "deep_research", "message": "..."})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("First phase should be 'connecting'" in e for e in summary["errors"])
    
    def test_phase_complete_without_start(self, validator):
        """Test detection of phase_complete for unstarted phase."""
        validator.add_event("phase_complete", {"phase": "connecting", "summary": "..."})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("phase that wasn't started" in e for e in summary["errors"])
    
    def test_duplicate_phase_complete(self, validator):
        """Test detection of duplicate phase_complete."""
        validator.add_event("phase", {"phase": "connecting", "message": "..."})
        validator.add_event("phase_complete", {"phase": "connecting", "summary": "..."})
        validator.add_event("phase_complete", {"phase": "connecting", "summary": "..."})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("Duplicate phase_complete" in e for e in summary["errors"])
    
    def test_thought_missing_step(self, validator):
        """Test detection of thought without step number."""
        validator.add_event("thought", {"type": "reasoning", "content": "..."})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("missing 'step'" in e for e in summary["errors"])
    
    def test_tool_call_missing_tool(self, validator):
        """Test detection of tool_call without tool name."""
        validator.add_event("thought", {"step": 1, "type": "tool_call", "content": "..."})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("missing 'tool'" in e for e in summary["errors"])
    
    def test_response_missing_chunk(self, validator):
        """Test detection of response without chunk."""
        validator.add_event("response", {})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("missing 'chunk'" in e for e in summary["errors"])
    
    def test_complete_with_missing_phases(self, validator):
        """Test detection of complete event with incomplete phases."""
        validator.add_event("phase", {"phase": "connecting", "message": "..."})
        validator.add_event("phase_complete", {"phase": "connecting", "summary": "..."})
        validator.add_event("complete", {"duration_ms": 5000})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("Phase not completed before 'complete'" in e for e in summary["errors"])
    
    def test_negative_duration(self, validator):
        """Test detection of negative duration_ms."""
        validator.add_event("complete", {"duration_ms": -100})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("Invalid duration_ms" in e for e in summary["errors"])


class TestEventDataValidation:
    """Tests for individual event data validation."""
    
    def test_phase_event_missing_phase(self, validator):
        """Test detection of phase event without phase field."""
        validator.add_event("phase", {"message": "Starting..."})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("missing 'phase' field" in e for e in summary["errors"])
    
    def test_phase_event_unknown_phase(self, validator):
        """Test detection of unknown phase name."""
        validator.add_event("phase", {"phase": "unknown_phase", "message": "..."})
        
        summary = validator.get_summary()
        assert not summary["valid"]
        assert any("Unknown phase" in e for e in summary["errors"])
    
    def test_error_event_missing_fields(self, validator):
        """Test detection of error event with missing fields."""
        validator.add_event("error", {})
        
        summary = validator.get_summary()
        assert any("missing 'code'" in e for e in summary["errors"])
        assert any("missing 'message'" in e for e in summary["errors"])
    
    def test_thought_non_standard_type(self, validator):
        """Test warning for non-standard thought type."""
        validator.add_event("thought", {
            "step": 1, 
            "type": "custom_type", 
            "content": "..."
        })
        
        summary = validator.get_summary()
        assert any("Non-standard thought type" in w for w in summary["warnings"])


class TestPhaseTracking:
    """Tests for phase tracking functionality."""
    
    def test_phases_tracked_correctly(self, validator, valid_event_sequence):
        """Test that phases are tracked in correct order."""
        for event in valid_event_sequence:
            validator.add_event(event["type"], event["data"])
        
        assert validator.phases_started == EXPECTED_PHASE_ORDER
        assert validator.phases_completed == EXPECTED_PHASE_ORDER
    
    def test_current_phase_updates(self, validator):
        """Test that current_phase updates on phase events."""
        validator.add_event("phase", {"phase": "connecting", "message": "..."})
        assert validator.current_phase == "connecting"
        
        validator.add_event("phase_complete", {"phase": "connecting", "summary": "..."})
        validator.add_event("phase", {"phase": "deep_research", "message": "..."})
        assert validator.current_phase == "deep_research"


# =============================================================================
# Performance Tests
# =============================================================================

class TestEventTiming:
    """Tests for event timing validation."""
    
    def test_reasonable_duration(self, validator, valid_event_sequence):
        """Test that total duration is within expected bounds."""
        for event in valid_event_sequence:
            validator.add_event(event["type"], event["data"])
        
        # Check the complete event has reasonable duration
        complete_event = next(
            e for e in validator.events if e["type"] == "complete"
        )
        duration_ms = complete_event["data"].get("duration_ms")
        
        assert duration_ms is not None
        assert 0 < duration_ms < 120000  # Less than 2 minutes
    
    def test_event_count_reasonable(self, validator, valid_event_sequence):
        """Test that event count is within expected range."""
        for event in valid_event_sequence:
            validator.add_event(event["type"], event["data"])
        
        summary = validator.get_summary()
        
        # Should have at least: 5 phase + 5 phase_complete + 1 complete = 11
        assert summary["total_events"] >= 11
        
        # Shouldn't have excessive events (memory concern)
        assert summary["total_events"] < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
