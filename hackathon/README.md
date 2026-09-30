# MavrickGPT · Tool Call Efficiency 🏆

> **Hacktoberfest 2025 — open-source AI & open-weight models.**
> A small, focused contribution to the [MavrickGPT](https://mavrickgpt.dev) eval
> harness that makes agent **tool-calling efficiency** a first-class, measurable
> signal — the kind of waste that mostly shows up on small open-weight models.

---

## The problem

MavrickGPT evals score one thing: **correctness** — did the agent reach
the right answer? But two agents can both be "correct" while behaving very
differently under the hood:

- one reaches the answer in **3 sharp tool calls**,
- the other **flails** — repeating the same call with near-identical args, or
  **retrying an identical failing call** instead of switching tools.

That inefficiency costs tokens, latency and money, and it's **most visible on
small open-weight models** (the Hacktoberfest theme). Correctness-only scoring is
blind to it.

## What this adds

An **advisory tool-call efficiency metric**, computed purely from the recorded
run trajectory — **no extra LLM call, no new dependencies**, and it **never fails
a test** (correctness scoring is completely untouched).

For any eval that declares an expected budget, the judge now also reports:

| Metric | Meaning |
| --- | --- |
| `total_tool_calls` | how many tool calls the run actually made |
| `duplicate_calls` | same tool + same args seen earlier (arg order & whitespace normalized) |
| `retry_loops` | an identical call repeated **right after** an error / empty result |
| `efficiency_score` | `min(1, expected/actual) × (1 − duplicates/total)` |

Opt in per eval with one line in `test_case.yaml`:

```yaml
expected_tool_calls: 1   # advisory only — omit to skip the metric entirely
```

The score is surfaced right next to correctness in both the **terminal Rich
report** and the **GitHub Actions markdown report**, with `⧉` markers for
duplicates and `↻` for retry loops.

## Run the demo (offline, no API key, no Kubernetes)

```bash
python hackathon/mavrick_efficiency_demo.py
```

It feeds hand-built trajectories through the **real** metric implementation and
prints a colored report:

```
╭────────────────────────────────────────────────────────────────────────╮
│ MavrickGPT · Tool Call Efficiency                                        │
│ Hacktoberfest 2025 — surfacing wasted tool calls on open-weight models   │
╰────────────────────────────────────────────────────────────────────────╯
 Scenario           What happens                     Exp.  Act.  Efficiency  Signals
 Clean run          Three sharp, distinct calls        3     3        100%   clean
 Duplicate-heavy    Repeats the same lookup            2     4         25%   ⧉ 2 dup
 Retry loop         Retries an identical failing call  1     4         12%   ⧉ 2 dup  ↻ 2 retry
 Metric skipped     No expected_tool_calls declared    —     4          —    ⧉ 2 dup
```

## Run the unit tests

```bash
poetry run pytest tests/llm/utils/test_tool_call_efficiency.py -q
# 10 passed
```

## How it fits the codebase

| Piece | Location |
| --- | --- |
| Metric (pure, reusable) | `tests/llm/utils/tool_call_efficiency.py` |
| Unit tests | `tests/llm/utils/test_tool_call_efficiency.py` |
| New eval field `expected_tool_calls` | `tests/llm/utils/test_case_utils.py` |
| Wire-in from recorded trajectory | `tests/llm/test_ask_mavrick.py` |
| Terminal report column | `tests/llm/utils/reporting/terminal_reporter.py` |
| GitHub report column | `tests/llm/utils/reporting/github_reporter.py` |
| Example opted-in evals | `tests/llm/fixtures/test_ask_mavrick/0{1,3,4,5}_*/test_case.yaml` |

## Design principles

- **Zero behavior change by default** — evals without `expected_tool_calls` are
  unaffected; the metric is advisory and never flips a pass/fail.
- **No new dependencies**, follows existing typing/naming conventions.
- **Single source of truth** — the demo, the reports and the tests all call the
  same `compute_tool_call_efficiency`.
