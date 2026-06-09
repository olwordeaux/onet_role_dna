"""
Diagnostic utility that programmatically audits the workspace lifecycle steps
and prints a real-time progress and health dashboard.
"""

import pathlib
import subprocess
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def run_command(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True).returncode == 0
    except Exception:
        return False


def check_git():
    try:
        res = subprocess.run(["git", "status"], capture_output=True, text=True, check=True).stdout
        clean = "nothing to commit, working tree clean" in res
        ahead = "ahead of" in res
        if ahead:
            return clean, "Unpushed Commits (Ahead of GitHub)"
        if clean:
            return True, "Synchronized and Clean"
        return False, "Uncommitted Modifications Pending"
    except Exception as e:
        return False, f"Git Error: {e}"


def check_data():
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
        from onet_role_dna.validator import validate_directory

        out = sys.stdout
        sys.stdout = open("/dev/null", "w")
        ok = validate_directory("data")
        sys.stdout = out
        return ok
    except Exception:
        return False


def fmt(ok, msg=None):
    text = msg if msg else ("PASS" if ok else "FAIL")
    color = "green" if ok else "red"
    return f"[bold {color}]{text}[/bold {color}]"


def main():
    console.print("\n[bold blue]Evaluating Workspace Lifecycle Steps...[/bold blue]\n")

    r = run_command(["ruff", "check", "src/"])
    t = run_command(["pyright", "src/"])
    p = run_command(["pytest"])
    d = check_data()
    gc, gmsg = check_git()

    table = Table(title="O*NET Role DNA Workspace Status Dashboard", show_header=True, header_style="bold magenta")
    table.add_column("Step", style="dim", width=6)
    table.add_column("Workspace Audit Layer", width=35)
    table.add_column("Tool Utilized", width=15)
    table.add_column("Status", justify="center", width=20)

    table.add_row("1", "Code Linting & Style Formatting", "ruff", fmt(r))
    table.add_row("2", "Static Type Safety Analysis", "pyright", fmt(t))
    table.add_row("3", "Business Logic & Unit Testing", "pytest", fmt(p))
    table.add_row("4", "Data Governance & File Integrity", "validator.py", fmt(d))
    table.add_row("5", "Git Repository Synchronization", "git", fmt(gc, gmsg))

    console.print(table)

    if not r:
        focus = "Step 1: Fix code formatting/style warnings using ruff check src/ --fix."
    elif not t:
        focus = "Step 2: Correct typing violations reported by pyright src/."
    elif not p:
        focus = "Step 3: Resolve logic failures in your unit test suite by running pytest."
    elif not d:
        focus = "Step 4: Clean up or correct un-validated data files reported by validator.py."
    elif not gc:
        if "Ahead" in gmsg:
            focus = "Step 5: Publish committed changes to GitHub using git push origin main."
        else:
            focus = "Step 5: Stage and commit modifications."
    else:
        focus = "Project is fully validated, synchronized, type-safe, and operational in production!"

    # Assign Panel parameters to variable first to keep lines under 120 chars
    panel = Panel(
        f"[bold yellow]Next Focus Action:[/bold yellow]\n{focus}",
        title="Validation Recommendation",
        border_style="yellow",
    )
    console.print(panel)


if __name__ == "__main__":
    main()
