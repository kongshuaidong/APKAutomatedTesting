#!/usr/bin/env python3
"""
Natural Language Android Automation Tool
=========================================
Entry point – connect a phone, mirror its screen, then control it via
natural language commands powered by an LLM.
"""

import sys
import uiautomator2 as u2
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from config import OPENAI_API_KEY
from core.device_manager import DeviceManager
from core.app_controller import AppController
from core.ui_automator import UIAutomator
from core.screen_mirror import ScreenMirror
from core.exception_handler import ExceptionHandler
from nlp.command_parser import CommandParser
from nlp.action_executor import ActionExecutor
from utils.logger import logger

console = Console()

BANNER = """
[bold blue] ███╗   ██╗██╗      █████╗ ██╗   ██╗████████╗ ██████╗  ██████╗ ██╗     [/bold blue]
[bold blue] ████╗  ██║██║     ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔═══██╗██║     [/bold blue]
[bold blue] ██╔██╗ ██║██║     ███████║██║   ██║   ██║   ██║   ██║██║   ██║██║     [/bold blue]
[bold blue] ██║╚██╗██║██║     ██╔══██║██║   ██║   ██║   ██║   ██║██║   ██║██║     [/bold blue]
[bold blue] ██║ ╚████║███████╗██║  ██║╚██████╔╝   ██║   ╚██████╔╝╚██████╔╝███████╗[/bold blue]
[bold blue] ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝[/bold blue]
[dim]   Android UI Automation · Natural Language · Screen Mirror[/dim]
"""

