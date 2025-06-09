import logging
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uvicorn
import os
from ..flow import SQLAgentGraph
from ..database.seed import seed_database
from ..utils.tracing import setup_tracing

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up tracing
setup_tracing()

# Create the FastAPI app
app = FastAPI(
    title="SQL Agent API",
    description="An API for a SQL Agent that converts natural language to SQL",
    version="1.0.0",
)

# Create the SQL Agent Graph
sql_agent_graph = SQLAgentGraph()

# Define request and response models
class QuestionRequest(BaseModel):
    user_id: str = Field(default="anonymous", description="The ID of the user")
    question: str = Field(..., description="The natural language question to convert to SQL")

class QuestionResponse(BaseModel):
    question: str = Field(..., description="The original question")
    sql_query: str = Field(..., description="The generated SQL query")
    response: str = Field(..., description="The formatted response")
    success: bool = Field(..., description="Whether the request was successful")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Any errors that occurred")

@app.post("/api/question", response_model=QuestionResponse)
async def process_question(request: QuestionRequest):
    """
    Process a natural language question and return a response.
    """
    logger.info(f"Received question from user {request.user_id}: {request.question}")
    
    try:
        # Process the question
        result = sql_agent_graph.process_question(request.user_id, request.question)
        
        logger.info(f"Processed question successfully: {result['success']}")
        
        return result
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/api/health")
async def health_check():
    """
    Check the health of the API.
    """
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """
    Initialize the database on startup.
    """
    logger.info("Initializing database...")
    try:
        seed_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

def start():
    """
    Start the FastAPI server.
    """
    port = int(os.getenv("PORT", "8181"))
    uvicorn.run("sql_agent.api.app:app", host="0.0.0.0", port=port, reload=True)

if __name__ == "__main__":
    start()