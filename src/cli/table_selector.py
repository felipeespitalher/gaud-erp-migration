"""Interactive table selection from source schema."""
from typing import List, Set
import click
from colorama import Fore, Style

from src.schema.models import SourceSchema, SourceTable

try:
    import questionary
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False


class TableSelector:
    """Interactive selection of tables from source schema."""

    def __init__(self, source_schema: SourceSchema):
        """Initialize selector."""
        self.source_schema = source_schema
        self.selected_tables: Set[str] = set()

    def prompt_selection(self) -> List[str]:
        """
        Prompt user to select tables interactively.

        Returns:
            List[str]: Names of selected tables
        """
        if not self.source_schema.tables:
            click.echo(f"{Fore.YELLOW}No tables found in backup")
            return []

        click.echo(f"\n{Fore.CYAN}Select tables to import:")
        click.echo(f"{Fore.CYAN}{'=' * 60}\n")

        # Display tables with row counts
        for i, table in enumerate(self.source_schema.tables, 1):
            rows = table.estimated_rows or 0
            click.echo(f"{i:2d}. {table.name:30s} ({rows:,d} rows)")

        click.echo(f"\n{Fore.YELLOW}Enter table numbers (comma-separated):")
        click.echo(f"{Fore.YELLOW}Example: 1,3,5  (for tables 1, 3, 5)")
        click.echo(f"{Fore.YELLOW}Or type 'all' for all tables")
        click.echo(f"{Fore.YELLOW}Or press ENTER to skip this step\n")

        while True:
            selection = click.prompt("Select tables", default="", type=str).strip()

            if not selection:
                click.echo(f"{Fore.YELLOW}No tables selected")
                return []

            if selection.lower() == 'all':
                selected = [t.name for t in self.source_schema.tables]
                self.selected_tables = set(selected)
                self._display_selection()
                return selected

            # Parse numbers
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]

                # Validate indices
                invalid = [i + 1 for i in indices if i < 0 or i >= len(self.source_schema.tables)]
                if invalid:
                    click.echo(f"{Fore.RED}Invalid table numbers: {invalid}")
                    continue

                selected = [self.source_schema.tables[i].name for i in indices]
                self.selected_tables = set(selected)
                self._display_selection()
                return selected

            except ValueError:
                click.echo(f"{Fore.RED}Invalid input. Please enter comma-separated numbers.")

    def _display_selection(self):
        """Display selected tables."""
        if not self.selected_tables:
            return

        click.echo(f"\n{Fore.GREEN}✅ Selected {len(self.selected_tables)} table(s):")

        total_rows = 0
        for table in self.source_schema.tables:
            if table.name in self.selected_tables:
                rows = table.estimated_rows or 0
                click.echo(f"{Fore.GREEN}   • {table.name:30s} ({rows:,d} rows)")
                total_rows += rows

        click.echo(f"{Fore.GREEN}   Total rows: {total_rows:,d}\n")

    def get_selected_tables(self) -> List[SourceTable]:
        """Get selected SourceTable objects."""
        return [
            t for t in self.source_schema.tables
            if t.name in self.selected_tables
        ]

    def filter_schema(self, source_schema: SourceSchema) -> SourceSchema:
        """Filter schema to include only selected tables."""
        filtered_schema = SourceSchema(
            database_type=source_schema.database_type,
            created_at=source_schema.created_at,
        )

        for table in source_schema.tables:
            if table.name in self.selected_tables:
                filtered_schema.tables.append(table)

        # Recalculate totals
        filtered_schema.total_estimated_rows = sum(
            t.estimated_rows for t in filtered_schema.tables
        )

        return filtered_schema
