"""
Fit Check Agent - LangGraph-based AI Agent for Employer Fit Analysis.

This module implements a ReAct (Reasoning + Acting) agent that:
1. Classifies employer queries (company name vs. job description)
2. Researches using web search and analysis tools
3. Generates personalized fit analysis responses
4. Streams thinking process and responses via callbacks
"""

import logging
import os
from pathlib import Path
from typing import TypedDict, Annotated, Optional, List, Any, AsyncGenerator, Callable

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from config.llm import get_llm
from config.engineer_profile import get_formatted_profile
from services.tools.web_search import web_search
from services.tools.skill_matcher import analyze_skill_match
from services.tools.experience_matcher import analyze_experience_relevance

logger = logging.getLogger(__name__)


# =============================================================================
# State Definition
# =============================================================================

class FitCheckState(TypedDict):
    """
    State definition for the Fit Check Agent.
    
    Attributes:
        messages: Conversation history with tool calls and responses
        query: Original user query (company name or job description)
        query_type: Classified type ('company' or 'job_position')
        research_results: Accumulated research findings
        skill_analysis: Results from skill matching
        experience_analysis: Results from experience matching
        step_count: Current step number for thought tracking
        final_response: Generated final response
        error: Error message if failed
    """
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    query_type: Optional[str]
    research_results: Optional[str]
    skill_analysis: Optional[str]
    experience_analysis: Optional[str]
    step_count: int
    final_response: Optional[str]
    error: Optional[str]


# =============================================================================
# System Prompt Loading
# =============================================================================

def load_system_prompt() -> str:
    """
    Load and format the system prompt with engineer profile.
    
    Returns:
        str: Formatted system prompt.
    """
    # Load prompt template
    prompt_path = Path(__file__).parent.parent / "prompts" / "fit_check_system.txt"
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        logger.warning(f"System prompt not found at {prompt_path}, using default")
        prompt_template = """You are a helpful career advisor analyzing fit between a software engineer and potential employers.
        
## ENGINEER PROFILE
{engineer_profile}

Analyze the employer's query and provide a personalized fit analysis. Use the available tools to research and analyze.
Keep your response under 400 words."""
    
    # Inject engineer profile
    engineer_profile = get_formatted_profile()
    return prompt_template.format(engineer_profile=engineer_profile)


# =============================================================================
# Agent Tools
# =============================================================================

# Tools available to the agent
AGENT_TOOLS = [web_search, analyze_skill_match, analyze_experience_relevance]


# =============================================================================
# Callback Types for Streaming
# =============================================================================

class ThoughtCallback:
    """
    Callback interface for streaming agent thoughts.
    
    Implement this to receive real-time updates about agent progress.
    """
    
    async def on_status(self, status: str, message: str) -> None:
        """Called when agent status changes."""
        pass
    
    async def on_thought(
        self,
        step: int,
        thought_type: str,
        content: str,
        tool: Optional[str] = None,
        tool_input: Optional[str] = None,
    ) -> None:
        """Called when agent has a thought (tool_call, observation, or reasoning)."""
        pass
    
    async def on_response_chunk(self, chunk: str) -> None:
        """Called when streaming response text."""
        pass
    
    async def on_complete(self, duration_ms: int) -> None:
        """Called when agent completes."""
        pass
    
    async def on_error(self, code: str, message: str) -> None:
        """Called when an error occurs."""
        pass


# =============================================================================
# Agent Node Functions
# =============================================================================

def should_continue(state: FitCheckState) -> str:
    """
    Determine if the agent should continue processing or end.
    
    Args:
        state: Current agent state.
    
    Returns:
        str: Next node to execute ('tools', 'respond', or END).
    """
    messages = state.get("messages", [])
    
    if not messages:
        return END
    
    last_message = messages[-1]
    
    # If there's an error, end
    if state.get("error"):
        return END
    
    # If the LLM made tool calls, execute them
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # Otherwise, the agent is done
    return END


