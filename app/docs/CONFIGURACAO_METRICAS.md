# Configuração de Métricas

Este documento explica como configurar e personalizar as métricas enviadas ao Datadog.

## Estrutura de Configuração

A aplicação utiliza uma abordagem híbrida para configuração de métricas:

### 1. Constants.py - Templates Base

O arquivo `app/src/config/constants.py` contém:

- **Prefixos de métricas**: Define o namespace de cada tipo (ex: `aws.ecs`, `aws.rds`)
- **Tags padrão**: Tags aplicadas automaticamente a todas as métricas do tipo
- **Tipo padrão**: Se a métrica é gauge, count, rate, etc.
- **Intervalo padrão**: Frequência de coleta em segundos

#### Exemplo de Configuração:

\`\`\`python
TipoMetrica.RDS: ConfiguracaoMetrica(
    prefixo="aws.rds",
    tags_padrao=["source:lambda", "aws_service:rds"],
    tipo_padrao="gauge",
    intervalo_padrao=300,  # 5 minutos
    descricao="Métricas de bancos de dados RDS"
)
\`\`\`

### 2. EventBridge - Informações de Execução

O evento do EventBridge passa apenas informações essenciais:

\`\`\`json
{
  "s3_bucket": "meu-bucket-metricas",
  "s3_key": "metricas/2024/01/15/rds-metricas.csv",
  "arquivo_nome": "rds-metricas.csv",
  "tipo_metrica": "rds"
}
\`\`\`

### 3. CSV - Dados Dinâmicos

O arquivo CSV contém os valores e metadados específicos de cada métrica:

\`\`\`csv
nome_metrica,valor,timestamp,tags,tipo,host,intervalo
cpu,45.2,1705315200,env:producao;instance:prod-db-01,gauge,rds-prod-01,300
conexoes,87,1705315200,env:producao;instance:prod-db-01,gauge,rds-prod-01,300
\`\`\`

## Tipos de Métricas Suportados

### AWS ECS
- **Prefixo**: `aws.ecs`
- **Métricas comuns**: cpu, memoria, tarefas, servicos

### AWS RDS
- **Prefixo**: `aws.rds`
- **Métricas comuns**: cpu, conexoes, iops, latencia_leitura, latencia_escrita, espaco_livre

### AWS EC2
- **Prefixo**: `aws.ec2`
- **Métricas comuns**: cpu, rede_entrada, rede_saida, disco_leitura, disco_escrita

### AWS Lambda
- **Prefixo**: `aws.lambda`
- **Métricas comuns**: invocacoes, erros, duracao, throttles, memoria_usada

### AWS ALB
- **Prefixo**: `aws.alb`
- **Métricas comuns**: requisicoes, tempo_resposta, erros_4xx, erros_5xx, conexoes_ativas

### AWS CloudFront
- **Prefixo**: `aws.cloudfront`
- **Métricas comuns**: requisicoes, bytes_baixados, bytes_enviados, erros_4xx, erros_5xx

### Custom
- **Prefixo**: `custom`
- **Uso**: Para métricas personalizadas que não se encaixam nos tipos AWS

## Adicionando Novo Tipo de Métrica

Para adicionar um novo tipo de métrica:

1. **Adicione o tipo no Enum**:
\`\`\`python
class TipoMetrica(str, Enum):
    # ... tipos existentes ...
    ELASTICACHE = "elasticache"
\`\`\`

2. **Configure o template**:
\`\`\`python
TipoMetrica.ELASTICACHE: ConfiguracaoMetrica(
    prefixo="aws.elasticache",
    tags_padrao=["source:lambda", "aws_service:elasticache"],
    tipo_padrao="gauge",
    intervalo_padrao=60,
    descricao="Métricas de clusters ElastiCache"
)
\`\`\`

3. **Adicione métricas comuns** (opcional):
\`\`\`python
TipoMetrica.ELASTICACHE: {
    "cpu": "cpu_utilization",
    "memoria": "memory_utilization",
    "conexoes": "current_connections"
}
\`\`\`

4. **Crie o CSV** com as métricas:
\`\`\`csv
nome_metrica,valor,timestamp,tags,tipo
cpu,65.5,1705315200,env:producao;cluster:redis-01,gauge
memoria,78.2,1705315200,env:producao;cluster:redis-01,gauge
\`\`\`

## Vantagens desta Abordagem

1. **Consistência**: Templates garantem nomenclatura e tags padronizadas
2. **Flexibilidade**: CSV permite dados dinâmicos sem redeploy
3. **Manutenibilidade**: Configurações centralizadas e versionadas
4. **Escalabilidade**: Fácil adicionar novos tipos de métricas
5. **Simplicidade**: EventBridge mantém-se simples e focado
