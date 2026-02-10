"""Import transformed data to gaud-erp-api using existing endpoints."""
from typing import Dict, List, Optional
import click
from colorama import Fore, Style

from src.api.gaud_client import GaudClient
from src.api.endpoint_mapper import EndpointMapper


class DataImporter:
    """Import data to gaud-erp-api using existing endpoints."""

    def __init__(self, gaud_client: GaudClient, batch_size: int = 500):
        """
        Initialize importer.

        Args:
            gaud_client: GaudClient instance
            batch_size: Number of records per batch
        """
        self.gaud_client = gaud_client
        self.batch_size = batch_size

    def import_tables(
        self,
        data: Dict[str, List[dict]],
        dry_run: bool = False,
    ) -> Dict[str, dict]:
        """
        Import data to appropriate endpoints.

        Does NOT send raw data blob. Instead, routes each table
        to its corresponding endpoint.

        Args:
            data: {table_name: [rows]}
            dry_run: If True, simulate import without making API calls

        Returns:
            {table_name: {created: N, errors: M, status: 'success'|'failed'}}
        """
        results = {}

        click.echo(f"\n{Fore.CYAN}{'=' * 70}")
        click.echo(f"{Fore.CYAN}📤 IMPORTING DATA VIA API ENDPOINTS")
        click.echo(f"{Fore.CYAN}{'=' * 70}\n")

        for table_name, rows in data.items():
            click.echo(f"{Fore.YELLOW}📊 Processing table: {table_name} ({len(rows)} rows)")

            # Get endpoint for table
            endpoint = EndpointMapper.get_endpoint(table_name)

            if not endpoint:
                click.echo(f"{Fore.RED}   ❌ No endpoint mapping found for '{table_name}'")
                results[table_name] = {
                    'status': 'failed',
                    'created': 0,
                    'errors': len(rows),
                    'error_message': 'No endpoint mapping found'
                }
                continue

            click.echo(f"{Fore.GREEN}   ✓ Endpoint: {endpoint}")

            # Import table data in batches
            try:
                result = self._import_table_batches(
                    table_name,
                    endpoint,
                    rows,
                    dry_run=dry_run,
                )
                results[table_name] = result
            except Exception as e:
                click.echo(f"{Fore.RED}   ❌ Error importing {table_name}: {str(e)}")
                results[table_name] = {
                    'status': 'failed',
                    'created': 0,
                    'errors': len(rows),
                    'error_message': str(e)
                }

        # Print summary
        click.echo(f"\n{Fore.CYAN}{'=' * 70}")
        click.echo(f"{Fore.CYAN}📈 IMPORT SUMMARY")
        click.echo(f"{Fore.CYAN}{'=' * 70}\n")

        total_created = 0
        total_errors = 0

        for table_name, result in results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            created = result.get('created', 0)
            errors = result.get('errors', 0)

            click.echo(f"{status_icon} {table_name:30s} → {created:6d} created, {errors:6d} errors")

            total_created += created
            total_errors += errors

        click.echo(f"\n{Fore.GREEN}TOTAL: {total_created} records created, {total_errors} errors\n")

        return results

    def _import_table_batches(
        self,
        table_name: str,
        endpoint: str,
        rows: List[dict],
        dry_run: bool = False,
    ) -> dict:
        """
        Import table data in batches to endpoint.

        Args:
            table_name: Source table name
            endpoint: Target API endpoint
            rows: Data rows to import
            dry_run: If True, simulate without calling API

        Returns:
            {created: N, errors: M, status: 'success'|'failed'}
        """
        total_created = 0
        total_errors = 0

        # Split into batches
        for batch_idx, batch_start in enumerate(range(0, len(rows), self.batch_size)):
            batch_end = min(batch_start + self.batch_size, len(rows))
            batch = rows[batch_start:batch_end]

            batch_num = batch_idx + 1
            total_batches = (len(rows) + self.batch_size - 1) // self.batch_size

            try:
                if dry_run:
                    # Simulate API call
                    click.echo(f"   [DRY RUN] Batch {batch_num}/{total_batches}: {len(batch)} rows")
                    total_created += len(batch)
                else:
                    # Call API endpoint
                    response = self.gaud_client.post(
                        endpoint,
                        json={'records': batch}
                    )

                    # Parse response
                    if isinstance(response, dict):
                        created = response.get('created', 0)
                        errors = response.get('errors', 0)
                    else:
                        # Assume all records created if response is success
                        created = len(batch)
                        errors = 0

                    total_created += created
                    total_errors += errors

                    click.echo(
                        f"   ✓ Batch {batch_num}/{total_batches}: "
                        f"{created} created, {errors} errors"
                    )

            except Exception as e:
                click.echo(f"   ❌ Batch {batch_num}/{total_batches} failed: {str(e)}")
                total_errors += len(batch)

        return {
            'status': 'success' if total_errors == 0 else 'partial',
            'created': total_created,
            'errors': total_errors,
        }

    def validate_mappings(self, table_names: List[str]) -> Dict[str, Optional[str]]:
        """
        Validate that all tables have endpoint mappings.

        Args:
            table_names: List of source table names

        Returns:
            {table_name: endpoint_or_none}
        """
        mappings = {}

        for table_name in table_names:
            endpoint = EndpointMapper.get_endpoint(table_name)
            mappings[table_name] = endpoint

        return mappings
