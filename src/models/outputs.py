"""
Pydantic models defining the strict JSON structure for the LLM deliverables.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class AttributeItem(BaseModel):
    """A strictly typed key-value pair for product attributes."""
    name: str = Field(..., description="Name of the attribute (e.g., Color, Material, Dimensions)")
    value: str = Field(..., description="Value of the attribute")

class GeneratedContent(BaseModel):
    """E-commerce ready product content."""
    title: str = Field(..., description="SEO optimized product title: [Brand] + [Product Type] + [Key Attribute] + [Color]")
    description: str = Field(..., description="3-4 sentence engaging product description highlighting lifestyle benefits")
    features: List[str] = Field(..., min_length=5, max_length=5, description="Exactly 5 key feature bullet points")
    attributes: List[AttributeItem] = Field(..., description="List of key product specifications")

class CompetitorInsight(BaseModel):
    """Competitor pricing and benchmarking analysis."""
    competitor_product: str = Field(..., description="Name of the comparable competitor product")
    marketplace: str = Field(..., description="Website or marketplace (e.g., Wayfair, Amazon)")
    competitor_price: float = Field(..., description="Price of the competitor product")
    our_price: float = Field(..., description="Our derived reference price")
    price_difference: float = Field(..., description="Difference between our price and competitor price")
    insight: str = Field(..., description="Short, 1-sentence competitive insight")

class FinalSkuOutput(BaseModel):
    """The final aggregated output for a single SKU."""
    sku: str
    content: GeneratedContent
    competitor_analysis: Optional[CompetitorInsight]
    lifestyle_image_path: Optional[str]