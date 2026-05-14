# MASTERMIND as a Service

> *MASTERMIND — strategic orchestration agent. Directive → plan → execute loop
> for autonomous multi-agent systems. This document is the contract for what
> MASTERMIND offers as a service to systems built on top of it.*

Companion specs:

- [aGLM — Autonomous General Learning Model](https://github.com/GATERAGE/aglm)
- [RAGE — Retrieval Augmented Generative Engine](https://github.com/GATERAGE/RAGE)

Together: **RAGE remembers, aGLM decides, MASTERMIND orchestrates.**

---

## 1. What MASTERMIND is

MASTERMIND is the strategic-orchestration layer. It accepts *directives* —
typed intents from operators, other agents, or contract events — turns
each one into a *plan* (an ordered sequence of steps), and executes the
plan by delegating each step to a registered agent.

The package distills the orchestrator pattern from mindX
([`agents/orchestration/mastermind_agent.py`](https://github.com/agenticplace)
— ~960 lines, integrated with the BDI engine, LLM router, and DAIO
governance). This package is the **agnostic, framework-independent
distillation** — roughly 600 LOC across four modules.

mindX is one consumer of this pattern; this repo is the canonical agnostic
home.

---

## 2. The four primitives

### 2.1 `Directive` — typed intent

```python
from mastermind import Directive, Priority

d = Directive(
    title="convene boardroom",
    body="Q2 strategy review",
    priority=Priority.HIGH,
    principal="ceo.agent",
    metadata={"quarter": "Q2"},
)
```

Properties:
- Immutable id (`directive_id`), settable principal (who issued it),
  priority enum (low/standard/high/critical), optional deadline.
- Serializable to/from dict for persistence.
- `is_overdue()` checks the deadline.

### 2.2 `Plan` and `PlanStep`

```python
from mastermind import Plan, PlanStep, StepStatus

p = Plan(directive_id=d.directive_id)
p.add_step(PlanStep(
    description="convene the cabinet",
    agent_id="boardroom.agent",
    action="convene",
    args={"members": "all"},
))
p.add_step(PlanStep(
    description="record minutes",
    agent_id="memory.agent",
    action="store",
    args={"kind": "boardroom_session"},
))
```

Properties:
- Each step names the `agent_id` to delegate to and the `action` for
  that agent to run.
- Steps may belong to a `parallel_group`; same-group steps run
  concurrently, None-group steps run serially in order.
- `plan.status` derives from step statuses: FAILED if any step failed,
  SUCCESS when all done, RUNNING/PENDING otherwise.

### 2.3 `AgentRegistry`

```python
from mastermind import AgentRegistry

async def my_executor(action, args):
    return {"success": True, "result": "..."}

registry = AgentRegistry()
registry.register(
    agent_id="my.agent",
    execute=my_executor,
    actions={"convene", "vote"},
    description="boardroom operator",
)
```

Properties:
- Pluggable: register any async callable that takes `(action, args)` and
  returns an outcome dict.
- Wildcard `"*"` makes an agent a catchall.
- `find_for_action` returns all agents that handle an action;
  `pick_for_action` returns the first. Subclass for capability-weighted
  routing.

### 2.4 `Orchestrator`

```python
from mastermind import Orchestrator

orch = Orchestrator(registry=registry, planner=my_planner)
result = await orch.handle(directive)
print(result.status, result.step_outcomes)
```

Properties:
- The full loop: directive → plan (via Planner) → execute (each step
  delegates to its registered agent).
- `Planner` is pluggable — `default_planner` builds a single-step plan
  from the directive title; consumers swap in LLM-backed planners,
  rule-based planners, or anything async.
- Tracks history; `orch.history(limit=50)` returns recent executions.
- Step failures isolated — a raised exception in one step doesn't crash
  the orchestrator.

---

## 3. The triangle

MASTERMIND is the top of a three-corner architecture:

```
                  ┌──────────────────┐
                  │   MASTERMIND     │   (this repo)
                  │  Orchestrator    │   directive → plan → execute
                  └────────┬─────────┘
                           │ delegates to
                           ▼
            ┌──────────────────────────────┐
            │             aGLM             │   github.com/GATERAGE/aglm
            │   Perceive-Orient-Decide-Act │
            │   BeliefSystem               │
            └─────────┬────────────────────┘
                      │ retrieves context via
                      ▼
            ┌──────────────────────────────┐
            │              RAGE            │   github.com/GATERAGE/RAGE
            │   IngestionEngine            │
            │   RetrievalEngine            │
            └──────────────────────────────┘
```

- MASTERMIND accepts directives and walks plans.
- Each plan step often invokes an aGLM core inside the executing agent.
- aGLM's `decide()` callback queries RAGE for relevant context.
- Outcomes ripple back up: belief revision in aGLM, history in
  MASTERMIND.

This is the shape mindX runs in production. Adopt any subset.

---

## 4. Service boundaries

MASTERMIND does **not**:

- Make LLM calls. Planning is pluggable; `default_planner` is
  rule-based. LLM-backed planners are the consumer's choice.
- Persist plans across restarts. Use `Plan.to_dict()` for serialization;
  storage is the consumer's job.
- Run a decision loop itself. The PODA cycle lives in aGLM; MASTERMIND
  is one level up.
- Adjudicate which agent gets a task when multiple match. Default is
  first-match; subclass `AgentRegistry.pick_for_action` for capability
  weighting.

MASTERMIND **does**:

- Provide typed Directive / Plan / PlanStep dataclasses.
- Provide a pluggable AgentRegistry.
- Run the directive → plan → execute loop, with parallel-group support.
- Surface execution history and live status.
- Stay framework-agnostic — no FastAPI, no LangChain, no LLM SDK.

---

## 5. Roadmap

| Phase | What lands | When |
|---|---|---|
| **MASTERMIND-1** | This spec + the four primitives + tests + examples | Shipped 2026-05-14 |
| **MASTERMIND-2** | Capability-weighted agent routing (load, latency, cost) | post-MVP |
| **MASTERMIND-3** | Pluggable plan persistence (JSON, SQLite, pgvector via RAGE) | post-MVP |
| **MASTERMIND-4** | LLM-backed `Planner` reference impl (with `aglm` integration) | post-MVP |
| **MASTERMIND-5** | Distributed orchestration (cross-process / cross-node directive routing) | post-MVP |
| **MASTERMIND-6** | Signed-envelope directive intake (cypherpunk2048 attribution rule) | post-MVP |

---

## 6. References

- `mastermind/directive.py` — `Directive` + `Priority`
- `mastermind/plan.py` — `Plan` + `PlanStep` + `StepStatus`
- `mastermind/agent.py` — `AgentRegistry`
- `mastermind/orchestrator.py` — `Orchestrator` + default planner
- `examples/quickstart.py` — two-agent walkthrough
- `examples/triangle.py` — the full RAGE+aGLM+MASTERMIND wiring
- [aGLM](https://github.com/GATERAGE/aglm) — autonomous decision substrate
- [RAGE](https://github.com/GATERAGE/RAGE) — retrieval substrate
- [mindX](https://github.com/agenticplace) — production consumer of all three
- [rage.pythai.net](https://rage.pythai.net) — RAGE/aGLM/MASTERMIND docs
