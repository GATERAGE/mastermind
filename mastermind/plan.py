# SPDX-License-Identifier: Apache-2.0
# (c) 2024-2026 GATERAGE — MASTERMIND
"""
Plan — an ordered sequence of steps that, when executed, satisfies a directive.

Distilled from mindX `agents/orchestration/mastermind_agent.py:_build_plan()`.
A Plan is just a typed list of PlanStep; the orchestrator walks it in order
(serial) or in groups (parallel via step.parallel_group).
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """One step in a plan: delegate to an agent + check the outcome."""

    description: str
    agent_id: str          # which agent in the registry executes this step
    action: str            # the action name the agent should run
    args: Dict[str, Any] = field(default_factory=dict)
    step_id: str = field(default_factory=lambda: f"step-{uuid.uuid4().hex[:8]}")
    status: StepStatus = StepStatus.PENDING
    outcome: Optional[Dict[str, Any]] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    parallel_group: Optional[str] = None  # steps in the same group run concurrently

    def mark(self, status: StepStatus, outcome: Optional[Dict[str, Any]] = None) -> None:
        self.status = status
        if status == StepStatus.RUNNING:
            self.started_at = time.time()
        if status in (StepStatus.SUCCESS, StepStatus.FAILED, StepStatus.SKIPPED):
            self.completed_at = time.time()
        if outcome is not None:
            self.outcome = outcome


@dataclass
class Plan:
    """An ordered sequence of PlanSteps targeting a single directive."""

    directive_id: str
    steps: List[PlanStep] = field(default_factory=list)
    plan_id: str = field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:10]}")
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: PlanStep) -> "Plan":
        self.steps.append(step)
        return self

    @property
    def status(self) -> StepStatus:
        """Overall plan status — failed if any step failed; success if all done; pending otherwise."""
        if any(s.status == StepStatus.FAILED for s in self.steps):
            return StepStatus.FAILED
        if self.steps and all(
            s.status in (StepStatus.SUCCESS, StepStatus.SKIPPED) for s in self.steps
        ):
            return StepStatus.SUCCESS
        if any(s.status == StepStatus.RUNNING for s in self.steps):
            return StepStatus.RUNNING
        return StepStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "directive_id": self.directive_id,
            "created_at": self.created_at,
            "status": self.status.value,
            "metadata": self.metadata,
            "steps": [
                {
                    "step_id": s.step_id,
                    "description": s.description,
                    "agent_id": s.agent_id,
                    "action": s.action,
                    "args": s.args,
                    "status": s.status.value,
                    "outcome": s.outcome,
                    "started_at": s.started_at,
                    "completed_at": s.completed_at,
                    "parallel_group": s.parallel_group,
                }
                for s in self.steps
            ],
        }
