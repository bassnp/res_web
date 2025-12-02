# TODO: AI Agent - Multi-Step Research Agent for Fit Analysis

## Overview
This document outlines the implementation plan for a LangGraph-based AI agent that researches companies/job positions and generates personalized "fit analysis" responses. The agent uses a multi-step reasoning process (ReAct pattern) with visible thinking to build trust and provide comprehensive, well-researched responses.

---

## 1. Agent Architecture

### Design Pattern: ReAct (Reasoning + Acting)
The agent follows the ReAct pattern, interleaving reasoning and action:

```
User Query → Agent Reasons → Calls Tool → Observes Result → Reasons Again → ... → Final Answer
```

### Agent Flow Diagram
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FIT CHECK AGENT                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐   │
│   │  START  │────▶│  PLAN NODE   │────▶│  TOOL NODE   │────▶│  REASON  │   │
│   │         │     │              │     │              │     │   NODE   │   │
│   └─────────┘     │ Decide what  │     │ Execute:     │     │          │   │
│                   │ to research  │     │ - web_search │     │ Analyze  │   │
│                   │              │     │ - job_search │     │ results  │   │
│                   └──────────────┘     └──────────────┘     └────┬─────┘   │
│                          ▲                                       │         │
│                          │                                       │         │
│                          │         ┌──────────────┐              │         │
│                          │         │   ENOUGH     │              │         │
│                          └─────────│   INFO?      │◀─────────────┘         │
│                            NO      │              │                        │
│                                    └──────┬───────┘                        │
│                                           │ YES                            │
│                                           ▼                                │
│                                    ┌──────────────┐                        │
│                                    │   GENERATE   │                        │
│                                    │   RESPONSE   │                        │
│                                    │              │                        │
│                                    └──────┬───────┘                        │
│                                           │                                │
│                                           ▼                                │
│                                    ┌──────────────┐                        │
│                                    │     END      │                        │
│                                    │              │                        │
│                                    └──────────────┘                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent Components

### 2.1 State Definition

```python
# services/fit_check_agent.py

from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages


class FitCheckState(TypedDict):
    """State definition for the Fit Check Agent."""
    
    # User input
    query: str                              # Original user query
    query_type: str                         # "company" or "job_position"
    
    # Research results
    company_info: Optional[str]             # Company research results
    job_requirements: Optional[str]         # Job/position requirements
    industry_context: Optional[str]         # Industry trends/context
    
    # Engineer profile (static, loaded from config)
    engineer_skills: List[str]              # List of skills
    engineer_experience: str                # Experience summary
    engineer_projects: List[str]            # Notable projects
    
    # Reasoning trace
    thoughts: Annotated[List[str], add_messages]  # Accumulated thinking steps
    current_step: int                       # Current step number
    
    # Final output
    analysis: Optional[str]                 # Generated fit analysis
    confidence: float                       # Confidence score (0-1)
    
    # Control flow
    needs_more_research: bool               # Should continue researching?
    error: Optional[str]                    # Error message if failed
```

### 2.2 Tools

#### Tool 1: Web Search (Company Research)
```python
@tool
def web_search(query: str) -> str:
    """
    Search the web for company information, culture, tech stack, and job postings.
    
    Use this tool to research:
    - Company overview and mission
    - Engineering culture and practices
    - Tech stack and technologies used
    - Recent news and developments
    - Job postings and requirements
    
    Args:
        query: Search query (e.g., "Google engineering culture", "Stripe tech stack")
    
    Returns:
        Relevant search results as formatted text.
    """
    # Implementation uses Google Custom Search Engine
    pass
```

#### Tool 2: Skill Matcher (Internal Analysis)
```python
@tool
def analyze_skill_match(requirements: str, candidate_skills: List[str]) -> str:
    """
    Analyze how well candidate skills match job/company requirements.
    
    This tool compares the provided requirements against the candidate's
    skills and generates a structured match analysis.
    
    Args:
        requirements: Extracted requirements from company/job research
        candidate_skills: List of candidate's skills
    
    Returns:
        Structured analysis of skill alignment with match scores.
    """
    # Implementation uses LLM to analyze alignment
    pass
```

