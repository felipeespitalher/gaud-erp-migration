#!/usr/bin/env python3
"""GAUD ERP Migration Tool - Entry point."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click
from colorama import Fore, Style, init

from config import app_config
from src.cli.interactive import InteractiveCLI

# Initialize colorama
init(autoreset=True)


def print_banner():
    """Print application banner."""
    print(f"{Fore.CYAN}{'=' * 44}")
    print(f"{Fore.CYAN}║   {Fore.WHITE}GAUD ERP Migration Tool{Fore.CYAN}              ║")
    print(f"{Fore.CYAN}║   {Fore.WHITE}Local Database Migration Assistant{Fore.CYAN}   ║")
    print(f"{Fore.CYAN}{'=' * 44}{Style.RESET_ALL}")
    print()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """GAUD ERP Migration Tool - Migrate customer databases locally."""
    pass


@cli.command()
@click.option(
    "--backup",
    type=click.Path(exists=True),
    help="Path to SQL dump file",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Run in non-interactive mode",
)
def migrate(backup, non_interactive):
    """Start a new migration."""
    print_banner()

    cli_tool = InteractiveCLI()

    if backup:
        # Direct mode
        click.echo(f"{Fore.GREEN}Loading backup from {backup}...")
        cli_tool.run_direct(backup, non_interactive)
    else:
        # Interactive mode
        cli_tool.run()


@cli.command()
def sync_schema():
    """Synchronize Gaud schema from API."""
    print_banner()

    cli_tool = InteractiveCLI()
    cli_tool.sync_gaud_schema()


@cli.command()
def list_migrations():
    """List saved migrations."""
    print_banner()

    cli_tool = InteractiveCLI()
    cli_tool.list_migrations()


@cli.command()
@click.argument("migration_id")
def load_migration(migration_id):
    """Load a saved migration."""
    print_banner()

    cli_tool = InteractiveCLI()
    cli_tool.load_migration(migration_id)


@cli.command()
def config_api():
    """Configure Gaud API credentials."""
    print_banner()

    click.echo(f"{Fore.YELLOW}Gaud API Configuration")
    click.echo(f"{Fore.YELLOW}{'=' * 30}")

    base_url = click.prompt("API Base URL", default=app_config.gaud_api.base_url)
    api_key = click.prompt("API Key (token)", hide_input=True, default="")

    app_config.gaud_api.base_url = base_url
    app_config.gaud_api.api_key = api_key

    click.echo(f"{Fore.GREEN}✅ Configuration saved!")


if __name__ == "__main__":
    cli()
