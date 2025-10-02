# Enviando Múltiplas Métricas

Este documento explica como enviar múltiplas métricas diferentes no mesmo arquivo CSV.

## Visão Geral

A Lambda suporta o envio de múltiplas métricas simultaneamente através de um único arquivo CSV. Cada linha do CSV representa uma métrica individual que será enviada ao Datadog.

## Formato do CSV

### Colunas Obrigatórias

- `nome_metrica`: Nome da métrica (pode ser nome curto ou completo)
- `valor`: Valor numérico da métrica

### Colunas Opcionais

- `timestamp`: Timestamp Unix (usa tempo atual se não fornecido)
- `tags`: Tags separadas por vírgula (ex: `env:prod,service:api`)
- `tipo`: Tipo da métrica (`gauge`, `count`, `rate`, `monotonic_count`)
- `host`: Nome do host
- `intervalo`: Intervalo em segundos
- `resources_name`: Nome do recurso
- `resources_type`: Tipo do recurso (`container`, `host`, `service`)

## Exemplo Prático

### CSV com Múltiplas Métricas

\`\`\`csv
nome_metrica,valor,timestamp,tags,tipo,resources_name,resources_type
latencia.request,120,1698667200,env:producao;servico:api;rota:/login,gauge,api-login,container
erros.request,3,1698667200,env:producao;servico:api;rota:/login,count,api-login,container
qtd_requisicoes,57,1698667200,env:producao;servico:api;rota:/login,count,api-login,container
\`\`\`

### Payload Gerado para o Datadog

\`\`\`json
{
  "series": [
    {
      "metric": "custom.latencia.request",
      "type": 0,
      "points": [[1698667200, 120]],
      "tags": ["source:lambda", "env:producao", "servico:api", "rota:/login"],
      "resources": [
        {
          "name": "api-login",
          "type": "container"
        }
      ]
    },
    {
      "metric": "custom.erros.request",
      "type": 1,
      "points": [[1698667200, 3]],
      "tags": ["source:lambda", "env:producao", "servico:api", "rota:/login"],
      "resources": [
        {
          "name": "api-login",
          "type": "container"
        }
      ]
    },
    {
      "metric": "custom.qtd_requisicoes",
      "type": 1,
      "points": [[1698667200, 57]],
      "tags": ["source:lambda", "env:producao", "servico:api", "rota:/login"],
      "resources": [
        {
          "name": "api-login",
          "type": "container"
        }
      ]
    }
  ]
}
\`\`\`

## Tipos de Métricas

### Gauge (type: 0)
Representa um valor em um ponto específico no tempo.
- **Exemplo**: Latência, uso de CPU, temperatura

### Count (type: 1)
Representa uma contagem de eventos.
- **Exemplo**: Número de requisições, erros, transações

### Rate (type: 2)
Representa uma taxa de mudança.
- **Exemplo**: Requisições por segundo, bytes por segundo

### Monotonic Count (type: 3)
Contador que só aumenta (nunca diminui).
- **Exemplo**: Total de requisições desde o início

## Envio em Lotes

A Lambda automaticamente divide as métricas em lotes de até 1000 métricas por requisição ao Datadog, garantindo:

- **Performance**: Envio otimizado em lotes grandes
- **Confiabilidade**: Retry automático em caso de falha
- **Escalabilidade**: Suporta milhares de métricas por execução

## Exemplo Completo: RDS

\`\`\`csv
nome_metrica,valor,timestamp,tags,tipo,host,intervalo
cpu,45.2,1705315200,env:producao;instance:prod-db-01,gauge,rds-prod-01,300
conexoes,87,1705315200,env:producao;instance:prod-db-01,gauge,rds-prod-01,300
iops,1250,1705315200,env:producao;instance:prod-db-01,gauge,rds-prod-01,300
\`\`\`

Este CSV gerará 3 métricas diferentes:
- `aws.rds.cpu_utilization`
- `aws.rds.database_connections`
- `aws.rds.iops`

Todas com as tags padrão do RDS (`source:lambda`, `aws_service:rds`) mais as tags específicas do CSV.

## Boas Práticas

1. **Agrupe métricas relacionadas**: Coloque métricas do mesmo recurso no mesmo CSV
2. **Use timestamps consistentes**: Para métricas do mesmo momento, use o mesmo timestamp
3. **Mantenha tags consistentes**: Use as mesmas tags para métricas relacionadas
4. **Limite razoável**: Embora suporte milhares, mantenha CSVs com tamanho gerenciável
5. **Nomes descritivos**: Use nomes de métricas que facilitem identificação no Datadog
