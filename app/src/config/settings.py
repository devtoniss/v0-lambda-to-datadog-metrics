"""
Configurações da aplicação.
Centraliza todas as variáveis de ambiente e constantes.
"""

import os
from typing import Optional


class Settings:
    """Classe de configuração centralizada."""
    
    def __init__(self):
        # Configurações do Datadog
        self.datadog_api_key: str = os.environ.get('DATADOG_API_KEY', '')
        self.datadog_app_key: str = os.environ.get('DATADOG_APP_KEY', '')
        self.datadog_site: str = os.environ.get('DATADOG_SITE', 'datadoghq.com')
        self.datadog_api_url: str = f"https://api.{self.datadog_site}/api/v2/series"
        
        # Configurações de lote
        self.tamanho_lote: int = int(os.environ.get('TAMANHO_LOTE', '1000'))
        self.timeout_request: int = int(os.environ.get('TIMEOUT_REQUEST', '30'))
        
        # Configurações do S3
        self.diretorio_temp: str = os.environ.get('DIRETORIO_TEMP', '/tmp')
        
        # Configurações de retry
        self.max_tentativas: int = int(os.environ.get('MAX_TENTATIVAS', '3'))
        self.delay_retry: int = int(os.environ.get('DELAY_RETRY', '2'))
        
        # Validar configurações obrigatórias
        self._validar_config()
    
    def _validar_config(self) -> None:
        """Valida se as configurações obrigatórias estão presentes."""
        if not self.datadog_api_key:
            raise ValueError("DATADOG_API_KEY não configurada")
        
        if not self.datadog_app_key:
            raise ValueError("DATADOG_APP_KEY não configurada")
