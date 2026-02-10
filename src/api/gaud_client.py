"""Gaud ERP API client."""
import requests
from typing import Optional, Dict, Any, List

from config import GaudApiConfig
from src.schema.models import SourceSchema
from src.mapper.mapping import MappingRule


class GaudClient:
    """Client for Gaud ERP API."""

    def __init__(self, config: GaudApiConfig):
        """Initialize client."""
        self.config = config
        self.session = requests.Session()

        if config.api_key:
            self.session.headers.update({"Authorization": f"Bearer {config.api_key}"})

    def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get Gaud schema from API."""
        try:
            url = f"{self.config.base_url}/v1/migration/schema"
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching schema: {e}")
            return None

    def import_data(
        self,
        source_schema: SourceSchema,
        mappings: List[MappingRule],
    ) -> Optional[str]:
        """Import data to Gaud."""
        try:
            url = f"{self.config.base_url}/v1/migration/import"

            payload = {
                "sourceDatabase": source_schema.database_type,
                "mappings": [m.to_dict() for m in mappings],
                "data": {},  # Placeholder
            }

            response = self.session.post(url, json=payload, timeout=self.config.timeout)
            response.raise_for_status()

            result = response.json()
            return result.get("jobId")

        except Exception as e:
            print(f"Error importing data: {e}")
            return None

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get import status."""
        try:
            url = f"{self.config.base_url}/v1/migration/status/{job_id}"
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting status: {e}")
            return None