#### Tool 3: Experience Matcher (Internal Analysis)
```python
@tool
def analyze_experience_relevance(context: str, experience_summary: str) -> str:
    """
    Analyze how candidate's experience relates to the target company/position.
    
    Args:
        context: Company/position context from research
        experience_summary: Candidate's experience summary
    
    Returns:
        Analysis of experience relevance with specific examples.
    """
    pass
```

---

## 3. System Prompt

```python
# prompts/fit_check_system.txt

FIT_CHECK_SYSTEM_PROMPT = """You are an expert career advisor and technical recruiter assistant helping a software engineer showcase their fit for potential employers.

## YOUR ROLE
You analyze companies and job positions to explain how the engineer's skills and experience align with their needs. Your goal is to be:
- **Honest**: Highlight genuine matches, acknowledge gaps professionally
- **Specific**: Use concrete examples from research and the engineer's background
- **Persuasive**: Frame the engineer's experience in the most relevant light
- **Professional**: Maintain a confident but not arrogant tone

## ENGINEER PROFILE
{engineer_profile}

## YOUR PROCESS
1. **Classify Query**: Determine if the employer provided a company name or job description
2. **Research Phase**: 
   - For companies: Search for company info, culture, tech stack, open positions
   - For job descriptions: Extract key requirements and responsibilities
3. **Analysis Phase**:
   - Match skills to requirements
   - Connect experience to company needs
   - Identify unique value propositions
4. **Response Phase**:
   - Generate a compelling, personalized pitch
   - Include specific examples and connections
   - Address potential gaps with growth mindset framing

## RESPONSE FORMAT
Structure your final response as:

### Why I'm a Great Fit for [Company/Position]

**Key Alignments:**
- [Specific skill/experience → Company need]
- [Specific skill/experience → Company need]
- [Specific skill/experience → Company need]

**What I Bring:**
[2-3 sentences on unique value proposition]

**Growth Areas:**
[1-2 sentences on areas for growth, framed positively]

**Let's Connect:**
[Friendly call-to-action]

## IMPORTANT GUIDELINES
- ALWAYS use tools to research before responding
- NEVER make up company information
- If you can't find specific info, say so and generalize appropriately
- Keep the total response under 400 words for readability
- Use the engineer's actual skills and experience, don't embellish
"""
```

---

## 4. Engineer Profile Configuration

```python
# config/engineer_profile.py

"""
Engineer profile configuration for the Fit Check Agent.
Edit this file to customize the engineer's information.
"""

ENGINEER_PROFILE = {
    "name": "Software Engineer",  # Can be personalized
    
    "skills": {
        "languages": ["JavaScript", "TypeScript", "Python", "SQL"],
        "frontend": ["React", "Next.js", "TailwindCSS", "HTML/CSS"],
        "backend": ["Node.js", "FastAPI", "PostgreSQL", "REST APIs"],
        "tools": ["Git", "Docker", "AWS", "Vercel"],
        "concepts": ["Responsive Design", "API Design", "Database Design", "CI/CD"],
    },
    
    "experience_summary": """
    Recent computer science graduate with hands-on experience building full-stack 
    web applications. Completed internship developing production features using 
    React and Node.js. Passionate about clean code, user experience, and 
    continuous learning. Active contributor to personal projects showcasing 
    modern web development practices.
    """,
    
    "notable_projects": [
        {
            "name": "Project Alpha",
            "description": "Full-stack web application with real-time updates",
            "technologies": ["React", "Node.js", "PostgreSQL", "WebSockets"],
            "highlights": ["Real-time collaboration", "Modern UI/UX"],
        },
        {
            "name": "Project Beta", 
            "description": "Mobile-first PWA with offline capabilities",
            "technologies": ["Next.js", "TypeScript", "Service Workers"],
            "highlights": ["Offline-first architecture", "Push notifications"],
        },
    ],
    
    "education": "B.S. Computer Science, 2024",
    
    "strengths": [
        "Fast learner who picks up new technologies quickly",
        "Strong communication skills for cross-functional collaboration",
        "Passionate about writing clean, maintainable code",
        "User-focused approach to development",
    ],
}


def get_formatted_profile() -> str:
    """Format engineer profile for system prompt injection."""
    profile = ENGINEER_PROFILE
    
    skills_formatted = []
    for category, items in profile["skills"].items():
        skills_formatted.append(f"  - {category.title()}: {', '.join(items)}")
    
    projects_formatted = []
    for p in profile["notable_projects"]:
        projects_formatted.append(
            f"  - {p['name']}: {p['description']} ({', '.join(p['technologies'])})"
        )
    
    return f"""
Name: {profile['name']}
Education: {profile['education']}

Skills:
{chr(10).join(skills_formatted)}

Experience:
{profile['experience_summary'].strip()}

Notable Projects:
{chr(10).join(projects_formatted)}

Key Strengths:
{chr(10).join(f'  - {s}' for s in profile['strengths'])}
"""
```

