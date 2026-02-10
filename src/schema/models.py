"""Modelos para representar schema de banco de dados."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class ForeignKey:
    """Representa uma chave estrangeira."""

    column: str
    referenced_table: str
    referenced_column: str


@dataclass
class Constraint:
    """Representa uma constraint."""

    name: str
    type: str  # "PRIMARY_KEY", "UNIQUE", "CHECK", "FOREIGN_KEY"
    columns: List[str]


@dataclass
class SourceColumn:
    """Representa uma coluna na tabela fonte."""

    name: str
    type: str  # VARCHAR, INT, DATE, BOOLEAN, UUID, etc
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False
    unique: bool = False
    auto_increment: bool = False

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, SourceColumn):
            return self.name == other.name
        return False


@dataclass
class SourceTable:
    """Representa uma tabela na fonte."""

    name: str
    columns: List[SourceColumn] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[ForeignKey] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    estimated_rows: int = 0

    def get_column(self, name: str) -> Optional[SourceColumn]:
        """Retorna coluna pelo nome."""
        for col in self.columns:
            if col.name.lower() == name.lower():
                return col
        return None


@dataclass
class SourceSchema:
    """Representa o schema completo da fonte."""

    tables: List[SourceTable] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    database_type: str = "unknown"  # "postgresql", "mysql", "oracle", etc
    total_estimated_rows: int = 0

    def get_table(self, name: str) -> Optional[SourceTable]:
        """Retorna tabela pelo nome."""
        for table in self.tables:
            if table.name.lower() == name.lower():
                return table
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "database_type": self.database_type,
            "created_at": self.created_at.isoformat(),
            "total_tables": len(self.tables),
            "total_estimated_rows": self.total_estimated_rows,
            "tables": [
                {
                    "name": table.name,
                    "estimated_rows": table.estimated_rows,
                    "columns": [
                        {
                            "name": col.name,
                            "type": col.type,
                            "nullable": col.nullable,
                            "primary_key": col.primary_key,
                            "unique": col.unique,
                            "auto_increment": col.auto_increment,
                        }
                        for col in table.columns
                    ],
                    "primary_keys": table.primary_keys,
                    "foreign_keys": [
                        {
                            "column": fk.column,
                            "referenced_table": fk.referenced_table,
                            "referenced_column": fk.referenced_column,
                        }
                        for fk in table.foreign_keys
                    ],
                }
                for table in self.tables
            ],
        }
