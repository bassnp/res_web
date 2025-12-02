"""
Diagnostic Test Script - Frontend User Flow Simulation

This script simulates the frontend user flow to rigorously test the backend
SSE streaming endpoint. It performs the following tests:

1. Health Check Validation
2. Request Validation (edge cases)
3. Full SSE Stream Parsing
4. End-to-End Fit Analysis Flow
5. Error Handling

Usage:
    python diagnostic_test.py [--live]
    
    --live: Run against actual API (requires GOOGLE_API_KEY in .env)
            Without --live, uses mocked agent responses
"""

import asyncio
import json
import sys
import time
from dataclasses import dataclass
from typing import List, Optional
import httpx


# =============================================================================
# Configuration
# =============================================================================

BASE_URL = "http://localhost:8000"
TIMEOUT = 120  # 2 minutes for AI processing


# =============================================================================
# SSE Event Parser
# =============================================================================

@dataclass
class SSEEvent:
    """Parsed SSE event."""
    event_type: str
    data: dict
    raw: str


def parse_sse_events(raw_text: str) -> List[SSEEvent]:
    """
    Parse raw SSE text into structured events.
    
    Args:
        raw_text: Raw SSE stream text.
    
    Returns:
        List of parsed SSE events.
    """
    events = []
    current_event_type = None
    current_data = None
    
    for line in raw_text.split("\n"):
        line = line.strip()
        
        if line.startswith("event:"):
            current_event_type = line[6:].strip()
        elif line.startswith("data:"):
            current_data = line[5:].strip()
            
            if current_event_type and current_data:
                try:
                    data_dict = json.loads(current_data)
                    events.append(SSEEvent(
                        event_type=current_event_type,
                        data=data_dict,
                        raw=f"event: {current_event_type}\ndata: {current_data}"
                    ))
                except json.JSONDecodeError:
                    events.append(SSEEvent(
                        event_type=current_event_type,
                        data={"raw": current_data},
                        raw=f"event: {current_event_type}\ndata: {current_data}"
                    ))
                current_event_type = None
                current_data = None
    
    return events


# =============================================================================
# Test Results Tracking
# =============================================================================

