from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule

from mavrick.config import Config
from mavrick.core.tool_calling_llm import LLMResult
from mavrick.plugins.destinations import DestinationType
from mavrick.plugins.interfaces import Issue
from mavrick.utils.colors import AI_COLOR


def handle_result(
    result: LLMResult,
    console: Console,
    destination: DestinationType,
    config: Config,
    issue: Issue,
    show_tool_output: bool,
    add_separator: bool,
    log_costs: bool = False,
):
    if destination == DestinationType.CLI:
        if show_tool_output and result.tool_calls:
            for tool_call in result.tool_calls:
                console.print("[bold magenta]Used Tool:[/bold magenta]", end="")
                # we need to print this separately with markup=False because it contains arbitrary text and we don't want console.print to interpret it
                console.print(
                    f"{tool_call.description}. Output=\n{tool_call.result}",
                    markup=False,
                )

        console.print(f"[bold {AI_COLOR}]AI:[/bold {AI_COLOR}]", end=" ")
        console.print(Markdown(result.result))  # type: ignore

        if log_costs and result.total_cost > 0:
            console.print(
                f"\n[bold yellow]💰 Total Cost:[/bold yellow] ${result.total_cost:.6f}"
            )
            console.print(
                f"[dim]Tokens: {result.prompt_tokens:,} prompt + {result.completion_tokens:,} completion = {result.total_tokens:,} total[/dim]"
            )

        if add_separator:
            console.print(Rule())

    elif destination == DestinationType.SLACK:
        slack = config.create_slack_destination()
        slack.send_issue(issue, result)
