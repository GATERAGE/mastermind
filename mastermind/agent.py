# SPDX-License-Identifier: Apache-2.0
# (c) 2024-2026 GATERAGE — MASTERMIND
"""
AgentRegistry — pluggable registry of sub-agents the orchestrator can delegate to.

Each registered agent exposes:
  - `agent_id: str` — unique stable id
  - `actions: Iterable[str]` — what action names the agent answers to
  - `execute(action, args) -> Awaitable[dict]` — runs an action

Distilled from mindX `agents/orchestration/coordinator_agent.py` agent map.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Set

logger = logging.getLogger("mastermind.agent")

# An agent's execute callable: takes (action_name, args) and returns an outcome dict.
ExecuteFn = Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]


@dataclass
class RegisteredAgent:
    """A sub-agent the orchestrator can delegate to."""

    agent_id: str
    description: str
    actions: Set[str]
    execute: ExecuteFn

    def handles(self, action: str) -> bool:
        return action in self.actions or "*" in self.actions


class AgentRegistry:
    """In-memory agent registry. Multiple agents may handle the same action;
    the orchestrator picks the first by default (override in subclass for
    capability-weighted routing).
    """

    def __init__(self) -> None:
        self._agents: Dict[str, RegisteredAgent] = {}

    def register(
        self,
        agent_id: str,
        execute: ExecuteFn,
        actions: Iterable[str],
        description: str = "",
    ) -> RegisteredAgent:
        if agent_id in self._agents:
            raise ValueError(f"Agent '{agent_id}' already registered")
        agent = RegisteredAgent(
            agent_id=agent_id,
            description=description,
            actions=set(actions),
            execute=execute,
        )
        self._agents[agent_id] = agent
        logger.info(f"Registered agent '{agent_id}' for actions: {sorted(agent.actions)}")
        return agent

    def unregister(self, agent_id: str) -> bool:
        if agent_id not in self._agents:
            return False
        del self._agents[agent_id]
        return True

    def get(self, agent_id: str) -> Optional[RegisteredAgent]:
        return self._agents.get(agent_id)

    def find_for_action(self, action: str) -> List[RegisteredAgent]:
        """Return all agents that handle the named action."""
        return [a for a in self._agents.values() if a.handles(action)]

    def pick_for_action(self, action: str) -> Optional[RegisteredAgent]:
        """Return the first agent that handles the named action, or None."""
        for a in self._agents.values():
            if a.handles(action):
                return a
        return None

    def list(self) -> List[RegisteredAgent]:
        return list(self._agents.values())

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        return agent_id in self._agents