async def agent_node(
    state: FitCheckState,
    callback: Optional[ThoughtCallback] = None,
) -> FitCheckState:
    """
    Main agent reasoning node.
    
    Invokes the LLM to reason about the query and potentially call tools.
    
    Args:
        state: Current agent state.
        callback: Optional callback for streaming thoughts.
    
    Returns:
        Updated state with new messages.
    """
    logger.info("Agent node executing")
    
    # Get LLM with tools bound
    llm = get_llm(streaming=False)
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)
    
    # Load system prompt
    system_prompt = load_system_prompt()
    
    # Build messages
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(state.get("messages", []))
    
    # Emit status
    if callback:
        step = state.get("step_count", 0)
        if step == 0:
            await callback.on_status("researching", "Analyzing your query...")
        else:
            await callback.on_status("analyzing", "Processing research results...")
    
    try:
        # Invoke LLM
        response = await llm_with_tools.ainvoke(messages)
        
        # Emit reasoning thought if there's content before tool calls
        if callback and response.content and not response.tool_calls:
            step = state.get("step_count", 0) + 1
            await callback.on_thought(
                step=step,
                thought_type="reasoning",
                content=response.content[:500],  # Truncate for display
            )
        
        # Track tool calls for thought emission
        if callback and response.tool_calls:
            step = state.get("step_count", 0) + 1
            for tool_call in response.tool_calls:
                await callback.on_thought(
                    step=step,
                    thought_type="tool_call",
                    content=f"Calling {tool_call['name']}",
                    tool=tool_call["name"],
                    tool_input=str(tool_call.get("args", {})),
                )
                step += 1
        
        return {
            "messages": [response],
            "step_count": state.get("step_count", 0) + len(response.tool_calls or [1]),
        }
        
    except Exception as e:
        logger.error(f"Agent node error: {e}")
        if callback:
            await callback.on_error("AGENT_ERROR", str(e))
        return {"error": str(e)}


async def tool_node(
    state: FitCheckState,
    callback: Optional[ThoughtCallback] = None,
) -> FitCheckState:
    """
    Execute tool calls from the agent.
    
    Args:
        state: Current agent state.
        callback: Optional callback for streaming observations.
    
    Returns:
        Updated state with tool results.
    """
    logger.info("Tool node executing")
    
    messages = state.get("messages", [])
    if not messages:
        return state
    
    last_message = messages[-1]
    
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return state
    
    # Execute tools
    tool_node_executor = ToolNode(tools=AGENT_TOOLS)
    
    try:
        result = await tool_node_executor.ainvoke(state)
        new_messages = result.get("messages", [])
        
        # Emit observations
        if callback and new_messages:
            step = state.get("step_count", 0) + 1
            for msg in new_messages:
                content = msg.content if hasattr(msg, "content") else str(msg)
                # Truncate long observations
                display_content = content[:500] + "..." if len(content) > 500 else content
                await callback.on_thought(
                    step=step,
                    thought_type="observation",
                    content=display_content,
                )
                step += 1
        
        return {
            "messages": new_messages,
            "step_count": state.get("step_count", 0) + len(new_messages),
        }
        
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        if callback:
            await callback.on_error("SEARCH_ERROR", f"Tool execution failed: {str(e)}")
        return {"error": str(e)}


# =============================================================================
# Agent Builder
# =============================================================================

def build_fit_check_graph():
    """
    Build the LangGraph state machine for the Fit Check Agent.
    
    Returns:
        Compiled LangGraph ready for execution.
    """
    # Create the graph
    workflow = StateGraph(FitCheckState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )
    
    # Tools always go back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    return workflow.compile()


# =============================================================================
# FitCheckAgent Class
# =============================================================================

