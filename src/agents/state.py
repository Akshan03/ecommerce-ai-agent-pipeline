"""
State definition for the LangGraph SKU processing workflow.
"""
from typing import TypedDict, Optional
from src.models.vendor import CleanedVendorProduct
from src.models.outputs import GeneratedContent, CompetitorInsight

class SkuAgentState(TypedDict, total=False):
    """
    Represents the operational state for a single SKU passing through the graph.
    """
    product: CleanedVendorProduct
    content: Optional[GeneratedContent]
    lifestyle_image_path: Optional[str]
    competitor_analysis: Optional[CompetitorInsight]
    error: Optional[str]
    skip_image: bool