# MASTERMIND

**Strategic orchestration agent. Directive → plan → execute loop for autonomous multi-agent systems.**

The modern agnostic distillation of the orchestrator pattern that runs inside [mindX](https://github.com/agenticplace) (`agents/orchestration/mastermind_agent.py`). Mirrored here as a clean Apache-2.0 Python distribution.

> *RAGE remembers, aGLM decides, MASTERMIND orchestrates.*

## Install

```bash
pip install .                  # core only — no LLM/retrieval deps
pip install ".[aglm]"          # with github.com/GATERAGE/aglm  (autonomous decision substrate)
pip install ".[rage]"          # with github.com/GATERAGE/RAGE  (retrieval substrate)
pip install ".[dev]"           # pytest + ruff
```

## Quick use

```python
import asyncio
from mastermind import AgentRegistry, Directive, Orchestrator, Plan, PlanStep

async def echo_exec(action, args):
    print(f"  echo.agent runs {action!r}")
    return {"success": True, "echoed": args}

async def two_step_planner(directive, registry):
    p = Plan(directive_id=directive.directive_id)
    p.add_step(PlanStep("echo body", agent_id="echo.agent", action="echo",
                       args={"body": directive.body}))
    return p

async def main():
    registry = AgentRegistry()
    registry.register("echo.agent", echo_exec, actions={"echo"})
    orch = Orchestrator(registry=registry, planner=two_step_planner)
    result = await orch.handle(Directive(title="hello", body="hi there"))
    print("status:", result.status.value)

asyncio.run(main())
```

## Four primitives

| Module | Class | Responsibility |
|---|---|---|
| `mastermind/directive.py` | `Directive` | typed intent: title, body, priority, deadline, principal |
| `mastermind/plan.py` | `Plan`, `PlanStep` | ordered sequence of steps (with parallel groups) |
| `mastermind/agent.py` | `AgentRegistry`, `RegisteredAgent` | pluggable registry of sub-agents |
| `mastermind/orchestrator.py` | `Orchestrator`, `ExecutionResult` | directive → plan → execute loop |

## The triangle

```
                  ┌──────────────────┐
                  │   MASTERMIND     │  (this repo)
                  │  Orchestrator    │
                  └────────┬─────────┘
                           │ delegates to
                           ▼
            ┌──────────────────────────────┐
            │             aGLM             │  github.com/GATERAGE/aglm
            │   Perceive-Orient-Decide-Act │
            └─────────┬────────────────────┘
                      │ retrieves context via
                      ▼
            ┌──────────────────────────────┐
            │              RAGE            │  github.com/GATERAGE/RAGE
            │   Ingestion + Retrieval      │
            └──────────────────────────────┘
```

Together they form the substrate mindX runs in production. Each repo is independently installable; adopt any subset.

## Tests

```bash
pip install ".[dev]"
pytest -v
```

## Examples

- `examples/quickstart.py` — two-agent walkthrough
- `examples/triangle.py` — full RAGE + aGLM + MASTERMIND wiring

## Spec

[`docs/mastermind_as_a_service.md`](docs/mastermind_as_a_service.md) — canonical contract for what MASTERMIND offers as a primitive.

## Background

Project lineage: the MASTERMIND concept originates from the [Professor-Codephreak / easyAGI](https://chatgpt.com/g/g-gNLDlpcAv-professor-codephreak) lineage (2024) — see [`github.com/GATERAGE/aglm`](https://github.com/GATERAGE/aglm) for the foundational papers and earlier research code. This repo is the modern production-grade distillation that emerged from running those ideas in mindX for a year.

Project documentation lives at [rage.pythai.net](https://rage.pythai.net).

## License

Apache-2.0. (c) 2024-2026 GATERAGE / Professor Codephreak.
