"""SQL Dialect Detection."""
import re
from typing import Optional


class SqlDialectDetector:
    """Detecta qual SQL dialect está sendo usado."""

    @staticmethod
    def detect(sql_content: str) -> str:
        """
        Detecta o dialect SQL do conteúdo.

        Returns:
            str: 'postgresql', 'mysql', 'oracle', 'firebird', ou 'unknown'
        """
        content_lower = sql_content.lower()

        # PostgreSQL indicators
        postgresql_indicators = [
            r'\bSERIAL\b',  # SERIAL, BIGSERIAL
            r'\bBIGSERIAL\b',
            r'\bUUID\b',
            r'\bCREATE\s+TABLE.*USING\s+btree',
            r'ON\s+CONFLICT',
            r'\bENUM\s*\(',  # PostgreSQL ENUM
            r'\\d\+',  # psql meta-commands
            r'\bGENERATED\s+ALWAYS\b',
        ]

        # MySQL indicators
        mysql_indicators = [
            r'AUTO_INCREMENT',
            r'ENGINE\s*=\s*\w+',  # ENGINE=InnoDB, ENGINE=MyISAM
            r'COLLATE\s+\w+',
            r'`\w+`\s*[\s,]',  # Backticks for identifiers
            r'CHARACTER\s+SET',
            r'COLLATION',
            r'AUTOINCREMENT',  # SQLite uses this too
        ]

        # Oracle indicators
        oracle_indicators = [
            r'\bNUMBER\s*\(',
            r'\bCLOB\b',
            r'\bBLOB\b',
            r'\bCREATE\s+SEQUENCE',
            r'\bSTART\s+WITH',
            r'NEXTVAL',
            r'\bSYSDATE\b',
            r'\bTO_DATE\b',
            r'\bTO_CHAR\b',
        ]

        # Firebird indicators
        firebird_indicators = [
            r'BLOB\s+SUB_TYPE',
            r'SEGMENT\s+SIZE',
            r'COMPUTED\s+BY',
            r'BEFORE\s+(?:INSERT|UPDATE|DELETE)',
            r'COLLATE\s+\w+',
            r'\bDATABASE\b',  # CREATE DATABASE (Firebird specific)
        ]

        # Count matches
        postgresql_score = sum(
            1 for pattern in postgresql_indicators
            if re.search(pattern, content_lower)
        )
        mysql_score = sum(
            1 for pattern in mysql_indicators
            if re.search(pattern, content_lower)
        )
        oracle_score = sum(
            1 for pattern in oracle_indicators
            if re.search(pattern, content_lower)
        )
        firebird_score = sum(
            1 for pattern in firebird_indicators
            if re.search(pattern, content_lower)
        )

        scores = {
            'postgresql': postgresql_score,
            'mysql': mysql_score,
            'oracle': oracle_score,
            'firebird': firebird_score,
        }

        # Return dialect with highest score
        best_dialect = max(scores, key=scores.get)

        # If all scores are 0, return unknown
        if scores[best_dialect] == 0:
            return 'unknown'

        return best_dialect

    @staticmethod
    def suggest_dialects(sql_content: str) -> dict:
        """
        Retorna um dicionário com scores de cada dialect.

        Returns:
            dict: {dialect: score, ...}
        """
        content_lower = sql_content.lower()

        postgresql_indicators = [
            r'\bSERIAL\b',
            r'\bBIGSERIAL\b',
            r'\bUUID\b',
            r'ON\s+CONFLICT',
        ]
        mysql_indicators = [
            r'AUTO_INCREMENT',
            r'ENGINE\s*=',
            r'`\w+`',
        ]
        oracle_indicators = [
            r'\bNUMBER\s*\(',
            r'\bCLOB\b',
            r'\bBLOB\b',
        ]
        firebird_indicators = [
            r'BLOB\s+SUB_TYPE',
            r'SEGMENT\s+SIZE',
        ]

        return {
            'postgresql': sum(1 for p in postgresql_indicators if re.search(p, content_lower)),
            'mysql': sum(1 for p in mysql_indicators if re.search(p, content_lower)),
            'oracle': sum(1 for p in oracle_indicators if re.search(p, content_lower)),
            'firebird': sum(1 for p in firebird_indicators if re.search(p, content_lower)),
        }
