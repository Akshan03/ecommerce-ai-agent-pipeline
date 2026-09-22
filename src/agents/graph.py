"""
LangGraph definition and compilation for SKU processing.
"""
from langgraph.graph import StateGraph, START, END
from src.agents.state import SkuAgentState
from src.agents.nodes import (
    generate_content_node,
    generate_image_node,
    competitor_analysis_node
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def build_sku_graph():
    """
    Constructs and compiles the LangGraph state machine for processing a single SKU.
    
    Returns:
        CompiledStateGraph: Ready-to-execute workflow.
    """
    logger.info("Assembling LangGraph workflow for SKU pipeline...")
    workflow = StateGraph(SkuAgentState)
    
    # Register Nodes
    workflow.add_node("content_generation", generate_content_node)
    workflow.add_node("image_generation", generate_image_node)
    workflow.add_node("competitor_analysis", competitor_analysis_node)
    
    # Define Linear Sequence: START -> content -> image -> competitor -> END
    workflow.add_edge(START, "content_generation")
    workflow.add_edge("content_generation", "image_generation")
    workflow.add_edge("image_generation", "competitor_analysis")
    workflow.add_edge("competitor_analysis", END)
    
    compiled_graph = workflow.compile()
    logger.info("LangGraph workflow compiled successfully.")
    return compiled_graph