#!/usr/bin/env python3
"""
Accuracy Test Runner for Fit Check Pipeline.

This script executes all accuracy test cases against the running Docker container
and generates comprehensive validation reports.

Usage:
    # Run all test cases
    python -m tests.simulation.accuracy.run_accuracy_tests
    
    # Run specific category
    python -m tests.simulation.accuracy.run_accuracy_tests --category A
    
    # Run single test case
    python -m tests.simulation.accuracy.run_accuracy_tests --test-id A1
    
    # Save results to file
    python -m tests.simulation.accuracy.run_accuracy_tests --output results.json
    
    # Dry run (show test cases without executing)
    python -m tests.simulation.accuracy.run_accuracy_tests --dry-run

Test Execution Protocol:
    1. Health check backend container
    2. For each test case:
        a. Send query via SSE stream
        b. Collect pipeline response
        c. Parse score, tier, gaps, quality flags
        d. Validate against expected outcomes
        e. Record accuracy result
    3. Calculate aggregate metrics
    4. Generate failure analyses for failed tests
    5. Output comprehensive report
"""

import asyncio
import json
import time
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import httpx

from .test_definitions import (
    TestCase,
    TestCategory,
    ConfidenceTier,
    get_all_test_cases,
    get_test_cases_by_category,
    get_test_case_by_id,
    generate_test_summary,
)
from .accuracy_validator import (
    AccuracyResult,
    AccuracyMetrics,
    ValidationStatus,
    validate_test_result,
    calculate_aggregate_metrics,
    generate_accuracy_report,
)
from .failure_analyzer import (
    FailureAnalysis,
    analyze_failure,
    generate_failure_report,
    generate_individual_failure_template,
)


# =============================================================================
# Configuration
# =============================================================================

BASE_URL = "http://localhost:8000"
SSE_ENDPOINT = f"{BASE_URL}/api/fit-check/stream"
HEALTH_ENDPOINT = f"{BASE_URL}/health"
DEFAULT_TIMEOUT = 120.0  # Generous timeout for accuracy tests

# Output directory for results
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "accuracy"


# =============================================================================
# Response Parsing
# =============================================================================

