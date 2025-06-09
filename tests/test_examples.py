import os
import sys
import logging
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the sql_agent package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_agent.flow import SQLAgentGraph
from sql_agent.database.seed import seed_database

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_example_questions():
    """
    Test the SQL Agent with the example questions from the requirements.
    """
    # Initialize the database
    logger.info("Initializing the database...")
    seed_database()
    
    # Create the SQL Agent Graph
    sql_agent = SQLAgentGraph()
    
    # Example questions from the requirements
    example_questions = [
        "Quais clientes compraram um Notebook?",
        "Quanto cada cliente gastou no total?",
        "Quem tem saldo suficiente para comprar um Smartphone?"
    ]
    
    # Process each question
    for i, question in enumerate(example_questions):
        logger.info(f"\n\n--- Example Question {i+1}: {question} ---")
        
        # Process the question
        result = sql_agent.process_question("test_user", question)
        
        # Print the results
        logger.info(f"Question: {result['question']}")
        logger.info(f"SQL Query: {result['sql_query']}")
        logger.info(f"Response: {result['response']}")
        logger.info(f"Success: {result['success']}")
        
        if not result['success']:
            logger.error(f"Errors: {result['errors']}")
        
        logger.info("---\n\n")

if __name__ == "__main__":
    test_example_questions()