---

## 5. Node Implementations

### 5.1 Query Classifier Node

```python
async def classify_query_node(state: FitCheckState) -> FitCheckState:
    """
    Classify the user's query as either a company name or job description.
    
    This node uses the LLM to determine the query type and extract
    key information for subsequent research.
    """
    query = state["query"]
    
    # Use LLM to classify
    classification_prompt = f"""
    Classify this employer query:
    
    Query: "{query}"
    
    Is this:
    A) A company name (e.g., "Google", "Stripe", "a startup in fintech")
    B) A job description/requirements (e.g., "looking for a React developer with...")
    
    Respond with just "company" or "job_position".
    """
    
    llm = get_llm()
    response = await llm.ainvoke(classification_prompt)
    
    query_type = "company" if "company" in response.content.lower() else "job_position"
    
    return {
        **state,
        "query_type": query_type,
        "thoughts": state["thoughts"] + [f"Classified query as: {query_type}"],
        "current_step": 1,
    }
```

### 5.2 Research Node

```python
async def research_node(state: FitCheckState) -> FitCheckState:
    """
    Conduct web research based on the query type.
    
    For companies: Search for company info, culture, tech stack
    For job positions: Extract requirements and search for context
    """
    query = state["query"]
    query_type = state["query_type"]
    
    research_results = {}
    thoughts = state["thoughts"].copy()
    
    if query_type == "company":
        # Research company
        thoughts.append(f"🔍 Researching {query}...")
        
        # Search 1: Company overview
        overview = await web_search.ainvoke(f"{query} company overview engineering")
        research_results["company_info"] = overview
        thoughts.append(f"📊 Found company overview information")
        
        # Search 2: Tech stack and culture
        tech_culture = await web_search.ainvoke(f"{query} tech stack engineering culture")
        research_results["industry_context"] = tech_culture
        thoughts.append(f"💻 Researched tech stack and engineering culture")
        
    else:  # job_position
        thoughts.append("📋 Analyzing job requirements...")
        
        # Extract requirements from the query itself
        research_results["job_requirements"] = query
        
        # Search for industry context
        industry_search = await web_search.ainvoke(f"software engineer requirements {query[:100]}")
        research_results["industry_context"] = industry_search
        thoughts.append("🔍 Researched industry context for position")
    
    return {
        **state,
        **research_results,
        "thoughts": thoughts,
        "current_step": state["current_step"] + 1,
    }
```

### 5.3 Analysis Node