class PipelineResponseParser:
    """
    Parser for extracting accuracy metrics from pipeline SSE responses.
    
    Extracts:
        - Match score (0-100)
        - Confidence tier
        - Identified gaps
        - Quality flags
        
    Response Format Examples:
        - "50% (MEDIUM) match based on..."
        - "68% (MEDIUM): The candidate demonstrates..."
        - "**At a Glance:** 75% overall match (HIGH confidence)"
        - "Calibrated confidence: 30% (LOW)"
    """
    
    # Combined pattern for "XX% (TIER)" format (most common)
    COMBINED_SCORE_TIER_PATTERN = r"(\d{1,3})%\s*\((\w+(?:[-_]\w+)?)\)"
    
    # Regex patterns for score extraction (priority order)
    SCORE_PATTERNS = [
        # "68% (MEDIUM):" or "50% (MEDIUM) match" - primary format
        r"(\d{1,3})%\s*\([^)]+\)",
        # "At a Glance:** 75% overall match"
        r"at a glance[:\s*]+(\d{1,3})%",
        # "Calibrated confidence: 30%"
        r"calibrated\s+(?:confidence|score)[:\s]+(\d{1,3})%?",
        # "overall match: 75%"
        r"(?:match|fit|overall|compatibility)[\s:]+(\d{1,3})%",
        # "75% match"
        r"(\d{1,3})%\s*(?:match|fit|overall|compatibility)",
        # "score: 75"
        r"score[:\s]+(\d{1,3})",
    ]
    
    # Regex patterns for tier extraction (priority order)
    TIER_PATTERNS = [
        # "68% (MEDIUM):" or "50% (MEDIUM) match" - extract tier from parentheses after percentage
        r"\d{1,3}%\s*\((\w+(?:[-_]\w+)?)\)",
        # "(HIGH confidence)"
        r"\((\w+(?:[-_]\w+)?)\s*confidence\)",
        # "confidence: HIGH"
        r"confidence[:\s]*(high|medium[-_]?high|medium|low[-_]?medium|low|insufficient(?:[-_]data)?)",
        # "tier: MEDIUM"
        r"tier[:\s]*(high|medium[-_]?high|medium|low[-_]?medium|low|insufficient(?:[-_]data)?)",
        # "HIGH fit" or "MEDIUM match"
        r"(high|medium[-_]?high|medium|low[-_]?medium|low|insufficient)\s*(?:confidence|tier|fit|match)",
    ]
    
    # Gap identification patterns
    GAP_PATTERNS = [
        r"\*\*\[([^\]]+)\]\*\*[:\s]*([^\n]+)",  # **[Gap Name]**: description
        r"(?:gap|missing|lack(?:ing)?|need)[:\s]*([^\n.]+)",
        r"(?:would need|should develop|requires)[:\s]*([^\n.]+)",
        r"areas?\s+to\s+address[:\s]*([^\n.]+)",
    ]
    
    @classmethod
    def parse_response(cls, response_text: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse pipeline response to extract accuracy metrics.
        
        Args:
            response_text: Full response text from pipeline.
            events: List of SSE events received.
            
        Returns:
            Dict with score, tier, gaps, and quality_flags.
        """
        result = {
            "score": None,
            "tier": None,
            "gaps": [],
            "quality_flags": [],
        }
        
        # Try to extract from events first (structured data)
        for event in events:
            event_type = event.get("event_type", "")
            data = event.get("data", {})
            
            # Look for phase_complete events with structured data
            if event_type == "phase_complete":
                phase = data.get("phase", "")
                summary = data.get("summary", "")
                
                if phase == "confidence_reranker":
                    # Try to extract score and tier from reranker output
                    result.update(cls._parse_reranker_output(data))
                
                elif phase == "skills_matching":
                    # Extract gaps from skills matching
                    result["gaps"].extend(cls._extract_gaps_from_data(data))
                
                elif phase == "generate_results":
                    # Extract quality flags
                    if "quality_flags" in data:
                        result["quality_flags"] = data["quality_flags"]
            
            # Check for quality flags in any event
            if "quality_flags" in data:
                result["quality_flags"].extend(data["quality_flags"])
            if "data_quality_tier" in data:
                quality_tier = data["data_quality_tier"]
                if quality_tier in ["SPARSE", "GARBAGE", "UNRELIABLE"]:
                    result["quality_flags"].append(quality_tier)
        
        # Fall back to text extraction if structured data not found
        if result["score"] is None:
            result["score"] = cls._extract_score_from_text(response_text)
        
        if result["tier"] is None:
            result["tier"] = cls._extract_tier_from_text(response_text)
        
        if not result["gaps"]:
            result["gaps"] = cls._extract_gaps_from_text(response_text)
        
        # Deduplicate
        result["quality_flags"] = list(set(result["quality_flags"]))
        result["gaps"] = list(set(result["gaps"]))
        
        return result
    
    @classmethod
    def _parse_reranker_output(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract score and tier from confidence reranker output."""
        result = {"score": None, "tier": None}
        
        # Direct fields
        if "final_score" in data:
            result["score"] = data["final_score"]
        elif "match_score" in data:
            result["score"] = data["match_score"]
        elif "score" in data:
            result["score"] = data["score"]
        
        if "confidence_tier" in data:
            result["tier"] = data["confidence_tier"]
        elif "tier" in data:
            result["tier"] = data["tier"]
        
        # Parse from summary text
        summary = data.get("summary", "")
        if result["score"] is None:
            result["score"] = cls._extract_score_from_text(summary)
        if result["tier"] is None:
            result["tier"] = cls._extract_tier_from_text(summary)
        
        return result
    
    @classmethod
    def _extract_gaps_from_data(cls, data: Dict[str, Any]) -> List[str]:
        """Extract gaps from structured data."""
        gaps = []
        
        if "gaps" in data:
            if isinstance(data["gaps"], list):
                gaps.extend(data["gaps"])
            elif isinstance(data["gaps"], str):
                gaps.append(data["gaps"])
        
        if "skill_gaps" in data:
            gaps.extend(data["skill_gaps"] if isinstance(data["skill_gaps"], list) else [data["skill_gaps"]])
        
        if "missing_skills" in data:
            gaps.extend(data["missing_skills"] if isinstance(data["missing_skills"], list) else [data["missing_skills"]])
        
        return gaps
    
    @classmethod
    def _extract_score_from_text(cls, text: str) -> Optional[float]:
        """Extract numeric score from response text."""
        text_lower = text.lower()
        
        for pattern in cls.SCORE_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                try:
                    score = float(match)
                    if 0 <= score <= 100:
                        return score
                except ValueError:
                    continue
        
        return None
    
    @classmethod
    def _extract_tier_from_text(cls, text: str) -> Optional[str]:
        """Extract confidence tier from response text."""
        for pattern in cls.TIER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tier = match.group(1).strip()
                # Normalize tier names
                tier_normalized = tier.upper().replace("-", "_").replace(" ", "_")
                # Map variations to canonical names
                tier_map = {
                    "INSUFFICIENT": "INSUFFICIENT_DATA",
                    "INSUFFICIENT_DATA": "INSUFFICIENT_DATA",
                    "LOW_MEDIUM": "LOW_MEDIUM",
                    "MEDIUM_HIGH": "MEDIUM_HIGH",
                    "HIGH": "HIGH",
                    "MEDIUM": "MEDIUM",
                    "LOW": "LOW",
                }
                return tier_map.get(tier_normalized, tier_normalized)
        
        return None
    
    @classmethod
    def _extract_gaps_from_text(cls, text: str) -> List[str]:
        """Extract identified gaps from response text."""
        gaps = []
        
        # Look for "Areas to Address" section
        areas_section = re.search(r"(?:areas?\s+to\s+address|gaps?|missing)[:\s]*\n((?:[-*]\s*[^\n]+\n?)+)", text, re.IGNORECASE)
        if areas_section:
            items = re.findall(r"[-*]\s*\*?\*?\[?([^\]:\n*]+)", areas_section.group(1))
            gaps.extend([item.strip() for item in items if item.strip()])
        
        # Also look for bullet points with **[Name]** format
        bracket_items = re.findall(r"\*\*\[([^\]]+)\]\*\*", text)
        gaps.extend(bracket_items)
        
        # General gap patterns as fallback
        for pattern in cls.GAP_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    gap = match[0].strip() if match[0] else match[-1].strip() if len(match) > 1 else ""
                else:
                    gap = match.strip()
                if gap and len(gap) > 3 and len(gap) < 100:
                    gaps.append(gap)
        
        # Deduplicate and limit
        seen = set()
        unique_gaps = []
        for gap in gaps:
            gap_lower = gap.lower()
            if gap_lower not in seen:
                seen.add(gap_lower)
                unique_gaps.append(gap)
        
        return unique_gaps[:10]  # Limit to 10 gaps


# =============================================================================
# Test Runner
# =============================================================================

class AccuracyTestRunner:
    """
    Main test runner for accuracy validation.
    """
    
    def __init__(
        self,
        verbose: bool = True,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Initialize the test runner.
        
        Args:
            verbose: Whether to print detailed output.
            timeout: Request timeout in seconds.
        """
        self.verbose = verbose
        self.timeout = timeout
        self.results: List[AccuracyResult] = []
        self.failures: List[FailureAnalysis] = []
        self.raw_responses: Dict[str, Dict[str, Any]] = {}
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with color coding."""
        colors = {
            "INFO": "\033[94m",     # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",    # Red
            "HEADER": "\033[95m",   # Magenta
            "RESET": "\033[0m",
        }
        if self.verbose:
            print(f"{colors.get(level, '')}{message}{colors['RESET']}")
    
    async def check_health(self) -> bool:
        """Check if the backend is healthy."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(HEALTH_ENDPOINT, timeout=10.0)
                return response.status_code == 200
        except Exception as e:
            self.log(f"Health check failed: {e}", "ERROR")
            return False
    
    async def run_single_test(self, test_case: TestCase) -> AccuracyResult:
        """
        Execute a single test case.
        
        Args:
            test_case: The TestCase to run.
            
        Returns:
            AccuracyResult with validation results.
        """
        self.log(f"\n  Running {test_case.id}: {test_case.name}", "INFO")
        self.log(f"    Query: \"{test_case.query[:60]}{'...' if len(test_case.query) > 60 else ''}\"", "INFO")
        
        # Collect response
        response_text = ""
        events: List[Dict[str, Any]] = []
        error_message = None
        
        payload = {
            "query": test_case.query,
            "include_thoughts": True,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    SSE_ENDPOINT,
                    json=payload,
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    if response.status_code != 200:
                        error_message = f"HTTP {response.status_code}"
                    else:
                        buffer = ""
                        async for chunk in response.aiter_text():
                            buffer += chunk
                            
                            # Parse events from buffer
                            while '\n\n' in buffer:
                                event_block, buffer = buffer.split('\n\n', 1)
                                parsed = self._parse_sse_block(event_block)
                                if parsed:
                                    events.append(parsed)
                                    
                                    # Collect response text
                                    if parsed.get("event_type") == "response":
                                        chunk_text = parsed.get("data", {}).get("chunk", "")
                                        response_text += chunk_text
        
        except httpx.TimeoutException:
            error_message = f"Timeout after {self.timeout}s"
        except Exception as e:
            error_message = str(e)
        
        # Store raw response for debugging
        self.raw_responses[test_case.id] = {
            "query": test_case.query,
            "response_text": response_text,
            "events": events,
            "error": error_message,
        }
        
        # Parse response
        parsed = PipelineResponseParser.parse_response(response_text, events)
        
        # Log parsed values
        if self.verbose:
            self.log(f"    Parsed: score={parsed['score']}, tier={parsed['tier']}, gaps={len(parsed['gaps'])}", "INFO")
        
        # Validate against expected
        result = validate_test_result(
            test_case=test_case,
            actual_score=parsed["score"],
            actual_tier=parsed["tier"],
            actual_gaps=parsed["gaps"],
            actual_quality_flags=parsed["quality_flags"],
        )
        
        # Add error warning if present
        if error_message:
            result.warnings.append(f"Request error: {error_message}")
        
        # Log result
        status_symbol = {
            ValidationStatus.PASS: "✓",
            ValidationStatus.PARTIAL: "◐",
            ValidationStatus.FAIL: "✗",
        }[result.overall_status]
        status_color = {
            ValidationStatus.PASS: "SUCCESS",
            ValidationStatus.PARTIAL: "WARNING",
            ValidationStatus.FAIL: "ERROR",
        }[result.overall_status]
        
        self.log(f"    {status_symbol} {result.overall_status.value}", status_color)
        
        return result
    
    def _parse_sse_block(self, block: str) -> Optional[Dict[str, Any]]:
        """Parse a single SSE event block."""
        event_type = None
        data = None
        
        for line in block.split('\n'):
            line = line.strip()
            if line.startswith('event:'):
                event_type = line[6:].strip()
            elif line.startswith('data:'):
                try:
                    data = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    data = {"raw": line[5:].strip()}
        
        if event_type:
            return {"event_type": event_type, "data": data or {}}
        return None
    
    async def run_tests(
        self,
        test_cases: List[TestCase],
        stop_on_failure: bool = False,
    ) -> Tuple[List[AccuracyResult], AccuracyMetrics]:
        """
        Run multiple test cases.
        
        Args:
            test_cases: List of TestCase objects to run.
            stop_on_failure: Whether to stop on first failure.
            
        Returns:
            Tuple of (results list, aggregate metrics).
        """
        self.log("\n" + "═" * 70, "HEADER")
        self.log("  ACCURACY TEST EXECUTION", "HEADER")
        self.log("═" * 70 + "\n", "HEADER")
        
        # Health check
        self.log("Checking backend health...", "INFO")
        if not await self.check_health():
            self.log("Backend is not healthy! Run: docker compose up -d", "ERROR")
            return [], AccuracyMetrics()
        self.log("Backend is healthy ✓\n", "SUCCESS")
        
        # Run tests
        self.log(f"Running {len(test_cases)} test cases...\n", "INFO")
        
        for i, test_case in enumerate(test_cases, 1):
            self.log(f"[{i}/{len(test_cases)}] {test_case.category.value}: {test_case.name}", "HEADER")
            
            result = await self.run_single_test(test_case)
            self.results.append(result)
            
            # Analyze failures
            if result.overall_status == ValidationStatus.FAIL:
                failure = analyze_failure(result, test_case)
                self.failures.append(failure)
                
                if stop_on_failure:
                    self.log("\nStopping on first failure.", "WARNING")
                    break
            
            # Brief delay between tests
            await asyncio.sleep(0.5)
        
        # Calculate metrics
        metrics = calculate_aggregate_metrics(self.results)
        
        return self.results, metrics
    
    async def run_all_tests(self) -> Tuple[List[AccuracyResult], AccuracyMetrics]:
        """
        Run all test cases.
        
        Returns:
            Tuple of (results list, aggregate metrics).
        """
        all_tests = get_all_test_cases()
        return await self.run_tests(all_tests)
    
    async def run_category(
        self,
        category: TestCategory,
    ) -> Tuple[List[AccuracyResult], AccuracyMetrics]:
        """
        Run all tests in a specific category.
        
        Args:
            category: The TestCategory to run.
            
        Returns:
            Tuple of (results list, aggregate metrics).
        """
        tests = get_test_cases_by_category(category)
        return await self.run_tests(tests)
    
    def generate_reports(self, metrics: AccuracyMetrics) -> str:
        """
        Generate comprehensive reports.
        
        Args:
            metrics: Aggregate AccuracyMetrics.
            
        Returns:
            Combined report string.
        """
        reports = []
        
        # Accuracy report
        reports.append(generate_accuracy_report(self.results, metrics))
        
        # Failure analysis (if any failures)
        if self.failures:
            reports.append(generate_failure_report(self.failures))
            
            # Individual failure templates
            reports.append("\n" + "═" * 70)
            reports.append("  INDIVIDUAL FAILURE TEMPLATES")
            reports.append("═" * 70)
            for failure in self.failures:
                reports.append(generate_individual_failure_template(failure))
        
        return "\n".join(reports)
    
    def save_results(self, output_path: Path):
        """
        Save results to JSON file.
        
        Args:
            output_path: Path to output file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "test_id": r.test_id,
                    "test_name": r.test_name,
                    "query": r.query,
                    "expected_score_min": r.expected_score_min,
                    "expected_score_max": r.expected_score_max,
                    "actual_score": r.actual_score,
                    "expected_tier": r.expected_tier.value,
                    "actual_tier": r.actual_tier,
                    "score_accuracy": r.score_accuracy.value,
                    "tier_accuracy": r.tier_accuracy.value,
                    "gap_accuracy": r.gap_accuracy,
                    "actual_gap_count": r.actual_gap_count,
                    "overall_status": r.overall_status.value,
                    "warnings": r.warnings,
                }
                for r in self.results
            ],
            "failures": [
                {
                    "test_id": f.test_id,
                    "root_cause": f.root_cause.value,
                    "root_cause_confidence": f.root_cause_confidence,
                    "impact_severity": f.impact_severity.value,
                    "recommended_fixes": f.recommended_fixes,
                }
                for f in self.failures
            ],
            "raw_responses": self.raw_responses,
        }
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        
        self.log(f"\nResults saved to: {output_path}", "SUCCESS")


