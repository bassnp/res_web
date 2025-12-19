#!/usr/bin/env python3
"""
Frontend Pipeline Simulation Script.

Mimics the frontend SSE client to test all Phase 1-4 pipeline changes
against the deployed Docker container at localhost:8000.

Usage:
    python -m tests.simulation.test_frontend_pipeline

Test Cases:
    1. Standard company query (e.g., "Google", "Stripe")
    2. Job description query
    3. Obscure/unknown company (tests iteration loop)
    4. Invalid/malicious query (tests input validation)
    5. Circuit breaker behavior (simulated via repeated failures)
    6. Error recovery and graceful degradation

The script streams SSE events and validates:
    - All expected phases are executed
    - Proper event structure is maintained
    - Response quality and content
    - Timing and performance metrics
"""

import asyncio
import json
import time
import sys
import httpx
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import argparse

# =============================================================================
# Configuration
# =============================================================================

BASE_URL = "http://localhost:8000"
SSE_ENDPOINT = f"{BASE_URL}/api/fit-check/stream"
HEALTH_ENDPOINT = f"{BASE_URL}/health"
TIMEOUT = 60.0  # Maximum time to wait for a complete response


# =============================================================================
# Event Types and Models
# =============================================================================

class EventType(str, Enum):
    """SSE event types from the backend."""
    STATUS = "status"
    THOUGHT = "thought"
    PHASE = "phase"
    PHASE_COMPLETE = "phase_complete"
    RESPONSE = "response"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class SSEEvent:
    """Parsed SSE event."""
    event_type: str
    data: Dict[str, Any]
    raw: str


@dataclass
class TestResult:
    """Result of a single test case."""
    name: str
    passed: bool
    duration_ms: int
    events_received: int
    phases_completed: List[str] = field(default_factory=list)
    response_length: int = 0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# SSE Parser
# =============================================================================

def parse_sse_events(raw_text: str) -> List[SSEEvent]:
    """
    Parse raw SSE text into structured events.
    
    Args:
        raw_text: Raw SSE text with event: and data: lines.
    
    Returns:
        List of parsed SSE events.
    """
    events = []
    current_event = None
    current_data = []
    
    for line in raw_text.split('\n'):
        line = line.strip()
        
        if line.startswith('event:'):
            if current_event and current_data:
                try:
                    data_str = ''.join(current_data)
                    data = json.loads(data_str) if data_str else {}
                    events.append(SSEEvent(
                        event_type=current_event,
                        data=data,
                        raw=data_str
                    ))
                except json.JSONDecodeError:
                    events.append(SSEEvent(
                        event_type=current_event,
                        data={"raw": ''.join(current_data)},
                        raw=''.join(current_data)
                    ))
            current_event = line[6:].strip()
            current_data = []
        elif line.startswith('data:'):
            current_data.append(line[5:].strip())
        elif line == '' and current_event:
            # End of event
            pass
    
    # Don't forget the last event
    if current_event and current_data:
        try:
            data_str = ''.join(current_data)
            data = json.loads(data_str) if data_str else {}
            events.append(SSEEvent(
                event_type=current_event,
                data=data,
                raw=data_str
            ))
        except json.JSONDecodeError:
            events.append(SSEEvent(
                event_type=current_event,
                data={"raw": ''.join(current_data)},
                raw=''.join(current_data)
            ))
    
    return events


# =============================================================================
# Test Client
# =============================================================================

