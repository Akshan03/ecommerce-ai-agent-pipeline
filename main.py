"""
Main entry point for the AI Agent Screening Test pipeline.
Executes the end-to-end process: Data Load -> Sales Analysis -> SKU Graph Execution -> Export.
"""
import argparse
import json
from pathlib import Path
from pydantic import BaseModel

from config.settings import settings
from src.utils.logger import setup_logger
from src.cleaner.pipeline import DataPipeline
from src.agents.graph import build_sku_graph
from src.agents.sales_analyst import generate_sales_insights
from src.models.outputs import FinalSkuOutput
import time

logger = setup_logger("main")

def export_json(data: BaseModel | list[BaseModel], output_path: Path):
    """Helper to export Pydantic models to JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        if isinstance(data, list):
            json.dump([item.model_dump() for item in data], f, indent=4)
        else:
            json.dump(data.model_dump(), f, indent=4)
    logger.info(f"Successfully exported data to {output_path.name}")

def main():
    # 1. Parse CLI Arguments
    parser = argparse.ArgumentParser(description="Run the E-commerce AI Agent Pipeline.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input Excel file (e.g., data/test_data.xlsx)")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.critical(f"Input file not found: {input_path}")
        return

    logger.info("=== STARTING AI AGENT PIPELINE ===")

    # 2. Data Loading & Cleaning
    pipeline = DataPipeline(input_path)
    cleaned_vendor_products, sales_metrics = pipeline.run()

    # 3. Sales Analysis Node (Task 4)
    logger.info("=== RUNNING SALES ANALYSIS ===")
    sales_report = generate_sales_insights(sales_metrics)
    export_json(sales_report, settings.REPORTS_DIR / "sales_analysis_report.json")

    # 4. SKU Processing Graph (Tasks 1, 2, 3)
    logger.info("=== RUNNING VENDOR SKU GRAPH ===")
    graph = build_sku_graph()
    final_outputs = []
    
    # Track quota to prevent massive timeouts or free-tier blocking
    images_generated = 0
    image_limit = settings.IMAGE_GENERATION_LIMIT

    for idx, product in enumerate(cleaned_vendor_products, 1):
        logger.info(f"--- Processing SKU {idx}/{len(cleaned_vendor_products)}: {product.sku} ---")
        
        # Decide if we generate an image based on the quota limit
        skip_image = images_generated >= image_limit
        if not skip_image:
            images_generated += 1
            
        initial_state = {
            "product": product,
            "skip_image": skip_image
        }
        
        # Invoke the LangGraph workflow
        final_state = graph.invoke(initial_state)
        
        # Compile final output
        sku_output = FinalSkuOutput(
            sku=product.sku,
            content=final_state.get("content"),
            competitor_analysis=final_state.get("competitor_analysis"),
            lifestyle_image_path=final_state.get("lifestyle_image_path")
        )
        final_outputs.append(sku_output)

        time.sleep(12)

    # 5. Export Final Vendor Results
    logger.info("=== EXPORTING FINAL RESULTS ===")
    export_json(final_outputs, settings.CONTENT_DIR / "vendor_content_and_competitors.json")
    
    logger.info(f"Pipeline complete! Output files generated in: {settings.OUTPUT_DIR}")

if __name__ == "__main__":
    main()