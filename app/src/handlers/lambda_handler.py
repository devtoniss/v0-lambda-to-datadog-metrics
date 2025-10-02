"""
Handler principal da função Lambda AWS.
Processa eventos do EventBridge, baixa CSV do S3 e envia métricas para o Datadog.
"""

import json
import logging
from typing import Dict, Any

from ..services.s3_service import S3Service
from ..services.csv_service import CSVService
from ..services.payload_service import PayloadService
from ..services.datadog_service import DatadogService
from ..config.settings import Settings
from ..utils.logger import configurar_logger

# Configurar logger
logger = configurar_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler principal da Lambda.
    
    Args:
        event: Evento do EventBridge contendo:
            - s3_bucket: Nome do bucket S3
            - s3_path: Caminho da pasta ou arquivo CSV no S3 (ex: 'rds/' ou 'rds/resultados_rds.csv')
            - payloads: Lista de templates de payload para gerar métricas
        context: Contexto da Lambda
        
    Returns:
        Dicionário com status da execução
    """
    try:
        logger.info(f"Iniciando processamento. Evento: {json.dumps(event)}")
        
        # Validar evento
        s3_bucket = event.get('s3_bucket')
        s3_path = event.get('s3_path')
        payloads = event.get('payloads', [])
        
        if not s3_bucket or not s3_path:
            raise ValueError("Parâmetros obrigatórios ausentes: s3_bucket, s3_path")
        
        if not payloads:
            raise ValueError("Nenhum template de payload fornecido no evento")
        
        if not isinstance(payloads, list):
            raise ValueError("Campo 'payloads' deve ser uma lista de templates")
        
        # Inicializar configurações e serviços
        settings = Settings()
        s3_service = S3Service(settings)
        csv_service = CSVService()
        payload_service = PayloadService()
        datadog_service = DatadogService(settings)
        
        # 1. Baixar CSV do S3
        logger.info(f"Baixando CSV de s3://{s3_bucket}/{s3_path}")
        caminho_local = s3_service.baixar_csv_da_pasta(s3_bucket, s3_path)
        
        # 2. Ler CSV genérico
        logger.info(f"Lendo CSV: {caminho_local}")
        linhas_csv = csv_service.ler_csv(caminho_local)
        
        if not linhas_csv:
            logger.warning("CSV vazio ou sem dados")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'mensagem': 'CSV vazio, nenhuma métrica para processar',
                    'linhas_processadas': 0
                })
            }
        
        # 3. Processar templates e gerar métricas
        logger.info(f"Processando {len(linhas_csv)} linhas com {len(payloads)} template(s)")
        metricas = payload_service.processar_templates(linhas_csv, payloads)
        
        if not metricas:
            logger.warning("Nenhuma métrica foi gerada dos templates")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'mensagem': 'Nenhuma métrica gerada dos templates',
                    'linhas_processadas': len(linhas_csv),
                    'metricas_geradas': 0
                })
            }
        
        # 4. Enviar métricas para o Datadog em lotes
        logger.info(f"Enviando {len(metricas)} métricas para o Datadog")
        resultado = datadog_service.enviar_metricas_em_lotes(metricas)
        
        # 5. Limpar arquivo temporário
        s3_service.limpar_arquivo_local(caminho_local)
        
        logger.info(
            f"Processamento concluído com sucesso. "
            f"Linhas: {len(linhas_csv)}, Métricas: {resultado['total_enviadas']}"
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'mensagem': 'Métricas enviadas com sucesso',
                'linhas_processadas': len(linhas_csv),
                'metricas_geradas': len(metricas),
                'metricas_enviadas': resultado['total_enviadas'],
                'lotes_enviados': resultado['lotes_enviados']
            })
        }
        
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'mensagem': 'Erro no processamento',
                'erro': str(e)
            })
        }
