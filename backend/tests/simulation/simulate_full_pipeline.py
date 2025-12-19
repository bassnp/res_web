#!/usr/bin/env python3
"""
Full Pipeline SSE Simulation

This script simulates frontend SSE consumption, capturing all events
and validating the complete pipeline flow end-to-end.

Usage:
    python simulate_full_pipeline.py --query "Google" --verbose
    python simulate_full_pipeline.py --query "Senior Python Developer" --save-output
    
Features:
    - Real SSE stream consumption (like frontend would)
    - Event sequence validation
    - Phase transition tracking
    - Output quality analysis
    - Performance timing metrics
"""

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum

import httpx


# =============================================================================
# Configuration
# =============================================================================

API_URL = os.environ.get("API_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 60.0  # seconds


class PhaseStatus(Enum):
    """Phase execution status."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETE = "complete"
    ERROR = "error"


PHASE_ORDER = [
    "connecting",
    "deep_research",
    "research_reranker",  # Phase 2B - Research Quality Validation
    "content_enrich",     # Phase 2C - Content Enrichment
    "skeptical_comparison",
    "skills_matching",
    "confidence_reranker",
    "generate_results",
]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SSEEvent:
    """Represents a single SSE event."""
    type: str
    data: Dict[str, Any]
    timestamp: float
    raw: str = ""


@dataclass
class PhaseRecord:
    """Records phase execution details."""
    phase: str
    status: PhaseStatus = PhaseStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    message: str = ""
    summary: str = ""
    thoughts: List[Dict] = field(default_factory=list)
    
    @property
    def duration_ms(self) -> Optional[int]:
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return None


@dataclass
class SimulationResult:
    """Complete simulation result."""
    query: str
    success: bool
    total_duration_ms: int
    events: List[SSEEvent]
    phases: Dict[str, PhaseRecord]
    final_response: str
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "success": self.success,
            "total_duration_ms": self.total_duration_ms,
            "event_count": len(self.events),
            "events": [
                {"type": e.type, "data": e.data, "timestamp": e.timestamp}
                for e in self.events
            ],
            "phases": {
                name: {
                    "status": p.status.value,
                    "duration_ms": p.duration_ms,
                    "message": p.message,
                    "summary": p.summary,
                    "thought_count": len(p.thoughts),
                }
                for name, p in self.phases.items()
            },
            "final_response": self.final_response,
            "response_word_count": len(self.final_response.split()),
            "errors": self.errors,
            "warnings": self.warnings,
        }


# =============================================================================
# SSE Parser
# =============================================================================

class SSEParser:
    """Parses Server-Sent Events from a stream."""
    
    def __init__(self):
        self.buffer = ""
    
    def feed(self, chunk: str) -> List[SSEEvent]:
        """
        Feed raw SSE data and return parsed events.
        
        Args:
            chunk: Raw SSE string data.
            
        Returns:
            List of complete SSEEvent objects.
        """
        self.buffer += chunk
        events = []
        
        while "\n\n" in self.buffer:
            event_text, self.buffer = self.buffer.split("\n\n", 1)
            event = self._parse_event(event_text)
            if event:
                events.append(event)
        
        return events
    
    def _parse_event(self, text: str) -> Optional[SSEEvent]:
        """Parse a single event block."""
        event_type = None
        event_data = None
        
        for line in text.strip().split("\n"):
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                event_data = line[5:].strip()
        
        if event_type and event_data:
            try:
                data = json.loads(event_data)
                return SSEEvent(
                    type=event_type,
                    data=data,
                    timestamp=time.time(),
                    raw=text,
                )
            except json.JSONDecodeError:
                return SSEEvent(
                    type=event_type,
                    data={"raw": event_data},
                    timestamp=time.time(),
                    raw=text,
                )
        
        return None


# =============================================================================
# Event Processor (Simulates Frontend State Machine)
# =============================================================================

class FrontendSimulator:
    """
    Simulates frontend state management.
    
    This class mimics how the React frontend would process SSE events
    and update its state, allowing us to validate the full flow.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.events: List[SSEEvent] = []
        self.phases: Dict[str, PhaseRecord] = {
            name: PhaseRecord(phase=name)
            for name in PHASE_ORDER
        }
        self.current_phase: Optional[str] = None
        self.final_response = ""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def process_event(self, event: SSEEvent) -> None:
        """
        Process a single SSE event.
        
        Args:
            event: The SSE event to process.
        """
        self.events.append(event)
        
        if self.verbose:
            self._log_event(event)
        
        handler = getattr(self, f"_handle_{event.type}", None)
        if handler:
            handler(event)
        else:
            self.warnings.append(f"Unknown event type: {event.type}")
    
    def _handle_phase(self, event: SSEEvent) -> None:
        """Handle phase transition event."""
        phase_name = event.data.get("phase")
        message = event.data.get("message", "")
        
        if phase_name not in self.phases:
            self.errors.append(f"Unknown phase: {phase_name}")
            return
        
        # Validate phase order
        if self.current_phase:
            current_idx = PHASE_ORDER.index(self.current_phase)
            new_idx = PHASE_ORDER.index(phase_name)
            if new_idx != current_idx + 1:
                self.warnings.append(
                    f"Phase order violation: {self.current_phase} -> {phase_name}"
                )
        
        # Update phase record
        self.current_phase = phase_name
        self.phases[phase_name].status = PhaseStatus.ACTIVE
        self.phases[phase_name].start_time = event.timestamp
        self.phases[phase_name].message = message
    
    def _handle_phase_complete(self, event: SSEEvent) -> None:
        """Handle phase completion event."""
        phase_name = event.data.get("phase")
        summary = event.data.get("summary", "")
        
        if phase_name not in self.phases:
            self.errors.append(f"Unknown phase complete: {phase_name}")
            return
        
        self.phases[phase_name].status = PhaseStatus.COMPLETE
        self.phases[phase_name].end_time = event.timestamp
        self.phases[phase_name].summary = summary
    
    def _handle_status(self, event: SSEEvent) -> None:
        """Handle status event (legacy compatibility)."""
        pass  # Status events are informational
    
    def _handle_thought(self, event: SSEEvent) -> None:
        """Handle thought event."""
        phase = event.data.get("phase") or self.current_phase
        
        if phase and phase in self.phases:
            self.phases[phase].thoughts.append(event.data)
    
    def _handle_response(self, event: SSEEvent) -> None:
        """Handle response chunk event."""
        chunk = event.data.get("chunk", "")
        self.final_response += chunk
    
    def _handle_complete(self, event: SSEEvent) -> None:
        """Handle completion event."""
        self.end_time = event.timestamp
    
    def _handle_error(self, event: SSEEvent) -> None:
        """Handle error event."""
        code = event.data.get("code", "UNKNOWN")
        message = event.data.get("message", "Unknown error")
        self.errors.append(f"[{code}] {message}")
        
        if self.current_phase:
            self.phases[self.current_phase].status = PhaseStatus.ERROR
    
    def _log_event(self, event: SSEEvent) -> None:
        """Log event to console."""
        color = {
            "phase": "\033[94m",       # Blue
            "phase_complete": "\033[92m",  # Green
            "thought": "\033[93m",     # Yellow
            "response": "\033[96m",    # Cyan
            "complete": "\033[95m",    # Magenta
            "error": "\033[91m",       # Red
        }.get(event.type, "\033[0m")
        
        reset = "\033[0m"
        
        if event.type == "response":
            # Truncate response chunks for readability
            chunk = event.data.get("chunk", "")[:50]
            print(f"{color}[{event.type}]{reset} {chunk}...")
        else:
            print(f"{color}[{event.type}]{reset} {json.dumps(event.data, indent=2)}")
    
    def get_result(self, query: str) -> SimulationResult:
        """
        Generate simulation result.
        
        Args:
            query: The original query.
            
        Returns:
            SimulationResult with all collected data.
        """
        duration = 0
        if self.start_time and self.end_time:
            duration = int((self.end_time - self.start_time) * 1000)
        
        success = (
            len(self.errors) == 0
            and all(p.status == PhaseStatus.COMPLETE for p in self.phases.values())
            and len(self.final_response) > 0
        )
        
        return SimulationResult(
            query=query,
            success=success,
            total_duration_ms=duration,
            events=self.events,
            phases=self.phases,
            final_response=self.final_response,
            errors=self.errors,
            warnings=self.warnings,
        )


# =============================================================================
# Validation Functions
# =============================================================================

def validate_phase_sequence(result: SimulationResult) -> List[str]:
    """
    Validate that phases executed in correct order.
    
    Args:
        result: Simulation result to validate.
        
    Returns:
        List of validation error messages.
    """
    errors = []
    
    # Check all phases completed
    for name in PHASE_ORDER:
        phase = result.phases.get(name)
        if not phase:
            errors.append(f"Missing phase: {name}")
        elif phase.status != PhaseStatus.COMPLETE:
            errors.append(f"Phase not complete: {name} (status: {phase.status.value})")
    
    # Check phase timing sequence
    prev_end = None
    for name in PHASE_ORDER:
        phase = result.phases.get(name)
        if phase and phase.start_time:
            if prev_end and phase.start_time < prev_end:
                errors.append(f"Phase {name} started before previous phase ended")
            if phase.end_time:
                prev_end = phase.end_time
    
    return errors


def validate_skeptical_output(result: SimulationResult) -> List[str]:
    """
    Validate Phase 3 (Skeptical Comparison) output quality.
    
    This is CRITICAL - the anti-sycophancy check.
    
    Args:
        result: Simulation result to validate.
        
    Returns:
        List of validation error messages.
    """
    errors = []
    
    phase3 = result.phases.get("skeptical_comparison")
    if not phase3:
        errors.append("Missing skeptical_comparison phase")
        return errors
    
    # Check summary mentions gaps
    if phase3.summary and "gap" not in phase3.summary.lower():
        errors.append("Phase 3 summary should mention identified gaps")
    
    # Sycophantic phrase detection
    SYCOPHANTIC_PHRASES = [
        "perfect fit", "ideal candidate", "excellent match",
        "amazing", "outstanding", "exceptional", "flawless",
    ]
    
    summary_lower = phase3.summary.lower()
    for phrase in SYCOPHANTIC_PHRASES:
        if phrase in summary_lower:
            errors.append(f"Sycophantic phrase detected in Phase 3: '{phrase}'")
    
    return errors


def validate_final_response(result: SimulationResult) -> List[str]:
    """
    Validate Phase 5 (Generate Results) output quality.
    
    Args:
        result: Simulation result to validate.
        
    Returns:
        List of validation error messages.
    """
    errors = []
    response = result.final_response
    
    if not response:
        errors.append("Empty final response")
        return errors
    
    # Word count check
    word_count = len(response.split())
    if word_count > 450:  # Allow some buffer
        errors.append(f"Response exceeds 400 words: {word_count} words")
    
    # Required section headers (with accepted variations)
    required_sections = {
        "Key Alignments": ["key alignments", "where i align", "alignments:"],
        "What I Bring": ["what i bring", "what i offer"],
        "Growth Areas": ["growth areas", "the learning curve", "areas for growth"],
        "Let's Connect": ["let's connect", "lets connect", "connect with me"],
    }
    
    response_lower = response.lower()
    for section, variations in required_sections.items():
        if not any(v in response_lower for v in variations):
            errors.append(f"Missing required section: {section}")
    
    # Sycophantic phrase detection in final response
    SYCOPHANTIC_PHRASES = [
        "perfect fit", "ideal candidate", "couldn't be better",
    ]
    
    for phrase in SYCOPHANTIC_PHRASES:
        if phrase in response_lower:
            errors.append(f"Sycophantic phrase in response: '{phrase}'")
    
    return errors


# =============================================================================
# Main Simulation
# =============================================================================

async def run_simulation(
    query: str,
    verbose: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    api_url: str = API_URL,
) -> SimulationResult:
    """
    Run the full pipeline simulation.
    
    Args:
        query: Query to send to the API.
        verbose: Whether to log events in real-time.
        timeout: Request timeout in seconds.
        api_url: API base URL.
        
    Returns:
        SimulationResult with all collected data.
    """
    simulator = FrontendSimulator(verbose=verbose)
    parser = SSEParser()
    
    print(f"\n{'='*60}")
    print(f"SIMULATION START: {datetime.now().isoformat()}")
    print(f"Query: {query}")
    print(f"API URL: {api_url}")
    print(f"{'='*60}\n")
    
    simulator.start_time = time.time()
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream(
                "POST",
                f"{api_url}/api/fit-check/stream",
                json={"query": query, "include_thoughts": True},
                headers={"Accept": "text/event-stream"},
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    simulator.errors.append(
                        f"HTTP {response.status_code}: {error_text.decode()}"
                    )
                    return simulator.get_result(query)
                
                async for chunk in response.aiter_text():
                    events = parser.feed(chunk)
                    for event in events:
                        simulator.process_event(event)
        
        except httpx.TimeoutException:
            simulator.errors.append(f"Request timeout after {timeout}s")
        except httpx.ConnectError as e:
            simulator.errors.append(f"Connection error: {e}")
        except Exception as e:
            simulator.errors.append(f"Unexpected error: {e}")
    
    if not simulator.end_time:
        simulator.end_time = time.time()
    
    return simulator.get_result(query)


def print_results(result: SimulationResult) -> None:
    """Print formatted simulation results."""
    print(f"\n{'='*60}")
    print("SIMULATION RESULTS")
    print(f"{'='*60}\n")
    
    # Overall status
    status_color = "\033[92m" if result.success else "\033[91m"
    reset = "\033[0m"
    print(f"Status: {status_color}{'SUCCESS' if result.success else 'FAILED'}{reset}")
    print(f"Duration: {result.total_duration_ms}ms")
    print(f"Events: {len(result.events)}")
    print(f"Response Words: {len(result.final_response.split())}")
    
    # Phase summary
    print(f"\n{'-'*40}")
    print("PHASE SUMMARY")
    print(f"{'-'*40}")
    for name in PHASE_ORDER:
        phase = result.phases.get(name)
        if phase:
            status_sym = "✓" if phase.status == PhaseStatus.COMPLETE else "✗"
            duration = f"{phase.duration_ms}ms" if phase.duration_ms else "N/A"
            print(f"  [{status_sym}] {name}: {duration} - {phase.summary[:50] if phase.summary else 'No summary'}...")
    
    # Validation
    print(f"\n{'-'*40}")
    print("VALIDATION")
    print(f"{'-'*40}")
    
    phase_errors = validate_phase_sequence(result)
    skeptical_errors = validate_skeptical_output(result)
    response_errors = validate_final_response(result)
    
    all_errors = phase_errors + skeptical_errors + response_errors + result.errors
    
    if all_errors:
        print("\033[91mErrors:\033[0m")
        for error in all_errors:
            print(f"  ✗ {error}")
    else:
        print("\033[92mAll validations passed!\033[0m")
    
    if result.warnings:
        print("\n\033[93mWarnings:\033[0m")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")
    
    # Response preview
    print(f"\n{'-'*40}")
    print("RESPONSE PREVIEW (first 500 chars)")
    print(f"{'-'*40}")
    print(result.final_response[:500] + "..." if len(result.final_response) > 500 else result.final_response)


def save_output(result: SimulationResult, filename: str) -> None:
    """Save simulation output to JSON file."""
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)
    
    print(f"\nOutput saved to: {filepath}")


# =============================================================================
# Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Simulate frontend SSE consumption for Fit Check pipeline"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Google",
        help="Query to send (company name or job description)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print events in real-time",
    )
    parser.add_argument(
        "--save-output",
        "-s",
        action="store_true",
        help="Save output to JSON file",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help=f"API URL (default: {API_URL})",
    )
    
    args = parser.parse_args()
    
    # Determine API URL to use
    api_url = args.api_url if args.api_url else API_URL
    
    # Run simulation
    result = asyncio.run(run_simulation(
        query=args.query,
        verbose=args.verbose,
        timeout=args.timeout,
        api_url=api_url,
    ))
    
    # Print results
    print_results(result)
    
    # Save output if requested
    if args.save_output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simulation_{timestamp}.json"
        save_output(result, filename)
        
        # Also save as "last_run.json" for easy reference
        save_output(result, "last_run.json")
    
    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
