"""
Serviço para operações com AWS S3.
Responsável por baixar arquivos e gerenciar armazenamento temporário.
"""

import boto3
import os
from typing import Optional
from botocore.exceptions import ClientError

from ..config.settings import Settings
from ..utils.logger import configurar_logger

logger = configurar_logger(__name__)


class S3Service:
    """Serviço para gerenciar operações com S3."""
    
    def __init__(self, settings: Settings):
        """
        Inicializa o serviço do S3.
        
        Args:
            settings: Objeto de configurações
        """
        self.settings = settings
        self.s3_client = boto3.client('s3')
    
    def baixar_csv_da_pasta(self, bucket: str, pasta: str) -> str:
        """
        Baixa o arquivo CSV de uma pasta no S3.
        Se a pasta contiver múltiplos CSVs, baixa o primeiro encontrado.
        
        Args:
            bucket: Nome do bucket S3
            pasta: Caminho da pasta no S3 (ex: 'rds/' ou 'rds/resultados_rds.csv')
            
        Returns:
            Caminho completo do arquivo baixado
            
        Raises:
            ClientError: Se houver erro ao acessar o S3
            FileNotFoundError: Se nenhum CSV for encontrado
        """
        try:
            # Se o path já é um arquivo .csv, baixar diretamente
            if pasta.endswith('.csv'):
                nome_arquivo = os.path.basename(pasta)
                return self.baixar_arquivo(bucket, pasta, nome_arquivo)
            
            # Caso contrário, listar arquivos na pasta e encontrar CSV
            logger.info(f"Listando arquivos em s3://{bucket}/{pasta}")
            
            # Garantir que a pasta termina com /
            if not pasta.endswith('/'):
                pasta += '/'
            
            resposta = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=pasta
            )
            
            if 'Contents' not in resposta:
                raise FileNotFoundError(f"Nenhum arquivo encontrado em s3://{bucket}/{pasta}")
            
            # Encontrar primeiro arquivo CSV
            for obj in resposta['Contents']:
                key = obj['Key']
                if key.endswith('.csv'):
                    nome_arquivo = os.path.basename(key)
                    logger.info(f"Arquivo CSV encontrado: {key}")
                    return self.baixar_arquivo(bucket, key, nome_arquivo)
            
            raise FileNotFoundError(f"Nenhum arquivo CSV encontrado em s3://{bucket}/{pasta}")
            
        except ClientError as e:
            logger.error(f"Erro ao acessar S3: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar CSV: {e}")
            raise
    
    def baixar_arquivo(self, bucket: str, key: str, nome_arquivo: str) -> str:
        """
        Baixa um arquivo do S3 para o diretório temporário.
        
        Args:
            bucket: Nome do bucket S3
            key: Caminho do arquivo no S3
            nome_arquivo: Nome do arquivo para salvar localmente
            
        Returns:
            Caminho completo do arquivo baixado
            
        Raises:
            ClientError: Se houver erro ao baixar do S3
        """
        try:
            caminho_local = os.path.join(self.settings.diretorio_temp, nome_arquivo)
            
            logger.info(f"Baixando s3://{bucket}/{key} para {caminho_local}")
            
            self.s3_client.download_file(bucket, key, caminho_local)
            
            # Verificar se o arquivo foi baixado
            if not os.path.exists(caminho_local):
                raise FileNotFoundError(f"Arquivo não encontrado após download: {caminho_local}")
            
            tamanho = os.path.getsize(caminho_local)
            logger.info(f"Arquivo baixado com sucesso. Tamanho: {tamanho} bytes")
            
            return caminho_local
            
        except ClientError as e:
            logger.error(f"Erro ao baixar arquivo do S3: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao baixar arquivo: {e}")
            raise
    
    def limpar_arquivo_local(self, caminho: str) -> None:
        """
        Remove arquivo temporário do sistema de arquivos.
        
        Args:
            caminho: Caminho do arquivo a ser removido
        """
        try:
            if os.path.exists(caminho):
                os.remove(caminho)
                logger.info(f"Arquivo temporário removido: {caminho}")
        except Exception as e:
            logger.warning(f"Erro ao remover arquivo temporário {caminho}: {e}")
