# Guia de Templates de Payload

Este documento explica como criar templates de payload para a Lambda de métricas do Datadog.

## Conceito

A Lambda é **100% genérica** e funciona com qualquer estrutura de CSV. Os templates de payload são definidos no **EventBridge** e determinam como os dados do CSV serão transformados em métricas do Datadog.

## Estrutura do Evento EventBridge

\`\`\`json
{
  "s3_bucket": "nome-do-bucket",
  "s3_path": "pasta/arquivo.csv",
  "payloads": [
    {
      "metric": "nome.da.metrica",
      "type": 0,
      "points": [...],
      "tags": [...],
      "host": "...",
      "interval": 60,
      "resources": [...]
    }
  ]
}
\`\`\`

### Campos Obrigatórios

- **s3_bucket**: Nome do bucket S3
- **s3_path**: Caminho da pasta ou arquivo CSV (ex: `rds/` ou `rds/resultados.csv`)
- **payloads**: Array de templates de payload (mínimo 1)

### Estrutura do Payload

Cada payload deve conter:

#### Campos Obrigatórios

- **metric** (string): Nome da métrica
- **type** (int): Tipo da métrica
  - `0` = gauge (valor instantâneo)
  - `1` = count (contador)
  - `2` = rate (taxa)
  - `3` = monotonic_count (contador monotônico)
- **points** (array): Array de pontos de dados
  - Formato: `[{"timestamp": ..., "value": ...}]`

#### Campos Opcionais

- **tags** (array): Lista de tags
- **host** (string): Nome do host
- **interval** (int): Intervalo em segundos
- **resources** (array): Lista de recursos
  - Formato: `[{"name": "...", "type": "..."}]`

## Sintaxe de Templates

Os templates suportam **expressões Python** que são avaliadas dinamicamente para cada linha do CSV.

### Variáveis Disponíveis

- **linha**: Dicionário com os dados da linha atual do CSV
  - Acesso: `linha['nome_coluna']`
- **timestamp**: Timestamp Unix atual (int)
- **Funções**: `int()`, `float()`, `str()`, `len()`

### Exemplos de Expressões

#### Acessar Valor do CSV
\`\`\`python
"linha['configured_iops_provisionado']"
\`\`\`

#### Converter Tipos
\`\`\`python
"float(linha['cpu_usage'])"
"int(linha['max_connections'])"
"str(linha['account_id']).zfill(12)"
\`\`\`

#### F-Strings para Tags
\`\`\`python
"f\"account_id:{str(linha['account_id']).zfill(12)}\""
"f\"cluster:{linha['cluster_name']}\""
"f\"region:{linha['region']}\""
\`\`\`

#### Valores Literais
\`\`\`python
"\"env:production\""
"\"team:backend\""
\`\`\`

## Exemplos Completos

### Exemplo 1: RDS com Múltiplas Métricas

**CSV (rds/resultados_rds.csv):**
\`\`\`csv
account_id,account_name,db_instance_identifier,engine,configured_iops_provisionado,allocated_storage_gb,max_connections
123456789012,Producao,db-prod-01,postgres,3000,100,500
\`\`\`

**EventBridge:**
\`\`\`json
{
  "s3_bucket": "metricas-aws",
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
        "f\"db_instance:{linha['db_instance_identifier']}\"",
        "f\"engine:{linha['engine']}\"",
        "\"env:production\""
      ]
    },
    {
      "metric": "custom_aws.rds.storage.allocated",
      "type": 0,
      "points": [
        {
          "timestamp": "timestamp",
          "value": "float(linha['allocated_storage_gb'])"
        }
      ],
      "tags": [
        "f\"account_id:{str(linha['account_id']).zfill(12)}\"",
        "f\"db_instance:{linha['db_instance_identifier']}\"",
        "\"env:production\""
      ]
    }
  ]
}
\`\`\`

**Resultado:** Para cada linha do CSV, serão geradas 2 métricas (IOPS e Storage).

### Exemplo 2: ECS com Resources

**CSV (ecs/resultados_ecs.csv):**
\`\`\`csv
account_id,cluster_name,service_name,task_arn,cpu_limit,memory_limit
123456789012,prod-cluster,api-service,arn:aws:ecs:...,1024,2048
\`\`\`

**EventBridge:**
\`\`\`json
{
  "s3_bucket": "metricas-aws",
  "s3_path": "ecs/resultados_ecs.csv",
  "payloads": [
    {
      "metric": "custom_aws.ecs.task.cpu_limit",
      "type": 0,
      "points": [
        {
          "timestamp": "timestamp",
          "value": "float(linha['cpu_limit'])"
        }
      ],
      "tags": [
        "f\"account_id:{str(linha['account_id']).zfill(12)}\"",
        "f\"cluster:{linha['cluster_name']}\"",
        "f\"service:{linha['service_name']}\""
      ],
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

### Exemplo 3: Métrica Simples

**CSV (ec2/instancias.csv):**
\`\`\`csv
instance_id,cpu_usage,memory_usage
i-1234567890,45.5,78.2
\`\`\`

**EventBridge:**
\`\`\`json
{
  "s3_bucket": "metricas-aws",
  "s3_path": "ec2/instancias.csv",
  "payloads": [
    {
      "metric": "custom_aws.ec2.cpu.usage",
      "type": 0,
      "points": [
        {
          "timestamp": "timestamp",
          "value": "float(linha['cpu_usage'])"
        }
      ],
      "tags": [
        "f\"instance_id:{linha['instance_id']}\""
      ]
    }
  ]
}
\`\`\`

## Boas Práticas

### 1. Nomenclatura de Métricas
Use prefixo consistente:
\`\`\`
custom_aws.<servico>.<recurso>.<metrica>
\`\`\`

Exemplos:
- `custom_aws.rds.iops.provisioned`
- `custom_aws.ecs.task.cpu_limit`
- `custom_aws.ec2.instance.cpu_usage`

### 2. Tags Essenciais
Sempre inclua:
- `account_id`: Identificação da conta AWS
- Identificador do recurso (instance_id, db_instance, cluster, etc.)
- `env`: Ambiente (production, staging, development)

### 3. Tipos de Métrica
- **Gauge (0)**: Valores instantâneos (CPU, memória, IOPS)
- **Count (1)**: Contadores que podem diminuir (requisições, erros)
- **Rate (2)**: Taxa de mudança (requisições/segundo)
- **Monotonic Count (3)**: Contadores que só aumentam (total de requisições)

### 4. Conversão de Tipos
Sempre converta valores para o tipo correto:
\`\`\`python
"float(linha['valor_decimal'])"  # Para números decimais
"int(linha['valor_inteiro'])"    # Para números inteiros
"str(linha['texto'])"             # Para strings
\`\`\`

### 5. Formatação de IDs
Para account_id AWS (12 dígitos):
\`\`\`python
"str(linha['account_id']).zfill(12)"
\`\`\`

### 6. Múltiplas Métricas
Agrupe métricas relacionadas no mesmo evento para otimizar processamento:
\`\`\`json
{
  "payloads": [
    {"metric": "custom_aws.rds.iops.provisioned", ...},
    {"metric": "custom_aws.rds.storage.allocated", ...},
    {"metric": "custom_aws.rds.connections.max", ...}
  ]
}
\`\`\`

## Validação

A Lambda valida automaticamente:
- Campos obrigatórios (metric, type, points)
- Formato de points (array de arrays)
- Tipos de dados (conversões)
- Expressões Python (sintaxe)

Erros são logados mas não interrompem o processamento de outras linhas/métricas.

## Troubleshooting

### Métrica não aparece no Datadog
1. Verifique os logs da Lambda
2. Confirme que o campo `value` está sendo avaliado corretamente
3. Verifique se o nome da coluna no CSV está correto

### Erro de avaliação de expressão
1. Verifique a sintaxe Python
2. Confirme que a coluna existe no CSV
3. Use conversões de tipo apropriadas

### Tags incorretas
1. Use f-strings com aspas duplas externas e simples internas
2. Exemplo correto: `"f\"tag:{linha['valor']}\""`
3. Para valores literais: `"\"env:production\""`

## Segurança

A Lambda usa `eval()` com contexto restrito:
- Apenas funções seguras disponíveis: `int`, `float`, `str`, `len`
- Sem acesso a `__builtins__`
- Sem acesso a módulos externos
- Apenas variáveis `linha` e `timestamp` disponíveis

**Importante:** Configure o EventBridge com cuidado, pois as expressões são executadas na Lambda.
