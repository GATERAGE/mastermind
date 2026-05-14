# SPDX-License-Identifier: Apache-2.0
"""Smoke tests for AgentRegistry."""
from __future__ import annotations

import pytest

from mastermind import AgentRegistry


@pytest.mark.asyncio
async def test_register_and_find():
    async def echo_exec(action, args):
        return {"success": True, "echoed": args}

    reg = AgentRegistry()
    reg.register("echo.agent", echo_exec, actions={"echo", "ping"}, description="echo demo")

    a = reg.get("echo.agent")
    assert a is not None
    assert a.handles("echo") is True
    assert a.handles("unknown") is False

    found = reg.find_for_action("ping")
    assert len(found) == 1
    assert found[0].agent_id == "echo.agent"


def test_duplicate_registration_raises():
    reg = AgentRegistry()
    async def x(action, args): return {}
    reg.register("a1", x, {"x"})
    with pytest.raises(ValueError):
        reg.register("a1", x, {"y"})


def test_wildcard_action():
    async def catchall(action, args): return {"success": True}
    reg = AgentRegistry()
    reg.register("catchall", catchall, {"*"})
    a = reg.pick_for_action("anything")
    assert a is not None
    assert a.agent_id == "catchall"


def test_unregister():
    async def x(action, args): return {}
    reg = AgentRegistry()
    reg.register("a", x, {"x"})
    assert "a" in reg
    assert reg.unregister("a") is True
    assert "a" not in reg
    assert reg.unregister("a") is False
