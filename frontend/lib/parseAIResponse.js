'use client';

/**
 * parseAIResponse - Parses the AI response markdown into structured data
 * for the Pros/Cons card layout.
 * 
 * Expected response format:
 * ### [Company/Role] Fit Analysis
 * 
 * [Summary sentence with confidence score]
 * 
 * **Key Strengths**
 * - **[Skill]**: [Evidence]
 * 
 * **Growth Opportunities**
 * - **[Gap]**: [Transferable skill]
 * 
 * @param {string} rawResponse - The raw markdown response from the AI
 * @returns {Object} Parsed response with structured sections
 */
export function parseAIResponse(rawResponse) {
  if (!rawResponse || typeof rawResponse !== 'string') {
    return {
      title: '',
      strengths: [],
      valueProposition: '',
      growthAreas: [],
      rawContent: ''
    };
  }

  const result = {
    title: '',
    strengths: [],
    valueProposition: '',
    growthAreas: [],
    rawContent: rawResponse,
    hasFundamentalMismatch: false,
    mismatchReason: null,
    calibratedScore: null,
    confidenceTier: null,
  };

  // Detect fundamental mismatch warning
  result.hasFundamentalMismatch = 
    rawResponse.toLowerCase().includes('fundamental mismatch') ||
    rawResponse.toLowerCase().includes('primarily requires') ||
    rawResponse.toLowerCase().includes('significant misalignment');
  
  // Extract mismatch reason if present
  const mismatchMatch = rawResponse.match(/(?:fundamental(?:ly)?\s+(?:mismatch|different|misaligned|misalignment)|primarily requires)[^.]*\./i);
  if (mismatchMatch) {
    result.mismatchReason = mismatchMatch[0];
  }

  // Extract calibrated score and tier
  // Pattern: 85% (HIGH) or 85% confidence (HIGH)
  const scoreTierMatch = rawResponse.match(/(\d+)%\s*(?:confidence)?\s*\((\w+)\)/i);
  if (scoreTierMatch) {
    result.calibratedScore = parseInt(scoreTierMatch[1], 10);
    result.confidenceTier = scoreTierMatch[2].toUpperCase();
  } else {
    // Fallback: just look for percentage
    const scoreMatch = rawResponse.match(/(\d+)%/);
    if (scoreMatch) {
      result.calibratedScore = parseInt(scoreMatch[1], 10);
    }
    // Fallback: just look for tier
    const tierMatch = rawResponse.match(/\b(HIGH|MEDIUM|LOW|INSUFFICIENT_DATA)\b/i);
    if (tierMatch) {
      result.confidenceTier = tierMatch[1].toUpperCase();
    }
  }

  // Split content into lines
  const lines = rawResponse.split('\n').map(line => line.trim()).filter(Boolean);
  
  let currentSection = null;
  let currentContent = [];
  let foundFirstSection = false;

  for (const line of lines) {
    // Detect title (### header)
    if (line.startsWith('###')) {
      result.title = line.replace(/^###\s*/, '').trim();
      continue;
    }

    // Detect section headers - multiple formats:
    // 1. **Header:** or **Header** (just bold, possibly with colon)
    // 2. Plain text headers like "Key Strengths" or "Growth Opportunities"
    const boldSectionMatch = line.match(/^\*\*(.+?)\*\*:?\s*$/);
    const boldWithContentMatch = line.match(/^\*\*(.+?):\*\*\s*(.+)$/);
    const plainSectionMatch = line.match(/^(Key Strengths|Growth Opportunities|Growth Areas|What I Bring|Where I Align|The Learning Curve)$/i);
    
    if (boldSectionMatch) {
      // Save previous section content
      saveCurrentSection(result, currentSection, currentContent);
      
      // Start new section
      const sectionName = boldSectionMatch[1].toLowerCase();
      currentSection = detectSectionType(sectionName);
      currentContent = [];
      foundFirstSection = true;
      continue;
    }
    
    if (boldWithContentMatch) {
      // Save previous section content
      saveCurrentSection(result, currentSection, currentContent);
      
      // Start new section
      const sectionName = boldWithContentMatch[1].toLowerCase();
      currentSection = detectSectionType(sectionName);
      currentContent = [];
      foundFirstSection = true;
      
      // If there's content after the header on same line, add it
      if (boldWithContentMatch[2]) {
        currentContent.push({ type: 'text', text: boldWithContentMatch[2].trim() });
      }
      continue;
    }
    
    if (plainSectionMatch) {
      // Save previous section content
      saveCurrentSection(result, currentSection, currentContent);
      
      // Start new section
      const sectionName = plainSectionMatch[1].toLowerCase();
      currentSection = detectSectionType(sectionName);
      currentContent = [];
      foundFirstSection = true;
      continue;
    }

    // Detect bullet points (including numbered lists)
    if (line.startsWith('- ') || line.startsWith('• ') || line.startsWith('* ') || /^\d+\.\s/.test(line)) {
      const bulletContent = line.replace(/^[-•*]\s*/, '').replace(/^\d+\.\s*/, '').trim();
      currentContent.push({ type: 'bullet', text: bulletContent });
      continue;
    }

    // Regular text content - add to current section or capture as valueProposition
    if (currentSection) {
      currentContent.push({ type: 'text', text: line });
    } else if (!foundFirstSection && line.length > 20) {
      // Capture summary/intro text before first section as valueProposition
      result.valueProposition = (result.valueProposition ? result.valueProposition + ' ' : '') + line;
    }
  }

  // Save final section
  saveCurrentSection(result, currentSection, currentContent);

  // Post-process: ensure we have meaningful content
  result.strengths = processStrengths(result.strengths);
  result.growthAreas = processGrowthAreas(result.growthAreas);

  return result;
}

/**
 * Detect section type from header text
 */
function detectSectionType(sectionName) {
  const strengthKeywords = ['key alignment', 'alignment', 'strength', 'bring', 'value', 'skill', 'match', 'fit'];
  const growthKeywords = ['growth', 'area', 'develop', 'opportunity', 'learn', 'improve', 'curve'];

  if (strengthKeywords.some(kw => sectionName.includes(kw))) {
    return 'strengths';
  }
  if (growthKeywords.some(kw => sectionName.includes(kw))) {
    return 'growthAreas';
  }
  
  // Default to strengths for "What I Bring" type sections
  if (sectionName.includes('what i')) {
    return 'valueProposition';
  }

  return 'strengths'; // Default
}

/**
 * Save accumulated content to the appropriate section
 */
function saveCurrentSection(result, sectionType, content) {
  if (!sectionType || content.length === 0) return;

  switch (sectionType) {
    case 'strengths':
      result.strengths.push(...content);
      break;
    case 'valueProposition':
      result.valueProposition = content
        .map(c => typeof c === 'string' ? c : c.text)
        .join(' ');
      break;
    case 'growthAreas':
      result.growthAreas.push(...content);
      break;
  }
}

/**
 * Process strengths into clean array of strings
 */
function processStrengths(items) {
  return items
    .map(item => {
      if (typeof item === 'string') return item;
      if (item && item.text) return item.text;
      return null;
    })
    .filter(Boolean)
    .slice(0, 6); // Max 6 strengths for UI
}

/**
 * Process growth areas into clean array of strings
 */
function processGrowthAreas(items) {
  return items
    .map(item => {
      if (typeof item === 'string') return item;
      if (item && item.text) return item.text;
      return null;
    })
    .filter(Boolean)
    .slice(0, 4); // Max 4 growth areas for UI
}

/**
 * Extract a summary snippet from the response
 */
export function extractSummary(rawResponse, maxLength = 150) {
  if (!rawResponse) return '';
  
  // Find first paragraph after title
  const lines = rawResponse.split('\n').filter(line => line.trim());
  
  for (const line of lines) {
    const trimmed = line.trim();
    // Skip headers and bullet points
    if (trimmed.startsWith('#') || trimmed.startsWith('-') || 
        trimmed.startsWith('•') || trimmed.startsWith('**')) {
      continue;
    }
    // Found a paragraph
    if (trimmed.length > 20) {
      return trimmed.length > maxLength 
        ? trimmed.substring(0, maxLength) + '...'
        : trimmed;
    }
  }
  
  return '';
}

export default parseAIResponse;
