from typing import Any
from app.core.logging_config import logger


class BaseAgent:
    """Abstract base for all pipeline agents."""

    def __init__(self, name: str):
        """Initialise the agent with a human-readable name.

        Args:
            name: Unique identifier for this agent.
        """
        self.name = name

    async def execute(self, state: dict) -> dict:
        """Execute the agent's core logic against the current pipeline state.

        Args:
            state: Pipeline state dictionary.

        Returns:
            Updated state fragment.

        Raises:
            NotImplementedError: Must be overridden by subclasses.
        """
        raise NotImplementedError


class AgentRegistry:
    """Thread-safe registry of named agents."""

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register a new agent.

        Args:
            agent: Agent instance to register.
        """
        self._agents[agent.name] = agent
        logger.info("agent_registered", name=agent.name)

    def get(self, name: str) -> BaseAgent | None:
        """Retrieve a registered agent by name.

        Args:
            name: Agent name.

        Returns:
            The agent, or None if not found.
        """
        return self._agents.get(name)

    def list(self) -> list[str]:
        """Return the names of all registered agents.

        Returns:
            Sorted list of agent names.
        """
        return sorted(self._agents.keys())


# Global singleton registry shared across the application.
agent_registry = AgentRegistry()
