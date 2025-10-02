"""
Serviço de processamento de templates de payload.
Avalia templates dinâmicos do EventBridge e gera métricas do Datadog.
"""

import time
from typing import List, Dict, Any, Optional
from ..utils.logger import configurar_logger

logger = configurar_logger(__name__)


class PayloadService:
    """Serviço para processar templates de payload e gerar métricas."""
    
    def __init__(self):
        """Inicializa o serviço de processamento de payloads."""
        pass
    
    def processar_templates(
        self, 
        linhas_csv: List[Dict[str, Any]], 
        templates_payload: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Processa templates de payload para cada linha do CSV.
        
        Args:
            linhas_csv: Lista de dicionários com dados do CSV
            templates_payload: Lista de templates de payload do EventBridge
            
        Returns:
            Lista de métricas no formato do Datadog
        """
        metricas = []
        timestamp_atual = int(time.time())
        
        logger.info(
            f"Processando {len(linhas_csv)} linhas com {len(templates_payload)} template(s)"
        )
        
        for idx, linha in enumerate(linhas_csv, start=1):
            try:
                # Processar cada template para esta linha
                for template_idx, template in enumerate(templates_payload, start=1):
                    metrica = self._processar_template(
                        linha, 
                        template, 
                        timestamp_atual,
                        idx,
                        template_idx
                    )
                    if metrica:
                        metricas.append(metrica)
                        
            except Exception as e:
                logger.warning(
                    f"Erro ao processar linha {idx} com templates: {e}. Linha: {linha}"
                )
                continue
        
        logger.info(f"Geradas {len(metricas)} métricas dos templates")
        return metricas
    
    def _processar_template(
        self,
        linha: Dict[str, Any],
        template: Dict[str, Any],
        timestamp_atual: int,
        linha_idx: int,
        template_idx: int
    ) -> Optional[Dict[str, Any]]:
        """
        Processa um template de payload para uma linha específica.
        
        Args:
            linha: Dicionário com dados da linha do CSV
            template: Template de payload do EventBridge
            timestamp_atual: Timestamp Unix atual
            linha_idx: Índice da linha (para logging)
            template_idx: Índice do template (para logging)
            
        Returns:
            Métrica no formato do Datadog ou None se inválida
        """
        try:
            # Criar contexto seguro para avaliação
            contexto = {
                'linha': linha,
                'timestamp': timestamp_atual,
                'int': int,
                'float': float,
                'str': str,
                'len': len,
            }
            
            # Processar cada campo do template
            metrica = {}
            
            # Metric name (obrigatório)
            if 'metric' not in template:
                logger.warning(f"Template {template_idx} sem campo 'metric'")
                return None
            
            metrica['metric'] = self._avaliar_campo(template['metric'], contexto)
            
            # Type (obrigatório)
            if 'type' not in template:
                logger.warning(f"Template {template_idx} sem campo 'type'")
                return None
            
            metrica['type'] = self._avaliar_campo(template['type'], contexto)
            
            # Points (obrigatório) - formato: [[timestamp, value]]
            if 'points' not in template:
                logger.warning(f"Template {template_idx} sem campo 'points'")
                return None
            
            points_template = template['points']
            if isinstance(points_template, list) and len(points_template) > 0:
                # Avaliar cada ponto
                points = []
                for point in points_template:
                    if isinstance(point, dict):
                        # Formato: {"timestamp": ..., "value": ...}
                        ts = self._avaliar_campo(point.get('timestamp', timestamp_atual), contexto)
                        val = self._avaliar_campo(point.get('value'), contexto)
                        points.append([int(ts), float(val)])
                    elif isinstance(point, list) and len(point) == 2:
                        # Formato: [timestamp, value]
                        ts = self._avaliar_campo(point[0], contexto)
                        val = self._avaliar_campo(point[1], contexto)
                        points.append([int(ts), float(val)])
                
                metrica['points'] = points
            else:
                logger.warning(f"Template {template_idx} com formato de 'points' inválido")
                return None
            
            # Tags (opcional)
            if 'tags' in template:
                tags_template = template['tags']
                if isinstance(tags_template, list):
                    tags = []
                    for tag in tags_template:
                        tag_avaliada = self._avaliar_campo(tag, contexto)
                        if tag_avaliada:
                            tags.append(str(tag_avaliada))
                    metrica['tags'] = tags
            
            # Host (opcional)
            if 'host' in template:
                host = self._avaliar_campo(template['host'], contexto)
                if host:
                    metrica['host'] = str(host)
            
            # Interval (opcional)
            if 'interval' in template:
                interval = self._avaliar_campo(template['interval'], contexto)
                if interval:
                    metrica['interval'] = int(interval)
            
            # Resources (opcional)
            if 'resources' in template:
                resources_template = template['resources']
                if isinstance(resources_template, list):
                    resources = []
                    for resource in resources_template:
                        if isinstance(resource, dict):
                            resource_avaliado = {
                                'name': str(self._avaliar_campo(resource.get('name', ''), contexto)),
                                'type': str(self._avaliar_campo(resource.get('type', ''), contexto))
                            }
                            resources.append(resource_avaliado)
                    if resources:
                        metrica['resources'] = resources
            
            return metrica
            
        except Exception as e:
            logger.warning(
                f"Erro ao processar template {template_idx} para linha {linha_idx}: {e}"
            )
            return None
    
    def _avaliar_campo(self, campo: Any, contexto: Dict[str, Any]) -> Any:
        """
        Avalia um campo do template, substituindo referências a variáveis.
        
        Args:
            campo: Campo a ser avaliado (pode ser string, número, etc.)
            contexto: Contexto com variáveis disponíveis
            
        Returns:
            Valor avaliado
        """
        # Se for string e contiver referências Python, avaliar
        if isinstance(campo, str):
            # Verificar se é uma expressão Python (contém 'linha[' ou 'timestamp')
            if 'linha[' in campo or 'timestamp' in campo or 'float(' in campo or 'int(' in campo or 'str(' in campo:
                try:
                    # Avaliar expressão de forma segura
                    resultado = eval(campo, {"__builtins__": {}}, contexto)
                    return resultado
                except Exception as e:
                    logger.warning(f"Erro ao avaliar expressão '{campo}': {e}")
                    return campo
            else:
                # String literal, retornar como está
                return campo
        else:
            # Não é string, retornar como está
            return campo
