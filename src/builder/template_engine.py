"""
Template Engine - Evaluates template expressions for dynamic payload building

Supports:
- Variable substitution (${variable})
- Conditional expressions (if/else)
- Simple arithmetic
- Method calls
"""

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Simple template engine for Gaud payload generation"""

    # Pattern for variable substitution: ${var_name}
    VARIABLE_PATTERN = re.compile(r'\$\{([^}]+)\}')

    # Pattern for conditional: ${if condition ? true_value : false_value}
    CONDITIONAL_PATTERN = re.compile(r'\$\{if\s+([^?]+)\s*\?\s*([^:]+)\s*:\s*([^}]+)\}')

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        Initialize TemplateEngine

        Args:
            context: Dictionary of variables available for substitution
        """
        self.context = context or {}

    def evaluate(self, template: str) -> Any:
        """
        Evaluate a template string

        Args:
            template: Template string (e.g., "${column_name}")

        Returns:
            Evaluated value
        """
        if not isinstance(template, str):
            return template

        # Handle conditionals first
        template = self._evaluate_conditionals(template)

        # Handle variables
        template = self._evaluate_variables(template)

        return template

    def _evaluate_variables(self, template: str) -> str:
        """Substitute variables in template"""
        def replace_var(match):
            var_name = match.group(1).strip()
            value = self.context.get(var_name)

            if value is None:
                logger.warning(f"Variable not found in context: {var_name}")
                return ""

            return str(value)

        return self.VARIABLE_PATTERN.sub(replace_var, template)

    def _evaluate_conditionals(self, template: str) -> str:
        """Evaluate conditional expressions"""
        def evaluate_condition(condition: str) -> bool:
            """Evaluate a condition (simple implementation)"""
            condition = condition.strip()

            # Check if variable exists in context
            if condition in self.context:
                return bool(self.context[condition])

            # Try to parse as comparison (e.g., "weight > 10")
            # For now, just check existence
            return condition in self.context

        def replace_conditional(match):
            condition = match.group(1)
            true_value = match.group(2).strip()
            false_value = match.group(3).strip()

            if evaluate_condition(condition):
                return true_value
            else:
                return false_value

        return self.CONDITIONAL_PATTERN.sub(replace_conditional, template)

    def set_context(self, context: Dict[str, Any]) -> None:
        """Update template context"""
        self.context = context

    def update_context(self, **kwargs) -> None:
        """Update template context with keyword arguments"""
        self.context.update(kwargs)

    @staticmethod
    def escape_string(value: str) -> str:
        """Escape special characters in string for API"""
        if value is None:
            return None

        value = str(value)
        # Escape quotes
        value = value.replace('"', '\\"')
        # Escape newlines
        value = value.replace('\n', '\\n')
        # Escape tabs
        value = value.replace('\t', '\\t')

        return value