# =============================================================================
# CLI Entry Point
# =============================================================================

async def main():
    """Main entry point for the accuracy test runner."""
    parser = argparse.ArgumentParser(
        description="Accuracy Test Runner for Fit Check Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run all tests
    python -m tests.simulation.accuracy.run_accuracy_tests
    
    # Run Category A only
    python -m tests.simulation.accuracy.run_accuracy_tests --category A
    
    # Run single test
    python -m tests.simulation.accuracy.run_accuracy_tests --test-id A1
    
    # Save results
    python -m tests.simulation.accuracy.run_accuracy_tests --output results.json
        """
    )
    
    parser.add_argument(
        "--category", "-c",
        choices=["A", "B", "C", "D"],
        help="Run only tests from this category"
    )
    parser.add_argument(
        "--test-id", "-t",
        help="Run only this specific test (e.g., A1, B2)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Save results to this JSON file"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Reduce output verbosity"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show test cases without executing"
    )
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="Stop execution on first test failure"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})"
    )
    
    args = parser.parse_args()
    
    # Dry run - just show test summary
    if args.dry_run:
        print(generate_test_summary())
        return
    
    # Initialize runner
    runner = AccuracyTestRunner(
        verbose=not args.quiet,
        timeout=args.timeout,
    )
    
    # Determine which tests to run
    if args.test_id:
        test_case = get_test_case_by_id(args.test_id)
        if not test_case:
            print(f"Error: Test case '{args.test_id}' not found", file=sys.stderr)
            sys.exit(1)
        results, metrics = await runner.run_tests([test_case])
    elif args.category:
        category = TestCategory(args.category)
        results, metrics = await runner.run_category(category)
    else:
        results, metrics = await runner.run_all_tests()
    
    # Generate and print reports
    report = runner.generate_reports(metrics)
    print(report)
    
    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        runner.save_results(output_path)
    else:
        # Default save to outputs directory
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_output = OUTPUT_DIR / f"accuracy_results_{timestamp}.json"
        runner.save_results(default_output)
    
    # Exit with appropriate code
    if metrics.pass_rate >= 0.75:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
