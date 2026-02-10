"""Transformer registry."""
from typing import Dict, Any


class TransformerRegistry:
    """Registry of available transformers."""

    def __init__(self):
        """Initialize registry."""
        self.transformers = {
            "NONE": lambda x, **kw: x,
            "FORMAT_CPF": self._format_cpf,
            "FORMAT_CNPJ": self._format_cnpj,
            "FORMAT_DATE": self._format_date,
            "UPPERCASE": lambda x, **kw: str(x).upper() if x else x,
            "LOWERCASE": lambda x, **kw: str(x).lower() if x else x,
            "TRIM": lambda x, **kw: str(x).strip() if x else x,
        }

    def get(self, name: str):
        """Get transformer by name."""
        return self.transformers.get(name, self.transformers["NONE"])

    def transform(self, value: Any, transformer_name: str, **config) -> Any:
        """Apply transformation."""
        transformer = self.get(transformer_name)
        return transformer(value, **config)

    @staticmethod
    def _format_cpf(value: str, **config) -> str:
        """Format CPF."""
        if not value:
            return value

        clean = "".join(c for c in str(value) if c.isdigit())

        if len(clean) == 11:
            return f"{clean[:3]}.{clean[3:6]}.{clean[6:9]}-{clean[9:]}"

        return value

    @staticmethod
    def _format_cnpj(value: str, **config) -> str:
        """Format CNPJ."""
        if not value:
            return value

        clean = "".join(c for c in str(value) if c.isdigit())

        if len(clean) == 14:
            return f"{clean[:2]}.{clean[2:5]}.{clean[5:8]}/{clean[8:12]}-{clean[12:]}"

        return value

    @staticmethod
    def _format_date(value: str, **config) -> str:
        """Format date."""
        if not value:
            return value

        # Simple date format conversion
        date_format = config.get("format", "%Y-%m-%d")

        try:
            return str(value)  # Placeholder
        except Exception:
            return value
