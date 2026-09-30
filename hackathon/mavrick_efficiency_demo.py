#!/usr/bin/env python3
"""MavrickGPT — Tool Call Efficiency demo (Hacktoberfest).

A self-contained, offline showcase of the "tool call efficiency" metric added
to the MavrickGPT eval judge. It needs no API key and no Kubernetes:
it feeds hand-built agent trajectories through the real metric
(``tests.llm.utils.tool_call_efficiency.compute_tool_call_efficiency``) and
renders a colored report.

Why it matters: evals normally score only *correctness*. Two agents can both be
"correct" while one reaches the answer in three sharp tool calls and another
flails — repeating near-identical calls or retrying an identical failing call
instead of switching tools. That waste is most visible on small open-weight
models (the Hacktoberfest 2025 theme), and this metric surfaces it with zero
extra LLM calls.

Run it:

    python hackathon/mavrick_efficiency_demo.py
"""

from __future__ import annotations

import os
import sys
from types import SimpleNamespace
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Make the repo root importable when run directly (python hackathon/<file>.py).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mavrick.core.tools import StructuredToolResultStatus  # noqa: E402
from tests.llm.utils.tool_call_efficiency import (  # noqa: E402
    ToolCallEfficiency,
    compute_tool_call_efficiency,
)

console = Console(width=118)


def call(
    tool_name: str,
    params: dict,
    status: StructuredToolResultStatus = StructuredToolResultStatus.SUCCESS,
    data="<output>",
    error=None,
):
    """A lightweight, duck-typed stand-in for a recorded ToolCallResult.

    The metric only reads ``.tool_name`` and ``.result.{params,status,data,
    error}`` via getattr, so a SimpleNamespace is enough to drive the real
    implementation without constructing heavy pydantic models.
    """
    return SimpleNamespace(
        tool_name=tool_name,
        result=SimpleNamespace(
            params=params, status=status, data=data, error=error
        ),
    )


def _err(tool_name: str, params: dict, error: str = "not found"):
    return call(
        tool_name,
        params,
        status=StructuredToolResultStatus.ERROR,
        data=None,
        error=error,
    )


# --- Demo scenarios ---------------------------------------------------------

CLEAN: List = [
    call("kubectl_get", {"resource": "pods", "namespace": "app-01"}),
    call("kubectl_describe", {"resource": "pod", "name": "web-0"}),
    call("kubectl_logs", {"name": "web-0"}),
]

DUPLICATE_HEAVY: List = [
    call("kubectl_get", {"resource": "pods", "namespace": "app-01"}),
    # Same call, args reordered + extra whitespace — still a duplicate.
    call("kubectl_get", {"namespace": "app-01", "resource": "pods  "}),
    call("kubectl_get", {"resource": "pods", "namespace": "app-01"}),
    call("kubectl_logs", {"name": "web-0"}),
]

RETRY_LOOP: List = [
    _err("kubectl_logs", {"name": "web-0"}),
    # Identical call right after the failure — a retry loop instead of a pivot.
    _err("kubectl_logs", {"name": "web-0"}),
    _err("kubectl_logs", {"name": "web-0"}),
    call("kubectl_get", {"resource": "events", "namespace": "app-04"}),
]

SCENARIOS = [
    ("Clean run", "Three sharp, distinct calls — exactly what we want.", CLEAN, 3),
    (
        "Duplicate-heavy run",
        "Repeats the same lookup with cosmetically different args.",
        DUPLICATE_HEAVY,
        2,
    ),
    (
        "Retry loop",
        "Retries an identical FAILING call instead of switching tools.",
        RETRY_LOOP,
        1,
    ),
    (
        "Metric skipped",
        "Eval didn't declare expected_tool_calls — advisory only, never fails.",
        DUPLICATE_HEAVY,
        None,
    ),
]


def _score_cell(metrics: ToolCallEfficiency) -> str:
    if metrics.efficiency_score is None:
        return "[dim]— (skipped)[/dim]"
    pct = round(metrics.efficiency_score * 100)
    color = (
        "green"
        if metrics.efficiency_score >= 0.9
        else "yellow"
        if metrics.efficiency_score >= 0.6
        else "red"
    )
    return f"[{color}]{pct}%[/{color}]"


def _markers(metrics: ToolCallEfficiency) -> str:
    bits = []
    if metrics.duplicate_calls:
        bits.append(f"[yellow]⧉ {metrics.duplicate_calls} dup[/yellow]")
    if metrics.retry_loops:
        bits.append(f"[red]↻ {metrics.retry_loops} retry[/red]")
    return "  ".join(bits) if bits else "[green]clean[/green]"


def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]MavrickGPT[/bold cyan] · Tool Call Efficiency\n"
            "[dim]Hacktoberfest 2025 — surfacing wasted tool calls on "
            "open-weight models[/dim]",
            border_style="cyan",
        )
    )

    table = Table(show_lines=True, header_style="bold magenta")
    table.add_column("Scenario", style="cyan", width=18)
    table.add_column("What happens", style="white", width=38)
    table.add_column("Exp.", justify="right", width=4)
    table.add_column("Act.", justify="right", width=4)
    table.add_column("Efficiency", justify="right", width=10)
    table.add_column("Signals", width=20)

    for name, description, trajectory, expected in SCENARIOS:
        metrics = compute_tool_call_efficiency(trajectory, expected)
        table.add_row(
            name,
            description,
            "—" if expected is None else str(expected),
            str(metrics.total_tool_calls),
            _score_cell(metrics),
            _markers(metrics),
        )

    console.print(table)
    console.print(
        "\n[dim]efficiency_score = min(1, expected/actual) × (1 − duplicates/total)."
        " Correctness scoring is untouched; this metric never fails a test.[/dim]"
    )


if __name__ == "__main__":
    main()
