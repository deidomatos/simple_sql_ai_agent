# Agente SQL Inteligente

Este repositório contém um agente SQL inteligente que converte perguntas em linguagem natural para consultas SQL e as executa em um banco de dados PostgreSQL.

## Visão Geral

Este projeto implementa um agente SQL inteligente que:
1. Recebe perguntas em linguagem natural
2. Converte-as automaticamente em consultas SQL
3. Executa as consultas em um banco de dados PostgreSQL
4. Retorna respostas formatadas em linguagem natural

O sistema é capaz de interpretar perguntas complexas e lidar com consultas simples e avançadas, incluindo JOINs, filtros e agregações.

## Funcionalidades

- Conversão de linguagem natural para SQL usando LangChain
- Execução segura de consultas SQL com validação e proteção contra SQL Injection
- Formatação de resultados em respostas naturais e compreensíveis
- Memória persistente multi-sessão para manter contexto de conversas passadas
- Orquestração multi-agente com papéis especializados
- Observabilidade e tracing com OpenTelemetry

## Arquitetura

O projeto segue uma arquitetura de múltiplos agentes especializados:

1. **SQL Generator**: Converte perguntas em linguagem natural para SQL
2. **SQL Executor**: Executa consultas SQL de forma segura e retorna os resultados
3. **Response Formatter**: Formata os resultados em respostas naturais
4. **Memory Manager**: Gerencia a memória persistente entre sessões

Esses agentes são orquestrados por um fluxo LangGraph que coordena o processamento das perguntas.

### Banco de Dados

O sistema utiliza um banco de dados PostgreSQL com três tabelas inter-relacionadas:
- **clientes**: Informações dos clientes (id, nome, email, saldo, data_cadastro)
- **produtos**: Produtos disponíveis para venda (id, nome, descricao, preco, estoque)
- **transacoes**: Compras realizadas por cada cliente (id, cliente_id, produto_id, quantidade, valor_total, data_transacao)

Relacionamentos:
- Um cliente pode ter várias transações (1:N)
- Cada transação está associada a um único produto (N:1)

## Instalação

### Pré-requisitos

- Python 3.8+
- PostgreSQL
- OpenAI API Key

## Configuração do Ambiente

### 1. Python Environment

- Instale Python 3.8+ (recomendado)
- Instale todas as dependências necessárias:

```bash
pip install -r requirements.txt
```

Os pacotes principais incluem:
- LangChain e pacotes relacionados para o framework de agentes
- psycopg2-binary para conectividade com PostgreSQL
- python-dotenv para gerenciamento de variáveis de ambiente
- OpenAI API client
- FAISS e sentence-transformers para a implementação RAG
- FastAPI e uvicorn para a interface API
- OpenTelemetry para tracing e observabilidade

### 2. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto baseado no template `.env.example`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```
# Database Configuration
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sql_agent_db
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key
# Application Configuration
LOG_LEVEL=INFO
ENABLE_TRACING=true
TRACING_EXPORTER=console  # console, otlp
OTLP_ENDPOINT=http://localhost:4317  # Only needed if TRACING_EXPORTER=otlp
```

A variável mais crítica é `OPENAI_API_KEY`, que deve ser configurada com uma chave de API válida da sua conta OpenAI.

### 3. PostgreSQL Database

- Instale PostgreSQL se ainda não estiver instalado
- Crie um banco de dados chamado `sql_agent_db`:
  ```bash
  createdb sql_agent_db
  ```
- Certifique-se de que o PostgreSQL esteja rodando na porta padrão (5432)
- As credenciais do banco de dados no arquivo `.env` devem corresponder à sua configuração do PostgreSQL

### 4. Inicialização do Banco de Dados

Execute o script de seed do banco de dados para criar tabelas e populá-las com dados de exemplo:

```bash
python -m sql_agent.database.seed
```

Este script irá:
1. Criar as tabelas `clientes`, `produtos` e `transacoes`
2. Inserir dados de exemplo em cada tabela
3. Estabelecer os relacionamentos entre as tabelas

## Uso

### Iniciar o servidor API

```bash
python -m sql_agent --api
```

O servidor API estará disponível em `http://localhost:8181`.

### Testar com exemplos

```bash
python -m tests.test_examples
```

### API Endpoints

- **POST /api/question**: Processa uma pergunta em linguagem natural
  ```json
  {
    "user_id": "user123",
    "question": "Quais clientes compraram um Notebook?"
  }
  ```

- **GET /api/health**: Verifica a saúde da API

## Exemplos de Perguntas

O sistema foi testado com as seguintes perguntas:

1. "Quais clientes compraram um Notebook?"
2. "Quanto cada cliente gastou no total?"
3. "Quem tem saldo suficiente para comprar um Smartphone?"

## Demonstração RAG

Para executar o script de demonstração RAG que mostra como a implementação RAG funciona:

```bash
python -m sql_agent.rag_demo
```

Este script demonstrativo:

1. Inicializa o RAG retriever e o gerador SQL
2. Processa perguntas de exemplo
3. Para cada pergunta:
   - Recupera documentos relevantes usando o RAG retriever
   - Gera uma consulta SQL usando o gerador SQL (que agora usa RAG)
   - Exibe os documentos recuperados e a consulta SQL gerada

A saída mostrará:
- Os documentos relevantes recuperados para cada pergunta
- O tipo de cada documento (schema, pattern, etc.)
- A consulta SQL gerada com base na pergunta e nos documentos recuperados

Esta demonstração fornece uma visão clara de como a implementação RAG melhora a geração de SQL fornecendo contexto adicional a partir de documentos relevantes.

## Diferenciais Implementados

### RAG (Retrieval-Augmented Generation)

Implementamos RAG para melhorar a geração de consultas SQL, utilizando documentação do esquema do banco de dados e padrões comuns de SQL como fontes adicionais de contexto. O sistema:

1. Armazena documentos sobre o esquema do banco (tabelas, colunas, relacionamentos)
2. Armazena exemplos de padrões comuns de SQL para diferentes tipos de consultas
3. Utiliza embeddings e busca por similaridade para recuperar documentos relevantes
4. Incorpora os documentos recuperados no prompt para gerar consultas SQL mais precisas

Isso permite que o sistema gere consultas SQL mais precisas e eficientes, especialmente para perguntas complexas que envolvem múltiplas tabelas e relacionamentos.

### Arquitetura MCP (Model-Context-Protocol)

Implementamos uma arquitetura MCP que padroniza o contexto compartilhado entre agentes, garantindo coerência e escalabilidade. O contexto é representado por um modelo Pydantic que contém todas as informações necessárias para o processamento da pergunta.

### Memória Persistente Multisessão

O sistema mantém o contexto de conversas passadas por usuário, permitindo referências a perguntas anteriores e construção de conhecimento ao longo do tempo. A memória é armazenada em arquivos JSON por usuário.

### Orquestração Multi-Agente com Papéis Diferentes

Implementamos múltiplos agentes especializados, cada um com um papel específico no processamento da pergunta. Esses agentes são orquestrados por um fluxo LangGraph que coordena o processamento.

### Observabilidade e Tracing

O sistema utiliza OpenTelemetry para registrar logs detalhados de interações, geração de query, execuções e eventuais erros. Os traces podem ser exportados para console ou para um coletor OTLP.

## Segurança

O sistema implementa várias medidas de segurança:
- Validação de consultas SQL para evitar operações perigosas
- Uso de parâmetros em consultas SQL para evitar SQL Injection
- Tratamento adequado de erros para evitar vazamento de informações sensíveis

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.
