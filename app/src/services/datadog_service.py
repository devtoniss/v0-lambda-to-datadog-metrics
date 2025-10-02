"""
Serviço para envio de métricas ao Datadog.
Gerencia envio em lotes e retry de requisições.
"""

import requests
from typing import List, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config.settings import Settings
from ..utils.logger import configurar_logger

logger = configurar_logger(__name__)


class DatadogService:
    """Serviço para interação com a API do Datadog."""
    
    def __init__(self, settings: Settings):
        """
        Inicializa o serviço do Datadog.
        
        Args:
            settings: Objeto de configurações
        """
        self.settings = settings
        self.session = self._criar_sessao()
    
    def _criar_sessao(self) -> requests.Session:
        """
        Cria sessão HTTP com retry automático.
        
        Returns:
            Sessão configurada
        """
        sessao = requests.Session()
        
        # Configurar retry
        retry_strategy = Retry(
            total=self.settings.max_tentativas,
            backoff_factor=self.settings.delay_retry,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        sessao.mount("https://", adapter)
        sessao.mount("http://", adapter)
        
        return sessao
    
    def enviar_metricas_em_lotes(self, metricas: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Envia métricas para o Datadog em lotes.
        
        Args:
            metricas: Lista de métricas a enviar
            
        Returns:
            Dicionário com estatísticas do envio
        """
        total_metricas = len(metricas)
        tamanho_lote = self.settings.tamanho_lote
        total_enviadas = 0
        lotes_enviados = 0
        erros = 0
        
        logger.info(f"Iniciando envio de {total_metricas} métricas em lotes de {tamanho_lote}")
        
        # Dividir em lotes
        for i in range(0, total_metricas, tamanho_lote):
            lote = metricas[i:i + tamanho_lote]
            lote_numero = (i // tamanho_lote) + 1
            total_lotes = (total_metricas + tamanho_lote - 1) // tamanho_lote
            
            logger.info(f"Enviando lote {lote_numero}/{total_lotes} com {len(lote)} métricas")
            
            try:
                self._enviar_lote(lote)
                total_enviadas += len(lote)
                lotes_enviados += 1
                logger.info(f"Lote {lote_numero} enviado com sucesso")
                
            except Exception as e:
                erros += 1
                logger.error(f"Erro ao enviar lote {lote_numero}: {e}")
                # Continua processando os próximos lotes
                continue
        
        resultado = {
            'total_enviadas': total_enviadas,
            'lotes_enviados': lotes_enviados,
            'erros': erros,
            'total_metricas': total_metricas
        }
        
        logger.info(f"Envio concluído: {resultado}")
        return resultado
    
    def _enviar_lote(self, lote: List[Dict[str, Any]]) -> None:
        """
        Envia um lote de métricas para o Datadog.
        
        Args:
            lote: Lista de métricas do lote
            
        Raises:
            requests.RequestException: Se houver erro na requisição
        """
        payload = {
            'series': lote
        }
        
        headers = {
            'Content-Type': 'application/json',
            'DD-API-KEY': self.settings.datadog_api_key,
        }
        
        # Adicionar DD-APPLICATION-KEY se disponível (opcional na v2)
        if self.settings.datadog_app_key:
            headers['DD-APPLICATION-KEY'] = self.settings.datadog_app_key
        
        logger.debug(f"Payload sendo enviado: {payload}")
        
        try:
            resposta = self.session.post(
                self.settings.datadog_api_url,
                json=payload,
                headers=headers,
                timeout=self.settings.timeout_request
            )
            
            resposta.raise_for_status()
            
            logger.debug(f"Resposta do Datadog: {resposta.status_code} - {resposta.text}")
            
        except requests.RequestException as e:
            logger.error(f"Erro na requisição ao Datadog: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Resposta de erro: {e.response.text}")
                logger.error(f"Payload que causou erro: {payload}")
            raise
