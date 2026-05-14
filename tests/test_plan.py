# SPDX-License-Identifier: Apache-2.0
"""Smoke tests for Plan + PlanStep."""
from __future__ import annotations

from mastermind import Plan, PlanStep, StepStatus


def test_plan_starts_pending():
    p = Plan(directive_id="dir-x")
    p.add_step(PlanStep(description="step1", agent_id="a", action="x"))
    p.add_step(PlanStep(description="step2", agent_id="b", action="y"))
    assert p.status == StepStatus.PENDING


def test_plan_status_success_when_all_done():
    p = Plan(directive_id="dir-x")
    s1 = PlanStep(description="step1", agent_id="a", action="x")
    s2 = PlanStep(description="step2", agent_id="b", action="y")
    p.add_step(s1).add_step(s2)
    s1.mark(StepStatus.SUCCESS, {"ok": True})
    s2.mark(StepStatus.SUCCESS, {"ok": True})
    assert p.status == StepStatus.SUCCESS


def test_plan_status_failed_when_any_step_fails():
    p = Plan(directive_id="dir-x")
    s1 = PlanStep(description="step1", agent_id="a", action="x")
    s2 = PlanStep(description="step2", agent_id="b", action="y")
    p.add_step(s1).add_step(s2)
    s1.mark(StepStatus.SUCCESS)
    s2.mark(StepStatus.FAILED, {"error": "boom"})
    assert p.status == StepStatus.FAILED


def test_plan_serialization():
    p = Plan(directive_id="dir-x")
    p.add_step(PlanStep(description="d", agent_id="a", action="x", args={"k": 1}))
    data = p.to_dict()
    assert data["directive_id"] == "dir-x"
    assert len(data["steps"]) == 1
    assert data["steps"][0]["args"] == {"k": 1}
