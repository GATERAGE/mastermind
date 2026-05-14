# SPDX-License-Identifier: Apache-2.0
# (c) 2024-2026 GATERAGE — MASTERMIND
"""
Directive — a typed intent from a principal (operator, agent, contract event)
that the orchestrator should plan against and execute.

Distilled from mindX `agents/orchestration/mastermind_agent.py:handle_directive()`.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class Priority(str, Enum):
    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Directive:
    """A typed intent. The orchestrator turns this into a Plan."""

    title: str
    body: str = ""
    priority: Priority = Priority.STANDARD
    deadline_unix: Optional[float] = None
    principal: str = "operator"  # who issued the directive
    directive_id: str = field(default_factory=lambda: f"dir-{uuid.uuid4().hex[:12]}")
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_overdue(self, now: Optional[float] = None) -> bool:
        if self.deadline_unix is None:
            return False
        return (now or time.time()) > self.deadline_unix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "directive_id": self.directive_id,
            "title": self.title,
            "body": self.body,
            "priority": self.priority.value,
            "deadline_unix": self.deadline_unix,
            "principal": self.principal,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Directive":
        return cls(
            title=data["title"],
            body=data.get("body", ""),
            priority=Priority(data.get("priority", "standard")),
            deadline_unix=data.get("deadline_unix"),
            principal=data.get("principal", "operator"),
            directive_id=data.get("directive_id", f"dir-{uuid.uuid4().hex[:12]}"),
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {}),
        )
