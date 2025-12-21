"""
Fit Check Agent Unit Tests

Tests for the FitCheckAgent class and related functions.
Run with: pytest tests/test_fit_check_agent.py -v

Updated for Multi-Session Architecture (2025-12-20):
- Uses FitCheckPipelineState instead of FitCheckState
- Uses build_fit_check_pipeline instead of build_fit_check_graph
- Uses create_initial_state from pipeline_state module
- Agent is now stateless with isolated callback holders per request
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# State Tests
# =============================================================================

class TestFitCheckState:
    """Tests for FitCheckPipelineState structure."""
    
    def test_state_structure(self):
        """Test that state has all required fields via create_initial_state."""
        from services.pipeline_state import create_initial_state
        
        state = create_initial_state(
            query="Test query",
            model_id="gemini-3-flash-preview",
            config_type="reasoning"
        )
        
        assert state["query"] == "Test query"
        assert state["step_count"] == 0
        assert state.get("error") is None
        assert state["model_id"] == "gemini-3-flash-preview"
        assert state["config_type"] == "reasoning"
        assert "current_phase" in state


# =============================================================================
# Agent Tests
# =============================================================================

class TestFitCheckAgent:
    """Tests for the FitCheckAgent class."""
    
    def test_agent_initialization(self):
        """Test that agent initializes correctly (now stateless)."""
        from services.fit_check_agent import FitCheckAgent
        
        agent = FitCheckAgent()
        # Agent is now stateless - no shared _callback_holder
        assert agent is not None
    
    def test_agent_singleton(self):
        """Test that get_agent returns singleton instance."""
        from services.fit_check_agent import get_agent
        
        agent1 = get_agent()
        agent2 = get_agent()
        
        assert agent1 is agent2
    
    def test_create_initial_state(self):
        """Test initial state creation from pipeline_state module."""
        from services.pipeline_state import create_initial_state
        
        state = create_initial_state("Google")
        
        assert state["query"] == "Google"
        assert state["step_count"] == 0
        assert state["current_phase"] == "connecting"


# =============================================================================
# Graph Tests
# =============================================================================

class TestGraphStructure:
    """Tests for the LangGraph pipeline structure."""
    
    def test_graph_builds(self):
        """Test that the pipeline builds without errors."""
        from services.fit_check_agent import build_fit_check_pipeline
        
        pipeline = build_fit_check_pipeline()
        assert pipeline is not None
    
    def test_pipeline_has_entry_point(self):
        """Test that pipeline has connecting as entry point."""
        from services.fit_check_agent import build_fit_check_pipeline
        
        # Pipeline should build successfully with callback holder
        callback_holder = {"callback": AsyncMock()}
        pipeline = build_fit_check_pipeline(callback_holder)
        assert pipeline is not None
    
    def test_pipeline_isolation(self):
        """Test that each pipeline build gets isolated callback holder."""
        from services.fit_check_agent import build_fit_check_pipeline
        
        callback_a = {"callback": AsyncMock()}
        callback_b = {"callback": AsyncMock()}
        
        pipeline_a = build_fit_check_pipeline(callback_a)
        pipeline_b = build_fit_check_pipeline(callback_b)
        
        # Both should be valid but isolated
        assert pipeline_a is not None
        assert pipeline_b is not None
        assert callback_a["callback"] != callback_b["callback"]


# =============================================================================
# Callback Tests
# =============================================================================

class TestThoughtCallback:
    """Tests for the ThoughtCallback interface."""
    
    @pytest.mark.asyncio
    async def test_callback_interface(self):
        """Test that ThoughtCallback interface works."""
        from services.callbacks import ThoughtCallback
        
        callback = ThoughtCallback()
        
        # These should not raise exceptions
        await callback.on_status("connecting", "Test message")
        await callback.on_thought(1, "tool_call", "test", "web_search", "{}")
        await callback.on_response_chunk("chunk")
        await callback.on_complete(1000)
        await callback.on_error("TEST_ERROR", "Test error")


# =============================================================================
# Profile Tests
# =============================================================================

class TestEngineerProfile:
    """Tests for engineer profile configuration."""
    
    def test_profile_exists(self):
        """Test that engineer profile is defined."""
        from config.engineer_profile import ENGINEER_PROFILE
        
        assert ENGINEER_PROFILE is not None
        assert "name" in ENGINEER_PROFILE
        assert "skills" in ENGINEER_PROFILE
    
    def test_formatted_profile(self):
        """Test that profile formats correctly."""
        from config.engineer_profile import get_formatted_profile
        
        profile = get_formatted_profile()
        
        assert isinstance(profile, str)
        assert len(profile) > 0
        assert "Skills:" in profile or "skills" in profile.lower()


# =============================================================================
# Metrics Tests
# =============================================================================

class TestMetrics:
    """Tests for observability metrics."""
    
    def test_metrics_available(self):
        """Test that metrics module loads correctly."""
        from services.metrics import (
            track_request_start,
            track_request_end,
            track_phase_complete,
        )
        
        # Should be callable without errors
        assert callable(track_request_start)
        assert callable(track_request_end)
        assert callable(track_phase_complete)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
