/**
 * Phase Insights Utilities
 * 
 * Extract meaningful metadata from phase outputs to display
 * rich context instead of raw JSON data. These utilities parse
 * the phase summaries and thought content to extract structured
 * insights for display.
 */

/**
 * Extract insights from a phase summary string.
 * Parses phase completion summaries to extract structured data.
 * 
 * @param {string} phase - Phase name
 * @param {string} summary - Phase summary string
 * @returns {Object} Extracted insights
 */
export function extractPhaseInsights(phase, summary) {
  if (!summary) return null;
  
  switch (phase) {
    case 'connecting':
      return extractConnectingInsights(summary);
    case 'deep_research':
      return extractResearchInsights(summary);
    case 'research_reranker':
      return extractRerankerInsights(summary);
    case 'content_enrich':
      return extractContentEnrichInsights(summary);
    case 'skeptical_comparison':
      return extractSkepticalInsights(summary);
    case 'skills_matching':
      return extractSkillsInsights(summary);
    case 'confidence_reranker':
      return extractConfidenceInsights(summary);
    case 'generate_results':
      return extractResultsInsights(summary);
    default:
      return { summary };
  }
}

/**
 * Extract connecting phase insights
 * Example: "Query classified as 'company', company: Palantir"
 */
function extractConnectingInsights(summary) {
  const insights = {
    type: 'classification',
    queryType: null,
    company: null,
    jobTitle: null,
    isValid: true,
  };
  
  // Extract query type
  const typeMatch = summary.match(/classified as ['"]?(\w+)['"]?/i);
  if (typeMatch) {
    insights.queryType = typeMatch[1];
  }
  
  // Extract company name
  const companyMatch = summary.match(/company:\s*([^,]+)/i);
  if (companyMatch) {
    insights.company = companyMatch[1].trim();
  }
  
  // Extract job title if present
  const titleMatch = summary.match(/job[_ ]?title:\s*([^,]+)/i);
  if (titleMatch) {
    insights.jobTitle = titleMatch[1].trim();
  }
  
  // Check for rejection
  if (summary.toLowerCase().includes('rejected') || 
      summary.toLowerCase().includes('invalid') ||
      summary.toLowerCase().includes('early_exit')) {
    insights.isValid = false;
  }
  
  return insights;
}

/**
 * Extract deep research insights
 * Example: "Identified 2 technologies, 2 requirements, 4 culture signals"
 */
function extractResearchInsights(summary) {
  const insights = {
    type: 'research',
    techCount: 0,
    requirementsCount: 0,
    cultureCount: 0,
    technologies: [],
    requirements: [],
    cultureSignals: [],
  };
  
  // Extract counts
  const techMatch = summary.match(/(\d+)\s*technolog/i);
  const reqMatch = summary.match(/(\d+)\s*requirement/i);
  const cultureMatch = summary.match(/(\d+)\s*culture/i);
  
  if (techMatch) insights.techCount = parseInt(techMatch[1], 10);
  if (reqMatch) insights.requirementsCount = parseInt(reqMatch[1], 10);
  if (cultureMatch) insights.cultureCount = parseInt(cultureMatch[1], 10);
  
  return insights;
}

/**
 * Extract research reranker insights
 * Example: "Data: SPARSE | Quality: LOW | Confidence: 35% | Action: ENHANCE_SEARCH"
 */
function extractRerankerInsights(summary) {
  const insights = {
    type: 'quality_gate',
    dataLevel: null,
    qualityTier: null,
    confidence: null,
    action: null,
    flags: [],
    verifiability: null,
  };
  
  // Parse pipe-separated format
  const parts = summary.split('|').map(p => p.trim());
  
  for (const part of parts) {
    const [key, value] = part.split(':').map(s => s.trim());
    
    if (!key || !value) continue;

    const lowerKey = key.toLowerCase();
    
    if (lowerKey === 'data' || lowerKey === 'data_quality_tier') {
      insights.dataLevel = value;
    } else if (lowerKey === 'quality' || lowerKey === 'research_quality_tier') {
      insights.qualityTier = value;
    } else if (lowerKey === 'confidence' || lowerKey === 'data_confidence_score') {
      const match = value.match(/(\d+)/);
      if (match) insights.confidence = parseInt(match[1], 10);
    } else if (lowerKey === 'action' || lowerKey === 'recommended_action') {
      insights.action = value;
    } else if (lowerKey === 'flags' || lowerKey === 'quality_flags') {
      insights.flags = value.split(',').map(f => f.trim()).filter(Boolean);
    } else if (lowerKey === 'verifiability' || lowerKey === 'company_verifiability') {
      insights.verifiability = value;
    }
  }
  
  return insights;
}

/**
 * Extract content enrichment insights
 * Example: "Extracted 3 pages, 45.2 KB content"
 */
function extractContentEnrichInsights(summary) {
  const insights = {
    type: 'enrichment',
    pagesExtracted: 0,
    contentSize: null,
    topSources: [],
  };
  
  // Parse "Extracted X pages, Y KB content" or "Enriched X/Y sources"
  const pagesMatch = summary.match(/(\d+)\s*page/i) || summary.match(/Enriched (\d+)/i);
  const sizeMatch = summary.match(/(\d+(?:\.\d+)?)\s*(?:KB|MB)/i);
  
  if (pagesMatch) insights.pagesExtracted = parseInt(pagesMatch[1], 10);
  if (sizeMatch) insights.contentSize = sizeMatch[0];
  
  return insights;
}

/**
 * Extract skeptical comparison insights
 * Example: "Critical analysis completed with conservative defaults"
 */
function extractSkepticalInsights(summary) {
  const insights = {
    type: 'gap_analysis',
    hasGaps: false,
    gapCount: 0,
    riskLevel: null,
    issues: [],
  };
  
  // Check for gap indicators
  if (summary.toLowerCase().includes('gap')) {
    insights.hasGaps = true;
    const gapMatch = summary.match(/(\d+)\s*gap/i);
    if (gapMatch) insights.gapCount = parseInt(gapMatch[1], 10);
  }
  
  // Check for risk level
  if (summary.toLowerCase().includes('critical')) {
    insights.riskLevel = 'critical';
  } else if (summary.toLowerCase().includes('high')) {
    insights.riskLevel = 'high';
  } else if (summary.toLowerCase().includes('medium')) {
    insights.riskLevel = 'medium';
  } else if (summary.toLowerCase().includes('low')) {
    insights.riskLevel = 'low';
  }
  
  // Check for issues/errors
  if (summary.toLowerCase().includes('issue') || 
      summary.toLowerCase().includes('error') ||
      summary.toLowerCase().includes('conservative')) {
    insights.issues.push(summary);
  }
  
  return insights;
}

/**
 * Extract skills matching insights
 * Example: "Match score: 85% (4 matched, 0 gaps)"
 */
function extractSkillsInsights(summary) {
  const insights = {
    type: 'skill_match',
    matchScore: null,
    matchedCount: 0,
    gapCount: 0,
    matches: [],
    gaps: [],
  };
  
  // Extract match score
  const scoreMatch = summary.match(/(\d+)%/);
  if (scoreMatch) {
    insights.matchScore = parseInt(scoreMatch[1], 10);
  }
  
  // Extract counts
  const matchedMatch = summary.match(/(\d+)\s*matched/i);
  const gapMatch = summary.match(/(\d+)\s*gap/i);
  
  if (matchedMatch) insights.matchedCount = parseInt(matchedMatch[1], 10);
  if (gapMatch) insights.gapCount = parseInt(gapMatch[1], 10);
  
  return insights;
}

/**
 * Extract confidence reranker insights
 * Example: "Calibrated: 78% (HIGH) | Flags: sparse_tech_stack | Adj: -5%"
 */
function extractConfidenceInsights(summary) {
  const insights = {
    type: 'confidence',
    calibratedScore: null,
    tier: null,
    qualityFlags: [],
    adjustment: null,
  };
  
  // Parse "Calibrated: 78% (HIGH) | Flags: sparse_tech_stack | Adj: -5%"
  const scoreMatch = summary.match(/(\d+)%/);
  const tierMatch = summary.match(/\((HIGH|MEDIUM|LOW|INSUFFICIENT_DATA)\)/i);
  const flagsMatch = summary.match(/Flags?:\s*([^|]+)/i);
  const adjMatch = summary.match(/Adj(?:ustment)?:\s*([+-]?\d+%?)/i);
  
  if (scoreMatch) insights.calibratedScore = parseInt(scoreMatch[1], 10);
  if (tierMatch) insights.tier = tierMatch[1].toUpperCase();
  if (flagsMatch) {
    insights.qualityFlags = flagsMatch[1].split(',').map(f => f.trim()).filter(Boolean);
  }
  if (adjMatch) insights.adjustment = adjMatch[1];
  
  return insights;
}

/**
 * Extract results generation insights
 * Example: "Generated 266 word response"
 */
function extractResultsInsights(summary) {
  const insights = {
    type: 'results',
    wordCount: null,
  };
  
  const wordMatch = summary.match(/(\d+)\s*word/i);
  if (wordMatch) {
    insights.wordCount = parseInt(wordMatch[1], 10);
  }
  
  return insights;
}

/**
 * Parse thought content to extract richer context.
 * Analyzes reasoning content to extract key findings.
 * 
 * @param {Object} thought - Thought object
 * @returns {Object} Enhanced thought data
 */
export function parseThoughtContent(thought) {
  if (!thought) return null;
  
  const enhanced = {
    ...thought,
    extractedData: null,
    displaySummary: null,
  };
  
  const content = thought.content || '';
  
  // Extract key insights from reasoning content
  if (thought.type === 'reasoning') {
    enhanced.displaySummary = formatReasoningSummary(content);
    enhanced.extractedData = extractReasoningData(content);
  } else if (thought.type === 'tool_call') {
    enhanced.displaySummary = formatToolCallSummary(thought.tool, thought.input);
  } else if (thought.type === 'observation') {
    enhanced.displaySummary = formatObservationSummary(content);
  }
  
  return enhanced;
}

/**
 * Format reasoning content into a display-friendly summary
 */
function formatReasoningSummary(content) {
  if (!content) return null;
  
  // Remove quotes if wrapped
  let cleaned = content.replace(/^["']|["']$/g, '');
  
  // Truncate if too long, but keep meaningful content
  if (cleaned.length > 200) {
    // Try to find a sentence boundary
    const sentenceEnd = cleaned.substring(0, 200).lastIndexOf('.');
    if (sentenceEnd > 100) {
      cleaned = cleaned.substring(0, sentenceEnd + 1);
    } else {
      cleaned = cleaned.substring(0, 197) + '...';
    }
  }
  
  return cleaned;
}

/**
 * Extract structured data from reasoning content
 */
function extractReasoningData(content) {
  const data = {};
  
  // Look for confidence scores
  const confMatch = content.match(/(\d+)%\s*(confidence|match)/i);
  if (confMatch) {
    data.confidence = parseInt(confMatch[1], 10);
  }
  
  // Look for tier indicators
  const tierMatch = content.match(/\b(HIGH|MEDIUM|LOW|INSUFFICIENT)\b/i);
  if (tierMatch) {
    data.tier = tierMatch[1].toUpperCase();
  }
  
  // Look for technology mentions (common tech keywords)
  const techPatterns = /\b(Python|JavaScript|TypeScript|React|Node\.js|AWS|Docker|Kubernetes|PostgreSQL|Redis|Kafka|Go|Rust|Java|C\+\+|FastAPI|Django|Flask)\b/gi;
  const techMatches = content.match(techPatterns);
  if (techMatches) {
    data.technologies = [...new Set(techMatches.map(t => t.toLowerCase()))];
  }
  
  return Object.keys(data).length > 0 ? data : null;
}

/**
 * Format tool call into a summary
 */
function formatToolCallSummary(tool, input) {
  if (!tool) return null;
  
  const toolNames = {
    'web_search': 'Searching the web',
    'analyze_skill_match': 'Analyzing skill alignment',
    'analyze_experience_relevance': 'Evaluating experience relevance',
  };
  
  const toolName = toolNames[tool] || 'Using tool';
  
  if (input && typeof input === 'string') {
    const shortInput = input.length > 60 ? input.substring(0, 57) + '...' : input;
    return `${toolName}: "${shortInput}"`;
  }
  
  return toolName;
}

/**
 * Format observation into a summary
 */
function formatObservationSummary(content) {
  if (!content) return null;
  
  // Common generic observations that we can enhance
  const genericPatterns = {
    'Found relevant employer information': 'Retrieved company intelligence data',
    'Skill analysis complete': 'Completed skill-to-requirement mapping',
    'Experience analysis complete': 'Evaluated experience relevance',
  };
  
  for (const [pattern, enhanced] of Object.entries(genericPatterns)) {
    if (content.includes(pattern)) {
      return enhanced;
    }
  }
  
  // Keep original if not a generic pattern
  return content.length > 150 ? content.substring(0, 147) + '...' : content;
}

/**
 * Get phase display metadata for UI
 */
export function getPhaseDisplayMeta(phase, insights) {
  const meta = {
    icon: null,
    color: null,
    summary: null,
    metrics: [],
  };
  
  if (!insights) return meta;
  
  switch (insights.type) {
    case 'classification':
      meta.summary = insights.company 
        ? `Identified: ${insights.company}` 
        : insights.queryType 
          ? `Type: ${insights.queryType}` 
          : null;
      break;
      
    case 'research':
      meta.metrics = [
        { label: 'Tech', value: insights.techCount, icon: 'code' },
        { label: 'Reqs', value: insights.requirementsCount, icon: 'target' },
        { label: 'Culture', value: insights.cultureCount, icon: 'users' },
      ];
      meta.summary = `Found ${insights.techCount} technologies, ${insights.requirementsCount} requirements`;
      break;
      
    case 'enrichment':
      meta.metrics = [
        { label: 'Enriched', value: `${insights.enrichedCount}/${insights.totalCount}`, icon: 'database' },
      ];
      meta.summary = `Extracted full content for ${insights.enrichedCount} sources`;
      break;
      
    case 'gap_analysis':
      meta.metrics = [
        { label: 'Gaps', value: insights.gapCount, icon: 'target' },
      ];
      meta.summary = insights.riskLevel 
        ? `Risk Level: ${insights.riskLevel.toUpperCase()}` 
        : 'Gap analysis completed';
      break;
      
    case 'quality_gate':
      meta.color = getQualityColor(insights.qualityTier);
      meta.summary = insights.action === 'CONTINUE' 
        ? 'Quality validated ✓' 
        : `Action: ${insights.action}`;
      if (insights.confidence) {
        meta.metrics.push({ label: 'Confidence', value: `${insights.confidence}%` });
      }
      if (insights.dataLevel) {
        meta.dataLevel = insights.dataLevel;
      }
      if (insights.flags && insights.flags.length > 0) {
        meta.flags = insights.flags;
      }
      break;
      
    case 'skill_match':
      meta.color = getScoreColor(insights.matchScore);
      meta.summary = insights.matchScore 
        ? `${insights.matchScore}% match (${insights.matchedCount} skills)` 
        : null;
      break;
      
    case 'confidence':
      meta.color = getTierColor(insights.tier);
      meta.summary = insights.confidence 
        ? `${insights.confidence}% ${insights.tier || ''}`.trim()
        : null;
      if (insights.flags && insights.flags.length > 0) {
        meta.flags = insights.flags;
      }
      break;
      
    case 'results':
      meta.summary = insights.wordCount 
        ? `Generated ${insights.wordCount} word response` 
        : null;
      break;
  }
  
  return meta;
}

/**
 * Get color for quality tier
 */
function getQualityColor(tier) {
  const colors = {
    HIGH: 'muted-teal',
    MEDIUM: 'amber-500',
    LOW: 'red-500',
    INSUFFICIENT: 'red-600',
  };
  return colors[tier?.toUpperCase()] || 'twilight';
}

/**
 * Get color for numeric score
 */
function getScoreColor(score) {
  if (!score) return 'twilight';
  if (score >= 70) return 'muted-teal';
  if (score >= 40) return 'amber-500';
  return 'red-500';
}

/**
 * Get color for confidence tier
 */
function getTierColor(tier) {
  const colors = {
    HIGH: 'muted-teal',
    MEDIUM: 'amber-500',
    LOW: 'red-500',
  };
  return colors[tier?.toUpperCase()] || 'burnt-peach';
}

export default {
  extractPhaseInsights,
  parseThoughtContent,
  getPhaseDisplayMeta,
};
