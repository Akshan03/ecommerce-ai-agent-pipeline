"""
LLM Utility module.
Provides resilient, unified access to LLMs using LiteLLM and Tenacity.
"""
import json
from typing import Type, TypeVar, Any
from pydantic import BaseModel
import litellm
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)

# Configure litellm to not drop parameters and suppress noisy logs
litellm.drop_params = True 

@retry(
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    retry=retry_if_exception_type((litellm.RateLimitError, litellm.APIConnectionError, litellm.Timeout)),
    reraise=True
)
def generate_structured_output(
    prompt: str, 
    response_model: Type[T], 
    model_name: str = "groq/openai/gpt-oss-20b"
) -> T:
    """
    Generates a structured JSON response from an LLM and parses it into a Pydantic model.
    
    Args:
        prompt (str): The instruction and context for the LLM.
        response_model (Type[T]): The Pydantic model class to enforce and return.
        model_name (str): The LiteLLM formatted model string.
        
    Returns:
        T: An instance of the requested Pydantic model.
    """
    logger.debug(f"Calling LLM ({model_name}) for structured output: {response_model.__name__}")
    
    try:
        response = litellm.completion(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a precise, data-driven e-commerce AI assistant. Always output valid JSON matching the requested schema. Do not include markdown formatting blocks (like ```json) in your response."},
                {"role": "user", "content": prompt}
            ],
            response_format=response_model,
            temperature=0.1,
            timeout=30
        )
        
        # Extract the raw string content
        raw_content = response.choices[0].message.content
        
        # Parse the JSON string into the Pydantic model
        parsed_data = json.loads(raw_content)
        return response_model(**parsed_data)
        
    except Exception as e:
        logger.error(f"LLM Generation failed for {response_model.__name__}: {e}")
        raise