```python
async def analysis_node(state: FitCheckState) -> FitCheckState:
    """
    Analyze how the engineer's profile matches the research findings.
    
    This node synthesizes research results with the engineer's skills
    and experience to identify key alignments and gaps.
    """
    thoughts = state["thoughts"].copy()
    thoughts.append("🧠 Analyzing skill and experience alignment...")
    
    # Combine all research
    research_context = f"""
    Company/Position Info: {state.get('company_info', 'N/A')}
    Job Requirements: {state.get('job_requirements', 'N/A')}
    Industry Context: {state.get('industry_context', 'N/A')}
    """
    
    # Get engineer profile
    profile = get_formatted_profile()
    
    # Use skill matcher tool
    skill_analysis = await analyze_skill_match.ainvoke({
        "requirements": research_context,
        "candidate_skills": ENGINEER_PROFILE["skills"],
    })
    thoughts.append("✅ Completed skill alignment analysis")
    
    # Use experience matcher tool
    experience_analysis = await analyze_experience_relevance.ainvoke({
        "context": research_context,
        "experience_summary": ENGINEER_PROFILE["experience_summary"],
    })
    thoughts.append("✅ Completed experience relevance analysis")
    
    # Determine if we have enough info
    has_enough = bool(state.get("company_info") or state.get("job_requirements"))
    
    return {
        **state,
        "thoughts": thoughts,
        "analysis": f"{skill_analysis}\n\n{experience_analysis}",
        "needs_more_research": not has_enough,
        "current_step": state["current_step"] + 1,
    }
```

### 5.4 Response Generation Node

```python
async def generate_response_node(state: FitCheckState) -> FitCheckState:
    """
    Generate the final fit analysis response.
    
    This node uses all gathered information to create a compelling,
    personalized pitch that demonstrates the engineer's fit.
    """
    thoughts = state["thoughts"].copy()
    thoughts.append("✍️ Crafting personalized response...")
    
    # Build context for final generation
    context = f"""
    ## Research Results
    {state.get('company_info', '')}
    {state.get('job_requirements', '')}
    {state.get('industry_context', '')}
    
    ## Analysis
    {state.get('analysis', '')}
    
    ## Engineer Profile
    {get_formatted_profile()}
    """
    
    # Generate final response with streaming
    llm = get_llm()
    
    generation_prompt = f"""
    Based on the research and analysis below, generate a compelling response 
    explaining why this software engineer would be a great fit.
    
    {context}
    
    Follow the response format from your system instructions.
    Be specific, use concrete examples, and maintain a professional tone.
    Keep the response under 400 words.
    """
    
    # This will be streamed to the frontend
    response = await llm.ainvoke(generation_prompt)
    
    return {
        **state,
        "thoughts": thoughts + ["🎉 Response complete!"],
        "analysis": response.content,
        "current_step": state["current_step"] + 1,
    }
```

---

## 6. Graph Construction

