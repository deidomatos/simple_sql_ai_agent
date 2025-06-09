import logging
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..utils.llm import get_llm
from ..utils.tracing import get_tracer
from .rag_retriever import RAGRetriever

# Set up logging
logger = logging.getLogger(__name__)

# Set up tracing
tracer = get_tracer("sql_generator")

# Template for generating SQL from natural language with RAG context
SQL_GENERATION_TEMPLATE = """
You are an expert SQL query generator for a PostgreSQL database. Your task is to convert natural language questions into correct and efficient SQL queries.

Database Schema:
- clientes (id, nome, email, saldo, data_cadastro)
- produtos (id, nome, descricao, preco, estoque)
- transacoes (id, cliente_id, produto_id, quantidade, valor_total, data_transacao)

Relationships:
- clientes.id = transacoes.cliente_id (One client can have many transactions)
- produtos.id = transacoes.produto_id (One product can be in many transactions)

{context}

Question: {question}

Think step by step:
1. Understand what tables and fields are needed
2. Determine the necessary joins
3. Identify any filters, groupings, or aggregations
4. Construct a valid SQL query

Important guidelines:
- Use proper SQL syntax for PostgreSQL
- Include appropriate JOINs when querying across tables
- Use aliases for readability (e.g., "c" for clientes)
- Apply proper filtering in WHERE clauses
- Use aggregation functions (SUM, COUNT, AVG) when needed
- Format the query with proper indentation
- Do not use any dangerous operations (DROP, DELETE, UPDATE, INSERT, etc.)
- Return ONLY the SQL query without any explanations or markdown formatting

SQL Query:
"""

class SQLGenerator:
    """
    A class that generates SQL queries from natural language questions.
    Uses Retrieval-Augmented Generation (RAG) to provide additional context.
    """

    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.0):
        """
        Initialize the SQL Generator.

        Args:
            model_name: The name of the language model to use.
            temperature: Controls randomness in the model's output.
        """
        self.llm = get_llm(temperature=temperature, model_name=model_name)
        self.prompt = ChatPromptTemplate.from_template(SQL_GENERATION_TEMPLATE)

        # Initialize the RAG retriever
        self.rag_retriever = RAGRetriever()

        # Create the chain
        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_sql(self, question: str) -> str:
        """
        Generate a SQL query from a natural language question.
        Uses RAG to retrieve relevant context for the question.

        Args:
            question: The natural language question to convert to SQL.

        Returns:
            A SQL query string.
        """
        with tracer.start_as_current_span("generate_sql") as span:
            span.set_attribute("question", question)

            logger.info(f"Generating SQL for question: {question}")

            try:
                # Retrieve relevant documents using RAG
                with tracer.start_as_current_span("retrieve_context") as context_span:
                    relevant_docs = self.rag_retriever.retrieve_relevant_documents(question)
                    context = self.rag_retriever.get_context_from_documents(relevant_docs)
                    context_span.set_attribute("doc_count", len(relevant_docs))
                    logger.info(f"Retrieved {len(relevant_docs)} relevant documents for context")

                # Invoke the chain with the question and context
                sql_query = self.chain.invoke({
                    "question": question,
                    "context": context
                })

                # Clean up the SQL query (remove backticks, etc.)
                sql_query = sql_query.strip()
                if sql_query.startswith("```sql"):
                    sql_query = sql_query[6:]
                if sql_query.endswith("```"):
                    sql_query = sql_query[:-3]
                sql_query = sql_query.strip()

                logger.info(f"Generated SQL query: {sql_query}")
                span.set_attribute("sql_query", sql_query)
                span.set_attribute("used_rag", True)

                return sql_query
            except Exception as e:
                logger.error(f"Error generating SQL: {str(e)}")
                span.record_exception(e)
                raise
