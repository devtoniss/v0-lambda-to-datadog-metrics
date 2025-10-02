# Lambda AWS - Processador de Métricas para Datadog

Lambda function em Python que processa arquivos CSV do S3 e envia métricas customizadas para o Datadog em lotes escaláveis.

## 📋 Funcionalidades

- ✅ Trigada automaticamente pelo EventBridge a cada 5 minutos
- ✅ Download de arquivos CSV do S3
- ✅ Processamento genérico de métricas (ECS, RDS, EC2, etc.)
- ✅ Envio em lotes grandes para o Datadog (até 1000 métricas por lote)
- ✅ Retry automático em caso de falhas
- ✅ Logging detalhado para troubleshooting
- ✅ Código modular e testável

## 🏗️ Arquitetura

\`\`\`
EventBridge (5 min) → Lambda → S3 (download CSV) → Processamento → Datadog API
\`\`\`

## 📁 Estrutura do Projeto

\`\`\`
scripts/
├── lambda_function.py      # Handler principal
├── config.py              # Configurações centralizadas
├── s3_handler.py          # Operações com S3
├── csv_processor.py       # Processamento de CSV
├── datadog_client.py      # Cliente Datadog
└── requirements.txt       # Dependências Python

template.yaml              # CloudFormation/SAM template
exemplo-evento-eventbridge.json  # Exemplo de evento
exemplo-csv-ecs.csv       # Exemplo CSV para ECS
exemplo-csv-rds.csv       # Exemplo CSV para RDS
\`\`\`

## 🚀 Deploy

### Pré-requisitos

- AWS CLI configurado
- SAM CLI instalado
- Conta no Datadog com API Key e App Key

### Passos para Deploy

1. **Instalar dependências localmente (para testes)**
\`\`\`bash
pip install -r scripts/requirements.txt
\`\`\`

2. **Build da aplicação**
\`\`\`bash
sam build
\`\`\`

3. **Deploy**
\`\`\`bash
sam deploy --guided
\`\`\`

Durante o deploy, você será solicitado a fornecer:
- `DatadogApiKey`: Sua chave de API do Datadog
- `DatadogAppKey`: Sua chave de aplicação do Datadog
- `DatadogSite`: Site do Datadog (ex: datadoghq.com)
- `S3BucketName`: Nome do bucket S3 com os CSVs

## 📊 Formato do CSV

O CSV deve conter as seguintes colunas:

| Coluna | Obrigatório | Descrição | Exemplo |
|--------|-------------|-----------|---------|
| `nome_metrica` | ✅ Sim | Nome da métrica | `aws.ecs.cpu_utilization` |
| `valor` | ✅ Sim | Valor numérico | `75.5` |
| `timestamp` | ❌ Não | Unix timestamp | `1705315200` |
| `tags` | ❌ Não | Tags separadas por `;` | `env:prod;service:api` |
| `tipo` | ❌ Não | Tipo (gauge/count/rate) | `gauge` |
| `host` | ❌ Não | Nome do host | `ecs-host-01` |
| `intervalo` | ❌ Não | Intervalo em segundos | `60` |

### Exemplo de CSV

\`\`\`csv
nome_metrica,valor,timestamp,tags,tipo,host,intervalo
aws.ecs.cpu_utilization,75.5,1705315200,env:prod;service:api,gauge,ecs-host-01,60
aws.rds.connections,125,1705315200,env:prod;database:postgres,gauge,rds-instance-01,60
\`\`\`

## 🔧 Configuração do EventBridge

O EventBridge deve enviar um evento com o seguinte formato:

\`\`\`json
{
  "s3_bucket": "meu-bucket-metricas",
  "s3_key": "metricas/ecs/dados.csv",
  "arquivo_nome": "dados.csv",
  "tipo_metrica": "ecs"
}
\`\`\`

### Parâmetros do Evento

- `s3_bucket`: Nome do bucket S3
- `s3_key`: Caminho completo do arquivo no S3
- `arquivo_nome`: Nome do arquivo para salvar localmente
- `tipo_metrica`: Tipo da métrica (usado como tag)

## ⚙️ Variáveis de Ambiente

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `DATADOG_API_KEY` | ✅ Sim | - | Chave de API do Datadog |
| `DATADOG_APP_KEY` | ✅ Sim | - | Chave de aplicação do Datadog |
| `DATADOG_SITE` | ❌ Não | `datadoghq.com` | Site do Datadog |
| `TAMANHO_LOTE` | ❌ Não | `1000` | Métricas por lote |
| `TIMEOUT_REQUEST` | ❌ Não | `30` | Timeout em segundos |
| `MAX_TENTATIVAS` | ❌ Não | `3` | Tentativas de retry |
| `DELAY_RETRY` | ❌ Não | `2` | Delay entre retries |

## 📈 Escalabilidade

A Lambda foi projetada para ser escalável:

- **Lotes grandes**: Envia até 1000 métricas por requisição
- **Processamento paralelo**: Cada invocação processa um arquivo independentemente
- **Retry inteligente**: Retry automático com backoff exponencial
- **Memória otimizada**: 512MB suficiente para processar arquivos grandes

### Limites Recomendados

- Tamanho máximo do CSV: ~50MB
- Métricas por arquivo: ~100.000
- Tempo de execução: <5 minutos

## 🔍 Monitoramento

### CloudWatch Logs

Todos os logs são enviados para CloudWatch com retenção de 7 dias:
- `/aws/lambda/datadog-metrics-processor`

### Métricas CloudWatch

Monitore as seguintes métricas:
- `Duration`: Tempo de execução
- `Errors`: Erros na execução
- `Throttles`: Throttling da Lambda

## 🧪 Testes Locais

Para testar localmente:

\`\`\`bash
# Criar evento de teste
cat > evento-teste.json << EOF
{
  "s3_bucket": "meu-bucket",
  "s3_key": "metricas/teste.csv",
  "arquivo_nome": "teste.csv",
  "tipo_metrica": "teste"
}
EOF

# Invocar localmente
sam local invoke MetricsProcessorFunction -e evento-teste.json
\`\`\`

## 🛠️ Troubleshooting

### Erro: "DATADOG_API_KEY não configurada"
- Verifique se as variáveis de ambiente estão configuradas corretamente

### Erro: "Arquivo não encontrado após download"
- Verifique se o bucket e key do S3 estão corretos
- Confirme que a Lambda tem permissão de leitura no bucket

### Erro: "Erro na requisição ao Datadog"
- Verifique se as chaves do Datadog estão corretas
- Confirme se o site do Datadog está correto (datadoghq.com vs datadoghq.eu)

## 📝 Boas Práticas Implementadas

- ✅ Type hints em todas as funções
- ✅ Docstrings em português
- ✅ Logging estruturado
- ✅ Tratamento de erros robusto
- ✅ Configuração via variáveis de ambiente
- ✅ Código modular e testável
- ✅ Retry automático
- ✅ Limpeza de recursos temporários

## 📄 Licença

Este projeto é de código aberto e está disponível sob a licença MIT.
