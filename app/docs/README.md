# Lambda AWS - Métricas Customizadas para Datadog

Lambda AWS 100% genérica para processar CSVs do S3 e enviar métricas customizadas para o Datadog.

## Características

- **Totalmente Genérica**: Funciona com qualquer estrutura de CSV
- **Templates Dinâmicos**: Payloads definidos no EventBridge
- **Escalável**: Processa milhares de métricas em lotes otimizados
- **Flexível**: Suporta múltiplas métricas por linha do CSV
- **Segura**: Avaliação controlada de expressões Python

## Arquitetura

\`\`\`
EventBridge (5 min) → Lambda → S3 (CSV) → Processar Templates → Datadog
\`\`\`

### Fluxo de Dados

1. **EventBridge** dispara a Lambda a cada 5 minutos
2. **Lambda** recebe:
   - Path do S3 (pasta ou arquivo CSV)
   - Templates de payload (como transformar CSV em métricas)
3. **S3 Service** baixa o CSV
4. **CSV Service** lê o CSV (qualquer estrutura)
5. **Payload Service** aplica templates para cada linha
6. **Datadog Service** envia métricas em lotes (até 1000 por vez)

## Estrutura do Projeto

\`\`\`
app/
├── src/
│   ├── handlers/
│   │   └── lambda_handler.py          # Handler principal
│   ├── services/
│   │   ├── s3_service.py              # Download do S3
│   │   ├── csv_service.py             # Leitura de CSV
│   │   ├── payload_service.py         # Processamento de templates
│   │   └── datadog_service.py         # Envio para Datadog
│   ├── config/
│   │   └── settings.py                # Configurações
│   └── utils/
│       └── logger.py                  # Logger configurado
├── exemplos/
│   ├── eventos/                       # Exemplos de eventos EventBridge
│   └── csvs/                          # Exemplos de CSVs
├── docs/
│   ├── GUIA_TEMPLATES.md             # Guia completo de templates
│   └── README.md                      # Este arquivo
└── tests/
    └── test_payload_service.py        # Testes unitários
\`\`\`

## Como Usar

### 1. Preparar o CSV

Crie um CSV com os metadados dos seus serviços AWS:

**Exemplo RDS (rds/resultados_rds.csv):**
\`\`\`csv
account_id,db_instance_identifier,configured_iops_provisionado,allocated_storage_gb
123456789012,db-prod-01,3000,100
\`\`\`

### 2. Configurar o EventBridge

Crie um evento com os templates de payload:

\`\`\`json
{
  "s3_bucket": "meu-bucket",
  "s3_path": "rds/",
  "payloads": [
    {
      "metric": "custom_aws.rds.iops.provisioned",
      "type": 0,
      "points": [
        {
          "timestamp": "timestamp",
          "value": "float(linha['configured_iops_provisionado'])"
        }
      ],
      "tags": [
        "f\"account_id:{str(linha['account_id']).zfill(12)}\"",
        "f\"db_instance:{linha['db_instance_identifier']}\""
      ]
    }
  ]
}
\`\`\`

### 3. Deploy

\`\`\`bash
sam build
sam deploy --guided
\`\`\`

### 4. Configurar Variáveis de Ambiente

No console AWS Lambda, configure:
- `DATADOG_API_KEY`: Sua API key do Datadog
- `DATADOG_SITE`: Site do Datadog (ex: `datadoghq.com`)

## Exemplos de Uso

### RDS - Múltiplas Métricas

Enviar IOPS, Storage e Connections para cada banco:

\`\`\`json
{
  "s3_bucket": "metricas-aws",
  "s3_path": "rds/resultados_rds.csv",
  "payloads": [
    {
      "metric": "custom_aws.rds.iops.provisioned",
      "type": 0,
      "points": [{"timestamp": "timestamp", "value": "float(linha['configured_iops_provisionado'])"}],
      "tags": ["f\"db_instance:{linha['db_instance_identifier']}\""]
    },
    {
      "metric": "custom_aws.rds.storage.allocated",
      "type": 0,
      "points": [{"timestamp": "timestamp", "value": "float(linha['allocated_storage_gb'])"}],
      "tags": ["f\"db_instance:{linha['db_instance_identifier']}\""]
    }
  ]
}
\`\`\`

### ECS - Com Resources

\`\`\`json
{
  "s3_bucket": "metricas-aws",
  "s3_path": "ecs/resultados_ecs.csv",
  "payloads": [
    {
      "metric": "custom_aws.ecs.task.cpu_limit",
      "type": 0,
      "points": [{"timestamp": "timestamp", "value": "float(linha['cpu_limit'])"}],
      "tags": ["f\"cluster:{linha['cluster_name']}\""],
      "resources": [
        {
          "name": "linha['task_arn']",
          "type": "\"ecs_task\""
        }
      ]
    }
  ]
}
\`\`\`

## Sintaxe de Templates

### Acessar Dados do CSV
\`\`\`python
"linha['nome_coluna']"
\`\`\`

### Conversões
\`\`\`python
"float(linha['valor_decimal'])"
"int(linha['valor_inteiro'])"
"str(linha['texto']).zfill(12)"
\`\`\`

### Tags com F-Strings
\`\`\`python
"f\"tag_name:{linha['valor']}\""
\`\`\`

### Valores Literais
\`\`\`python
"\"env:production\""
\`\`\`

## Tipos de Métrica

- **0 (gauge)**: Valor instantâneo (CPU, memória, IOPS)
- **1 (count)**: Contador (requisições, erros)
- **2 (rate)**: Taxa de mudança (req/s)
- **3 (monotonic_count)**: Contador que só aumenta

## Configuração do EventBridge

### Regra do EventBridge

\`\`\`yaml
EventBridgeRule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: "rate(5 minutes)"
    State: ENABLED
    Targets:
      - Arn: !GetAtt LambdaFunction.Arn
        Input: |
          {
            "s3_bucket": "meu-bucket",
            "s3_path": "rds/",
            "payloads": [...]
          }
\`\`\`

### Múltiplas Regras

Crie uma regra para cada tipo de métrica:

- **RDS**: A cada 5 minutos, processa `rds/`
- **ECS**: A cada 5 minutos, processa `ecs/`
- **EC2**: A cada 5 minutos, processa `ec2/`

## Monitoramento

### Logs CloudWatch

A Lambda gera logs detalhados:
\`\`\`
[INFO] Iniciando processamento. Evento: {...}
[INFO] Baixando CSV de s3://bucket/path
[INFO] Lidas 150 linhas do CSV
[INFO] Processando 150 linhas com 3 template(s)
[INFO] Geradas 450 métricas dos templates
[INFO] Enviando 450 métricas para o Datadog
[INFO] Lote 1/1 enviado com sucesso (450 métricas)
[INFO] Processamento concluído com sucesso
\`\`\`

### Métricas da Lambda

Monitore:
- **Duration**: Tempo de execução
- **Errors**: Erros durante execução
- **Invocations**: Número de invocações

## Troubleshooting

### CSV não encontrado
- Verifique o path no S3
- Confirme permissões IAM da Lambda

### Métricas não aparecem no Datadog
- Verifique a API key
- Confirme o site do Datadog
- Veja os logs da Lambda

### Erro ao avaliar expressão
- Verifique sintaxe Python
- Confirme nome das colunas no CSV
- Use conversões de tipo apropriadas

## Segurança

- **IAM**: Lambda precisa de permissão para ler do S3
- **Secrets**: API key do Datadog em variável de ambiente
- **Eval**: Contexto restrito, apenas funções seguras

## Performance

- **Lotes**: Até 1000 métricas por requisição
- **Retry**: 3 tentativas com backoff exponencial
- **Timeout**: Configure timeout adequado (recomendado: 5 minutos)
- **Memória**: Recomendado 512MB ou mais

## Desenvolvimento

### Testes Locais

\`\`\`bash
# Instalar dependências
pip install -r requirements.txt

# Executar testes
python -m pytest tests/

# Testar localmente com SAM
sam local invoke -e exemplos/eventos/eventbridge-rds.json
\`\`\`

### Adicionar Nova Métrica

1. Crie o CSV com os dados
2. Faça upload para o S3
3. Configure o EventBridge com os templates
4. Deploy (não precisa alterar código!)

## Documentação Adicional

- [Guia Completo de Templates](GUIA_TEMPLATES.md)
- [Datadog Metrics API](https://docs.datadoghq.com/api/latest/metrics/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
\`\`\`

\`\`\`typescriptreact file="app/src/config/constants.py" isDeleted="true"
...deleted...