HELP_TEXT = """\
[bold]Available commands:[/bold]
  [cyan]<natural language>[/cyan]   – Describe what you want to do on the phone
  [cyan]screenshot[/cyan]           – Take a screenshot right now
  [cyan]info[/cyan]                 – Show connected device information
  [cyan]apps[/cyan]                 – List installed apps (third-party)
  [cyan]reset[/cyan]                – Clear the AI conversation context
  [cyan]mirror[/cyan]               – (Re-)start screen mirroring
  [cyan]stop-mirror[/cyan]          – Stop screen mirroring
  [cyan]help[/cyan]                 – Show this help
  [cyan]quit / exit[/cyan]          – Exit the tool
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _banner():
    console.print(BANNER)
    console.print(
        Panel(
            "[bold green]Ready to control your Android device with natural language![/bold green]",
            border_style="green",
            expand=False,
        )
    )


def _check_api_key():
    if not OPENAI_API_KEY:
        console.print(
            "[red bold]ERROR:[/red bold] OPENAI_API_KEY is not set.\n"
            "Copy [yellow].env.example[/yellow] to [yellow].env[/yellow] and fill in your key."
        )
        sys.exit(1)


def _select_device(dm: DeviceManager):
    """Interactive device selection. Returns the selected adbutils Device."""
    console.print("\n[yellow]Scanning for connected devices …[/yellow]")
    devices = dm.list_devices()

    if not devices:
        console.print(
            "[red]No devices found.[/red]\n"
            "  1. Enable [bold]Developer Options[/bold] on your phone\n"
            "  2. Enable [bold]USB Debugging[/bold]\n"
            "  3. Connect via USB (or run 'adb connect <ip>:<port>' for WiFi ADB)"
        )
        return None

    if len(devices) == 1:
        dev = devices[0]
        console.print(f"[green]Found device:[/green] {dev.serial}")
        return dm.connect(dev.serial)

    table = Table(title="Connected Devices", border_style="blue")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Serial", style="green")
    table.add_column("State", style="yellow")
    for i, d in enumerate(devices):
        table.add_row(str(i), d.serial, d.state)
    console.print(table)

    choice = Prompt.ask("Select device number", default="0")
    try:
        return dm.connect(devices[int(choice)].serial)
    except (ValueError, IndexError):
        console.print("[red]Invalid selection.[/red]")
        return None


def _start_mirror(serial: str) -> ScreenMirror | None:
    mirror = ScreenMirror(serial)
    try:
        mirror.start()
        console.print("[green]Screen mirroring started – scrcpy window should appear.[/green]")
        return mirror
    except RuntimeError as e:
        console.print(f"[yellow]Screen mirroring unavailable:[/yellow] {e}")
        return None


def _show_device_info(d: u2.Device):
    info = d.info
    table = Table(title="Device Info", border_style="blue")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    for k, v in info.items():
        table.add_row(str(k), str(v))
    console.print(table)


def _show_apps(app_ctrl: AppController):
    with console.status("Fetching installed apps …"):
        apps = app_ctrl.list_installed_apps()
    console.print(f"[green]Found {len(apps)} third-party apps[/green]")
    for pkg in sorted(apps):
        console.print(f"  [dim]•[/dim] {pkg}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    _banner()
    _check_api_key()

    # ── Device connection ──────────────────────────────────────────────────
    dm = DeviceManager()
    adb_dev = _select_device(dm)
    if adb_dev is None:
        sys.exit(1)

    serial = adb_dev.serial

    # ── UIAutomator2 ───────────────────────────────────────────────────────
    console.print("\n[yellow]Initialising UIAutomator2 on device …[/yellow]")
    try:
        d = u2.connect(serial)
        console.print(f"[green]UIAutomator2 connected.[/green] Screen: {d.window_size()}")
    except Exception as e:
        console.print(
            f"[red]UIAutomator2 init failed:[/red] {e}\n"
            "[dim]Tip: run  python -m uiautomator2 init  first.[/dim]"
        )
        sys.exit(1)

    app_ctrl = AppController(d)
    ui_auto = UIAutomator(d)
    exc_handler = ExceptionHandler(ui_auto)

    # ── NLP layer ─────────────────────────────────────────────────────────
    parser = CommandParser()
    executor = ActionExecutor(app_ctrl, ui_auto)

    # ── Screen mirroring (optional) ────────────────────────────────────────
    mirror: ScreenMirror | None = None
    start_mirror = Prompt.ask(
        "\n[cyan]Start screen mirroring?[/cyan] (requires scrcpy)",
        choices=["y", "n"],
        default="y",
    )
    if start_mirror == "y":
        mirror = _start_mirror(serial)

    # ── Interactive command loop ───────────────────────────────────────────
    console.print()
    console.print(Panel(HELP_TEXT, title="Help", border_style="dim", expand=False))
    console.print()

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]>[/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Interrupted.[/yellow]")
            break

        if not user_input:
            continue

        cmd_lower = user_input.lower()

        # ── Built-in commands ──────────────────────────────────────────────
        if cmd_lower in ("quit", "exit", "q"):
            break

        if cmd_lower == "help":
            console.print(Panel(HELP_TEXT, title="Help", border_style="dim", expand=False))
            continue

        if cmd_lower == "reset":
            parser.reset()
            console.print("[yellow]AI conversation context cleared.[/yellow]")
            continue

        if cmd_lower == "screenshot":
            try:
                path = executor.take_screenshot()
                console.print(f"[green]{path}[/green]")
            except Exception as e:
                exc_handler.handle(e, "manual screenshot")
            continue

        if cmd_lower == "info":
            _show_device_info(d)
            continue

        if cmd_lower == "apps":
            _show_apps(app_ctrl)
            continue

        if cmd_lower == "mirror":
            if mirror and mirror.is_running():
                console.print("[yellow]Mirror is already running.[/yellow]")
            else:
                mirror = _start_mirror(serial)
            continue

        if cmd_lower == "stop-mirror":
            if mirror and mirror.is_running():
                mirror.stop()
                console.print("[yellow]Screen mirroring stopped.[/yellow]")
            else:
                console.print("[dim]Mirror is not running.[/dim]")
            continue

        # ── Natural language → LLM → actions ──────────────────────────────
        with console.status("[dim]Thinking …[/dim]"):
            try:
                actions, ai_msg = parser.parse(user_input)
            except Exception as e:
                exc_handler.handle(e, "command parsing")
                continue

        if ai_msg:
            console.print(f"[blue]AI:[/blue] {ai_msg}")

        if not actions:
            if not ai_msg:
                console.print("[dim]No actions to execute.[/dim]")
            continue

        console.print(f"[dim]Executing {len(actions)} action(s) …[/dim]")

        results = executor.execute(actions)

        for r in results:
            content = r.get("content", "")
            if content.startswith("ERROR"):
                console.print(f"  [red]{content}[/red]")
            else:
                console.print(f"  [green]{content}[/green]")

        # Feed results back so the model can reason on the outcome
        parser.add_tool_results(results)

        # Check whether the model wants to continue with more actions
        with console.status("[dim]Checking for follow-up actions …[/dim]"):
            try:
                follow_actions, follow_msg = parser.follow_up()
            except Exception:
                follow_actions, follow_msg = [], None

        if follow_msg:
            console.print(f"[blue]AI:[/blue] {follow_msg}")

        if follow_actions:
            console.print(f"[dim]Follow-up: {len(follow_actions)} more action(s) …[/dim]")
            follow_results = executor.execute(follow_actions)
            for r in follow_results:
                content = r.get("content", "")
                if content.startswith("ERROR"):
                    console.print(f"  [red]{content}[/red]")
                else:
                    console.print(f"  [green]{content}[/green]")
            parser.add_tool_results(follow_results)

    # ── Cleanup ────────────────────────────────────────────────────────────
    if mirror and mirror.is_running():
        mirror.stop()

    console.print("\n[bold blue]Goodbye![/bold blue]")


if __name__ == "__main__":
    main()
