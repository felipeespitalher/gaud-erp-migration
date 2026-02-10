"""Configuração da aplicação."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class GaudApiConfig:
    """Configuração da API Gaud."""

    base_url: str = "http://localhost:8080"
    api_key: str = ""  # Lê de .env ou user input
    timeout: int = 60
    batch_size: int = 500

    @classmethod
    def from_env(cls) -> "GaudApiConfig":
        """Carrega config de variáveis de ambiente."""
        return cls(
            base_url=os.getenv("GAUD_API_URL", "http://localhost:8080"),
            api_key=os.getenv("GAUD_API_KEY", ""),
        )


@dataclass
class AppConfig:
    """Configuração da aplicação."""

    backup_dir: str = "./backup"
    output_dir: str = "./output"
    config_dir: str = "./config"
    gaud_api: GaudApiConfig = None

    def __post_init__(self):
        """Inicializa valores padrão."""
        if self.gaud_api is None:
            self.gaud_api = GaudApiConfig.from_env()

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Carrega config de variáveis de ambiente."""
        return cls(
            backup_dir=os.getenv("MIGRATION_BACKUP_DIR", "./backup"),
            output_dir=os.getenv("MIGRATION_OUTPUT_DIR", "./output"),
            config_dir=os.getenv("MIGRATION_CONFIG_DIR", "./config"),
            gaud_api=GaudApiConfig.from_env(),
        )


# Instância global
app_config = AppConfig()
