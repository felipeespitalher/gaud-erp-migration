"""Interactive CLI for GAUD Migration Tool."""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

import click
from colorama import Fore, Style

from config import app_config
from src.parser.sql_parser import SqlParser
from src.mapper.heuristic import HeuristicMapper
from src.transformer.registry import TransformerRegistry
from src.validator.data_validator import DataValidator
from src.exporter.json_exporter import JsonExporter
from src.api.gaud_client import GaudClient


class InteractiveCLI:
    """Interactive CLI interface."""

    def __init__(self):
        """Initialize CLI."""
        self.gaud_client = GaudClient(app_config.gaud_api)
        self.transformer_registry = TransformerRegistry()
        self.current_migration = None
        self.current_schema = None
        self.mappings = []

    def print_header(self, title: str):
        """Print a section header."""
        print(f"\n{Fore.CYAN}{'━' * 45}")
        print(f"{Fore.CYAN}{title}")
        print(f"{Fore.CYAN}{'━' * 45}{Style.RESET_ALL}\n")

    def run(self):
        """Run interactive CLI."""
        while True:
            self.print_header("Main Menu")
            click.echo("1. Sync Gaud Schema")
            click.echo("2. New Migration")
            click.echo("3. Load Migration")
            click.echo("4. Exit\n")

            choice = click.prompt("Choose", type=int, default=1)

            if choice == 1:
                self.sync_gaud_schema()
            elif choice == 2:
                self.new_migration()
            elif choice == 3:
                self.load_migration(None)
            elif choice == 4:
                click.echo(f"{Fore.YELLOW}Goodbye!")
                break
            else:
                click.echo(f"{Fore.RED}Invalid choice")

    def sync_gaud_schema(self):
        """Sync Gaud schema from API."""
        self.print_header("Sync Gaud Schema")

        try:
            click.echo(f"{Fore.CYAN}Connecting to {app_config.gaud_api.base_url}...")

            schema = self.gaud_client.get_schema()

            if schema:
                # Save to cache
                cache_file = Path(app_config.config_dir) / "gaud_schema.json"
                cache_file.parent.mkdir(parents=True, exist_ok=True)

                with open(cache_file, "w") as f:
                    json.dump(schema, f, indent=2)

                table_count = len(schema.get("tables", []))
                click.echo(f"{Fore.GREEN}✅ Schema synced successfully!")
                click.echo(f"{Fore.GREEN}   Tables: {table_count}")
                click.echo(f"{Fore.GREEN}   Cached at: {cache_file}")

                self.current_schema = schema
            else:
                click.echo(f"{Fore.RED}Failed to fetch schema from API")

        except Exception as e:
            click.echo(f"{Fore.RED}Error: {e}")

    def new_migration(self):
        """Start new migration."""
        self.print_header("New Migration")

        # List available backup files
        backup_dir = Path(app_config.backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_files = sorted(backup_dir.glob("*.sql"))

        if not backup_files:
            click.echo(f"{Fore.YELLOW}No SQL files found in {backup_dir}")
            return

        click.echo("Available backups:")
        for i, f in enumerate(backup_files, 1):
            size = f.stat().st_size / 1024 / 1024  # MB
            click.echo(f"{i}. {f.name} ({size:.1f} MB)")

        choice = click.prompt("Select backup", type=int, default=1)

        if 1 <= choice <= len(backup_files):
            backup_file = backup_files[choice - 1]
            self._process_migration(backup_file)
        else:
            click.echo(f"{Fore.RED}Invalid choice")

    def _process_migration(self, backup_file: Path):
        """Process a migration step by step."""
        click.echo(f"\n{Fore.CYAN}Loading {backup_file.name}...")

        # Read SQL
        with open(backup_file, "r") as f:
            sql_content = f.read()

        # Step 1: Parse
        self.print_header("Step 1: Parse SQL Dump")
        click.echo(f"{Fore.CYAN}Parsing schema...")

        parser = SqlParser()
        source_schema = parser.parse(sql_content)

        click.echo(f"{Fore.GREEN}✅ Parsed successfully!")
        click.echo(f"   Tables: {len(source_schema.tables)}")
        click.echo(f"   Total columns: {sum(len(t.columns) for t in source_schema.tables)}")

        for table in source_schema.tables[:5]:  # Show first 5
            click.echo(f"   • {table.name} ({len(table.columns)} cols)")

        if len(source_schema.tables) > 5:
            click.echo(f"   ... and {len(source_schema.tables) - 5} more")

        self.current_schema = source_schema

        # Step 2: Auto-map
        self._auto_map_schema(source_schema)

        # Step 3: Edit mappings (interactive)
        self._edit_mappings()

        # Step 4: Validate (optional)
        if click.confirm("Validate data before export?", default=True):
            self._validate_data(sql_content)

        # Step 5: Export
        if click.confirm("Export to JSON?", default=True):
            self._export_migration(backup_file.stem, source_schema, sql_content)

        # Step 6: Import (optional)
        if click.confirm("Import to Gaud API?", default=False):
            self._import_migration()

    def _auto_map_schema(self, source_schema):
        """Auto-map source schema to Gaud schema."""
        self.print_header("Step 2: Auto-Mapping")

        if not self.current_schema:
            click.echo(f"{Fore.YELLOW}Gaud schema not cached. Run 'sync_schema' first.")
            if not click.confirm("Continue without schema validation?", default=True):
                return

        mapper = HeuristicMapper(self.current_schema)
        self.mappings = mapper.suggest_mappings(source_schema)

        click.echo(f"{Fore.CYAN}Generated {len(self.mappings)} mappings")

        for m in self.mappings[:10]:  # Show first 10
            icon = "✓" if m.target_table else "✗"
            click.echo(f"{Fore.GREEN}{icon} {m.source_table} → {m.target_table or 'SKIP'}")

        if len(self.mappings) > 10:
            click.echo(f"... and {len(self.mappings) - 10} more")

    def _edit_mappings(self):
        """Edit mappings interactively."""
        self.print_header("Step 3: Edit Mappings")

        while True:
            pending = [m for m in self.mappings if not m.target_table]

            if pending:
                click.echo(f"Pending mappings: {len(pending)}\n")

                mapping = pending[0]
                click.echo(f"Source table: {Fore.YELLOW}{mapping.source_table}")

                target = click.prompt("Target table (or SKIP)", default="", type=str)

                if target.upper() != "SKIP":
                    mapping.target_table = target

                if not click.confirm("Edit another?", default=len(pending) > 1):
                    break
            else:
                click.echo(f"{Fore.GREEN}All mappings configured!")
                break

    def _validate_data(self, sql_content: str):
        """Validate data."""
        self.print_header("Step 4: Validate Data")

        click.echo(f"{Fore.CYAN}Validating data...")

        validator = DataValidator()
        errors = validator.validate(self.current_schema, self.mappings)

        click.echo(f"{Fore.GREEN}✅ Validation complete")
        click.echo(f"   Errors: {len(errors)}")

        if errors:
            click.echo(f"\n{Fore.YELLOW}Sample errors:")
            for error in errors[:5]:
                click.echo(f"   • {error}")

    def _export_migration(self, name: str, schema, sql_content: str):
        """Export migration to JSON."""
        self.print_header("Step 5: Export JSON")

        click.echo(f"{Fore.CYAN}Exporting...")

        output_dir = Path(app_config.output_dir) / "migrations"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = output_dir / f"{timestamp}_{name}.json"

        exporter = JsonExporter()
        exporter.export(output_file, schema, self.mappings)

        click.echo(f"{Fore.GREEN}✅ Exported!")
        click.echo(f"   File: {output_file}")

    def _import_migration(self):
        """Import migration to Gaud API."""
        self.print_header("Step 6: Import via API")

        if not app_config.gaud_api.api_key:
            click.echo(f"{Fore.YELLOW}API key not configured")
            app_config.gaud_api.api_key = click.prompt("Enter API key", hide_input=True)

        click.echo(f"{Fore.CYAN}Importing to {app_config.gaud_api.base_url}...")

        try:
            job_id = self.gaud_client.import_data(
                source_schema=self.current_schema,
                mappings=self.mappings,
            )

            click.echo(f"{Fore.GREEN}✅ Import started!")
            click.echo(f"   Job ID: {job_id}")

            # Monitor progress
            self._monitor_import(job_id)

        except Exception as e:
            click.echo(f"{Fore.RED}Import failed: {e}")

    def _monitor_import(self, job_id: str):
        """Monitor import progress."""
        click.echo(f"\n{Fore.CYAN}Monitoring progress...")

        with click.progressbar(length=100, label="Progress") as bar:
            for i in range(10):
                status = self.gaud_client.get_status(job_id)

                if status:
                    progress = status.get("progress", 0)
                    bar.update(progress - bar.pos)

                    if status.get("status") == "COMPLETED":
                        click.echo(f"\n{Fore.GREEN}✅ Import completed!")
                        click.echo(
                            f"   Records: {status.get('statistics', {}).get('successRecords', 0)}"
                        )
                        break

                click.echo(".")

    def run_direct(self, backup_file: str, non_interactive: bool = False):
        """Run migration directly without interactive menu."""
        backup_path = Path(backup_file)

        if not backup_path.exists():
            click.echo(f"{Fore.RED}File not found: {backup_file}")
            return

        self._process_migration(backup_path)

    def load_migration(self, migration_id: Optional[str] = None):
        """Load a saved migration."""
        self.print_header("Load Migration")

        migrations_dir = Path(app_config.output_dir) / "migrations"

        if not migrations_dir.exists():
            click.echo(f"{Fore.YELLOW}No migrations found")
            return

        migration_files = sorted(migrations_dir.glob("*.json"))

        if not migration_files:
            click.echo(f"{Fore.YELLOW}No migrations found")
            return

        for i, f in enumerate(migration_files, 1):
            click.echo(f"{i}. {f.name}")

        if not migration_id:
            choice = click.prompt("Select migration", type=int, default=1)
            if 1 <= choice <= len(migration_files):
                migration_file = migration_files[choice - 1]
            else:
                click.echo(f"{Fore.RED}Invalid choice")
                return
        else:
            migration_file = migrations_dir / migration_id

        with open(migration_file, "r") as f:
            migration_data = json.load(f)

        click.echo(f"{Fore.GREEN}Loaded: {migration_file.name}")
        click.echo(f"   Tables: {len(migration_data.get('mappings', []))}")

    def list_migrations(self):
        """List all saved migrations."""
        self.print_header("Saved Migrations")

        migrations_dir = Path(app_config.output_dir) / "migrations"

        if not migrations_dir.exists():
            click.echo(f"{Fore.YELLOW}No migrations found")
            return

        migration_files = sorted(migrations_dir.glob("*.json"))

        for f in migration_files:
            stat = f.stat()
            size = stat.st_size / 1024
            click.echo(f"{f.name} ({size:.1f} KB)")
