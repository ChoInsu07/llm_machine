import os
import sys
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.models.schemas import AgentConfig
from src.backend.orchestrator import Orchestrator

console = Console()

LOGO = """
[bold cyan]
  LLM Machine - OpenCode-style Local IDE Agent
[/bold cyan]
"""


def print_banner():
    console.print(LOGO)
    console.print(Panel(
        "[yellow]OpenCode-style LLM Local IDE System[/yellow]\n"
        "Type [bold]exit[/bold] or [bold]/quit[/bold] to quit.\n"
        "Type [bold]/plan[/bold] to toggle planning mode.\n"
        "Type [bold]/status[/bold] to check system health.",
        title="Welcome",
        border_style="cyan",
    ))


def run_cli(config: AgentConfig):
    orch = Orchestrator(config)
    print_banner()

    history_path = Path.home() / ".llm_machine_history"
    session = PromptSession(history=FileHistory(str(history_path)))

    use_planning = True

    while True:
        try:
            user_input = session.prompt("\n>>> ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        if not user_input.strip():
            continue

        cmd = user_input.strip().lower()

        if cmd in ("exit", "/quit", ":q"):
            console.print("[yellow]Goodbye![/yellow]")
            break

        if cmd == "/plan":
            use_planning = not use_planning
            console.print(f"[green]Planning mode: {'ON' if use_planning else 'OFF'}[/green]")
            continue

        if cmd == "/status":
            health = orch.check_health()
            console.print(f"[cyan]Ollama:[/cyan] {'OK' if health['ollama'] else 'DISCONNECTED'}")
            console.print(f"[cyan]Model:[/cyan] {health['model']}")
            console.print(f"[cyan]Workspace:[/cyan] {health['workspace']}")
            continue

        if cmd == "/help":
            console.print(Panel(
                "[bold]Commands:[/bold]\n"
                "  /plan      - Toggle planning mode\n"
                "  /status    - Check system health\n"
                "  /help      - Show this help\n"
                "  exit       - Exit the program\n\n"
                "[bold]Examples:[/bold]\n"
                '  "Create a hello world Python script"\n'
                '  "Search for all TODO comments"\n'
                '  "Run pytest and fix any failures"',
                title="Help",
            ))
            continue

        result = orch.execute_task(user_input, use_planning=use_planning)
        console.print(f"\n[dim]Result: {result}[/dim]")
