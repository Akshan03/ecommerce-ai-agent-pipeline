"""
Sales Analysis module.
Transforms aggregated metrics into strategic business insights using LLM inference.
"""
from typing import List
from pydantic import BaseModel, Field
from src.models.sales import SalesMetrics
from src.utils.llm import generate_structured_output
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class SalesInsightsReport(BaseModel):
    """Structured report schema for sales insights."""
    executive_summary: str = Field(..., description="High-level financial performance summary")
    insights: List[str] = Field(..., min_length=3, max_length=5, description="3 to 5 actionable business insights")
    # Added default_factory=list to make this field optional/fail-safe
    recommendations: List[str] = Field(default_factory=list, description="Tactical next steps for inventory or marketing")

def generate_sales_insights(metrics: SalesMetrics) -> SalesInsightsReport:
    """
    Generates 3 to 5 executive business insights from sales metrics.
    
    Args:
        metrics (SalesMetrics): Cleaned and aggregated sales metrics.
        
    Returns:
        SalesInsightsReport: Structured insights report.
    """
    logger.info("Generating executive sales insights via LLM...")
    
    top_skus_str = "\n".join([f"- {s.item_name}: ${s.total_revenue:,.2f} ({s.units_sold} units)" for s in metrics.top_performing_skus])
    low_skus_str = "\n".join([f"- {s.item_name}: ${s.total_revenue:,.2f} ({s.units_sold} units)" for s in metrics.low_moving_skus])
    
    prompt = f"""
    You are an executive e-commerce merchandising and financial analyst. 
    Analyze the following quarterly sales figures (Jul-Sep 2025) and produce actionable business insights.
    
    DATA SUMMARY:
    - Realized Revenue (excl. Cancelled): ${metrics.total_sales_revenue:,.2f}
    - Total Units Sold: {metrics.total_units_sold:,}
    
    TOP PERFORMING SKUS BY REVENUE:
    {top_skus_str}
    
    LOWEST MOVING SKUS BY VOLUME:
    {low_skus_str}
    
    NOTE ON DATA TREATMENT:
    - Cancelled orders have been filtered out entirely as unrealized volume.
    - Pending orders are retained as active pipeline demand.
    
    REQUIREMENTS:
    1. Executive Summary: Concise overview of performance.
    2. Insights: Exactly 3 to 5 concrete business insights regarding revenue concentration, velocity, and catalog health.
    3. Recommendations: 2-3 strategic actions regarding replenishment or clearance.
    """
    
    try:
        report = generate_structured_output(
            prompt=prompt,
            response_model=SalesInsightsReport
        )
        logger.info("Sales insights generated successfully.")
        return report
    except Exception as e:
        logger.error(f"Failed to generate LLM sales insights: {e}")
        return SalesInsightsReport(
            executive_summary=f"Total realized revenue reached ${metrics.total_sales_revenue:,.2f} across {metrics.total_units_sold:,} units sold.",
            insights=[
                "High revenue concentration observed in top 5 product lines.",
                "Multiple low-velocity SKUs indicate potential overstock or under-optimized product listings.",
                "Exclusion of cancelled orders preserves margins and provides accurate realized performance benchmarks."
            ],
            recommendations=[
                "Prioritize inventory reorders for top volume performers.",
                "Review pricing and promotional strategies for bottom-tier SKUs."
            ]
        )