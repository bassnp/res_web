import asyncio
import pytest
import httpx
import json
import time
from typing import List

@pytest.mark.asyncio
async def test_concurrent_sessions_isolation():
    """
    Verify that multiple concurrent sessions are isolated and don't interfere.
    """
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60.0) as client:
        # Start two concurrent requests with different queries
        async def run_session(query: str) -> List[str]:
            events = []
            try:
                async with client.stream(
                    "POST", "/api/fit-check/stream",
                    json={"query": query, "include_thoughts": True}
                ) as response:
                    assert response.status_code == 200
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            data = json.loads(line[5:])
                            events.append(data)
            except Exception as e:
                print(f"Session error for {query}: {e}")
            return events

        # Run sessions concurrently
        results = await asyncio.gather(
            run_session("Google"),
            run_session("Microsoft")
        )

        google_events = results[0]
        microsoft_events = results[1]

        assert len(google_events) > 0
        assert len(microsoft_events) > 0

        # Verify that Google events don't contain Microsoft data and vice versa
        # We check the 'status' and 'thought' events
        for event in google_events:
            if event.get("event") == "status":
                # Status messages are generic, but let's check if any mention the other company
                assert "Microsoft" not in str(event)
            if event.get("event") == "thought":
                assert "Microsoft" not in str(event.get("data", {}).get("content", ""))

        for event in microsoft_events:
            if event.get("event") == "status":
                assert "Google" not in str(event)
            if event.get("event") == "thought":
                assert "Google" not in str(event.get("data", {}).get("content", ""))

@pytest.mark.asyncio
async def test_circuit_breaker_open():
    """
    Verify that the circuit breaker opens after failures.
    """
    from services.utils.circuit_breaker import AsyncCircuitBreaker, CircuitOpenError
    
    breaker = AsyncCircuitBreaker(max_failures=2, reset_timeout=1.0, name="test-breaker")
    
    async def failing_call():
        raise ValueError("Test failure")
    
    protected_call = breaker.protect(failing_call)
    
    # First failure
    with pytest.raises(ValueError):
        await protected_call()
    assert breaker.state.value == "closed"
    
    # Second failure -> should open
    with pytest.raises(ValueError):
        await protected_call()
    assert breaker.state.value == "open"
    
    # Third call -> should raise CircuitOpenError
    with pytest.raises(CircuitOpenError):
        await protected_call()

@pytest.mark.asyncio
async def test_llm_throttling():
    """
    Verify that LLM throttling limits concurrent calls.
    """
    from config.llm import with_llm_throttle, get_llm_semaphore
    import time
    
    # Set a small limit for testing
    semaphore = get_llm_semaphore()
    original_value = semaphore._value
    semaphore._value = 2
    
    start_time = time.time()
    
    async def slow_call():
        await asyncio.sleep(0.5)
        return True
    
    # Run 4 concurrent calls with limit 2
    # Should take at least 1.0 second total
    await asyncio.gather(
        with_llm_throttle(slow_call()),
        with_llm_throttle(slow_call()),
        with_llm_throttle(slow_call()),
        with_llm_throttle(slow_call())
    )
    
    duration = time.time() - start_time
    assert duration >= 1.0
    
    # Restore original value
    semaphore._value = original_value
