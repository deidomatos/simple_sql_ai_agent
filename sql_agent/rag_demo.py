"""
A simple demonstration of the RAG implementation for SQL generation.
This script shows how the RAG retriever works and how it enhances SQL generation.
"""

import logging
import os
import sys
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the RAG retriever and SQL generator
from sql_agent.agents.rag_retriever import RAGRetriever
from sql_agent.agents.sql_generator import SQLGenerator

def demonstrate_rag():
    """
    Demonstrate how the RAG implementation works.
    """
    logger.info("Initializing RAG retriever...")
    rag_retriever = RAGRetriever()
    
    logger.info("Initializing SQL generator...")
    sql_generator = SQLGenerator()
    
    # Example questions
    example_questions = [
        "Quais clientes compraram um Notebook?",
        "Quanto cada cliente gastou no total?",
        "Quem tem saldo suficiente para comprar um Smartphone?"
    ]
    
    # Process each question
    for i, question in enumerate(example_questions):
        logger.info(f"\n\n--- Example Question {i+1}: {question} ---")
        
        # Retrieve relevant documents
        logger.info("Retrieving relevant documents...")
        relevant_docs = rag_retriever.retrieve_relevant_documents(question)
        
        # Print the retrieved documents
        logger.info(f"Retrieved {len(relevant_docs)} relevant documents:")
        for j, doc in enumerate(relevant_docs):
            logger.info(f"Document {j+1} (type: {doc.metadata.get('type', 'unknown')}):")
            logger.info(doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)
        
        # Generate SQL query
        logger.info("Generating SQL query...")
        sql_query = sql_generator.generate_sql(question)
        
        # Print the generated SQL query
        logger.info(f"Generated SQL query: {sql_query}")
        
        logger.info("---\n\n")

if __name__ == "__main__":
    logger.info("Starting RAG demonstration...")
    demonstrate_rag()
    logger.info("RAG demonstration completed.")