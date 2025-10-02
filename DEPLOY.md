# Guia de Deploy

Este documento fornece instruções detalhadas para fazer o deploy da Lambda de métricas do Datadog.

## Pré-requisitos

1. **AWS CLI** instalado e configurado
   \`\`\`bash
   aws configure
   \`\`\`

2. **SAM CLI** instalado
   \`\`\`bash
   # macOS
   brew install aws-sam-cli
   
   # Linux
   pip install aws-sam-cli
   
   # Windows
   # Baixe o instalador em: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
   \`\`\`

3. **Python 3.11+** instalado

4. **Credenciais do Datadog**
   - API Key
   - Application Key
   - Site (datadoghq.com, datadoghq.eu, etc.)

## Estrutura do Projeto

\`\`\`
lambda-datadog-metrics/
├── app/                    # Código da aplicação
│   ├── src/               # Código fonte
│   ├── tests/             # Testes
│   ├── exemplos/          # Exemplos
│   └── docs/              # Documentação
├── template.yaml          # Template SAM
├── requirements.txt       # Dependências Python
└── README.md             # Documentação principal
\`\`\`

## Passo a Passo

### 1. Clone e Prepare o Ambiente

\`\`\`bash
# Clone o repositório
git clone <repo-url>
cd lambda-datadog-metrics

# Crie um ambiente virtual (opcional mas recomendado)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\\Scripts\\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
\`\`\`

### 2. Configure as Credenciais

Você pode configurar as credenciais de duas formas:

#### Opção A: Via Parâmetros no Deploy (Recomendado)

Durante o deploy, você será solicitado a fornecer as credenciais.

#### Opção B: Via Arquivo de Configuração

Crie um arquivo \`samconfig.toml\`:

\`\`\`toml
version = 0.1

[default.deploy.parameters]
stack_name = "datadog-metrics-stack"
region = "us-east-1"
capabilities = "CAPABILITY_IAM"
parameter_overrides = [
    "DatadogApiKey=sua-api-key",
    "DatadogAppKey=sua-app-key",
    "DatadogSite=datadoghq.com",
    "S3BucketName=seu-bucket-metricas"
]
\`\`\`

**⚠️ IMPORTANTE**: Adicione \`samconfig.toml\` ao \`.gitignore\` para não commitar credenciais!

### 3. Build da Aplicação

\`\`\`bash
sam build
\`\`\`

Este comando:
- Instala as dependências do \`requirements.txt\`
- Prepara o código para deploy
- Cria o diretório \`.aws-sam/\`

### 4. Deploy

#### Deploy Interativo (Primeira vez)

\`\`\`bash
sam deploy --guided
\`\`\`

Você será solicitado a fornecer:

\`\`\`
Stack Name [datadog-metrics-stack]: datadog-metrics-stack
AWS Region [us-east-1]: us-east-1
Parameter DatadogApiKey []: sua-datadog-api-key
Parameter DatadogAppKey []: sua-datadog-app-key
Parameter DatadogSite [datadoghq.com]: datadoghq.com
Parameter S3BucketName []: seu-bucket-metricas
Confirm changes before deploy [Y/n]: Y
Allow SAM CLI IAM role creation [Y/n]: Y
Save arguments to configuration file [Y/n]: Y
\`\`\`

#### Deploy Subsequente

Após o primeiro deploy, você pode usar:

\`\`\`bash
sam deploy
\`\`\`

### 5. Verificar o Deploy

\`\`\`bash
# Listar stacks
aws cloudformation list-stacks

# Descrever a stack
aws cloudformation describe-stacks --stack-name datadog-metrics-stack

# Ver logs da Lambda
sam logs -n MetricsProcessorFunction --stack-name datadog-metrics-stack --tail
\`\`\`

## Configuração do S3

### 1. Criar Bucket (se não existir)

\`\`\`bash
aws s3 mb s3://seu-bucket-metricas
\`\`\`

### 2. Estrutura de Pastas Recomendada

\`\`\`
seu-bucket-metricas/
├── metricas/
│   ├── ecs/
│   │   └── dados-ecs.csv
│   ├── rds/
│   │   └── dados-rds.csv
│   └── custom/
│       └── dados-custom.csv
\`\`\`

### 3. Upload de Arquivo de Teste

\`\`\`bash
# Copie um exemplo
cp app/exemplos/csvs/ecs.csv /tmp/teste-ecs.csv

# Faça upload
aws s3 cp /tmp/teste-ecs.csv s3://seu-bucket-metricas/metricas/ecs/dados.csv
\`\`\`

## Configuração do EventBridge

### Criar Regra Customizada

Se você quiser criar regras adicionais além da padrão:

\`\`\`bash
# Criar regra
aws events put-rule \\
  --name ProcessarMetricasRDS \\
  --schedule-expression "rate(5 minutes)" \\
  --state ENABLED

# Adicionar target (Lambda)
aws events put-targets \\
  --rule ProcessarMetricasRDS \\
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:datadog-metrics-processor","Input"='{"s3_bucket":"seu-bucket","s3_key":"metricas/rds/dados.csv","arquivo_nome":"dados.csv","tipo_metrica":"rds"}'

# Dar permissão ao EventBridge para invocar a Lambda
aws lambda add-permission \\
  --function-name datadog-metrics-processor \\
  --statement-id ProcessarMetricasRDS \\
  --action lambda:InvokeFunction \\
  --principal events.amazonaws.com \\
  --source-arn arn:aws:events:REGION:ACCOUNT:rule/ProcessarMetricasRDS
\`\`\`

## Testes

### Teste Local

\`\`\`bash
# Executar testes unitários
python -m pytest app/tests/

# Com coverage
python -m pytest app/tests/ --cov=app/src --cov-report=html
\`\`\`

### Teste da Lambda Localmente

\`\`\`bash
# Invocar localmente com evento de teste
sam local invoke MetricsProcessorFunction -e app/exemplos/eventos/eventbridge.json
\`\`\`

### Teste na AWS

\`\`\`bash
# Invocar a Lambda na AWS
aws lambda invoke \\
  --function-name datadog-metrics-processor \\
  --payload file://app/exemplos/eventos/eventbridge.json \\
  response.json

# Ver resposta
cat response.json
\`\`\`

## Monitoramento

### CloudWatch Logs

\`\`\`bash
# Ver logs em tempo real
sam logs -n MetricsProcessorFunction --stack-name datadog-metrics-stack --tail

# Ver logs de um período específico
aws logs filter-log-events \\
  --log-group-name /aws/lambda/datadog-metrics-processor \\
  --start-time $(date -d '1 hour ago' +%s)000
\`\`\`

### Métricas no CloudWatch

Acesse o console AWS CloudWatch e procure por:
- Invocations
- Duration
- Errors
- Throttles

### Métricas no Datadog

Acesse o Datadog e procure por:
- \`aws.ecs.*\`
- \`aws.rds.*\`
- \`custom.*\`

## Atualização

### Atualizar Código

\`\`\`bash
# Fazer alterações no código
# ...

# Build e deploy
sam build
sam deploy
\`\`\`

### Atualizar Configurações

\`\`\`bash
# Atualizar variáveis de ambiente
aws lambda update-function-configuration \\
  --function-name datadog-metrics-processor \\
  --environment "Variables={DATADOG_API_KEY=nova-key,DATADOG_APP_KEY=nova-app-key,TAMANHO_LOTE=2000}"
\`\`\`

## Rollback

Se algo der errado:

\`\`\`bash
# Listar versões da stack
aws cloudformation list-stack-resources --stack-name datadog-metrics-stack

# Fazer rollback para versão anterior
aws cloudformation cancel-update-stack --stack-name datadog-metrics-stack
\`\`\`

## Remoção

Para remover completamente a stack:

\`\`\`bash
# Deletar stack
sam delete --stack-name datadog-metrics-stack

# Ou via CloudFormation
aws cloudformation delete-stack --stack-name datadog-metrics-stack
\`\`\`

## Troubleshooting

### Erro: "Unable to import module 'src.handlers.lambda_handler'"

**Solução**: Verifique se a estrutura de pastas está correta e se todos os \`__init__.py\` existem.

### Erro: "DATADOG_API_KEY não configurada"

**Solução**: Verifique se as variáveis de ambiente foram configuradas corretamente no template.yaml.

### Erro: "Access Denied" ao acessar S3

**Solução**: Verifique se a Lambda tem permissão de leitura no bucket S3 especificado.

### Lambda timeout

**Solução**: Aumente o timeout no template.yaml (padrão: 300 segundos).

## Boas Práticas

1. **Use ambientes separados**: Dev, Staging, Production
2. **Versionamento**: Use tags Git para versionar deploys
3. **Monitoramento**: Configure alarmes no CloudWatch
4. **Segurança**: Nunca commite credenciais no código
5. **Testes**: Execute testes antes de cada deploy
6. **Logs**: Mantenha logs por período adequado (7-30 dias)
7. **Backup**: Mantenha backup dos CSVs no S3 com versionamento

## Suporte

Para problemas ou dúvidas:
- Consulte a documentação em \`app/docs/\`
- Verifique os exemplos em \`app/exemplos/\`
- Abra uma issue no repositório
\`\`\`