class TestResults:
    """Track test results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: List[str] = []
    
    def record(self, name: str, passed: bool, error: Optional[str] = None):
        """Record a test result."""
        if passed:
            self.passed += 1
            print(f"  ✅ {name}")
        else:
            self.failed += 1
            error_msg = f"{name}: {error}" if error else name
            self.errors.append(error_msg)
            print(f"  ❌ {name}" + (f" - {error}" if error else ""))
    
    def summary(self):
        """Print summary."""
        print("\n" + "=" * 60)
        print(f"TEST SUMMARY: {self.passed} passed, {self.failed} failed")
        if self.errors:
            print("\nFailed Tests:")
            for error in self.errors:
                print(f"  • {error}")
        print("=" * 60)
        return self.failed == 0


# =============================================================================
# Test Functions
# =============================================================================

async def test_health_checks(client: httpx.AsyncClient, results: TestResults):
    """Test health check endpoints."""
    print("\n🏥 Health Check Tests")
    
    # Test root endpoint
    try:
        r = await client.get("/")
        results.record(
            "Root endpoint returns API info",
            r.status_code == 200 and "name" in r.json()
        )
    except Exception as e:
        results.record("Root endpoint returns API info", False, str(e))
    
    # Test main health
    try:
        r = await client.get("/health")
        data = r.json()
        results.record(
            "Main health endpoint returns healthy",
            r.status_code == 200 and data.get("status") == "healthy"
        )
    except Exception as e:
        results.record("Main health endpoint returns healthy", False, str(e))
    
    # Test fit-check health
    try:
        r = await client.get("/api/fit-check/health")
        data = r.json()
        results.record(
            "Fit-check health endpoint returns healthy",
            r.status_code == 200 and data.get("service") == "fit-check",
            f"status={data.get('status')}" if r.status_code == 200 else f"status_code={r.status_code}"
        )
    except Exception as e:
        results.record("Fit-check health endpoint returns healthy", False, str(e))


async def test_request_validation(client: httpx.AsyncClient, results: TestResults):
    """Test request validation."""
    print("\n📋 Request Validation Tests")
    
    # Test missing query
    try:
        r = await client.post("/api/fit-check/stream", json={})
        results.record(
            "Missing query returns 422",
            r.status_code == 422
        )
    except Exception as e:
        results.record("Missing query returns 422", False, str(e))
    
    # Test query too short
    try:
        r = await client.post("/api/fit-check/stream", json={"query": "ab"})
        results.record(
            "Query too short (2 chars) returns 422",
            r.status_code == 422
        )
    except Exception as e:
        results.record("Query too short (2 chars) returns 422", False, str(e))
    
    # Test minimum valid query
    try:
        r = await client.post(
            "/api/fit-check/stream",
            json={"query": "abc"},
            timeout=5.0
        )
        results.record(
            "Minimum valid query (3 chars) returns 200",
            r.status_code == 200
        )
    except Exception as e:
        results.record("Minimum valid query (3 chars) returns 200", False, str(e))
    
    # Test query too long
    try:
        r = await client.post(
            "/api/fit-check/stream",
            json={"query": "x" * 2001}
        )
        results.record(
            "Query too long (2001 chars) returns 422",
            r.status_code == 422
        )
    except Exception as e:
        results.record("Query too long (2001 chars) returns 422", False, str(e))
    
    # Test invalid JSON
    try:
        r = await client.post(
            "/api/fit-check/stream",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        results.record(
            "Invalid JSON returns 422",
            r.status_code == 422
        )
    except Exception as e:
        results.record("Invalid JSON returns 422", False, str(e))


async def test_sse_headers(client: httpx.AsyncClient, results: TestResults):
    """Test SSE headers."""
    print("\n📡 SSE Header Tests")
    
    try:
        async with client.stream(
            "POST",
            "/api/fit-check/stream",
            json={"query": "Test Company"},
            timeout=30.0
        ) as response:
            content_type = response.headers.get("content-type", "")
            cache_control = response.headers.get("cache-control", "")
            
            results.record(
                "Content-Type is text/event-stream",
                "text/event-stream" in content_type,
                f"Got: {content_type}"
            )
            
            results.record(
                "Cache-Control is no-cache",
                "no-cache" in cache_control,
                f"Got: {cache_control}"
            )
    except Exception as e:
        results.record("SSE headers test", False, str(e))


async def test_sse_stream_parsing(client: httpx.AsyncClient, results: TestResults):
    """Test SSE stream parsing."""
    print("\n🔄 SSE Stream Parsing Tests")
    
    try:
        async with client.stream(
            "POST",
            "/api/fit-check/stream",
            json={"query": "Google", "include_thoughts": True},
            timeout=TIMEOUT
        ) as response:
            
            results.record(
                "Stream request returns 200",
                response.status_code == 200,
                f"Got status: {response.status_code}"
            )
            
            # Collect all stream data
            full_response = ""
            event_types_seen = set()
            
            async for chunk in response.aiter_text():
                full_response += chunk
                # Parse events as we go
                events = parse_sse_events(full_response)
                for event in events:
                    event_types_seen.add(event.event_type)
            
            # Parse all events
            events = parse_sse_events(full_response)
            
            results.record(
                "Stream contains events",
                len(events) > 0,
                f"Got {len(events)} events"
            )
            
            # Check for expected event types
            has_status = any(e.event_type == "status" for e in events)
            results.record(
                "Stream contains 'status' event",
                has_status
            )
            
            has_thought = any(e.event_type == "thought" for e in events)
            results.record(
                "Stream contains 'thought' events",
                has_thought
            )
            
            has_response = any(e.event_type == "response" for e in events)
            results.record(
                "Stream contains 'response' events",
                has_response
            )
            
            has_complete = any(e.event_type == "complete" for e in events)
            results.record(
                "Stream contains 'complete' event",
                has_complete
            )
            
            # Check complete event has duration
            complete_events = [e for e in events if e.event_type == "complete"]
            if complete_events:
                has_duration = "duration_ms" in complete_events[0].data
                results.record(
                    "Complete event has duration_ms",
                    has_duration
                )
            
            # Print event summary
            print(f"\n  📊 Event Summary:")
            print(f"     Total events: {len(events)}")
            for event_type in sorted(event_types_seen):
                count = sum(1 for e in events if e.event_type == event_type)
                print(f"     - {event_type}: {count}")
                
    except httpx.TimeoutException:
        results.record("SSE stream parsing", False, "Timeout waiting for response")
    except Exception as e:
        results.record("SSE stream parsing", False, str(e))


async def test_full_flow(client: httpx.AsyncClient, results: TestResults):
    """Test full end-to-end flow with detailed output."""
    print("\n🚀 Full End-to-End Flow Test")
    
    test_queries = [
        "PayPal",
        "I'm looking for a software engineer with Python and AI experience",
    ]
    
    for query in test_queries:
        print(f"\n  Testing query: '{query[:40]}...'")
        
        try:
            start_time = time.time()
            
            async with client.stream(
                "POST",
                "/api/fit-check/stream",
                json={"query": query, "include_thoughts": True},
                timeout=TIMEOUT
            ) as response:
                
                if response.status_code != 200:
                    results.record(
                        f"Flow for '{query[:20]}...'",
                        False,
                        f"Status code: {response.status_code}"
                    )
                    continue
                
                full_response = ""
                status_messages = []
                thought_steps = []
                response_chunks = []
                complete_data = None
                error_data = None
                
                async for chunk in response.aiter_text():
                    full_response += chunk
                
                # Parse all events
                events = parse_sse_events(full_response)
                
                for event in events:
                    if event.event_type == "status":
                        status_messages.append(event.data.get("message", ""))
                    elif event.event_type == "thought":
                        thought_steps.append(event.data)
                    elif event.event_type == "response":
                        chunk = event.data.get("chunk", "")
                        # Handle case where chunk might be a list
                        if isinstance(chunk, list):
                            chunk = "".join(str(c) for c in chunk)
                        response_chunks.append(str(chunk))
                    elif event.event_type == "complete":
                        complete_data = event.data
                    elif event.event_type == "error":
                        error_data = event.data
                
                elapsed = time.time() - start_time
                
                # Check for errors
                if error_data:
                    results.record(
                        f"Flow for '{query[:20]}...'",
                        False,
                        f"Error: {error_data.get('code')} - {error_data.get('message')}"
                    )
                    continue
                
                # Validate response
                final_response = "".join(response_chunks)
                
                results.record(
                    f"Flow for '{query[:20]}...' completes",
                    complete_data is not None,
                    f"Completed in {elapsed:.1f}s" if complete_data else "No complete event"
                )
                
                results.record(
                    f"Flow for '{query[:20]}...' has response",
                    len(final_response) > 0,
                    f"Response length: {len(final_response)} chars"
                )
                
                # Print details
                print(f"     Status updates: {len(status_messages)}")
                print(f"     Thought steps: {len(thought_steps)}")
                print(f"     Response length: {len(final_response)} chars")
                if complete_data:
                    print(f"     Duration: {complete_data.get('duration_ms', 'N/A')}ms")
                
                # Show thought steps
                if thought_steps:
                    print(f"     Thoughts:")
                    for thought in thought_steps[:5]:  # Show first 5
                        thought_type = thought.get("type", "unknown")
                        if thought_type == "tool_call":
                            tool = thought.get("tool", "unknown")
                            print(f"       - [{thought_type}] {tool}")
                        else:
                            content = thought.get("content", "")[:60]
                            print(f"       - [{thought_type}] {content}...")
                    if len(thought_steps) > 5:
                        print(f"       ... and {len(thought_steps) - 5} more")
                
        except httpx.TimeoutException:
            results.record(
                f"Flow for '{query[:20]}...'",
                False,
                f"Timeout after {TIMEOUT}s"
            )
        except Exception as e:
            results.record(
                f"Flow for '{query[:20]}...'",
                False,
                str(e)
            )


async def test_include_thoughts_flag(client: httpx.AsyncClient, results: TestResults):
    """Test include_thoughts flag."""
    print("\n🧠 Include Thoughts Flag Test")
    
    # Test with include_thoughts=False
    try:
        async with client.stream(
            "POST",
            "/api/fit-check/stream",
            json={"query": "Test Company", "include_thoughts": False},
            timeout=TIMEOUT
        ) as response:
            
            full_response = ""
            async for chunk in response.aiter_text():
                full_response += chunk
            
            events = parse_sse_events(full_response)
            thought_events = [e for e in events if e.event_type == "thought"]
            
            results.record(
                "include_thoughts=False suppresses thought events",
                len(thought_events) == 0,
                f"Got {len(thought_events)} thought events"
            )
            
    except Exception as e:
        results.record("include_thoughts flag test", False, str(e))


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Run all diagnostic tests."""
    print("=" * 60)
    print("🔬 DIAGNOSTIC TEST SUITE - Frontend User Flow Simulation")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Timeout: {TIMEOUT}s")
    
    results = TestResults()
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Check if server is reachable
        try:
            r = await client.get("/health", timeout=5.0)
            if r.status_code != 200:
                print(f"\n❌ Server not healthy: {r.status_code}")
                return False
        except Exception as e:
            print(f"\n❌ Cannot connect to server at {BASE_URL}: {e}")
            print("\nMake sure the server is running:")
            print("  cd res_web_backend")
            print("  uvicorn server:app --host 0.0.0.0 --port 8000 --reload")
            return False
        
        print("\n✅ Server is reachable and healthy")
        
        # Run test suites
        await test_health_checks(client, results)
        await test_request_validation(client, results)
        await test_sse_headers(client, results)
        await test_sse_stream_parsing(client, results)
        await test_full_flow(client, results)
        await test_include_thoughts_flag(client, results)
    
    return results.summary()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
