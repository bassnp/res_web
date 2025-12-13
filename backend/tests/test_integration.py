"""
Integration Tests - API Endpoints

Tests for the FastAPI endpoints including health checks and SSE streaming.
Run with: pytest tests/test_integration.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# =============================================================================
# Test Client Fixture
# =============================================================================

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from server import app
    
    return TestClient(app)


@pytest.fixture
def async_client():
    """Create an async test client for SSE testing."""
    from httpx import AsyncClient, ASGITransport
    from server import app
    
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# =============================================================================
# Health Check Tests
# =============================================================================

class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "Portfolio Backend API"
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
    
    def test_fit_check_health(self, client):
        """Test the fit-check specific health endpoint."""
        response = client.get("/api/fit-check/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "fit-check"


# =============================================================================
# Request Validation Tests
# =============================================================================

class TestRequestValidation:
    """Tests for request validation."""
    
    def test_missing_query(self, client):
        """Test that missing query returns 422."""
        response = client.post(
            "/api/fit-check/stream",
            json={}
        )
        
        assert response.status_code == 422
    
    def test_query_too_short(self, client):
        """Test that query under 3 characters returns 422."""
        response = client.post(
            "/api/fit-check/stream",
            json={"query": "ab"}  # Only 2 characters
        )
        
        assert response.status_code == 422
    
    def test_query_too_long(self, client):
        """Test that query over 2000 characters returns 422."""
        response = client.post(
            "/api/fit-check/stream",
            json={"query": "x" * 2001}
        )
        
        assert response.status_code == 422
    
    def test_valid_query_accepted(self, client):
        """Test that valid query is accepted (SSE stream starts)."""
        with patch('routers.fit_check.get_agent') as mock_agent:
            # Mock the agent to avoid actual API calls
            mock_instance = MagicMock()
            mock_instance.stream_analysis = AsyncMock(return_value=iter([]))
            mock_agent.return_value = mock_instance
            
            response = client.post(
                "/api/fit-check/stream",
                json={"query": "Google"},
                headers={"Accept": "text/event-stream"}
            )
            
            # Should return 200 with SSE content type
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")


# =============================================================================
# SSE Stream Tests
# =============================================================================

class TestSSEStream:
    """Tests for SSE streaming functionality."""
    
    def test_sse_content_type(self, client):
        """Test that SSE endpoint returns correct content type."""
        with patch('routers.fit_check.get_agent') as mock_agent:
            mock_instance = MagicMock()
            mock_instance.stream_analysis = AsyncMock(return_value=iter([]))
            mock_agent.return_value = mock_instance
            
            response = client.post(
                "/api/fit-check/stream",
                json={"query": "Test Company"}
            )
            
            content_type = response.headers.get("content-type", "")
            assert "text/event-stream" in content_type
    
    def test_sse_headers(self, client):
        """Test that SSE endpoint returns correct headers."""
        with patch('routers.fit_check.get_agent') as mock_agent:
            mock_instance = MagicMock()
            mock_instance.stream_analysis = AsyncMock(return_value=iter([]))
            mock_agent.return_value = mock_instance
            
            response = client.post(
                "/api/fit-check/stream",
                json={"query": "Test Company"}
            )
            
            # Check for SSE-specific headers
            assert response.headers.get("cache-control") == "no-cache"


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_json(self, client):
        """Test that invalid JSON returns 422."""
        response = client.post(
            "/api/fit-check/stream",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


# =============================================================================
# Pydantic Model Tests
# =============================================================================

class TestPydanticModels:
    """Tests for Pydantic request/response models."""
    
    def test_fit_check_request_valid(self):
        """Test valid FitCheckRequest."""
        from models.fit_check import FitCheckRequest
        
        request = FitCheckRequest(query="Google", include_thoughts=True)
        
        assert request.query == "Google"
        assert request.include_thoughts is True
    
    def test_fit_check_request_default_thoughts(self):
        """Test FitCheckRequest defaults include_thoughts to True."""
        from models.fit_check import FitCheckRequest
        
        request = FitCheckRequest(query="Test query")
        
        assert request.include_thoughts is True
    
    def test_status_event(self):
        """Test StatusEvent model."""
        from models.fit_check import StatusEvent
        
        event = StatusEvent(status="connecting", message="Test message")
        
        assert event.status == "connecting"
        assert event.message == "Test message"
    
    def test_thought_event(self):
        """Test ThoughtEvent model."""
        from models.fit_check import ThoughtEvent
        
        event = ThoughtEvent(
            step=1,
            type="tool_call",
            tool="web_search",
            input="test query"
        )
        
        assert event.step == 1
        assert event.type == "tool_call"
        assert event.tool == "web_search"
    
    def test_response_event(self):
        """Test ResponseEvent model."""
        from models.fit_check import ResponseEvent
        
        event = ResponseEvent(chunk="Test chunk")
        
        assert event.chunk == "Test chunk"
    
    def test_complete_event(self):
        """Test CompleteEvent model."""
        from models.fit_check import CompleteEvent
        
        event = CompleteEvent(duration_ms=5000)
        
        assert event.duration_ms == 5000
    
    def test_error_event(self):
        """Test ErrorEvent model."""
        from models.fit_check import ErrorEvent
        
        event = ErrorEvent(code="AGENT_ERROR", message="Test error")
        
        assert event.code == "AGENT_ERROR"
        assert event.message == "Test error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
