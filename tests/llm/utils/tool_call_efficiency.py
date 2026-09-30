"""Tool call efficiency metric for evals.

Evals score correctness, but two agents can both be "correct" while one reaches
the answer with a handful of well-chosen tool calls and the other flails —
repeating near-identical calls or retrying an identical failing call instead of
switching tools. That inefficiency is most visible on small open-weight models.

This module computes an advisory efficiency metric purely from the recorded
trajectory (``LLMResult.tool_calls``); it makes no extra LLM call and never
fails a test. It is skipped whenever a test case does not declare
``expected_tool_calls``.
"""

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence

from mavrick.core.tools import StructuredToolResultStatus


@dataclass
class ToolCallEfficiency:
    """Advisory efficiency metrics derived from a run's tool-call trajectory."""

    total_tool_calls: int
    duplicate_calls: int  # same tool + same (normalized) args seen earlier
    retry_loops: int  # identical call repeated right after an error/empty result
    expected_tool_calls: Optional[int]
    # min(1, expected/actual) scaled by a duplicate penalty. None when the test
    # case does not declare `expected_tool_calls` (metric skipped).
    efficiency_score: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _normalize_value(value: Any) -> Any:
    """Canonicalize an argument value so cosmetic differences don't hide a
    duplicate: dict keys are sorted and string leaves have their internal
    whitespace collapsed."""
    if isinstance(value, dict):
        return {k: _normalize_value(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [_normalize_value(v) for v in value]
    if isinstance(value, str):
        return " ".join(value.split())
    return value


def _call_signature(tool_call: Any) -> str:
    """A stable identity for a tool call: its name plus normalized args.

    Two calls with the same signature are considered the "same call" for the
    purposes of duplicate and retry-loop detection.
    """
    tool_name = getattr(tool_call, "tool_name", "") or ""
    result = getattr(tool_call, "result", None)
    params = getattr(result, "params", None) or {}
    normalized = _normalize_value(params)
    return json.dumps(
        [tool_name, normalized], sort_keys=True, separators=(",", ":")
    )


def _is_failed_or_empty(tool_call: Any) -> bool:
    """Whether a tool call errored or returned nothing useful — the precondition
    for counting a following identical call as a retry loop."""
    result = getattr(tool_call, "result", None)
    if result is None:
        return True
    status = getattr(result, "status", None)
    if status in (
        StructuredToolResultStatus.ERROR,
        StructuredToolResultStatus.NO_DATA,
    ):
        return True
    if getattr(result, "error", None):
        return True
    data = getattr(result, "data", None)
    if data is None:
        return True
    if isinstance(data, (str, list, dict, tuple, set)) and len(data) == 0:
        return True
    return False


def compute_tool_call_efficiency(
    tool_calls: Optional[Sequence[Any]],
    expected_tool_calls: Optional[int],
) -> ToolCallEfficiency:
    """Compute the efficiency metric for a run.

    Args:
        tool_calls: The run's recorded ``ToolCallResult`` trajectory (may be
            None/empty).
        expected_tool_calls: The eval's declared expectation. When None the
            ``efficiency_score`` is left None (metric skipped) but the raw
            counts are still returned for visibility.
    """
    calls: List[Any] = list(tool_calls or [])
    total = len(calls)

    seen: set = set()
    duplicate_calls = 0
    retry_loops = 0
    previous_signature: Optional[str] = None
    previous_failed = False

    for tool_call in calls:
        signature = _call_signature(tool_call)
        if signature in seen:
            duplicate_calls += 1
        else:
            seen.add(signature)

        if signature == previous_signature and previous_failed:
            retry_loops += 1

        previous_signature = signature
        previous_failed = _is_failed_or_empty(tool_call)

    efficiency_score: Optional[float] = None
    if expected_tool_calls is not None:
        if total == 0:
            # No tool calls means nothing was wasted.
            efficiency_score = 1.0
        else:
            ratio = min(1.0, expected_tool_calls / total)
            duplicate_penalty = 1.0 - (duplicate_calls / total)
            efficiency_score = max(0.0, ratio * duplicate_penalty)

    return ToolCallEfficiency(
        total_tool_calls=total,
        duplicate_calls=duplicate_calls,
        retry_loops=retry_loops,
        expected_tool_calls=expected_tool_calls,
        efficiency_score=efficiency_score,
    )
