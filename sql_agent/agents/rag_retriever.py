import logging
import os
from typing import Dict, Any, List, Optional
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from ..utils.tracing import get_tracer
from ..database.models import Cliente, Produto, Transacao

# Set up logging
logger = logging.getLogger(__name__)

# Set up tracing
tracer = get_tracer("rag_retriever")

class RAGRetriever:
    """
    A class that implements Retrieval-Augmented Generation (RAG) for SQL generation.
    It retrieves relevant documents based on the user's question to provide additional context.
    """

    # Use text-embedding-3-small for the best cost efficiency or text-embedding-ada-002 for higher accuracy
    openai_model = "text-embedding-3-small"
    
    def __init__(self, embeddings_model: str = openai_model): 
        """
        Initialize the RAG Retriever.
        
        Args:
            embeddings_model: The name of the embeddings model to use.
        """
        self.embeddings = OpenAIEmbeddings(model=embeddings_model)
        self.vector_store = None
        self.documents = []
        
        # Initialize the vector store
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """
        Initialize the vector store with documents about the database schema and common SQL patterns.
        """
        with tracer.start_as_current_span("initialize_vector_store") as span:
            logger.info("Initializing vector store for RAG")
            
            # Create documents about the database schema
            self.documents = self._create_schema_documents()
            
            # Add documents about common SQL patterns
            self.documents.extend(self._create_sql_pattern_documents())
            
            # Create the vector store
            if self.documents:
                try:
                    self.vector_store = FAISS.from_documents(self.documents, self.embeddings)
                    logger.info(f"Vector store initialized with {len(self.documents)} documents")
                    span.set_attribute("document_count", len(self.documents))
                except Exception as e:
                    logger.error(f"Error initializing vector store: {str(e)}")
                    span.record_exception(e)
            else:
                logger.warning("No documents to initialize vector store")
    
    def _create_schema_documents(self) -> List[Document]:
        """
        Create documents about the database schema.
        
        Returns:
            A list of Document objects.
        """
        documents = []
        
        # Document for Cliente table
        cliente_doc = Document(
            page_content="""
            Table: clientes
            Description: Contains information about clients.
            Columns:
            - id (Integer): Primary key
            - nome (String): Client name
            - email (String): Client email (unique)
            - saldo (Float): Client balance
            - data_cadastro (DateTime): Registration date
            Relationships:
            - One client can have many transactions (transacoes)
            """,
            metadata={"type": "schema", "table": "clientes"}
        )
        documents.append(cliente_doc)
        
        # Document for Produto table
        produto_doc = Document(
            page_content="""
            Table: produtos
            Description: Contains information about products.
            Columns:
            - id (Integer): Primary key
            - nome (String): Product name
            - descricao (String): Product description
            - preco (Float): Product price
            - estoque (Integer): Product stock
            Relationships:
            - One product can be in many transactions (transacoes)
            """,
            metadata={"type": "schema", "table": "produtos"}
        )
        documents.append(produto_doc)
        
        # Document for Transacao table
        transacao_doc = Document(
            page_content="""
            Table: transacoes
            Description: Contains information about transactions.
            Columns:
            - id (Integer): Primary key
            - cliente_id (Integer): Foreign key to clientes.id
            - produto_id (Integer): Foreign key to produtos.id
            - quantidade (Integer): Quantity of products
            - valor_total (Float): Total value of the transaction
            - data_transacao (DateTime): Transaction date
            Relationships:
            - Many transactions can belong to one client (cliente)
            - Many transactions can be for one product (produto)
            """,
            metadata={"type": "schema", "table": "transacoes"}
        )
        documents.append(transacao_doc)
        
        # Document for database relationships
        relationships_doc = Document(
            page_content="""
            Database Relationships:
            1. clientes to transacoes: One-to-Many
               - A client can have multiple transactions
               - Each transaction belongs to exactly one client
               - Join: clientes.id = transacoes.cliente_id
            
            2. produtos to transacoes: One-to-Many
               - A product can be in multiple transactions
               - Each transaction is for exactly one product
               - Join: produtos.id = transacoes.produto_id
            """,
            metadata={"type": "schema", "subject": "relationships"}
        )
        documents.append(relationships_doc)
        
        return documents
    
    def _create_sql_pattern_documents(self) -> List[Document]:
        """
        Create documents about common SQL patterns.
        
        Returns:
            A list of Document objects.
        """
        documents = []
        
        # Document for finding clients who bought a specific product
        clients_product_doc = Document(
            page_content="""
            Pattern: Find clients who bought a specific product
            SQL Example:
            ```sql
            SELECT DISTINCT c.id, c.nome, c.email
            FROM clientes c
            JOIN transacoes t ON c.id = t.cliente_id
            JOIN produtos p ON t.produto_id = p.id
            WHERE p.nome = 'Product Name'
            ```
            """,
            metadata={"type": "pattern", "subject": "clients_by_product"}
        )
        documents.append(clients_product_doc)
        
        # Document for calculating total spent by each client
        total_spent_doc = Document(
            page_content="""
            Pattern: Calculate total spent by each client
            SQL Example:
            ```sql
            SELECT c.id, c.nome, SUM(t.valor_total) as total_gasto
            FROM clientes c
            LEFT JOIN transacoes t ON c.id = t.cliente_id
            GROUP BY c.id, c.nome
            ORDER BY total_gasto DESC
            ```
            """,
            metadata={"type": "pattern", "subject": "total_spent"}
        )
        documents.append(total_spent_doc)
        
        # Document for finding clients with sufficient balance
        sufficient_balance_doc = Document(
            page_content="""
            Pattern: Find clients with sufficient balance to buy a product
            SQL Example:
            ```sql
            SELECT c.id, c.nome, c.email, c.saldo
            FROM clientes c
            WHERE c.saldo >= (SELECT preco FROM produtos WHERE nome = 'Product Name')
            ```
            """,
            metadata={"type": "pattern", "subject": "sufficient_balance"}
        )
        documents.append(sufficient_balance_doc)
        
        # Document for finding most popular products
        popular_products_doc = Document(
            page_content="""
            Pattern: Find most popular products
            SQL Example:
            ```sql
            SELECT p.id, p.nome, COUNT(t.id) as num_vendas
            FROM produtos p
            JOIN transacoes t ON p.id = t.produto_id
            GROUP BY p.id, p.nome
            ORDER BY num_vendas DESC
            ```
            """,
            metadata={"type": "pattern", "subject": "popular_products"}
        )
        documents.append(popular_products_doc)
        
        return documents
    
    def retrieve_relevant_documents(self, question: str, k: int = 3) -> List[Document]:
        """
        Retrieve relevant documents based on the user's question.
        
        Args:
            question: The user's question.
            k: The number of documents to retrieve.
            
        Returns:
            A list of relevant Document objects.
        """
        with tracer.start_as_current_span("retrieve_relevant_documents") as span:
            span.set_attribute("question", question)
            span.set_attribute("k", k)
            
            logger.info(f"Retrieving relevant documents for question: {question}")
            
            if not self.vector_store:
                logger.warning("Vector store not initialized")
                return []
            
            try:
                # Retrieve relevant documents
                docs = self.vector_store.similarity_search(question, k=k)
                
                logger.info(f"Retrieved {len(docs)} relevant documents")
                span.set_attribute("retrieved_count", len(docs))
                
                return docs
            except Exception as e:
                logger.error(f"Error retrieving documents: {str(e)}")
                span.record_exception(e)
                return []
    
    def get_context_from_documents(self, docs: List[Document]) -> str:
        """
        Extract context from retrieved documents.
        
        Args:
            docs: The retrieved documents.
            
        Returns:
            A string containing the context extracted from the documents.
        """
        if not docs:
            return ""
        
        context = "Relevant Database Information:\n\n"
        
        for i, doc in enumerate(docs):
            context += f"Document {i+1}:\n{doc.page_content}\n\n"
        
        return context