```python
# services/fit_check_agent.py

from langgraph.graph import StateGraph, END


def build_fit_check_agent():
    """
    Construct the Fit Check Agent graph.
    
    Graph Structure:
    START → classify → research → analyze → generate → END
                                    ↑          │
                                    └──────────┘ (if needs_more_research)
    """
    
    # Create graph with state schema
    graph = StateGraph(FitCheckState)
    
    # Add nodes
    graph.add_node("classify", classify_query_node)
    graph.add_node("research", research_node)
    graph.add_node("analyze", analysis_node)
    graph.add_node("generate", generate_response_node)
    
    # Add edges
    graph.add_edge("classify", "research")
    graph.add_edge("research", "analyze")
    
    # Conditional edge: loop back if needs more research
    graph.add_conditional_edges(
        "analyze",
        lambda state: "research" if state.get("needs_more_research") else "generate",
        {
            "research": "research",
            "generate": "generate",
        }
    )
    
    graph.add_edge("generate", END)
    
    # Set entry point
    graph.set_entry_point("classify")
    
    # Compile graph
    return graph.compile()


class FitCheckAgent:
    """
    High-level interface for the Fit Check Agent.
    
    Provides streaming execution with callback support.
    """
    
    def __init__(self):
        self.graph = build_fit_check_agent()
    
    async def stream_analysis(
        self,
        query: str,
        include_thoughts: bool = True,
    ):
        """
        Stream the fit analysis execution.
        
        Yields events for:
        - status: Agent status updates
        - thought: AI reasoning steps
        - response: Response text chunks
        
        Args:
            query: The employer's query (company name or job description)
            include_thoughts: Whether to include thinking steps
        
        Yields:
            Dict with "type" and "data" keys
        """
        # Initialize state
        initial_state: FitCheckState = {
            "query": query,
            "query_type": "",
            "company_info": None,
            "job_requirements": None,
            "industry_context": None,
            "engineer_skills": list(ENGINEER_PROFILE["skills"].keys()),
            "engineer_experience": ENGINEER_PROFILE["experience_summary"],
            "engineer_projects": [p["name"] for p in ENGINEER_PROFILE["notable_projects"]],
            "thoughts": [],
            "current_step": 0,
            "analysis": None,
            "confidence": 0.0,
            "needs_more_research": False,
            "error": None,
        }
        
        # Stream graph execution
        async for event in self.graph.astream(initial_state, stream_mode="values"):
            # Emit new thoughts
            if include_thoughts and event.get("thoughts"):
                for thought in event["thoughts"]:
                    if thought not in initial_state.get("thoughts", []):
                        yield {
                            "type": "thought",
                            "data": {
                                "step": event.get("current_step", 0),
                                "type": "reasoning",
                                "content": thought,
                            }
                        }
            
            # Emit status based on current node
            step = event.get("current_step", 0)
            status_map = {
                1: ("researching", "Classifying query..."),
                2: ("researching", "Conducting research..."),
                3: ("analyzing", "Analyzing fit..."),
                4: ("generating", "Generating response..."),
            }
            
            if step in status_map:
                status, message = status_map[step]
                yield {
                    "type": "status",
                    "data": {"status": status, "message": message}
                }
            
            # Update tracked thoughts
            initial_state["thoughts"] = event.get("thoughts", [])
        
        # Emit final response
        if event.get("analysis"):
            # Stream the response in chunks for typewriter effect
            response = event["analysis"]
            chunk_size = 10  # Characters per chunk
            
            for i in range(0, len(response), chunk_size):
                yield {
                    "type": "response",
                    "data": {"chunk": response[i:i + chunk_size]}
                }
```

---

## 7. Tool Implementations

### 7.1 Web Search Tool (Google CSE)

```python
# services/tools/web_search.py

import os
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.tools import tool


# Initialize search wrapper
_cse_api_key = os.getenv("GOOGLE_CSE_API_KEY")
_cse_id = os.getenv("GOOGLE_CSE_ID")

search_wrapper = GoogleSearchAPIWrapper(
    google_api_key=_cse_api_key,
    google_cse_id=_cse_id,
    k=5,  # Return top 5 results
)


@tool
async def web_search(query: str) -> str:
    """
    Search the web for company and job-related information.
    
    Use this tool to research:
    - Company overviews and mission statements
    - Engineering culture and team structure
    - Tech stacks and technologies used
    - Recent news and developments
    - Job postings and requirements
    
    Args:
        query: Search query (be specific for better results)
    
    Returns:
        Formatted search results as text.
    """
    try:
        results = search_wrapper.run(query)
        
        if not results or "No good Google Search Result" in results:
            return f"No results found for '{query}'. Try rephrasing the search."
        
        return results
        
    except Exception as e:
        return f"Search error: {str(e)}. Unable to complete web search."
```

### 7.2 Skill Match Tool

```python
# services/tools/skill_matcher.py

from langchain_core.tools import tool
from src.config import get_llm


@tool
async def analyze_skill_match(requirements: str, candidate_skills: dict) -> str:
    """
    Analyze alignment between requirements and candidate skills.
    
    Args:
        requirements: Text describing company/job requirements
        candidate_skills: Dict of skill categories and skills
    
    Returns:
        Structured analysis of skill matches and gaps.
    """
    llm = get_llm()
    
    skills_text = "\n".join(
        f"- {cat}: {', '.join(skills)}" 
        for cat, skills in candidate_skills.items()
    )
    
    prompt = f"""
    Analyze how well these candidate skills match the requirements:
    
    REQUIREMENTS:
    {requirements[:1500]}
    
    CANDIDATE SKILLS:
    {skills_text}
    
    Provide a brief analysis (max 150 words) of:
    1. Strong matches (skills that directly align)
    2. Transferable skills (adjacent skills that apply)
    3. Growth areas (skills to develop)
    
    Be specific and reference actual skills.
    """
    
    response = await llm.ainvoke(prompt)
    return response.content
```

