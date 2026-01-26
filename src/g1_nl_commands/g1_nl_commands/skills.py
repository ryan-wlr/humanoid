from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskPlan:
    """A simple, executor-agnostic task plan.

    This intentionally stays as a plain dict-friendly structure so it can be
    serialized into a std_msgs/String as JSON.
    """

    intent: str
    args: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"intent": self.intent, "args": self.args}


_PICK_RE = re.compile(
    r"^\s*(pick\s*up|grab|pick)\s+(an\s+|a\s+|the\s+)?(?P<object>.+?)\s*$",
    re.IGNORECASE,
)

_PLACE_RE = re.compile(
    r"^\s*(place|put|drop)\s+(an\s+|a\s+|the\s+)?(?P<object>.+?)\s*(on|into|in)\s+(?P<target>.+?)\s*$",
    re.IGNORECASE,
)

_GO_RE = re.compile(
    r"^\s*(go|walk|navigate)\s+(to\s+)?(?P<target>.+?)\s*$",
    re.IGNORECASE,
)


def parse_command(text: str) -> TaskPlan | None:
    """Parse a natural-language command into a TaskPlan.

    Supported examples:
    - "pick up apple"
    - "place apple on table"
    - "go to sink"
    """

    text = (text or "").strip()
    if not text:
        return None

    m = _PICK_RE.match(text)
    if m:
        obj = m.group("object").strip()
        return TaskPlan(intent="pick", args={"object": obj})

    m = _PLACE_RE.match(text)
    if m:
        obj = m.group("object").strip()
        target = m.group("target").strip()
        return TaskPlan(intent="place", args={"object": obj, "target": target})

    m = _GO_RE.match(text)
    if m:
        target = m.group("target").strip()
        return TaskPlan(intent="navigate", args={"target": target})

    # Fallback: leave as "unknown" so an LLM/planner can handle it later.
    return TaskPlan(intent="unknown", args={"text": text})
