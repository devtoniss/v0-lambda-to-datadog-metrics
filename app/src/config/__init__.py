"""
Módulo de configurações da aplicação.
"""

from .settings import Settings
from .constants import (
    TipoMetrica,
    ConfiguracaoMetrica,
    CONFIGURACOES_METRICAS,
    METRICAS_COMUNS,
    TIPOS_METRICA,
    obter_configuracao,
    construir_nome_metrica
)

__all__ = [
    'Settings',
    'TipoMetrica',
    'ConfiguracaoMetrica',
    'CONFIGURACOES_METRICAS',
    'METRICAS_COMUNS',
    'TIPOS_METRICA',
    'obter_configuracao',
    'construir_nome_metrica'
]
