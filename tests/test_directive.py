# SPDX-License-Identifier: Apache-2.0
"""Smoke tests for Directive."""
from __future__ import annotations

import time

from mastermind import Directive, Priority


def test_directive_defaults():
    d = Directive(title="ship the release")
    assert d.title == "ship the release"
    assert d.priority == Priority.STANDARD
    assert d.principal == "operator"
    assert d.directive_id.startswith("dir-")
    assert d.is_overdue() is False


def test_directive_overdue():
    d = Directive(title="x", deadline_unix=time.time() - 60)
    assert d.is_overdue() is True


def test_directive_round_trip():
    d = Directive(
        title="convene boardroom",
        body="quarterly directive review",
        priority=Priority.HIGH,
        principal="ceo.agent",
        metadata={"quarter": "Q2"},
    )
    data = d.to_dict()
    d2 = Directive.from_dict(data)
    assert d2.title == d.title
    assert d2.priority == Priority.HIGH
    assert d2.principal == "ceo.agent"
    assert d2.metadata == {"quarter": "Q2"}
