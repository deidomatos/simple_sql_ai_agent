import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

# Load environment variables
load_dotenv()

def get_llm(temperature: float = 0.0, model_name: str = "gpt-3.5-turbo") -> BaseChatModel:
    """
    Get a language model instance.
    
    Args:
        temperature: Controls randomness. Lower values make responses more deterministic.
        model_name: The name of the model to use.
        
    Returns:
        A language model instance.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    return ChatOpenAI(
        temperature=temperature,
        model=model_name,
        openai_api_key=openai_api_key,
        verbose=True
    )