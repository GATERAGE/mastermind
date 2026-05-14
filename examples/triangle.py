# SPDX-License-Identifier: Apache-2.0
"""
The full RAGE + aGLM + MASTERMIND triangle, sketched.

    pip install -e ".[aglm,rage]"
    python examples/triangle.py

This example wires:
  - MASTERMIND.Orchestrator   accepts a directive
  - aGLM.AGLMCore             runs the decision loop inside the executor agent
  - RAGE.RetrievalEngine      provides context to the decider

The example uses stubs where the real RAGE / aGLM aren't installed.
"""
from __future__ import annotations

import asyncio

from mastermind import AgentRegistry, Directive, Orchestrator, Plan, PlanStep


async def aglm_agent_exec(action, args):
    """
    Stand-in for an agent that wraps `aglm.AGLMCore`. The real one would:
      - perceive(): query RAGE for context relevant to args
      - decide(): pick an action using context + beliefs (LLM optional)
      - act(): execute and return outcome
    """
    print(f"  aglm.agent: running '{action}' over {args}")
    return {"success": True, "summary": f"completed {action}"}


async def directive_planner(directive, registry):
    p = Plan(directive_id=directive.directive_id)
    p.add_step(PlanStep(
        description="run the aGLM cycle for this directive",
        agent_id="aglm.agent",
        action="cycle",
        args={"context": directive.body},
    ))
    return p


async def main():
    registry = AgentRegistry()
    registry.register("aglm.agent", aglm_agent_exec, actions={"cycle"})

    orch = Orchestrator(registry=registry, planner=directive_planner)
    result = await orch.handle(Directive(
        title="evaluate proposal",
        body="Should we onboard a new training pipeline?",
    ))
    print()
    print(f"directive result: {result.status.value}")
    for s in result.step_outcomes:
        print(f"  - {s['description']}: {s['status']}  outcome={s['outcome']}")


if __name__ == "__main__":
    asyncio.run(main())
