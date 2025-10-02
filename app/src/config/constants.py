"""
Constantes e templates de métricas para o Datadog.
Centraliza configurações de cada tipo de métrica.
"""

from typing import Dict, Any, List
from enum import Enum


class TipoMetrica(str, Enum):
    """Tipos de métricas suportados."""
    ECS = "ecs"
    RDS = "rds"
    EC2 = "ec2"
    LAMBDA = "lambda"
    ALB = "alb"
    CLOUDFRONT = "cloudfront"
    CUSTOM = "custom"


class ConfiguracaoMetrica:
    """Configuração base para um tipo de métrica."""
    
    def __init__(
        self,
        prefixo: str,
        tags_padrao: List[str],
        tipo_padrao: str = "gauge",
        intervalo_padrao: int = 60,
        descricao: str = ""
    ):
        """
        Inicializa configuração de métrica.
        
        Args:
            prefixo: Prefixo para o nome da métrica (ex: 'aws.ecs')
            tags_padrao: Lista de tags padrão a adicionar
            tipo_padrao: Tipo padrão da métrica (gauge, count, rate)
            intervalo_padrao: Intervalo padrão em segundos
            descricao: Descrição do tipo de métrica
        """
        self.prefixo = prefixo
        self.tags_padrao = tags_padrao
        self.tipo_padrao = tipo_padrao
        self.intervalo_padrao = intervalo_padrao
        self.descricao = descricao


# Mapeamento de tipos de métrica para valores numéricos do Datadog
TIPOS_METRICA = {
    'gauge': 0,
    'count': 1,
    'rate': 2,
    'monotonic_count': 3
}


# Configurações de métricas por tipo
CONFIGURACOES_METRICAS: Dict[str, ConfiguracaoMetrica] = {
    TipoMetrica.ECS: ConfiguracaoMetrica(
        prefixo="aws.ecs",
        tags_padrao=["source:lambda", "aws_service:ecs"],
        tipo_padrao="gauge",
        intervalo_padrao=300,  # 5 minutos
        descricao="Métricas de containers ECS"
    ),
    
    TipoMetrica.RDS: ConfiguracaoMetrica(
        prefixo="aws.rds",
        tags_padrao=["source:lambda", "aws_service:rds"],
        tipo_padrao="gauge",
        intervalo_padrao=300,  # 5 minutos
        descricao="Métricas de bancos de dados RDS"
    ),
    
    TipoMetrica.EC2: ConfiguracaoMetrica(
        prefixo="aws.ec2",
        tags_padrao=["source:lambda", "aws_service:ec2"],
        tipo_padrao="gauge",
        intervalo_padrao=300,  # 5 minutos
        descricao="Métricas de instâncias EC2"
    ),
    
    TipoMetrica.LAMBDA: ConfiguracaoMetrica(
        prefixo="aws.lambda",
        tags_padrao=["source:lambda", "aws_service:lambda"],
        tipo_padrao="gauge",
        intervalo_padrao=60,  # 1 minuto
        descricao="Métricas de funções Lambda"
    ),
    
    TipoMetrica.ALB: ConfiguracaoMetrica(
        prefixo="aws.alb",
        tags_padrao=["source:lambda", "aws_service:alb"],
        tipo_padrao="count",
        intervalo_padrao=60,  # 1 minuto
        descricao="Métricas de Application Load Balancer"
    ),
    
    TipoMetrica.CLOUDFRONT: ConfiguracaoMetrica(
        prefixo="aws.cloudfront",
        tags_padrao=["source:lambda", "aws_service:cloudfront"],
        tipo_padrao="count",
        intervalo_padrao=300,  # 5 minutos
        descricao="Métricas de distribuições CloudFront"
    ),
    
    TipoMetrica.CUSTOM: ConfiguracaoMetrica(
        prefixo="custom",
        tags_padrao=["source:lambda"],
        tipo_padrao="gauge",
        intervalo_padrao=60,
        descricao="Métricas customizadas"
    )
}


# Mapeamento de nomes de métricas comuns por serviço
METRICAS_COMUNS = {
    TipoMetrica.ECS: {
        "cpu": "cpu_utilization",
        "memoria": "memory_utilization",
        "tarefas": "running_tasks_count",
        "servicos": "services_count"
    },
    
    TipoMetrica.RDS: {
        "cpu": "cpu_utilization",
        "conexoes": "database_connections",
        "iops": "iops",
        "latencia_leitura": "read_latency",
        "latencia_escrita": "write_latency",
        "espaco_livre": "free_storage_space"
    },
    
    TipoMetrica.EC2: {
        "cpu": "cpu_utilization",
        "rede_entrada": "network_in",
        "rede_saida": "network_out",
        "disco_leitura": "disk_read_bytes",
        "disco_escrita": "disk_write_bytes"
    },
    
    TipoMetrica.LAMBDA: {
        "invocacoes": "invocations",
        "erros": "errors",
        "duracao": "duration",
        "throttles": "throttles",
        "memoria_usada": "memory_used"
    },
    
    TipoMetrica.ALB: {
        "requisicoes": "request_count",
        "tempo_resposta": "target_response_time",
        "erros_4xx": "http_4xx_count",
        "erros_5xx": "http_5xx_count",
        "conexoes_ativas": "active_connection_count"
    },
    
    TipoMetrica.CLOUDFRONT: {
        "requisicoes": "requests",
        "bytes_baixados": "bytes_downloaded",
        "bytes_enviados": "bytes_uploaded",
        "erros_4xx": "4xx_error_rate",
        "erros_5xx": "5xx_error_rate"
    }
}


def obter_configuracao(tipo_metrica: str) -> ConfiguracaoMetrica:
    """
    Obtém configuração para um tipo de métrica.
    
    Args:
        tipo_metrica: Tipo da métrica
        
    Returns:
        Configuração da métrica
        
    Raises:
        ValueError: Se tipo não for suportado
    """
    tipo_metrica = tipo_metrica.lower()
    
    if tipo_metrica not in CONFIGURACOES_METRICAS:
        raise ValueError(
            f"Tipo de métrica '{tipo_metrica}' não suportado. "
            f"Tipos disponíveis: {list(CONFIGURACOES_METRICAS.keys())}"
        )
    
    return CONFIGURACOES_METRICAS[tipo_metrica]


def construir_nome_metrica(tipo_metrica: str, nome_curto: str) -> str:
    """
    Constrói nome completo da métrica com prefixo.
    
    Args:
        tipo_metrica: Tipo da métrica
        nome_curto: Nome curto da métrica (ex: 'cpu', 'memoria')
        
    Returns:
        Nome completo da métrica (ex: 'aws.ecs.cpu_utilization')
    """
    config = obter_configuracao(tipo_metrica)
    
    # Verificar se existe mapeamento comum
    if tipo_metrica in METRICAS_COMUNS:
        nome_mapeado = METRICAS_COMUNS[tipo_metrica].get(nome_curto, nome_curto)
    else:
        nome_mapeado = nome_curto
    
    return f"{config.prefixo}.{nome_mapeado}"
