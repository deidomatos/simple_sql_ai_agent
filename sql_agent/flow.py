import logging
from typing import Dict, Any, Tuple, List, Annotated, TypedDict
from langgraph.graph import StateGraph, END
from .agents.sql_generator import SQLGenerator
from .agents.sql_executor import SQLExecutor
from .agents.response_formatter import ResponseFormatter
from .agents.memory_manager import MemoryManager
from .agents.mcp import Context
from .utils.tracing import get_tracer, setup_tracing

# Set up logging
logger = logging.getLogger(__name__)

# Set up tracing
setup_tracing()
tracer = get_tracer("sql_agent_flow")

class SQLAgentGraph:
    """
    A class that implements the LangGraph flow for the SQL Agent.
    """
    
    def __init__(self):
        """Initialize the SQL Agent Graph."""
        # Initialize agents
        self.sql_generator = SQLGenerator()
        self.sql_executor = SQLExecutor()
        self.response_formatter = ResponseFormatter()
        self.memory_manager = MemoryManager()
        
        # Create the graph
        self.graph = self.build_graph()
    
    def build_graph(self) -> StateGraph:
        """
        Build the LangGraph flow.
        
        Returns:
            A StateGraph object representing the flow.
        """
        # Create a new graph
        graph = StateGraph(Context)
        
        # Add nodes to the graph
        graph.add_node("load_context", self.load_context)
        graph.add_node("generate_sql", self.generate_sql)
        graph.add_node("execute_sql", self.execute_sql)
        graph.add_node("format_response", self.format_response)
        graph.add_node("save_memory", self.save_memory)
        
        # Define the edges
        graph.add_edge("load_context", "generate_sql")
        graph.add_edge("generate_sql", "execute_sql")
        graph.add_edge("execute_sql", "format_response")
        graph.add_edge("format_response", "save_memory")
        graph.add_edge("save_memory", END)
        
        # Add conditional edges for error handling
        graph.add_conditional_edges(
            "generate_sql",
            self.check_for_errors,
            {
                "error": "format_response",
                "success": "execute_sql"
            }
        )
        
        graph.add_conditional_edges(
            "execute_sql",
            self.check_for_errors,
            {
                "error": "format_response",
                "success": "format_response"
            }
        )
        
        # Set the entry point
        graph.set_entry_point("load_context")
        
        return graph
    
    def load_context(self, context: Context) -> Context:
        """
        Load context for the user, including conversation history.
        
        Args:
            context: The current context.
            
        Returns:
            The updated context.
        """
        with tracer.start_as_current_span("load_context") as span:
            span.set_attribute("user_id", context.user_id)
            
            logger.info(f"Loading context for user {context.user_id}")
            
            try:
                # Get recent interactions from memory
                recent_interactions = self.memory_manager.get_recent_interactions(context.user_id)
                
                # Update the context with the recent interactions
                context.conversation_history = recent_interactions
                
                # Add metadata
                context.update_metadata("context_loaded", True)
                context.update_metadata("history_length", len(recent_interactions))
                
                logger.info(f"Loaded {len(recent_interactions)} recent interactions")
                
                return context
            except Exception as e:
                error_msg = f"Error loading context: {str(e)}"
                logger.error(error_msg)
                context.add_error("load_context", error_msg)
                return context
    
    def generate_sql(self, context: Context) -> Context:
        """
        Generate a SQL query from the user's question.
        
        Args:
            context: The current context.
            
        Returns:
            The updated context.
        """
        with tracer.start_as_current_span("generate_sql") as span:
            span.set_attribute("question", context.question)
            
            logger.info(f"Generating SQL for question: {context.question}")
            
            try:
                # Generate the SQL query
                sql_query = self.sql_generator.generate_sql(context.question)
                
                # Update the context
                context.sql_query = sql_query
                
                logger.info(f"Generated SQL query: {sql_query}")
                
                return context
            except Exception as e:
                error_msg = f"Error generating SQL: {str(e)}"
                logger.error(error_msg)
                context.add_error("generate_sql", error_msg)
                return context
    
    def execute_sql(self, context: Context) -> Context:
        """
        Execute the SQL query.
        
        Args:
            context: The current context.
            
        Returns:
            The updated context.
        """
        with tracer.start_as_current_span("execute_sql") as span:
            span.set_attribute("sql_query", context.sql_query)
            
            logger.info(f"Executing SQL query: {context.sql_query}")
            
            try:
                # Execute the SQL query
                results = self.sql_executor.execute_sql(context.sql_query)
                
                # Update the context
                context.query_results = results
                context.is_query_validated = results["success"]
                
                if results["success"]:
                    logger.info(f"Query executed successfully, returned {results['row_count']} rows")
                else:
                    error_msg = f"Query execution failed: {results['error']}"
                    logger.error(error_msg)
                    context.add_error("execute_sql", error_msg, "database_error")
                
                return context
            except Exception as e:
                error_msg = f"Error executing SQL: {str(e)}"
                logger.error(error_msg)
                context.add_error("execute_sql", error_msg)
                return context
    
    def format_response(self, context: Context) -> Context:
        """
        Format the response to the user.
        
        Args:
            context: The current context.
            
        Returns:
            The updated context.
        """
        with tracer.start_as_current_span("format_response") as span:
            span.set_attribute("has_errors", context.has_errors())
            
            logger.info("Formatting response")
            
            try:
                # If there are errors, create an error response
                if context.has_errors():
                    last_error = context.get_last_error()
                    error_msg = last_error["message"] if last_error else "An unknown error occurred"
                    
                    # Create a simple error response
                    context.response = f"I'm sorry, but I encountered an error: {error_msg}"
                    
                    logger.info(f"Created error response: {context.response}")
                else:
                    # Format the successful response
                    response = self.response_formatter.format_response(
                        context.question,
                        context.sql_query,
                        context.query_results
                    )
                    
                    # Update the context
                    context.response = response
                    
                    logger.info("Response formatted successfully")
                
                return context
            except Exception as e:
                error_msg = f"Error formatting response: {str(e)}"
                logger.error(error_msg)
                context.add_error("format_response", error_msg)
                
                # Provide a fallback response
                context.response = "I'm sorry, but I encountered an error while formatting the response."
                
                return context
    
    def save_memory(self, context: Context) -> Context:
        """
        Save the interaction to memory.
        
        Args:
            context: The current context.
            
        Returns:
            The updated context.
        """
        with tracer.start_as_current_span("save_memory") as span:
            span.set_attribute("user_id", context.user_id)
            
            logger.info(f"Saving memory for user {context.user_id}")
            
            try:
                # Save the interaction to memory
                self.memory_manager.add_interaction(
                    context.user_id,
                    context.question,
                    context.sql_query,
                    context.query_results,
                    context.response
                )
                
                logger.info("Memory saved successfully")
                
                return context
            except Exception as e:
                error_msg = f"Error saving memory: {str(e)}"
                logger.error(error_msg)
                context.add_error("save_memory", error_msg)
                return context
    
    def check_for_errors(self, context: Context) -> str:
        """
        Check if there are any errors in the context.
        
        Args:
            context: The current context.
            
        Returns:
            "error" if there are errors, "success" otherwise.
        """
        return "error" if context.has_errors() else "success"
    
    def process_question(self, user_id: str, question: str) -> Dict[str, Any]:
        """
        Process a user's question.
        
        Args:
            user_id: The ID of the user.
            question: The user's question.
            
        Returns:
            A dictionary containing the response and other information.
        """
        with tracer.start_as_current_span("process_question") as span:
            span.set_attribute("user_id", user_id)
            span.set_attribute("question", question)
            
            logger.info(f"Processing question for user {user_id}: {question}")
            
            # Create the initial context
            context = Context(
                user_id=user_id,
                question=question
            )
            
            # Run the graph
            final_context = self.graph.invoke(context)
            
            # Return the results
            return {
                "question": question,
                "sql_query": final_context.sql_query,
                "response": final_context.response,
                "success": not final_context.has_errors(),
                "errors": final_context.errors
            }