class FitCheckAgent:
    """
    High-level interface for the Fit Check Agent.
    
    Provides methods to run analysis with or without streaming.
    """
    
    def __init__(self):
        """Initialize the agent with compiled graph."""
        self._graph = None
    
    @property
    def graph(self):
        """Lazily build and cache the graph."""
        if self._graph is None:
            self._graph = build_fit_check_graph()
        return self._graph
    
    def _create_initial_state(self, query: str) -> FitCheckState:
        """
        Create initial state for a new query.
        
        Args:
            query: User's query (company name or job description).
        
        Returns:
            Initial agent state.
        """
        return FitCheckState(
            messages=[HumanMessage(content=query)],
            query=query,
            query_type=None,
            research_results=None,
            skill_analysis=None,
            experience_analysis=None,
            step_count=0,
            final_response=None,
            error=None,
        )
    
    async def analyze(self, query: str) -> str:
        """
        Run fit analysis without streaming.
        
        Args:
            query: Company name or job description.
        
        Returns:
            str: Final analysis response.
        
        Raises:
            Exception: If analysis fails.
        """
        logger.info(f"Starting analysis for query: {query[:50]}...")
        
        initial_state = self._create_initial_state(query)
        
        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        # Check for errors
        if final_state.get("error"):
            raise Exception(final_state["error"])
        
        # Extract final response
        messages = final_state.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                return last_message.content
        
        return "Unable to generate analysis. Please try again."
    
    async def stream_analysis(
        self,
        query: str,
        callback: ThoughtCallback,
    ) -> AsyncGenerator[str, None]:
        """
        Run fit analysis with streaming thoughts and response.
        
        This method streams the agent's thinking process in real-time
        via the callback, while yielding response chunks.
        
        Args:
            query: Company name or job description.
            callback: Callback for receiving thoughts and status updates.
        
        Yields:
            str: Response text chunks.
        
        Raises:
            Exception: If analysis fails.
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting streaming analysis for query: {query[:50]}...")
        
        # Emit initial status
        await callback.on_status("connecting", "Initializing AI agent...")
        
        initial_state = self._create_initial_state(query)
        
        try:
            # Stream through the graph
            current_state = initial_state
            
            async for event in self.graph.astream(current_state):
                # Process events
                for node_name, node_output in event.items():
                    if node_name == "agent":
                        messages = node_output.get("messages", [])
                        if messages:
                            last_msg = messages[-1]
                            # Check if this is tool calls
                            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                                step = node_output.get("step_count", 1)
                                for tool_call in last_msg.tool_calls:
                                    await callback.on_thought(
                                        step=step,
                                        thought_type="tool_call",
                                        content=f"Calling {tool_call['name']}",
                                        tool=tool_call["name"],
                                        tool_input=str(tool_call.get("args", {})),
                                    )
                                    step += 1
                            # Final response
                            elif hasattr(last_msg, "content") and last_msg.content:
                                await callback.on_status("generating", "Generating response...")
                                # Stream response in chunks
                                content = last_msg.content
                                # Handle Gemini's structured content format
                                # Content can be a list of dicts like [{"type": "text", "text": "..."}]
                                if isinstance(content, list):
                                    text_parts = []
                                    for part in content:
                                        if isinstance(part, dict) and part.get("type") == "text":
                                            text_parts.append(part.get("text", ""))
                                        elif isinstance(part, str):
                                            text_parts.append(part)
                                    content = "".join(text_parts)
                                elif not isinstance(content, str):
                                    content = str(content)
                                
                                chunk_size = 50
                                for i in range(0, len(content), chunk_size):
                                    chunk = content[i:i + chunk_size]
                                    await callback.on_response_chunk(chunk)
                                    yield chunk
                    
                    elif node_name == "tools":
                        messages = node_output.get("messages", [])
                        step = node_output.get("step_count", 1)
                        for msg in messages:
                            content = msg.content if hasattr(msg, "content") else str(msg)
                            display_content = content[:500] + "..." if len(content) > 500 else content
                            await callback.on_thought(
                                step=step,
                                thought_type="observation",
                                content=display_content,
                            )
                            step += 1
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            await callback.on_complete(duration_ms)
            
        except Exception as e:
            logger.error(f"Streaming analysis error: {e}")
            await callback.on_error("AGENT_ERROR", str(e))
            raise


# =============================================================================
# Singleton Instance
# =============================================================================

_agent_instance: Optional[FitCheckAgent] = None


def get_agent() -> FitCheckAgent:
    """
    Get or create the singleton FitCheckAgent instance.
    
    Returns:
        FitCheckAgent: The agent instance.
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = FitCheckAgent()
    return _agent_instance
