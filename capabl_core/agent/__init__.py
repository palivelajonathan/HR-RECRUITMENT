"""
LangChain ReAct Agent module for Recruitment Intelligence Agent.
"""

from capabl_core.agent.react_agent import (
    create_recruitment_agent,
    run_recruitment_agent,
    AgentExecutionResult,
    RECRUITMENT_AGENT_SYSTEM_PROMPT,
)

__all__ = [
    "create_recruitment_agent",
    "run_recruitment_agent",
    "AgentExecutionResult",
    "RECRUITMENT_AGENT_SYSTEM_PROMPT",
]
