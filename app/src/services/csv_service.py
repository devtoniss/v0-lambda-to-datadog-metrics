"""
Serviço de leitura de arquivos CSV genéricos.
Lê qualquer estrutura de CSV e retorna como lista de dicionários.
"""

import csv
from typing import List, Dict, Any

from ..utils.logger import configurar_logger

logger = configurar_logger(__name__)


class CSVService:
    """Serviço para ler arquivos CSV genéricos."""
    
    def __init__(self):
        """Inicializa o serviço de leitura de CSV."""
        pass
    
    def ler_csv(self, caminho_arquivo: str) -> List[Dict[str, Any]]:
        """
        Lê arquivo CSV e retorna lista de dicionários.
        
        Args:
            caminho_arquivo: Caminho do arquivo CSV
            
        Returns:
            Lista de dicionários, onde cada dicionário representa uma linha
        """
        linhas = []
        
        try:
            logger.info(f"Lendo arquivo CSV: {caminho_arquivo}")
            
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                leitor = csv.DictReader(arquivo)
                
                # Validar que o CSV tem colunas
                if not leitor.fieldnames:
                    raise ValueError("CSV não contém colunas (header)")
                
                logger.info(f"Colunas encontradas: {leitor.fieldnames}")
                
                # Ler todas as linhas
                for idx, linha in enumerate(leitor, start=1):
                    # Converter valores numéricos quando possível
                    linha_processada = self._processar_linha(linha)
                    linhas.append(linha_processada)
                
            logger.info(f"Lidas {len(linhas)} linhas do CSV")
            return linhas
            
        except Exception as e:
            logger.error(f"Erro ao ler CSV: {e}")
            raise
    
    def _processar_linha(self, linha: Dict[str, str]) -> Dict[str, Any]:
        """
        Processa uma linha do CSV, convertendo tipos quando possível.
        
        Args:
            linha: Dicionário com valores string do CSV
            
        Returns:
            Dicionário com valores convertidos
        """
        linha_processada = {}
        
        for chave, valor in linha.items():
            # Tentar converter para número
            if valor:
                # Tentar int
                try:
                    linha_processada[chave] = int(valor)
                    continue
                except ValueError:
                    pass
                
                # Tentar float
                try:
                    linha_processada[chave] = float(valor)
                    continue
                except ValueError:
                    pass
            
            # Manter como string
            linha_processada[chave] = valor
        
        return linha_processada
