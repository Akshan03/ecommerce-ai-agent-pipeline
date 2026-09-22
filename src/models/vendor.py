"""
Pydantic models for validated vendor product data.
"""
from typing import Optional
from pydantic import BaseModel, Field

class CleanedVendorProduct(BaseModel):
    """Represents a sanitized vendor product record ready for the agent pipeline."""
    sku: str = Field(..., description="Unique Product Identifier (Vendor SKU)")
    masked_sku: str = Field(..., description="Masked SKU")
    brand: str = Field(..., description="Brand name")
    category: str = Field(..., description="Product category")
    color: str = Field(..., description="Product color")
    material: str = Field(..., description="Materials used")
    assembly_required: str = Field(..., description="Assembly requirement status")
    raw_copy: str = Field(..., description="Concatenated raw bullet points")
    image_url: str = Field(..., description="Source image URL for the product")
    dimensions_text: str = Field(..., description="Summarized dimension and weight string")
    
    # Derived fields needed for competitor benchmarking
    reference_price: Optional[float] = Field(default=None, description="Derived reference price from sales data")