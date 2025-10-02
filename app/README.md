# Lambda AWS - Envio de Métricas para Datadog

Função Lambda AWS em Python que processa arquivos CSV do S3 e envia métricas customizadas para o Datadog em lotes otimizados.

## Características

- **Trigada por EventBridge**: Execução automática a cada 5 minutos
- **Processamento de CSV**: Lê e processa arquivos CSV do S3
- **Envio em Lotes**: Envia até 1000 métricas por requisição ao Datadog
- **Genérica e Escalável**: Suporta múltiplos tipos de métricas (ECS, RDS, EC2, Lambda, ALB, CloudFront, Custom)
- **Retry Automático**: Retry com backoff exponencial em caso de falhas
- **Logging Detalhado**: Logs estruturados para debugging e monitoramento
- **Código Limpo**: Arquitetura modular com boas práticas de Python

## Estrutura do Projeto

\`\`\`
app/
├── src/
│   ├── handlers/          # Handler principal da Lambda
│   ├── services/          # Lógica de negócio (S3, CSV, Datadog)
│   ├── models/            # Modelos de dados
│   ├── config/            # Configurações e constantes
│   └── utils/             # Utilitários (logger, etc)
├── tests/                 # Testes unitários
├── exemplos/              # Exemplos de eventos e CSVs
│   ├── eventos/
│   └── csvs/
└── docs/                  # Documentação
\`\`\`

## Instalação

### Pré-requisitos

- Python 3.9+
- AWS CLI configurado
- SAM CLI (para deploy)
- Conta no Datadog com API Key e Application Key

### Deploy

1. **Clone o repositório**:
\`\`\`bash
git clone <repo-url>
cd lambda-datadog-metrics
\`\`\`

2. **Instale as dependências**:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

3. **Configure as variáveis de ambiente**:
\`\`\`bash
export DATADOG_API_KEY="sua-api-key"
export DATADOG_APP_KEY="sua-app-key"
\`\`\`

4. **Deploy com SAM**:
\`\`\`bash
sam build
sam deploy --guided
\`\`\`

Durante o deploy, você será solicitado a fornecer:
- Stack Name
- AWS Region
- Datadog API Key
- Datadog Application Key
- Datadog Site (padrão: datadoghq.com)

## Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão | Obrigatória |
|----------|-------------|---------|-------------|
| `DATADOG_API_KEY` | API Key do Datadog | - | Sim |
| `DATADOG_APP_KEY` | Application Key do Datadog | - | Sim |
| `DATADOG_SITE` | Site do Datadog | datadoghq.com | Não |
| `TAMANHO_LOTE` | Métricas por lote | 1000 | Não |
| `TIMEOUT_REQUEST` | Timeout das requisições (s) | 30 | Não |
| `MAX_TENTATIVAS` | Tentativas de retry | 3 | Não |
| `DELAY_RETRY` | Delay entre retries (s) | 2 | Não |

### EventBridge

O EventBridge deve enviar eventos no seguinte formato:

\`\`\`json
{
  "s3_bucket": "meu-bucket-metricas",
  "s3_key": "metricas/2024/01/15/ecs-metricas.csv",
  "arquivo_nome": "ecs-metricas.csv",
  "tipo_metrica": "ecs"
}
\`\`\`

### Formato do CSV

#### Colunas Obrigatórias
- `nome_metrica`: Nome da métrica
- `valor`: Valor numérico

#### Colunas Opcionais
- `timestamp`: Timestamp Unix
- `tags`: Tags separadas por vírgula
- `tipo`: gauge, count, rate, monotonic_count
- `host`: Nome do host
- `intervalo`: Intervalo em segundos
- `resources_name`: Nome do recurso
- `resources_type`: Tipo do recurso

#### Exemplo

\`\`\`csv
nome_metrica,valor,timestamp,tags,tipo,host,intervalo
cpu,75.5,1705315200,env:producao;servico:api,gauge,ecs-host-01,300
memoria,82.3,1705315200,env:producao;servico:api,gauge,ecs-host-01,300
\`\`\`

## Tipos de Métricas Suportados

- **ECS**: Métricas de containers ECS
- **RDS**: Métricas de bancos de dados RDS
- **EC2**: Métricas de instâncias EC2
- **Lambda**: Métricas de funções Lambda
- **ALB**: Métricas de Application Load Balancer
- **CloudFront**: Métricas de distribuições CloudFront
- **Custom**: Métricas customizadas

Veja [CONFIGURACAO_METRICAS.md](docs/CONFIGURACAO_METRICAS.md) para detalhes.

## Uso

### Exemplo 1: Métricas de ECS

\`\`\`csv
nome_metrica,valor,tags,tipo
cpu,75.5,env:producao;cluster:main,gauge
memoria,82.3,env:producao;cluster:main,gauge
tarefas,12,env:producao;cluster:main,gauge
\`\`\`

### Exemplo 2: Múltiplas Métricas

\`\`\`csv
nome_metrica,valor,tags,tipo,resources_name,resources_type
latencia.request,120,env:producao;rota:/login,gauge,api-login,container
erros.request,3,env:producao;rota:/login,count,api-login,container
qtd_requisicoes,57,env:producao;rota:/login,count,api-login,container
\`\`\`

Veja [MULTIPLAS_METRICAS.md](docs/MULTIPLAS_METRICAS.md) para mais exemplos.

## Testes

Execute os testes unitários:

\`\`\`bash
python -m pytest app/tests/
\`\`\`

Ou com coverage:

\`\`\`bash
python -m pytest app/tests/ --cov=app/src --cov-report=html
\`\`\`

## Monitoramento

A Lambda gera logs detalhados no CloudWatch Logs:

- Início e fim do processamento
- Número de métricas processadas
- Lotes enviados ao Datadog
- Erros e warnings

### Exemplo de Log

\`\`\`
2024-01-15 10:00:00 - INFO - Iniciando processamento
2024-01-15 10:00:01 - INFO - Baixando arquivo do S3: s3://bucket/key
2024-01-15 10:00:02 - INFO - Processadas 150 métricas do CSV
2024-01-15 10:00:03 - INFO - Enviando lote 1/1 com 150 métricas
2024-01-15 10:00:04 - INFO - Processamento concluído. Métricas enviadas: 150
\`\`\`

## Troubleshooting

### Erro: "DATADOG_API_KEY não configurada"
- Verifique se as variáveis de ambiente estão configuradas corretamente

### Erro: "CSV deve conter as colunas: nome_metrica, valor"
- Verifique se o CSV tem as colunas obrigatórias

### Erro: "Tipo de métrica 'xyz' não suportado"
- Use um dos tipos suportados ou adicione novo tipo em `constants.py`

### Métricas não aparecem no Datadog
- Verifique se as credenciais do Datadog estão corretas
- Verifique os logs no CloudWatch para erros de envio
- Confirme que o site do Datadog está correto (datadoghq.com, datadoghq.eu, etc)

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

MIT License - veja LICENSE para detalhes.

## Suporte

Para dúvidas ou problemas:
- Abra uma issue no GitHub
- Consulte a documentação em `docs/`
- Verifique os exemplos em `exemplos/`
\`\`\`

```txt file="" isHidden
