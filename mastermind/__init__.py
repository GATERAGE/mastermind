# SPDX-License-Identifier: Apache-2.0
# (c) 2024-2026 GATERAGE — MASTERMIND: Strategic Orchestrator
"""
MASTERMIND — strategic orchestration agent.

The modern agnostic distillation of the orchestrator pattern that runs
inside mindX (`agents/orchestration/mastermind_agent.py`). This package
extracts the reusable primitives — directive intake, planning, execution,
and the agent registry — and ships them as an agnostic Apache-2.0
Python library.

Four primitives:
  - `Directive`     — a typed intent: title + body + priority + deadline
  - `Plan`          — an ordered sequence of steps targeting a directive
  - `AgentRegistry` — pluggable registry of sub-agents the orchestrator can delegate to
  - `Orchestrator`  — the directive → plan → execute loop

Companion repos:
  - github.com/GATERAGE/aglm  — autonomous decision substrate (PODA + beliefs)
  - github.com/GATERAGE/RAGE  — retrieval substrate (memory + grounding)

Together: RAGE remembers, aGLM decides, MASTERMIND orchestrates.

mindX (github.com/agenticplace) is one consumer of these patterns; this repo
is the canonical agnostic home.
"""

from .agent import AgentRegistry, RegisteredAgent
from .directive import Directive, Priority
from .orchestrator import ExecutionResult, Orchestrator
from .plan import Plan, PlanStep, StepStatus

__version__ = "0.1.0"

__all__ = [
    "Directive",
    "Priority",
    "Plan",
    "PlanStep",
    "StepStatus",
    "AgentRegistry",
    "RegisteredAgent",
    "Orchestrator",
    "ExecutionResult",
    "__version__",
]
