# SPDX-License-Identifier: Apache-2.0
"""
Quick-start for MASTERMIND. Registers two trivial agents, issues a directive,
walks it through plan → execute, prints the result.

    pip install -e .
    python examples/quickstart.py
"""
from __future__ import annotations

import asyncio

from mastermind import AgentRegistry, Directive, Orchestrator, Plan, PlanStep


async def echo_exec(action, args):
    print(f"  echo.agent runs {action!r} with {args}")
    return {"success": True, "echoed": args}


async def announce_exec(action, args):
    print(f"  announcer publishes: {args.get('message', '(no message)')}")
    return {"success": True}


async def two_step_planner(directive, registry):
    """A planner that builds a two-step plan from a directive."""
    p = Plan(directive_id=directive.directive_id)
    p.add_step(PlanStep(
        description="echo the directive body",
        agent_id="echo.agent",
        action="echo",
        args={"body": directive.body},
    ))
    p.add_step(PlanStep(
        description="announce completion",
        agent_id="announcer",
        action="announce",
        args={"message": f"Directive '{directive.title}' completed"},
    ))
    return p


async def main():
    registry = AgentRegistry()
    registry.register("echo.agent", echo_exec, actions={"echo"})
    registry.register("announcer", announce_exec, actions={"announce"})

    orch = Orchestrator(registry=registry, planner=two_step_planner)
    result = await orch.handle(Directive(
        title="hello world",
        body="MASTERMIND, hear me roar.",
    ))
    print()
    print(f"status: {result.status.value}")
    print(f"duration: {result.completed_at - result.started_at:.3f}s")


if __name__ == "__main__":
    asyncio.run(main())
