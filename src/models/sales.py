"""
Pydantic models for sales aggregations and insights.
"""
from typing import List
from pydantic import BaseModel, Field

class SkuPerformance(BaseModel):
    """Metrics for a single SKU's sales performance."""
    item_name: str
    total_revenue: float
    units_sold: int

class SalesMetrics(BaseModel):
    """Aggregated sales data ready for LLM insight generation."""
    total_sales_revenue: float = Field(..., description="Total realized revenue (excluding cancelled)")
    total_units_sold: int = Field(..., description="Total realized units (excluding cancelled)")
    top_performing_skus: List[SkuPerformance] = Field(..., description="Top SKUs by revenue")
    low_moving_skus: List[SkuPerformance] = Field(..., description="SKUs with very low sales volume")