### 7.3 Experience Relevance Tool

```python
# services/tools/experience_matcher.py

from langchain_core.tools import tool
from src.config import get_llm


@tool
async def analyze_experience_relevance(context: str, experience_summary: str) -> str:
    """
    Analyze how candidate experience relates to target context.
    
    Args:
        context: Company/position context from research
        experience_summary: Candidate's experience summary
    
    Returns:
        Analysis of experience relevance with examples.
    """
    llm = get_llm()
    
    prompt = f"""
    Analyze how this experience relates to the target company/position:
    
    CONTEXT:
    {context[:1500]}
    
    CANDIDATE EXPERIENCE:
    {experience_summary}
    
    Provide a brief analysis (max 150 words) of:
    1. Direct relevance (experience that directly applies)
    2. Transferable lessons (learnings that translate)
    3. Unique perspective (what the candidate brings that's different)
    
    Be specific and cite actual experiences.
    """
    
    response = await llm.ainvoke(prompt)
    return response.content
```

---

## 8. Configuration

### LLM Configuration

```python
# config/llm.py

import os
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory


# Model selection - Using Gemini 3 Pro for state-of-the-art reasoning
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")


def get_llm(streaming: bool = False) -> ChatGoogleGenerativeAI:
    """
    Get configured Gemini LLM instance.
    
    Args:
        streaming: Enable token streaming for responses
    
    Returns:
        Configured ChatGoogleGenerativeAI instance
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=api_key,
        temperature=0.7,  # Slightly creative for engaging responses
        max_retries=3,
        streaming=streaming,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        },
    )
```

---

## 9. Error Handling

```python
# services/fit_check_agent.py

class FitCheckError(Exception):
    """Base exception for Fit Check Agent errors."""
    pass


class ResearchError(FitCheckError):
    """Error during research phase."""
    pass


class AnalysisError(FitCheckError):
    """Error during analysis phase."""
    pass


class GenerationError(FitCheckError):
    """Error during response generation."""
    pass


async def safe_node_execution(node_func, state, error_class):
    """
    Execute a node with error handling.
    
    Args:
        node_func: The node function to execute
        state: Current state
        error_class: Exception class to use for errors
    
    Returns:
        Updated state or state with error
    """
    try:
        return await node_func(state)
    except Exception as e:
        return {
            **state,
            "error": str(e),
            "thoughts": state["thoughts"] + [f"❌ Error: {str(e)}"],
        }
```

---

## 10. Testing Strategy

### Unit Tests

```python
# tests/test_fit_check_agent.py

import pytest
from services.fit_check_agent import FitCheckAgent, classify_query_node, FitCheckState


@pytest.fixture
def initial_state():
    return FitCheckState(
        query="Google",
        query_type="",
        company_info=None,
        job_requirements=None,
        industry_context=None,
        engineer_skills=["Python", "React"],
        engineer_experience="2 years experience",
        engineer_projects=["Project A"],
        thoughts=[],
        current_step=0,
        analysis=None,
        confidence=0.0,
        needs_more_research=False,
        error=None,
    )


@pytest.mark.asyncio
async def test_classify_company_query(initial_state):
    """Test that company names are correctly classified."""
    state = await classify_query_node(initial_state)
    assert state["query_type"] == "company"


@pytest.mark.asyncio
async def test_classify_job_query():
    """Test that job descriptions are correctly classified."""
    state = FitCheckState(
        query="Looking for a senior React developer with 3+ years experience",
        # ... other fields
    )
    result = await classify_query_node(state)
    assert result["query_type"] == "job_position"


@pytest.mark.asyncio
async def test_agent_stream():
    """Test that agent streams events correctly."""
    agent = FitCheckAgent()
    events = []
    
    async for event in agent.stream_analysis("Test Company", include_thoughts=True):
        events.append(event)
    
    # Should have status, thought, and response events
    event_types = [e["type"] for e in events]
    assert "status" in event_types
    assert "response" in event_types
```

