# SPDX-License-Identifier: Apache-2.0
"""Smoke tests for the Orchestrator's directive → plan → execute loop."""
from __future__ import annotations

import pytest

from mastermind import (
    AgentRegistry,
    Directive,
    Orchestrator,
    Plan,
    PlanStep,
    StepStatus,
)


@pytest.mark.asyncio
async def test_default_planner_one_step_happy_path():
    calls = []

    async def echo_exec(action, args):
        calls.append((action, args))
        return {"success": True, "echoed": args}

    reg = AgentRegistry()
    reg.register("echo.agent", echo_exec, actions={"ship_release"}, description="ships")

    orch = Orchestrator(registry=reg)
    result = await orch.handle(Directive(title="ship release", metadata={"version": "1.0"}))

    assert result.status == StepStatus.SUCCESS
    assert len(result.step_outcomes) == 1
    assert calls == [("ship_release", {"version": "1.0"})]


@pytest.mark.asyncio
async def test_default_planner_no_matching_agent_yields_empty_plan():
    reg = AgentRegistry()
    orch = Orchestrator(registry=reg)
    result = await orch.handle(Directive(title="something nobody handles"))
    # Empty plan → status is PENDING (no steps to fail)
    assert result.status == StepStatus.PENDING
    assert len(result.step_outcomes) == 0


@pytest.mark.asyncio
async def test_step_failure_marks_plan_failed():
    async def failing_exec(action, args):
        return {"success": False, "error": "intentional"}

    reg = AgentRegistry()
    reg.register("bad.agent", failing_exec, actions={"do_thing"})
    orch = Orchestrator(registry=reg)
    result = await orch.handle(Directive(title="do thing"))
    assert result.status == StepStatus.FAILED
    assert result.step_outcomes[0]["outcome"]["error"] == "intentional"


@pytest.mark.asyncio
async def test_step_raises_is_captured():
    async def raises_exec(action, args):
        raise RuntimeError("boom")

    reg = AgentRegistry()
    reg.register("crashy.agent", raises_exec, actions={"crash"})
    orch = Orchestrator(registry=reg)
    result = await orch.handle(Directive(title="crash"))
    assert result.status == StepStatus.FAILED
    assert "boom" in result.step_outcomes[0]["outcome"]["error"]


@pytest.mark.asyncio
async def test_custom_planner_with_parallel_steps():
    seen = []

    async def exec_a(action, args):
        seen.append(("a", action))
        return {"success": True}

    async def exec_b(action, args):
        seen.append(("b", action))
        return {"success": True}

    reg = AgentRegistry()
    reg.register("a", exec_a, actions={"alpha"})
    reg.register("b", exec_b, actions={"beta"})

    async def parallel_planner(directive, registry):
        p = Plan(directive_id=directive.directive_id)
        p.add_step(PlanStep("first",  agent_id="a", action="alpha", parallel_group="g1"))
        p.add_step(PlanStep("second", agent_id="b", action="beta",  parallel_group="g1"))
        return p

    orch = Orchestrator(registry=reg, planner=parallel_planner)
    result = await orch.handle(Directive(title="multi"))
    assert result.status == StepStatus.SUCCESS
    assert len(seen) == 2


@pytest.mark.asyncio
async def test_status_counts():
    async def x(action, args): return {"success": True}
    reg = AgentRegistry()
    reg.register("ag", x, {"act"})
    orch = Orchestrator(registry=reg)
    await orch.handle(Directive(title="act"))
    await orch.handle(Directive(title="act"))
    s = orch.status()
    assert s["directives_seen"] == 2
    assert s["plans_built"] == 2
    assert s["executions_completed"] == 2
