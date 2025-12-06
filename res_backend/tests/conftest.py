"""
Pytest Configuration and Shared Fixtures

This module provides common fixtures and configuration for all tests.
"""

import os
import sys
import pytest
from pathlib import Path

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ.setdefault("GOOGLE_API_KEY", "test_api_key")
os.environ.setdefault("GOOGLE_CSE_API_KEY", "test_cse_key")
os.environ.setdefault("GOOGLE_CSE_ID", "test_cse_id")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3003")


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for Windows compatibility."""
    import asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture
def mock_env(monkeypatch):
    """Fixture to mock environment variables."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
    monkeypatch.setenv("GOOGLE_CSE_API_KEY", "test_cse_key")
    monkeypatch.setenv("GOOGLE_CSE_ID", "test_cse_id")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3003")


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "Google"


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
    Senior Software Engineer position at a fast-growing startup.
    Requirements:
    - 5+ years experience with Python
    - Experience with FastAPI or Django
    - Cloud platform experience (AWS/GCP)
    - Strong communication skills
    """


@pytest.fixture
def sample_thoughts():
    """Sample thought events for testing."""
    return [
        {
            "step": 1,
            "type": "tool_call",
            "tool": "web_search",
            "input": "Google company culture engineering",
        },
        {
            "step": 2,
            "type": "observation",
            "content": "Google is known for its innovative culture...",
        },
        {
            "step": 3,
            "type": "reasoning",
            "content": "Based on the research, the candidate's skills align well...",
        },
    ]


# =============================================================================
# Markers
# =============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
