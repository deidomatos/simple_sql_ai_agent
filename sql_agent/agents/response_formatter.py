import logging
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..utils.llm import get_llm
from ..utils.tracing import get_tracer

# Set up logging
logger = logging.getLogger(__name__)

# Set up tracing
tracer = get_tracer("response_formatter")

# Template for formatting SQL results into natural language
RESPONSE_FORMATTING_TEMPLATE = """
You are an expert at interpreting SQL query results and explaining them in natural language.
Your task is to take the results of a SQL query and the original question, and provide a clear, concise answer.

Original Question: {question}

SQL Query Used: {sql_query}

Query Results:
{results}

Please provide a natural language response that:
1. Directly answers the original question
2. Summarizes the key information from the results
3. Provides any relevant insights or patterns
4. Is conversational and easy to understand
5. Includes specific numbers or data points from the results when relevant

If the results are empty, explain that no data was found that matches the criteria.
If there was an error, explain what might have gone wrong in simple terms.

Your response should be helpful and informative without being overly technical.
"""

class ResponseFormatter:
    """
    A class that formats SQL query results into natural language responses.
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.3):
        """
        Initialize the Response Formatter.
        
        Args:
            model_name: The name of the language model to use.
            temperature: Controls randomness in the model's output.
        """
        self.llm = get_llm(temperature=temperature, model_name=model_name)
        self.prompt = ChatPromptTemplate.from_template(RESPONSE_FORMATTING_TEMPLATE)
        
        # Create the chain
        self.chain = (
            self.prompt
            | self.llm
            | StrOutputParser()
        )
    
    def format_response(self, question: str, sql_query: str, results: Dict[str, Any]) -> str:
        """
        Format SQL query results into a natural language response.
        
        Args:
            question: The original natural language question.
            sql_query: The SQL query that was executed.
            results: The results of the SQL query execution.
            
        Returns:
            A natural language response explaining the results.
        """
        with tracer.start_as_current_span("format_response") as span:
            span.set_attribute("question", question)
            span.set_attribute("sql_query", sql_query)
            
            logger.info(f"Formatting response for question: {question}")
            
            # Format the results as a string for the prompt
            if results["success"]:
                if results["row_count"] == 0:
                    results_str = "No results found."
                else:
                    # Create a string representation of the results
                    results_str = "Results:\n"
                    for i, row in enumerate(results["data"]):
                        results_str += f"Row {i+1}: {row}\n"
            else:
                results_str = f"Error: {results['error']}"
            
            try:
                # Invoke the chain with the question, SQL query, and results
                response = self.chain.invoke({
                    "question": question,
                    "sql_query": sql_query,
                    "results": results_str
                })
                
                logger.info("Response formatted successfully")
                return response
            except Exception as e:
                logger.error(f"Error formatting response: {str(e)}")
                span.record_exception(e)
                
                # Provide a fallback response
                if results["success"]:
                    if results["row_count"] == 0:
                        return "No results were found that match your query."
                    else:
                        return f"Found {results['row_count']} results. Here's the data: {str(results['data'])}"
                else:
                    return f"There was an error processing your query: {results['error']}"