import logging
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from ..database.connection import get_db_session
from ..utils.tracing import get_tracer

# Set up logging
logger = logging.getLogger(__name__)

# Set up tracing
tracer = get_tracer("sql_executor")

class SQLExecutor:
    """
    A class that safely executes SQL queries and formats the results.
    """
    
    def __init__(self):
        """Initialize the SQL Executor."""
        pass
    
    def validate_sql(self, sql_query: str) -> bool:
        """
        Validate that the SQL query is safe to execute.
        
        Args:
            sql_query: The SQL query to validate.
            
        Returns:
            True if the query is safe, False otherwise.
        """
        with tracer.start_as_current_span("validate_sql") as span:
            span.set_attribute("sql_query", sql_query)
            
            # Convert to lowercase for easier checking
            sql_lower = sql_query.lower()
            
            # Check for dangerous operations
            dangerous_keywords = [
                "drop", "delete", "truncate", "update", "insert", "alter", "create", 
                "grant", "revoke", "commit", "rollback", "begin", "end", "vacuum"
            ]
            
            for keyword in dangerous_keywords:
                if keyword in sql_lower.split():
                    logger.warning(f"Dangerous SQL operation detected: {keyword}")
                    span.set_attribute("is_safe", False)
                    span.set_attribute("dangerous_keyword", keyword)
                    return False
            
            # Ensure the query is a SELECT statement
            if not sql_lower.strip().startswith("select"):
                logger.warning("SQL query does not start with SELECT")
                span.set_attribute("is_safe", False)
                span.set_attribute("reason", "not_select")
                return False
            
            logger.info("SQL query validated as safe")
            span.set_attribute("is_safe", True)
            return True
    
    def execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute a SQL query and return the results.
        
        Args:
            sql_query: The SQL query to execute.
            
        Returns:
            A dictionary containing the results and metadata.
        """
        with tracer.start_as_current_span("execute_sql") as span:
            span.set_attribute("sql_query", sql_query)
            
            # Validate the SQL query
            if not self.validate_sql(sql_query):
                error_msg = "SQL query failed validation"
                logger.error(error_msg)
                span.set_attribute("error", error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "data": None,
                    "columns": None,
                    "row_count": 0
                }
            
            # Get a database session
            session_generator = get_db_session()
            session = next(session_generator)
            
            try:
                # Execute the query
                logger.info(f"Executing SQL query: {sql_query}")
                result = session.execute(text(sql_query))
                
                # Convert to pandas DataFrame for easier manipulation
                df = pd.DataFrame(result.fetchall())
                
                # If the result is empty, return empty lists
                if df.empty:
                    logger.info("Query returned no results")
                    return {
                        "success": True,
                        "data": [],
                        "columns": result.keys(),
                        "row_count": 0
                    }
                
                # Set column names
                df.columns = result.keys()
                
                # Convert DataFrame to list of dictionaries
                records = df.to_dict(orient="records")
                
                logger.info(f"Query executed successfully, returned {len(records)} rows")
                span.set_attribute("row_count", len(records))
                
                return {
                    "success": True,
                    "data": records,
                    "columns": list(df.columns),
                    "row_count": len(records)
                }
                
            except SQLAlchemyError as e:
                error_msg = f"Database error: {str(e)}"
                logger.error(error_msg)
                span.record_exception(e)
                return {
                    "success": False,
                    "error": error_msg,
                    "data": None,
                    "columns": None,
                    "row_count": 0
                }
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(error_msg)
                span.record_exception(e)
                return {
                    "success": False,
                    "error": error_msg,
                    "data": None,
                    "columns": None,
                    "row_count": 0
                }
            finally:
                session.close()
    
    def format_results(self, results: Dict[str, Any], format_type: str = "text") -> str:
        """
        Format the query results into a human-readable format.
        
        Args:
            results: The query results to format.
            format_type: The type of formatting to apply (text, html, etc.).
            
        Returns:
            A formatted string representation of the results.
        """
        with tracer.start_as_current_span("format_results") as span:
            span.set_attribute("format_type", format_type)
            span.set_attribute("success", results["success"])
            
            if not results["success"]:
                return f"Error: {results['error']}"
            
            if results["row_count"] == 0:
                return "No results found."
            
            if format_type == "text":
                # Create a pandas DataFrame for nice text formatting
                df = pd.DataFrame(results["data"])
                return df.to_string(index=False)
            
            elif format_type == "html":
                # Create a pandas DataFrame for HTML formatting
                df = pd.DataFrame(results["data"])
                return df.to_html(index=False)
            
            else:
                return str(results["data"])