"""
Fit Check Agent Unit Tests

Tests for the FitCheckAgent class and related functions.
Run with: pytest tests/test_fit_check_agent.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# State Tests
# =============================================================================

class TestFitCheckState:
    """Tests for FitCheckState structure."""
    
    def test_state_structure(self):
        """Test that state has all required fields."""
        from services.fit_check_agent import FitCheckState
        
        state = FitCheckState(
            messages=[],
            query="Test query",
            query_type=None,
            research_results=None,
            skill_analysis=None,
            experience_analysis=None,
            step_count=0,
            final_response=None,
            error=None,
        )
        
        assert state["query"] == "Test query"
        assert state["step_count"] == 0
        assert state["error"] is None


# =============================================================================
# Agent Tests
# =============================================================================

class TestFitCheckAgent:
    """Tests for the FitCheckAgent class."""
    
    def test_agent_initialization(self):
        """Test that agent initializes correctly."""
        from services.fit_check_agent import FitCheckAgent
        
        agent = FitCheckAgent()
        assert agent._graph is None  # Lazy initialization
    
    def test_agent_singleton(self):
        """Test that get_agent returns singleton instance."""
        from services.fit_check_agent import get_agent
        
        agent1 = get_agent()
        agent2 = get_agent()
        
        assert agent1 is agent2
    
    def test_create_initial_state(self):
        """Test initial state creation."""
        from services.fit_check_agent import FitCheckAgent
        
        agent = FitCheckAgent()
        state = agent._create_initial_state("Google")
        
        assert state["query"] == "Google"
        assert state["step_count"] == 0
        assert len(state["messages"]) == 1
        assert state["messages"][0].content == "Google"


# =============================================================================
# Graph Tests
# =============================================================================

class TestGraphStructure:
    """Tests for the LangGraph structure."""
    
    def test_graph_builds(self):
        """Test that the graph builds without errors."""
        from services.fit_check_agent import build_fit_check_graph
        
        graph = build_fit_check_graph()
        assert graph is not None
    
    def test_should_continue_with_tool_calls(self):
        """Test continuation logic with tool calls."""
        from services.fit_check_agent import should_continue, FitCheckState
        from langchain_core.messages import AIMessage
        
        # Create a mock message with tool calls
        mock_message = MagicMock()
        mock_message.tool_calls = [{"name": "web_search", "args": {"query": "test"}}]
        
        state = FitCheckState(
            messages=[mock_message],
            query="test",
            query_type=None,
            research_results=None,
            skill_analysis=None,
            experience_analysis=None,
            step_count=0,
            final_response=None,
            error=None,
        )
        
        result = should_continue(state)
        assert result == "tools"
    
    def test_should_continue_without_tool_calls(self):
        """Test continuation logic without tool calls."""
        from services.fit_check_agent import should_continue, FitCheckState
        from langchain_core.messages import AIMessage
        
        # Create a mock message without tool calls
        mock_message = MagicMock()
        mock_message.tool_calls = None
        
        state = FitCheckState(
            messages=[mock_message],
            query="test",
            query_type=None,
            research_results=None,
            skill_analysis=None,
            experience_analysis=None,
            step_count=0,
            final_response=None,
            error=None,
        )
        
        from langgraph.graph import END
        result = should_continue(state)
        assert result == END


# =============================================================================
# Callback Tests
# =============================================================================

class TestThoughtCallback:
    """Tests for the ThoughtCallback interface."""
    
    @pytest.mark.asyncio
    async def test_callback_interface(self):
        """Test that ThoughtCallback interface works."""
        from services.fit_check_agent import ThoughtCallback
        
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
# System Prompt Tests
# =============================================================================

class TestSystemPrompt:
    """Tests for system prompt loading."""
    
    def test_load_system_prompt(self):
        """Test that system prompt loads correctly."""
        from services.fit_check_agent import load_system_prompt
        
        prompt = load_system_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