### Integration Tests

```python
# tests/test_integration.py

import pytest
from httpx import AsyncClient
from server import app


@pytest.mark.asyncio
async def test_full_flow():
    """Test complete API flow from query to response."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/api/fit-check/stream",
            json={"query": "Google", "include_thoughts": True},
            timeout=60.0,
        ) as response:
            assert response.status_code == 200
            
            events = []
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    events.append(line)
            
            # Verify we got expected event types
            assert any("status" in e for e in events)
            assert any("complete" in e or "response" in e for e in events)
```

---

## 11. Directory Structure Summary

```
res_web_backend/
├── .env                            # Environment variables
├── requirements.txt                # Python dependencies
├── server.py                       # FastAPI application
├── config/
│   ├── __init__.py
│   ├── llm.py                      # LLM configuration
│   └── engineer_profile.py         # Engineer profile data
├── models/
│   ├── __init__.py
│   └── fit_check.py                # Pydantic models
├── routers/
│   ├── __init__.py
│   └── fit_check.py                # API endpoints
├── services/
│   ├── __init__.py
│   ├── fit_check_agent.py          # Main agent implementation
│   └── tools/
│       ├── __init__.py
│       ├── web_search.py           # Google CSE search tool
│       ├── skill_matcher.py        # Skill analysis tool
│       └── experience_matcher.py   # Experience analysis tool
├── prompts/
│   └── fit_check_system.txt        # System prompt
└── tests/
    ├── __init__.py
    ├── test_fit_check_agent.py     # Agent unit tests
    └── test_integration.py         # API integration tests
```

---

## 12. Implementation Checklist

### Phase 1: Core Agent
- [ ] Create state schema (`FitCheckState`)
- [ ] Implement `classify_query_node`
- [ ] Implement `research_node`
- [ ] Implement `analysis_node`
- [ ] Implement `generate_response_node`
- [ ] Build LangGraph graph

### Phase 2: Tools
- [ ] Implement `web_search` tool with Google CSE
- [ ] Implement `analyze_skill_match` tool
- [ ] Implement `analyze_experience_relevance` tool
- [ ] Test tools independently

### Phase 3: Configuration
- [ ] Create engineer profile configuration
- [ ] Create system prompt
- [ ] Set up LLM configuration
- [ ] Configure environment variables

### Phase 4: Streaming
- [ ] Implement `FitCheckAgent.stream_analysis()`
- [ ] Add thought event emission
- [ ] Add status event emission
- [ ] Add response chunking for streaming

### Phase 5: Integration
- [ ] Connect agent to FastAPI router
- [ ] Test end-to-end streaming
- [ ] Add error handling
- [ ] Write unit and integration tests

---

## 13. Performance Considerations

### Latency Optimization
- Use `gemini-3-pro-preview` for state-of-the-art reasoning and response quality
- Limit web search results to top 5
- Implement response caching for repeated queries
- Set reasonable timeouts (30s per node, 90s total)

### Token Optimization
- Truncate research results to 1500 chars per source
- Keep system prompt under 1000 tokens
- Limit final response to 400 words

### Reliability
- Implement retry logic with exponential backoff
- Add circuit breaker for external API calls
- Cache common company research results

---

## Summary

This AI agent provides a sophisticated multi-step research and analysis pipeline that:

1. **Classifies** the employer's query to determine research strategy
2. **Researches** using web search to gather relevant information
3. **Analyzes** skill and experience alignment using specialized tools
4. **Generates** a compelling, personalized response

The agent exposes its thinking process through event streaming, building trust with employers by showing the research and reasoning behind its conclusions. The modular design allows for easy customization of the engineer profile and extension of analysis capabilities.
