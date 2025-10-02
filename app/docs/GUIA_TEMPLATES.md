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
      "type": "gauge",
      "points": [...],
      "tags": [...],
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
- **type** (string): Tipo da métrica (API v2)
  - `"gauge"` = valor instantâneo (CPU, memória, IOPS)
  - `"count"` = contador acumulativo
  - `"rate"` = taxa de mudança
  - `"distribution"` = distribuição de valores
- **points** (array): Array de pontos de dados
  - Formato: `[{"timestamp": ..., "value": ...}]`

#### Campos Opcionais

- **tags** (array): Lista de tags
- **resources** (array): Lista de recursos associados
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
      "type": "gauge",
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
      ],
      "resources": [
        {
          "name": "linha['db_instance_identifier']",
          "type": "\"database\""
        }
      ]
    },
    {
      "metric": "custom_aws.rds.storage.allocated",
      "type": "gauge",
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
      ],
      "resources": [
        {
          "name": "linha['db_instance_identifier']",
          "type": "\"database\""
        }
      ]
    }
  ]
}
\`\`\`

**Resultado:** Para cada linha do CSV, serão geradas 2 métricas (IOPS e Storage).

### Exemplo 2: ECS com CPU e Memória

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
      "type": "gauge",
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
          "name": "linha['cluster_name']",
          "type": "\"ecs_cluster\""
        }
      ]
    }
  ]
}
\`\`\`

### Exemplo 3: Métrica Simples sem Resources

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
      "type": "gauge",
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

### 3. Tipos de Métrica (API v2)
- **gauge**: Valores instantâneos (CPU, memória, IOPS, storage)
- **count**: Contadores acumulativos (requisições totais, erros totais)
- **rate**: Taxa de mudança (requisições/segundo, bytes/segundo)
- **distribution**: Distribuição de valores (latências, tamanhos)

### 4. Resources (API v2)
Use resources para associar métricas a recursos específicos:
\`\`\`json
"resources": [
  {
    "name": "linha['db_instance_identifier']",
    "type": "\"database\""
  }
]
\`\`\`

Tipos comuns:
- `"host"` - Servidores/instâncias
- `"database"` - Bancos de dados
- `"ecs_cluster"` - Clusters ECS
- `"service"` - Serviços/aplicações

### 5. Conversão de Tipos
Sempre converta valores para o tipo correto:
\`\`\`python
"float(linha['valor_decimal'])"  # Para números decimais
"int(linha['valor_inteiro'])"    # Para números inteiros
"str(linha['texto'])"             # Para strings
\`\`\`

### 6. Formatação de IDs
Para account_id AWS (12 dígitos):
\`\`\`python
"str(linha['account_id']).zfill(12)"
\`\`\`

### 7. Múltiplas Métricas
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

## Compatibilidade com API v1

O código suporta automaticamente conversão de formato v1 para v2:

**Se você usar type como número:**
\`\`\`json
"type": 0
\`\`\`

Será convertido automaticamente para:
- `0` → `"gauge"`
- `1` → `"rate"`
- `2` → `"count"`
- `3` → `"distribution"`

**Se você usar host ao invés de resources:**
\`\`\`json
"host": "linha['hostname']"
\`\`\`

Será convertido automaticamente para:
\`\`\`json
"resources": [{"name": "hostname_value", "type": "host"}]
\`\`\`

## Validação

A Lambda valida automaticamente:
- Campos obrigatórios (metric, type, points)
- Formato de points (mantém como objetos `{"timestamp": ..., "value": ...}`)
- Tipos de dados (conversões)
- Expressões Python (sintaxe)

Erros são logados mas não interrompem o processamento de outras linhas/métricas.

## API do Datadog

Esta Lambda usa a **API v2** do Datadog:
- Endpoint: `https://api.{site}/api/v2/series`
- Formato de points: `[{"timestamp": 123456, "value": 10.5}]`
- Headers: `DD-API-KEY` e `DD-APPLICATION-KEY` (opcional)
- Type: string (`"gauge"`, `"count"`, `"rate"`, `"distribution"`)
- Resources: array de objetos `[{"name": "...", "type": "..."}]`

## Troubleshooting

### Métrica não aparece no Datadog
1. Verifique os logs da Lambda
2. Confirme que o campo `value` está sendo avaliado corretamente
3. Verifique se o nome da coluna no CSV está correto
4. Confirme que o valor não é `None` ou vazio
5. Verifique se o tipo da métrica está correto (string na v2)

### Erro de avaliação de expressão
1. Verifique a sintaxe Python
2. Confirme que a coluna existe no CSV
3. Use conversões de tipo apropriadas
4. Verifique os logs para ver a expressão exata que falhou

### Tags incorretas
1. Use f-strings com aspas duplas externas e simples internas
2. Exemplo correto: `"f\"tag:{linha['valor']}\""`
3. Para valores literais: `"\"env:production\""`

### Erro "invalid json structure"
- Confirme que está usando a API v2 (`/api/v2/series`)
- Verifique se o `type` é uma string (`"gauge"`, não `0`)
- Confirme que os points estão no formato de objeto
- Verifique os logs detalhados do payload enviado

### Resources não aparecem
- Verifique se o formato está correto: `[{"name": "...", "type": "..."}]`
- Confirme que as expressões estão sendo avaliadas corretamente
- Use aspas duplas para valores literais: `"\"database\""`

## Segurança

A Lambda usa `eval()` com contexto restrito:
- Apenas funções seguras disponíveis: `int`, `float`, `str`, `len`
- Sem acesso a `__builtins__`
- Sem acesso a módulos externos
- Apenas variáveis `linha` e `timestamp` disponíveis

**Importante:** Configure o EventBridge com cuidado, pois as expressões são executadas na Lambda.
