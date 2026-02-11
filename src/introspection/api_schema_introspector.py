"""
API Schema Introspector - Fetches and analyzes Gaud API OpenAPI specifications.

Features:
- Automatic schema discovery from multiple swagger endpoints
- Schema caching with 1-hour TTL
- Support for multiple authentication methods
- Graceful fallback to alternative swagger URLs
- Comprehensive error handling and logging
"""

import json
import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path
import hashlib

import requests
from requests.auth import HTTPBasicAuth

from .schema_analyzer import SchemaAnalyzer, APISchema

logger = logging.getLogger(__name__)


class ApiSchemaIntrospector:
    """
    Introspects Gaud API structure and discovers endpoint definitions

    Usage:
    ```python
    introspector = ApiSchemaIntrospector(
        api_url="https://api-v2.gauderp.com",
        credentials=("art motos", "admin")
    )
    schema = introspector.get_schema()
    print(f"Found {len(schema.endpoints)} endpoints")
    ```
    """

    # Common swagger/openapi endpoint locations
    SWAGGER_ENDPOINTS = [
        "/swagger.json",
        "/openapi.json",
        "/v1/swagger.json",
        "/api/swagger.json",
        "/docs/openapi.json",
        "/rest-api-docs",  # Gaud ERP specific
        "/api-docs",
    ]

    # Cache TTL in seconds (1 hour)
    CACHE_TTL = 3600

    def __init__(
        self,
        api_url: str,
        credentials: Optional[tuple] = None,
        timeout: int = 30,
        cache_dir: Optional[Path] = None,
    ):
        """
        Initialize API Schema Introspector

        Args:
            api_url: Base API URL (e.g., https://api-v2.gauderp.com)
            credentials: Tuple of (username, password) for Basic Auth
            timeout: HTTP request timeout in seconds
            cache_dir: Directory for caching schemas (optional)
        """
        self.api_url = api_url.rstrip("/")
        self.credentials = credentials
        self.timeout = timeout
        self.cache_dir = cache_dir or Path(".cache/schemas")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create session with auth
        self.session = requests.Session()
        if credentials:
            username, password = credentials
            self.session.auth = HTTPBasicAuth(username, password)

        # Instance cache (in-memory)
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._schema_timestamp: Dict[str, float] = {}
        self._schema: Optional[APISchema] = None

    def get_schema(self, force_refresh: bool = False) -> APISchema:
        """
        Get API schema, using cache if available

        Args:
            force_refresh: Force fresh fetch from API (bypass cache)

        Returns:
            APISchema object with discovered endpoints

        Raises:
            RuntimeError: If schema cannot be fetched from any swagger endpoint
        """
        # Check in-memory cache
        if not force_refresh and self._schema is not None and self._is_cache_valid():
            logger.info("Using cached schema")
            return self._schema

        # Try to fetch from API
        spec = self._fetch_openapi_spec(force_refresh)
        if spec is None:
            raise RuntimeError(
                f"Could not fetch OpenAPI spec from {self.api_url}. "
                f"Tried endpoints: {self.SWAGGER_ENDPOINTS}"
            )

        # Analyze spec and cache
        analyzer = SchemaAnalyzer()
        self._schema = analyzer.analyze_openapi_spec(spec)
        self._schema_timestamp["memory"] = time.time()

        logger.info(f"Successfully introspected {len(self._schema.endpoints)} API endpoints")
        return self._schema

    def _fetch_openapi_spec(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Fetch OpenAPI specification from API

        Tries multiple swagger endpoints and caches the result

        Args:
            force_refresh: Bypass all caches

        Returns:
            OpenAPI spec dictionary or None if all attempts fail
        """
        # Try file cache first (unless force_refresh)
        if not force_refresh:
            cached_spec = self._try_load_file_cache()
            if cached_spec is not None:
                logger.info("Loaded schema from file cache")
                return cached_spec

        # Try to fetch from API
        spec = self._fetch_from_api()
        if spec:
            # Save to file cache
            self._save_file_cache(spec)
            return spec

        return None

    def _fetch_from_api(self) -> Optional[Dict[str, Any]]:
        """Try fetching from all known swagger endpoints"""
        for swagger_endpoint in self.SWAGGER_ENDPOINTS:
            try:
                url = f"{self.api_url}{swagger_endpoint}"
                logger.debug(f"Trying swagger endpoint: {url}")

                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                spec = response.json()
                logger.info(f"Successfully fetched schema from {swagger_endpoint}")
                return spec

            except requests.exceptions.RequestException as e:
                logger.debug(f"Failed to fetch from {swagger_endpoint}: {e}")
                continue
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from {swagger_endpoint}: {e}")
                continue

        logger.error(f"Could not fetch OpenAPI spec from any endpoint")
        return None

    def _try_load_file_cache(self) -> Optional[Dict[str, Any]]:
        """Try to load cached schema from file"""
        try:
            cache_file = self._get_cache_file_path()
            if not cache_file.exists():
                return None

            # Check if cache is still valid (TTL)
            file_time = cache_file.stat().st_mtime
            if time.time() - file_time > self.CACHE_TTL:
                logger.debug(f"Cache file expired: {cache_file}")
                return None

            with open(cache_file, "r") as f:
                spec = json.load(f)
                logger.debug(f"Loaded schema from cache file: {cache_file}")
                return spec

        except Exception as e:
            logger.warning(f"Error loading cache file: {e}")
            return None

    def _save_file_cache(self, spec: Dict[str, Any]) -> None:
        """Save schema to file cache"""
        try:
            cache_file = self._get_cache_file_path()
            cache_file.parent.mkdir(parents=True, exist_ok=True)

            with open(cache_file, "w") as f:
                json.dump(spec, f, indent=2)
                logger.debug(f"Saved schema to cache file: {cache_file}")

        except Exception as e:
            logger.warning(f"Error saving cache file: {e}")

    def _get_cache_file_path(self) -> Path:
        """Get cache file path based on API URL"""
        # Hash the API URL to avoid filesystem issues
        url_hash = hashlib.md5(self.api_url.encode()).hexdigest()[:8]
        return self.cache_dir / f"schema_{url_hash}.json"

    def _is_cache_valid(self) -> bool:
        """Check if in-memory cache is still valid"""
        if "memory" not in self._schema_timestamp:
            return False

        age = time.time() - self._schema_timestamp["memory"]
        return age < self.CACHE_TTL

    def get_endpoint_schema(self, path: str, method: str = "POST"):
        """
        Get schema for a specific endpoint

        Args:
            path: API endpoint path (e.g., /v1/catalog/products)
            method: HTTP method (GET, POST, PUT, etc.)

        Returns:
            EndpointSchema or None if not found
        """
        schema = self.get_schema()
        return schema.get_endpoint(path, method)

    def validate_payload(self, path: str, payload: Dict[str, Any], method: str = "POST") -> tuple[bool, str]:
        """
        Validate payload against endpoint schema

        Args:
            path: API endpoint path
            payload: Payload to validate
            method: HTTP method

        Returns:
            Tuple of (is_valid, error_message)
        """
        endpoint_schema = self.get_endpoint_schema(path, method)
        if not endpoint_schema:
            return False, f"Endpoint {method} {path} not found in schema"

        # Check required fields
        for required_field in endpoint_schema.required_fields:
            if required_field not in payload:
                return False, f"Missing required field: {required_field}"

        # TODO: Implement full validation against field types, formats, etc.
        return True, ""

    def print_schema_summary(self) -> None:
        """Print a summary of discovered endpoints"""
        schema = self.get_schema()

        print(f"\n{'='*70}")
        print(f"API Schema: {schema.title} ({schema.version})")
        print(f"Base URL: {schema.base_url}")
        print(f"Total Endpoints: {len(schema.endpoints)}")
        print(f"{'='*70}\n")

        # Group by path
        endpoints_by_path = {}
        for key, endpoint in schema.endpoints.items():
            method, path = key.split(" ", 1)
            if path not in endpoints_by_path:
                endpoints_by_path[path] = []
            endpoints_by_path[path].append((method, endpoint))

        # Print grouped
        for path in sorted(endpoints_by_path.keys()):
            print(f"📍 {path}")
            for method, endpoint in endpoints_by_path[path]:
                print(f"  {method:6} | Fields: {len(endpoint.request_body_fields)}")
                if endpoint.request_body_fields:
                    for field_name, field in list(endpoint.request_body_fields.items())[:3]:
                        prefix = "    ├─ " if field != list(endpoint.request_body_fields.values())[-1] else "    └─ "
                        print(f"{prefix}{field_name}: {field.type.value}")
                    if len(endpoint.request_body_fields) > 3:
                        print(f"    ... +{len(endpoint.request_body_fields) - 3} more")
            print()
