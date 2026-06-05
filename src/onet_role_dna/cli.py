"""Console script for onet_role_dna."""

import typer
from rich.console import Console

from onet_role_dna import utils

app = typer.Typer()
console = Console()


@app.command()
def main() -> None:
    """Console script for onet_role_dna."""
    console.print("Replace this message by putting your code into onet_role_dna.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    utils.do_something_useful()


if __name__ == "__main__":
    app()
