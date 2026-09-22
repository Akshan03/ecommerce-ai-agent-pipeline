"""
Image Generation Utility.
Handles requests to Pollinations.ai for automated lifestyle image generation.
"""
import urllib.parse
import requests
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def generate_lifestyle_image(prompt: str, sku: str, init_image_url: str, output_dir: Path) -> str | None:
    """
    Generates a lifestyle image using Pollinations.ai and saves it locally.
    
    Args:
        prompt (str): The image generation prompt.
        sku (str): The SKU used for naming the file.
        init_image_url (str): The source product image URL for structural reference.
        output_dir (Path): The directory to save the image.
        
    Returns:
        str | None: The absolute path to the saved image, or None if it failed.
    """
    encoded_prompt = urllib.parse.quote(prompt)
    encoded_url = urllib.parse.quote(init_image_url)
    
    # Pollinations URL with the init_image to enforce product consistency
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed=42&width=1024&height=1024&nologo=true&image={encoded_url}"
    
    output_path = output_dir / f"{sku}_lifestyle.png"
    
    logger.info(f"Generating image for SKU {sku}...")
    try:
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
            
        logger.info(f"Image successfully saved to {output_path.name}")
        return str(output_path.absolute())
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to generate image for SKU {sku}: {e}")
        return None