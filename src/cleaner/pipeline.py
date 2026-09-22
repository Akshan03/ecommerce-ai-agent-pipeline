"""
Data cleaning and validation pipeline.
Reads raw Excel data, processes it via Pandas, and returns strictly typed Pydantic models.
"""
import pandas as pd
from typing import List, Tuple
from pathlib import Path

from config.settings import settings
from src.utils.logger import setup_logger
from src.models.vendor import CleanedVendorProduct
from src.models.sales import SalesMetrics, SkuPerformance

logger = setup_logger(__name__)

class DataPipeline:
    """Handles data extraction, cleaning, and Pydantic model instantiation."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.vendor_df = pd.DataFrame()
        self.sales_df = pd.DataFrame()

    def load_data(self) -> None:
        """Loads the Excel workbook and separates the sheets."""
        try:
            logger.info(f"Loading data from {self.file_path}...")
            
            with pd.ExcelFile(self.file_path) as xls:
                if len(xls.sheet_names) < 2:
                    raise ValueError("Expected at least two sheets (vendor and sales).")
                    
                self.vendor_df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
                self.sales_df = pd.read_excel(xls, sheet_name=xls.sheet_names[1])
            
            logger.info(f"Successfully loaded {len(self.vendor_df)} vendor rows and {len(self.sales_df)} sales rows.")
        except Exception as e:
            logger.error(f"Failed to load Excel file: {e}")
            raise

    def process_sales(self) -> Tuple[SalesMetrics, float]:
        """
        Cleans sales data, computes aggregated metrics, and calculates the global reference price.
        Cancelled orders are excluded.
        """
        logger.info("Processing sales data...")
        # 1. Filter out cancelled orders (but keep 'Pending' as pipeline revenue)
        valid_sales = self.sales_df[self.sales_df['orderStatus'].str.lower() != 'cancelled'].copy()
        
        # 2. Calculate global metrics
        total_revenue = float(valid_sales['amount'].sum())
        total_units = int(valid_sales['quantity'].sum())
        global_avg_price = float(valid_sales['price'].mean())
        
        # 3. Aggregate by SKU (itemName)
        sku_group = valid_sales.groupby('itemName').agg(
            total_revenue=('amount', 'sum'),
            units_sold=('quantity', 'sum')
        ).reset_index()
        
        # 4. Identify Top and Low moving SKUs
        top_skus_df = sku_group.sort_values(by='total_revenue', ascending=False).head(5)
        low_skus_df = sku_group.sort_values(by='units_sold', ascending=True).head(5)
        
        top_skus = [
            SkuPerformance(item_name=row['itemName'], total_revenue=row['total_revenue'], units_sold=row['units_sold'])
            for _, row in top_skus_df.iterrows()
        ]
        
        low_skus = [
            SkuPerformance(item_name=row['itemName'], total_revenue=row['total_revenue'], units_sold=row['units_sold'])
            for _, row in low_skus_df.iterrows()
        ]
        
        metrics = SalesMetrics(
            total_sales_revenue=total_revenue,
            total_units_sold=total_units,
            top_performing_skus=top_skus,
            low_moving_skus=low_skus
        )
        
        logger.info(f"Sales metrics computed. Global average price: ${global_avg_price:.2f}")
        return metrics, global_avg_price

    def process_vendor(self, global_avg_price: float) -> List[CleanedVendorProduct]:
        """
        Cleans vendor data, consolidates ragged columns, applies default dimension handling,
        and enforces the Pydantic schema.
        """
        logger.info("Processing vendor data...")
        cleaned_products = []
        
        # Identify bullet columns dynamically (Bullet 1 to Bullet 20)
        bullet_cols = [f'Bullet {i}' for i in range(1, 21) if f'Bullet {i}' in self.vendor_df.columns]
        
        for _, row in self.vendor_df.iterrows():
            try:
                # Concatenate bullets, ignoring NaNs
                bullets = [str(row[col]).strip() for col in bullet_cols if pd.notna(row[col]) and str(row[col]).strip() != ""]
                raw_copy = " | ".join(bullets)
                
                # Format dimensions gracefully handling NaNs
                w = float(row.get('Weight1', 0)) if pd.notna(row.get('Weight1')) else 0.0
                l = float(row.get('Length1', 0)) if pd.notna(row.get('Length1')) else 0.0
                width = float(row.get('Width1', 0)) if pd.notna(row.get('Width1')) else 0.0
                h = float(row.get('Height1', 0)) if pd.notna(row.get('Height1')) else 0.0
                
                dim_text = f"{w} lbs, {l}L x {width}W x {h}H"
                
                # Create and validate the Pydantic model
                product = CleanedVendorProduct(
                    sku=str(row['SKU']),
                    masked_sku=str(row['Masked SKU']),
                    brand=str(row.get('Brand', 'Unknown')),
                    category=str(row.get('Category', 'Furniture')),
                    color=str(row.get('Color', 'Not Specified')),
                    material=str(row.get('Material Used', 'Not Specified')),
                    assembly_required=str(row.get('Assembly Required', 'Unknown')),
                    raw_copy=raw_copy,
                    image_url=str(row['Image URL 1']),
                    dimensions_text=dim_text,
                    reference_price=global_avg_price
                )
                cleaned_products.append(product)
            except Exception as e:
                logger.error(f"Error processing vendor SKU {row.get('SKU', 'Unknown')}: {e}")
                continue
                
        logger.info(f"Successfully processed {len(cleaned_products)} vendor products.")
        return cleaned_products

    def run(self) -> Tuple[List[CleanedVendorProduct], SalesMetrics]:
        """Executes the full extraction and cleaning pipeline."""
        self.load_data()
        sales_metrics, global_avg_price = self.process_sales()
        cleaned_vendor_products = self.process_vendor(global_avg_price)
        return cleaned_vendor_products, sales_metrics