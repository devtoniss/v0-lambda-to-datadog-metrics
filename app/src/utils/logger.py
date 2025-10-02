"""
Utilitário para configuração de logging.
"""

import logging
import sys
from typing import Optional


def configurar_logger(
    nome: str,
    nivel: int = logging.INFO,
    formato: Optional[str] = None
) -> logging.Logger:
    """
    Configura e retorna um logger.
    
    Args:
        nome: Nome do logger
        nivel: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        formato: Formato customizado de log (opcional)
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(nome)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(nivel)
    
    # Criar handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(nivel)
    
    # Formato padrão
    if formato is None:
        formato = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(formato)
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger
