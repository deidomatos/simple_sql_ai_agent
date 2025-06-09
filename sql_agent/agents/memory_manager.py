import logging
from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class MemoryManager:
    """
    A class that manages persistent memory across sessions.
    """
    
    def __init__(self, memory_dir: str = "memory"):
        """
        Initialize the Memory Manager.
        
        Args:
            memory_dir: The directory to store memory files.
        """
        self.memory_dir = memory_dir
        
        # Create memory directory if it doesn't exist
        if not os.path.exists(memory_dir):
            os.makedirs(memory_dir)
    
    def get_user_memory_path(self, user_id: str) -> str:
        """
        Get the path to a user's memory file.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            The path to the user's memory file.
        """
        return os.path.join(self.memory_dir, f"{user_id}.json")
    
    def load_memory(self, user_id: str) -> Dict[str, Any]:
        """
        Load a user's memory from disk.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            The user's memory as a dictionary.
        """
        memory_path = self.get_user_memory_path(user_id)
        
        if os.path.exists(memory_path):
            try:
                with open(memory_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error decoding memory file for user {user_id}")
                return self.create_empty_memory()
        else:
            return self.create_empty_memory()
    
    def save_memory(self, user_id: str, memory: Dict[str, Any]) -> None:
        """
        Save a user's memory to disk.
        
        Args:
            user_id: The ID of the user.
            memory: The user's memory as a dictionary.
        """
        memory_path = self.get_user_memory_path(user_id)
        
        try:
            with open(memory_path, "w") as f:
                json.dump(memory, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory for user {user_id}: {str(e)}")
    
    def create_empty_memory(self) -> Dict[str, Any]:
        """
        Create an empty memory structure.
        
        Returns:
            An empty memory dictionary.
        """
        return {
            "conversations": [],
            "preferences": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def add_interaction(self, user_id: str, question: str, sql_query: str, 
                       results: Dict[str, Any], response: str) -> None:
        """
        Add an interaction to a user's memory.
        
        Args:
            user_id: The ID of the user.
            question: The user's question.
            sql_query: The SQL query that was executed.
            results: The results of the SQL query.
            response: The response that was given to the user.
        """
        memory = self.load_memory(user_id)
        
        # Create a new interaction
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "sql_query": sql_query,
            "results_summary": {
                "success": results["success"],
                "row_count": results["row_count"],
                "error": results.get("error", None)
            },
            "response": response
        }
        
        # Add the interaction to the conversations
        memory["conversations"].append(interaction)
        
        # Update the last_updated timestamp
        memory["last_updated"] = datetime.now().isoformat()
        
        # Save the updated memory
        self.save_memory(user_id, memory)
        
        logger.info(f"Added interaction to memory for user {user_id}")
    
    def get_recent_interactions(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get a user's recent interactions.
        
        Args:
            user_id: The ID of the user.
            limit: The maximum number of interactions to return.
            
        Returns:
            A list of the user's recent interactions.
        """
        memory = self.load_memory(user_id)
        
        # Get the most recent interactions
        recent_interactions = memory["conversations"][-limit:] if memory["conversations"] else []
        
        return recent_interactions
    
    def get_context_for_question(self, user_id: str, question: str) -> str:
        """
        Get context from memory that might be relevant to a question.
        
        Args:
            user_id: The ID of the user.
            question: The user's question.
            
        Returns:
            A string containing relevant context from memory.
        """
        recent_interactions = self.get_recent_interactions(user_id)
        
        if not recent_interactions:
            return "No previous interactions found."
        
        # Format the recent interactions as context
        context = "Previous interactions:\n"
        
        for i, interaction in enumerate(recent_interactions):
            context += f"Interaction {i+1}:\n"
            context += f"Question: {interaction['question']}\n"
            context += f"Response: {interaction['response']}\n\n"
        
        return context