"""Unit tests for the tool-call efficiency metric.

These use hand-built fake trajectories (no LLM, no network) to lock down the
duplicate / retry-loop / efficiency-score logic in
``tests.llm.utils.tool_call_efficiency``.
"""

from mavrick.core.models import ToolCallResult
from mavrick.core.tools import StructuredToolResult, StructuredToolResultStatus
from tests.llm.utils.tool_call_efficiency import compute_tool_call_efficiency


def _call(
    tool_name: str,
    params: dict,
    status: StructuredToolResultStatus = StructuredToolResultStatus.SUCCESS,
    data="some output",
    error=None,
) -> ToolCallResult:
    """Build a ToolCallResult mirroring what a real run records."""
    return ToolCallResult(
        tool_call_id=f"call_{tool_name}_{len(params)}",
        tool_name=tool_name,
        description=f"{tool_name}({params})",
        result=StructuredToolResult(
            status=status,
            data=data,
            error=error,
            params=params,
        ),
    )


def test_clean_run_is_fully_efficient():
    trajectory = [
        _call("kubectl_get", {"resource": "pods", "namespace": "app-01"}),
        _call("kubectl_describe", {"resource": "pod", "name": "web-0"}),
        _call("kubectl_logs", {"name": "web-0"}),
    ]

    metrics = compute_tool_call_efficiency(trajectory, expected_tool_calls=3)

    assert metrics.total_tool_calls == 3
    assert metrics.duplicate_calls == 0
    assert metrics.retry_loops == 0
    assert metrics.efficiency_score == 1.0


def test_fewer_calls_than_expected_still_caps_at_one():
    trajectory = [_call("kubectl_get", {"resource": "pods"})]

    metrics = compute_tool_call_efficiency(trajectory, expected_tool_calls=3)

    assert metrics.efficiency_score == 1.0


def test_duplicate_heavy_run_is_penalized():
    # 4 calls, 2 of them exact duplicates of the first.
    trajectory = [
        _call("kubectl_get", {"resource": "pods", "namespace": "app-01"}),
        _call("kubectl_get", {"resource": "pods", "namespace": "app-01"}),
        _call("kubectl_get", {"resource": "pods", "namespace": "app-01"}),
        _call("kubectl_logs", {"name": "web-0"}),
    ]

    metrics = compute_tool_call_efficiency(trajectory, expected_tool_calls=2)

    assert metrics.total_tool_calls == 4
    assert metrics.duplicate_calls == 2
    # ratio = min(1, 2/4) = 0.5; penalty = 1 - 2/4 = 0.5 -> 0.25
    assert metrics.efficiency_score == 0.25


def test_duplicate_detection_normalizes_arg_order_and_whitespace():
    trajectory = [
        _call("grep", {"pattern": "error log", "path": "/var"}),
        # Same call: keys reordered and extra internal whitespace.
        _call("grep", {"path": "/var", "pattern": "error    log"}),
    ]

    metrics = compute_tool_call_efficiency(trajectory, expected_tool_calls=1)

    assert metrics.duplicate_calls == 1


def test_retry_loop_after_error_is_counted():
    trajectory = [
        _call(
            "kubectl_logs",
            {"name": "web-0"},
            status=StructuredToolResultStatus.ERROR,
            data=None,
            error="pod not found",
        ),
        # Identical call right after the failure -> retry loop.
        _call(
            "kubectl_logs",
            {"name": "web-0"},
            status=StructuredToolResultStatus.ERROR,
            data=None,
            error="pod not found",
        ),
    ]

    metrics = compute_tool_call_efficiency(trajectory, expected_tool_calls=1)

    assert metrics.retry_loops == 1
    assert metrics.duplicate_calls == 1


def test_no_data_result_counts_as_empty_for_retry():
    trajectory = [
        _call(
            "search",
            {"q": "checkout"},
            status=StructuredToolResultStatus.NO_DATA,
            data=None,
        ),
        _call(
            "search",
            {"q": "checkout"},
            status=StructuredToolResultStatus.NO_DATA,
            data=None,
        ),
    ]

    metrics = compute_tool_call_efficiency(trajectory, expected_tool_calls=1)

    assert metrics.retry_loops == 1


def test_identical_calls_after_success_are_not_retry_loops():
    trajectory = [
        _call("kubectl_get", {"resource": "pods"}),
        _call("kubectl_get", {"resource": "pods"}),
    ]

    metrics = compute_tool_call_efficiency(trajectory, expected_tool_calls=1)

    assert metrics.duplicate_calls == 1
    assert metrics.retry_loops == 0


def test_missing_expected_field_skips_score_but_keeps_counts():
    trajectory = [
        _call("kubectl_get", {"resource": "pods"}),
        _call("kubectl_get", {"resource": "pods"}),
    ]

    metrics = compute_tool_call_efficiency(trajectory, expected_tool_calls=None)

    assert metrics.efficiency_score is None
    assert metrics.total_tool_calls == 2
    assert metrics.duplicate_calls == 1


def test_empty_trajectory():
    metrics = compute_tool_call_efficiency([], expected_tool_calls=2)

    assert metrics.total_tool_calls == 0
    assert metrics.duplicate_calls == 0
    assert metrics.retry_loops == 0
    assert metrics.efficiency_score == 1.0


def test_to_dict_round_trips_fields():
    metrics = compute_tool_call_efficiency(
        [_call("kubectl_get", {"resource": "pods"})], expected_tool_calls=1
    )

    assert metrics.to_dict() == {
        "total_tool_calls": 1,
        "duplicate_calls": 0,
        "retry_loops": 0,
        "expected_tool_calls": 1,
        "efficiency_score": 1.0,
    }
