from typing import Dict, Any, List, Optional, TypedDict, Union
from pydantic import BaseModel, Field

class Context(BaseModel):
    """
    A standardized context object shared between agents.
    Implements the Model-Context-Protocol (MCP) architecture.
    """
    # User information
    user_id: str = Field(default="anonymous", description="The ID of the user")
    
    # Input
    question: str = Field(default="", description="The original question from the user")
    
    # Processing state
    sql_query: str = Field(default="", description="The generated SQL query")
    is_query_validated: bool = Field(default=False, description="Whether the query has been validated")
    
    # Results
    query_results: Dict[str, Any] = Field(
        default_factory=dict, 
        description="The results of the SQL query execution"
    )
    
    # Response
    response: str = Field(default="", description="The formatted response to the user")
    
    # Memory and context
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent conversation history for context"
    )
    
    # Error handling
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Errors encountered during processing"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the request"
    )
    
    def add_error(self, agent_name: str, error_message: str, error_type: str = "general") -> None:
        """
        Add an error to the context.
        
        Args:
            agent_name: The name of the agent that encountered the error.
            error_message: A description of the error.
            error_type: The type of error.
        """
        self.errors.append({
            "agent": agent_name,
            "message": error_message,
            "type": error_type
        })
    
    def has_errors(self) -> bool:
        """
        Check if there are any errors in the context.
        
        Returns:
            True if there are errors, False otherwise.
        """
        return len(self.errors) > 0
    
    def get_last_error(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent error.
        
        Returns:
            The most recent error, or None if there are no errors.
        """
        if self.errors:
            return self.errors[-1]
        return None
    
    def update_metadata(self, key: str, value: Any) -> None:
        """
        Update a metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata value.
        
        Args:
            key: The metadata key.
            default: The default value to return if the key is not found.
            
        Returns:
            The metadata value, or the default value if the key is not found.
        """
        return self.metadata.get(key, default)