#!/usr/bin/env python3
"""
AI Output Quality Analyzer

Analyzes AI outputs from pipeline runs to identify:
1. Prompt optimization opportunities
2. Quality metrics scoring
3. Anti-sycophancy compliance
4. Template compliance

Usage:
    python analyze_ai_outputs.py --input-file outputs/last_run.json
    python analyze_ai_outputs.py --compare outputs/run1.json outputs/run2.json
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional


# =============================================================================
# Quality Metrics
# =============================================================================

@dataclass
class QualityMetrics:
    """Quality metrics for AI output analysis."""
    
    # Specificity: presence of specific names, numbers, technologies
    specificity_score: float = 0.0
    
    # Gap acknowledgment: Phase 3 gaps mentioned in Phase 5
    gap_acknowledgment: bool = False
    
    # Evidence density: references to research findings
    evidence_density: float = 0.0
    
    # Template compliance: required sections present
    template_compliance: float = 0.0
    
    # Word count
    word_count: int = 0
    
    # Sycophancy score: 0 = no sycophantic phrases, 1 = highly sycophantic
    sycophancy_score: float = 0.0
    
    # Overall quality (weighted average)
    overall_quality: float = 0.0
    
    # Issues found
    issues: List[str] = field(default_factory=list)
    
    # Optimization suggestions
    suggestions: List[str] = field(default_factory=list)


# =============================================================================
# Sycophancy Detection
# =============================================================================

SYCOPHANTIC_PHRASES = [
    "perfect fit",
    "ideal candidate",
    "excellent match",
    "amazing",
    "outstanding",
    "exceptional",
    "flawless",
    "perfect match",
    "ideal fit",
    "couldn't be better",
    "perfect alignment",
    "exactly what",
]

GENERIC_PHRASES = [
    "passionate about technology",
    "excited about this opportunity",
    "i believe i would be a great",
    "eager to learn",
    "hard-working",
    "team player",
    "fast learner",
    "excellent communication skills",
]


def detect_sycophancy(text: str) -> tuple[float, List[str]]:
    """
    Detect sycophantic language in text.
    
    Returns:
        Tuple of (sycophancy_score, list of detected phrases)
    """
    text_lower = text.lower()
    detected = []
    
    for phrase in SYCOPHANTIC_PHRASES:
        if phrase in text_lower:
            detected.append(phrase)
    
    # Score: 0 = none, 1 = heavily sycophantic
    score = min(1.0, len(detected) * 0.25)
    
    return score, detected


def detect_generic_phrases(text: str) -> List[str]:
    """
    Detect generic phrases that lack specificity.
    
    Returns:
        List of detected generic phrases
    """
    text_lower = text.lower()
    detected = []
    
    for phrase in GENERIC_PHRASES:
        if phrase in text_lower:
            detected.append(phrase)
    
    return detected


# =============================================================================
# Specificity Analysis
# =============================================================================

# Patterns that indicate specific content
SPECIFICITY_PATTERNS = [
    r'\b\d+\s*(?:years?|months?)\b',  # Time durations
    r'\b\d+%\b',                       # Percentages
    r'\bPython|JavaScript|Go|Rust|TypeScript|Java|C\+\+\b',  # Languages
    r'\bReact|Next\.js|FastAPI|Django|Flask|LangChain\b',    # Frameworks
    r'\bAWS|GCP|Azure|Kubernetes|Docker\b',                   # Cloud/infra
    r'\bTensorFlow|PyTorch|LangGraph|Gemini\b',               # AI/ML
    r'\b[A-Z][a-z]+\s+(?:project|system|platform)\b',         # Named projects
]


def analyze_specificity(text: str) -> tuple[float, int]:
    """
    Analyze text specificity.
    
    Returns:
        Tuple of (specificity_score, match_count)
    """
    match_count = 0
    
    for pattern in SPECIFICITY_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        match_count += len(matches)
    
    # Normalize: 0-5 matches = low, 5-10 = medium, 10+ = high
    word_count = len(text.split())
    normalized = match_count / max(1, word_count / 50)  # Per 50 words
    score = min(1.0, normalized / 3)  # Cap at 1.0
    
    return score, match_count


# =============================================================================
# Template Compliance
# =============================================================================

REQUIRED_SECTIONS = {
    "key_alignments": ["key alignments", "key alignment", "alignments:", "where i align"],
    "what_i_bring": ["what i bring", "what i offer"],
    "growth_areas": ["growth areas", "growth area", "areas for growth", "the learning curve", "learning curve"],
    "lets_connect": ["let's connect", "lets connect", "connect with me", "reach out"],
}


def check_template_compliance(response: str) -> tuple[float, List[str]]:
    """
    Check if response follows the required template structure.
    
    Returns:
        Tuple of (compliance_score, missing_sections)
    """
    response_lower = response.lower()
    missing = []
    
    for section, variations in REQUIRED_SECTIONS.items():
        found = any(v in response_lower for v in variations)
        if not found:
            missing.append(section)
    
    score = (len(REQUIRED_SECTIONS) - len(missing)) / len(REQUIRED_SECTIONS)
    return score, missing


# =============================================================================
# Evidence Analysis
# =============================================================================

def analyze_evidence_usage(
    response: str, 
    research_data: Optional[Dict] = None
) -> tuple[float, List[str]]:
    """
    Analyze how well the response uses research evidence.
    
    Returns:
        Tuple of (evidence_density, referenced_items)
    """
    referenced = []
    
    if research_data:
        # Check for tech stack mentions
        tech_stack = research_data.get("tech_stack", [])
        for tech in tech_stack:
            if tech.lower() in response.lower():
                referenced.append(f"tech:{tech}")
        
        # Check for requirement mentions
        requirements = research_data.get("identified_requirements", [])
        for req in requirements:
            # Check for key words from the requirement
            words = req.lower().split()
            if len(words) >= 2:
                key_words = [w for w in words if len(w) > 4][:2]
                if all(w in response.lower() for w in key_words):
                    referenced.append(f"req:{req[:30]}...")
        
        # Check for culture signal mentions
        culture = research_data.get("culture_signals", [])
        for signal in culture:
            if signal.lower() in response.lower():
                referenced.append(f"culture:{signal}")
    
    # Calculate density
    word_count = len(response.split())
    density = len(referenced) / max(1, word_count / 100)  # Per 100 words
    score = min(1.0, density)
    
    return score, referenced


# =============================================================================
# Gap Acknowledgment Analysis
# =============================================================================

def check_gap_acknowledgment(
    response: str,
    gaps: Optional[List[str]] = None
) -> tuple[bool, List[str]]:
    """
    Check if the response acknowledges gaps from skeptical analysis.
    
    Returns:
        Tuple of (acknowledged_any, acknowledged_gaps)
    """
    if not gaps:
        return False, []
    
    response_lower = response.lower()
    acknowledged = []
    
    for gap in gaps:
        # Check for key words from the gap
        gap_words = [w.lower() for w in gap.split() if len(w) > 4]
        
        # If at least half of significant words appear, consider it acknowledged
        matches = sum(1 for w in gap_words if w in response_lower)
        if gap_words and matches >= len(gap_words) / 2:
            acknowledged.append(gap)
    
    return len(acknowledged) > 0, acknowledged


# =============================================================================
# Main Analysis
# =============================================================================

def analyze_output(data: Dict) -> QualityMetrics:
    """
    Analyze a complete pipeline output for quality metrics.
    
    Args:
        data: Pipeline output data (from simulation JSON).
        
    Returns:
        QualityMetrics with all scores and issues.
    """
    metrics = QualityMetrics()
    response = data.get("final_response", "")
    phases = data.get("phases", {})
    
    # Extract phase data
    phase2_data = phases.get("deep_research", {})
    phase3_data = phases.get("skeptical_comparison", {})
    
    # Basic metrics
    metrics.word_count = len(response.split())
    
    # Word count check
    if metrics.word_count > 400:
        metrics.issues.append(f"Response exceeds 400 words: {metrics.word_count}")
        metrics.suggestions.append("Add stricter word count constraints to Phase 5 prompt")
    
    # Sycophancy analysis
    syc_score, syc_phrases = detect_sycophancy(response)
    metrics.sycophancy_score = syc_score
    if syc_phrases:
        metrics.issues.append(f"Sycophantic phrases detected: {syc_phrases}")
        metrics.suggestions.append("Strengthen anti-sycophancy constraints in Phase 5")
    
    # Generic phrase detection
    generic = detect_generic_phrases(response)
    if generic:
        metrics.issues.append(f"Generic phrases detected: {generic}")
        metrics.suggestions.append("Add examples of specific language in Phase 5 prompt")
    
    # Specificity analysis
    spec_score, spec_count = analyze_specificity(response)
    metrics.specificity_score = spec_score
    if spec_score < 0.5:
        metrics.issues.append(f"Low specificity score: {spec_score:.2f} ({spec_count} specific items)")
        metrics.suggestions.append("Require explicit evidence references in prompt")
    
    # Template compliance
    template_score, missing = check_template_compliance(response)
    metrics.template_compliance = template_score
    if missing:
        metrics.issues.append(f"Missing template sections: {missing}")
        metrics.suggestions.append("Add section headers as required format in prompt")
    
    # Evidence usage (if we have phase 2 data)
    if phase2_data:
        research = {
            "tech_stack": phase2_data.get("tech_stack", []),
            "identified_requirements": phase2_data.get("identified_requirements", []),
            "culture_signals": phase2_data.get("culture_signals", []),
        }
        ev_score, referenced = analyze_evidence_usage(response, research)
        metrics.evidence_density = ev_score
        if ev_score < 0.3:
            metrics.issues.append(f"Low evidence usage: {len(referenced)} references")
            metrics.suggestions.append("Add criteria requiring N specific research references")
    
    # Gap acknowledgment (if we have phase 3 data)
    if phase3_data:
        gaps = phase3_data.get("genuine_gaps", [])
        acknowledged, ack_gaps = check_gap_acknowledgment(response, gaps)
        metrics.gap_acknowledgment = acknowledged
        if not acknowledged and gaps:
            metrics.issues.append("Gaps from Phase 3 not acknowledged in response")
            metrics.suggestions.append("Add explicit gap reference requirement to Phase 5")
    
    # Calculate overall quality score
    weights = {
        "specificity": 0.20,
        "evidence": 0.20,
        "template": 0.15,
        "sycophancy": 0.25,  # Inverted
        "gaps": 0.10,
        "word_count": 0.10,
    }
    
    scores = {
        "specificity": metrics.specificity_score,
        "evidence": metrics.evidence_density,
        "template": metrics.template_compliance,
        "sycophancy": 1.0 - metrics.sycophancy_score,  # Invert: 1 = no sycophancy
        "gaps": 1.0 if metrics.gap_acknowledgment else 0.0,
        "word_count": 1.0 if metrics.word_count <= 400 else 0.5,
    }
    
    metrics.overall_quality = sum(
        weights[k] * scores[k] for k in weights
    )
    
    return metrics


# =============================================================================
# Reporting
# =============================================================================

def print_analysis_report(metrics: QualityMetrics, verbose: bool = False) -> None:
    """Print formatted analysis report."""
    print("\n" + "=" * 60)
    print("AI OUTPUT QUALITY ANALYSIS")
    print("=" * 60)
    
    # Overall score with color
    score = metrics.overall_quality
    if score >= 0.8:
        color = "\033[92m"  # Green
        grade = "EXCELLENT"
    elif score >= 0.6:
        color = "\033[93m"  # Yellow
        grade = "GOOD"
    elif score >= 0.4:
        color = "\033[91m"  # Red
        grade = "NEEDS IMPROVEMENT"
    else:
        color = "\033[91m"  # Red
        grade = "POOR"
    
    reset = "\033[0m"
    print(f"\nOverall Quality: {color}{score:.2f} ({grade}){reset}")
    
    # Individual scores
    print(f"\n{'-'*40}")
    print("INDIVIDUAL METRICS")
    print(f"{'-'*40}")
    print(f"  Specificity Score:    {metrics.specificity_score:.2f}")
    print(f"  Evidence Density:     {metrics.evidence_density:.2f}")
    print(f"  Template Compliance:  {metrics.template_compliance:.2f}")
    print(f"  Sycophancy Score:     {metrics.sycophancy_score:.2f} (lower is better)")
    print(f"  Gap Acknowledgment:   {'Yes' if metrics.gap_acknowledgment else 'No'}")
    print(f"  Word Count:           {metrics.word_count} / 400")
    
    # Issues
    if metrics.issues:
        print(f"\n{'-'*40}")
        print("\033[91mISSUES FOUND\033[0m")
        print(f"{'-'*40}")
        for issue in metrics.issues:
            print(f"  ✗ {issue}")
    
    # Suggestions
    if metrics.suggestions:
        print(f"\n{'-'*40}")
        print("\033[93mPROMPT OPTIMIZATION SUGGESTIONS\033[0m")
        print(f"{'-'*40}")
        for i, suggestion in enumerate(metrics.suggestions, 1):
            print(f"  {i}. {suggestion}")
    
    if not metrics.issues:
        print(f"\n\033[92m✓ No issues found - output meets quality standards\033[0m")
    
    print()


def compare_outputs(file1: str, file2: str) -> None:
    """Compare two output files for quality differences."""
    with open(file1, "r") as f:
        data1 = json.load(f)
    with open(file2, "r") as f:
        data2 = json.load(f)
    
    metrics1 = analyze_output(data1)
    metrics2 = analyze_output(data2)
    
    print("\n" + "=" * 60)
    print("COMPARATIVE ANALYSIS")
    print("=" * 60)
    
    print(f"\n{'Metric':<25} {'File 1':>12} {'File 2':>12} {'Delta':>12}")
    print("-" * 60)
    
    comparisons = [
        ("Overall Quality", metrics1.overall_quality, metrics2.overall_quality),
        ("Specificity", metrics1.specificity_score, metrics2.specificity_score),
        ("Evidence Density", metrics1.evidence_density, metrics2.evidence_density),
        ("Template Compliance", metrics1.template_compliance, metrics2.template_compliance),
        ("Sycophancy (lower=better)", metrics1.sycophancy_score, metrics2.sycophancy_score),
        ("Word Count", metrics1.word_count, metrics2.word_count),
    ]
    
    for name, v1, v2 in comparisons:
        delta = v2 - v1
        delta_str = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"
        
        # Color delta based on improvement (special case for sycophancy)
        if "Sycophancy" in name:
            color = "\033[92m" if delta < 0 else "\033[91m" if delta > 0 else ""
        else:
            color = "\033[92m" if delta > 0 else "\033[91m" if delta < 0 else ""
        reset = "\033[0m"
        
        print(f"{name:<25} {v1:>12.2f} {v2:>12.2f} {color}{delta_str:>12}{reset}")


# =============================================================================
# Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analyze AI output quality for prompt optimization"
    )
    parser.add_argument(
        "--input-file",
        type=str,
        help="JSON file from simulation output to analyze",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("FILE1", "FILE2"),
        help="Compare two output files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed analysis",
    )
    
    args = parser.parse_args()
    
    if args.compare:
        compare_outputs(args.compare[0], args.compare[1])
    elif args.input_file:
        with open(args.input_file, "r") as f:
            data = json.load(f)
        
        metrics = analyze_output(data)
        print_analysis_report(metrics, verbose=args.verbose)
    else:
        parser.print_help()
        print("\nError: Either --input-file or --compare must be specified")
        sys.exit(1)


if __name__ == "__main__":
    main()
