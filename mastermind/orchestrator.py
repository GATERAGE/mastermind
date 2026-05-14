# SPDX-License-Identifier: Apache-2.0
# (c) 2024-2026 GATERAGE — MASTERMIND
"""
Orchestrator — the directive → plan → execute loop.

Distilled from mindX `agents/orchestration/mastermind_agent.py`.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .agent import AgentRegistry
from .directive import Directive
from .plan import Plan, PlanStep, StepStatus

logger = logging.getLogger("mastermind.orchestrator")

# A Planner takes a directive + registry and returns a plan.
Planner = Callable[[Directive, AgentRegistry], Awaitable[Plan]]


@dataclass
class ExecutionResult:
    """The outcome of running a plan."""

    plan_id: str
    directive_id: str
    status: StepStatus
    started_at: float
    completed_at: float
    step_outcomes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "directive_id": self.directive_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.completed_at - self.started_at,
            "step_outcomes": self.step_outcomes,
        }


async def default_planner(directive: Directive, registry: AgentRegistry) -> Plan:
    """
    A trivial single-step planner: maps the directive title (lowercased) to an
    action name and finds an agent that handles it. Real consumers override this
    (LLM-backed planning, rule-based, etc.) — pass your own `Planner` to
    `Orchestrator(planner=...)`.
    """
    action_name = directive.title.lower().strip().replace(" ", "_")
    agent = registry.pick_for_action(action_name) or registry.pick_for_action("*")
    plan = Plan(directive_id=directive.directive_id)
    if agent:
        plan.add_step(PlanStep(
            description=directive.title,
            agent_id=agent.agent_id,
            action=action_name,
            args=dict(directive.metadata),
        ))
    return plan


class Orchestrator:
    """
    The strategic orchestrator. Accepts directives, builds plans via a Planner,
    and executes each plan step-by-step (with optional parallel groups).

    Example:
        registry = AgentRegistry()
        registry.register(
            agent_id="logger",
            execute=async_fn,
            actions={"log"},
            description="writes to the journal",
        )

        orch = Orchestrator(registry=registry, planner=default_planner)
        result = await orch.handle(Directive(title="log", body="hello"))
        print(result.status)  # StepStatus.SUCCESS
    """

    def __init__(
        self,
        registry: AgentRegistry,
        planner: Optional[Planner] = None,
    ):
        self.registry = registry
        self.planner: Planner = planner or default_planner
        self._directives: Dict[str, Directive] = {}
        self._plans: Dict[str, Plan] = {}
        self._history: List[ExecutionResult] = []

    async def handle(self, directive: Directive) -> ExecutionResult:
        """End-to-end: intake → plan → execute → return result."""
        self._directives[directive.directive_id] = directive
        logger.info(
            f"Received directive '{directive.directive_id}' "
            f"({directive.priority.value}): {directive.title}"
        )

        # Plan
        plan = await self.planner(directive, self.registry)
        self._plans[plan.plan_id] = plan

        # Execute
        started_at = time.time()
        await self._execute_plan(plan)
        completed_at = time.time()

        result = ExecutionResult(
            plan_id=plan.plan_id,
            directive_id=directive.directive_id,
            status=plan.status,
            started_at=started_at,
            completed_at=completed_at,
            step_outcomes=[
                {
                    "step_id": s.step_id,
                    "description": s.description,
                    "agent_id": s.agent_id,
                    "action": s.action,
                    "status": s.status.value,
                    "outcome": s.outcome,
                }
                for s in plan.steps
            ],
        )
        self._history.append(result)
        return result

    async def _execute_plan(self, plan: Plan) -> None:
        """Walk the plan steps, executing serially or in parallel groups."""
        # Group steps by parallel_group; None-group runs serially in order.
        groups: Dict[Optional[str], List[PlanStep]] = {}
        for step in plan.steps:
            groups.setdefault(step.parallel_group, []).append(step)

        # Serial group first (order preserved), then any parallel groups.
        if None in groups:
            for step in groups[None]:
                await self._execute_step(step)

        for gname, gsteps in groups.items():
            if gname is None:
                continue
            await asyncio.gather(*(self._execute_step(s) for s in gsteps))

    async def _execute_step(self, step: PlanStep) -> None:
        """Execute a single step by delegating to the registered agent."""
        agent = self.registry.get(step.agent_id)
        if agent is None:
            step.mark(StepStatus.FAILED, {"error": f"agent '{step.agent_id}' not registered"})
            return
        step.mark(StepStatus.RUNNING)
        try:
            outcome = await agent.execute(step.action, step.args)
            if outcome.get("success", True):
                step.mark(StepStatus.SUCCESS, outcome)
            else:
                step.mark(StepStatus.FAILED, outcome)
        except Exception as e:
            step.mark(StepStatus.FAILED, {"error": str(e), "exception": type(e).__name__})
            logger.warning(f"step {step.step_id} raised: {e}")

    @property
    def directive_count(self) -> int:
        return len(self._directives)

    @property
    def plan_count(self) -> int:
        return len(self._plans)

    def history(self, limit: int = 50) -> List[ExecutionResult]:
        """Recent execution results, newest first."""
        return list(reversed(self._history[-limit:]))

    def status(self) -> Dict[str, Any]:
        return {
            "directives_seen": len(self._directives),
            "plans_built": len(self._plans),
            "executions_completed": len(self._history),
            "agents_registered": len(self.registry),
        }