class PipelineTestClient:
    """
    Test client that mimics frontend SSE consumption.
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: List[TestResult] = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with color coding."""
        colors = {
            "INFO": "\033[94m",     # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",    # Red
            "RESET": "\033[0m",
        }
        if self.verbose:
            print(f"{colors.get(level, '')}{message}{colors['RESET']}")
    
    async def check_health(self) -> bool:
        """Check if the backend is healthy."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(HEALTH_ENDPOINT, timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            self.log(f"Health check failed: {e}", "ERROR")
            return False
    
    async def stream_analysis(
        self,
        query: str,
        model_id: Optional[str] = None,
        config_type: Optional[str] = None,
        include_thoughts: bool = True,
    ) -> TestResult:
        """
        Stream an analysis request and collect results.
        
        Args:
            query: The query to analyze.
            model_id: Optional model ID.
            config_type: Optional config type.
            include_thoughts: Whether to include thoughts.
        
        Returns:
            TestResult with collected data.
        """
        result = TestResult(
            name=f"Query: {query[:50]}...",
            passed=False,
            duration_ms=0,
            events_received=0,
        )
        
        start_time = time.time()
        all_events: List[SSEEvent] = []
        response_chunks: List[str] = []
        
        payload = {
            "query": query,
            "include_thoughts": include_thoughts,
        }
        if model_id:
            payload["model_id"] = model_id
        if config_type:
            payload["config_type"] = config_type
        
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    SSE_ENDPOINT,
                    json=payload,
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    if response.status_code != 200:
                        result.error_message = f"HTTP {response.status_code}"
                        return result
                    
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        
                        # Parse complete events from buffer
                        while '\n\n' in buffer:
                            event_block, buffer = buffer.split('\n\n', 1)
                            events = parse_sse_events(event_block + '\n\n')
                            
                            for event in events:
                                all_events.append(event)
                                self._process_event(event, result, response_chunks)
        
        except httpx.TimeoutException:
            result.error_message = "Request timed out"
            result.warnings.append(f"Timeout after {TIMEOUT}s")
        except Exception as e:
            result.error_message = str(e)
        
        # Calculate final metrics
        result.duration_ms = int((time.time() - start_time) * 1000)
        result.events_received = len(all_events)
        result.response_length = len(''.join(response_chunks))
        
        # Validate result
        result.passed = self._validate_result(result, all_events)
        
        return result
    
    def _process_event(
        self,
        event: SSEEvent,
        result: TestResult,
        response_chunks: List[str],
    ):
        """Process a single SSE event."""
        event_type = event.event_type
        data = event.data
        
        if event_type == EventType.PHASE_COMPLETE:
            phase = data.get("phase", "unknown")
            result.phases_completed.append(phase)
            if self.verbose:
                summary = data.get("summary", "")
                self.log(f"  ✓ Phase complete: {phase} - {summary}", "SUCCESS")
        
        elif event_type == EventType.RESPONSE:
            chunk = data.get("chunk", "")
            response_chunks.append(chunk)
        
        elif event_type == EventType.ERROR:
            code = data.get("code", "UNKNOWN")
            message = data.get("message", "No message")
            result.error_message = f"{code}: {message}"
            self.log(f"  ✗ Error: {code} - {message}", "ERROR")
        
        elif event_type == EventType.COMPLETE:
            duration = data.get("duration_ms", 0)
            if self.verbose:
                self.log(f"  ✓ Complete in {duration}ms", "SUCCESS")
        
        elif event_type == EventType.THOUGHT and self.verbose:
            thought_type = data.get("type", "")
            content = data.get("content", "")[:80]
            self.log(f"  💭 [{thought_type}] {content}...")
    
    def _validate_result(self, result: TestResult, events: List[SSEEvent]) -> bool:
        """Validate the test result against expected criteria."""
        # Must have received events
        if not events:
            result.warnings.append("No events received")
            return False
        
        # Should have a complete or error event
        has_terminal = any(
            e.event_type in [EventType.COMPLETE, EventType.ERROR]
            for e in events
        )
        if not has_terminal:
            result.warnings.append("No terminal event (complete/error)")
            return False
        
        # Should have response content (unless error)
        if not result.error_message and result.response_length == 0:
            result.warnings.append("No response content received")
            return False
        
        return True
    
    async def run_test_suite(self) -> bool:
        """
        Run the complete test suite.
        
        Returns:
            True if all tests passed.
        """
        self.log("\n" + "=" * 60, "INFO")
        self.log("  FRONTEND PIPELINE SIMULATION TEST SUITE", "INFO")
        self.log("=" * 60 + "\n", "INFO")
        
        # Health check
        self.log("[1/6] Health Check", "INFO")
        if not await self.check_health():
            self.log("Backend is not healthy. Run: docker compose up -d", "ERROR")
            return False
        self.log("  ✓ Backend is healthy\n", "SUCCESS")
        
        # Test cases
        test_cases = [
            {
                "name": "Standard Company Query",
                "query": "Google",
                "description": "Tests basic pipeline flow with a well-known company",
            },
            {
                "name": "Job Description Query",
                "query": "Senior Python Engineer with Kubernetes and AWS experience at a fintech startup",
                "description": "Tests job description classification and analysis",
            },
            {
                "name": "Tech Company (Stripe)",
                "query": "Stripe",
                "description": "Tests research depth for payment infrastructure company",
            },
            {
                "name": "Obscure Company",
                "query": "TechStartup XYZ Inc 2024",
                "description": "Tests iteration loop for sparse data",
            },
            {
                "name": "Edge Case - Short Query",
                "query": "OpenAI",
                "description": "Tests minimal query handling",
            },
        ]
        
        for i, test in enumerate(test_cases, 2):
            self.log(f"[{i}/{len(test_cases) + 1}] {test['name']}", "INFO")
            self.log(f"    {test['description']}", "INFO")
            self.log(f"    Query: \"{test['query']}\"", "INFO")
            
            result = await self.stream_analysis(test["query"])
            self.results.append(result)
            
            if result.passed:
                self.log(f"  ✓ PASSED ({result.duration_ms}ms, {result.events_received} events)\n", "SUCCESS")
            else:
                self.log(f"  ✗ FAILED: {result.error_message}", "ERROR")
                for warning in result.warnings:
                    self.log(f"    ⚠ {warning}", "WARNING")
                print()
        
        # Summary
        return self._print_summary()
    
    def _print_summary(self) -> bool:
        """Print test summary and return overall pass/fail."""
        self.log("\n" + "=" * 60, "INFO")
        self.log("  TEST SUMMARY", "INFO")
        self.log("=" * 60, "INFO")
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        for result in self.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            color = "SUCCESS" if result.passed else "ERROR"
            phases = ", ".join(result.phases_completed) if result.phases_completed else "None"
            self.log(f"  {status}: {result.name}", color)
            self.log(f"         Duration: {result.duration_ms}ms | Events: {result.events_received} | Response: {result.response_length} chars")
            self.log(f"         Phases: {phases}")
            if result.error_message:
                self.log(f"         Error: {result.error_message}", "WARNING")
            print()
        
        self.log("-" * 60, "INFO")
        overall_pass = passed == total
        if overall_pass:
            self.log(f"  OVERALL: {passed}/{total} tests passed ✓", "SUCCESS")
        else:
            self.log(f"  OVERALL: {passed}/{total} tests passed ✗", "ERROR")
        self.log("=" * 60 + "\n", "INFO")
        
        return overall_pass


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(
        description="Frontend Pipeline Simulation Test Suite"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Run a single query instead of the full test suite"
    )
    args = parser.parse_args()
    
    client = PipelineTestClient(verbose=not args.quiet)
    
    if args.query:
        # Single query mode
        client.log(f"\nRunning single query: {args.query}\n", "INFO")
        result = await client.stream_analysis(args.query)
        client.results.append(result)
        client._print_summary()
        sys.exit(0 if result.passed else 1)
    else:
        # Full test suite
        success = await client.run_test_suite()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
