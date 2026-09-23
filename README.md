# E-commerce AI Agent Pipeline

## Overview

This repository implements an automated, production-grade agentic pipeline designed to process unstructured e-commerce vendor catalogs and historical sales transactions. The system cleans ragged multi-column vendor attributes, synthesizes marketplace-ready product listings, generates contextual lifestyle imagery, performs competitive price benchmarking, and produces executive sales analytics.

- **Track Chosen:** Track A (Code-based Agent)
- **Framework & Architecture:** LangGraph (StateGraph DAG workflow) + LiteLLM Gateway
- **Language / Runtime:** Python 3.11+

---

## Architecture & Framework

The pipeline is organized in a modular `src/` layout orchestrated via a single CLI entry point (`main.py`):

1. **State Machine Orchestration (`langgraph`)**
   Each vendor product is processed through an isolated, stateful Directed Acyclic Graph (DAG) consisting of sequential execution nodes:
   - `Content Generation Node`: Synthesizes raw vendor bullets into SEO-optimized titles, descriptions, exactly 5 key feature bullets, and typed attribute lists.
   - `Lifestyle Image Generation Node`: Transforms product metadata and source catalog image URLs into contextual interior lifestyle photography via Pollinations.ai.
   - `Competitor Analysis Node`: Queries live web pricing via `ddgs` to benchmark marketplace pricing against derived reference metrics.

2. **Resilience & Unified LLM Gateway (`litellm` + `tenacity`)**
   Model calls are routed through LiteLLM using Groq (`openai/gpt-oss-20b`), wrapped with exponential backoff and jitter across network timeouts and rate limits.

3. **Strict Data Contracts (`pydantic` v2)**
   All node outputs are validated against strict JSON schemas utilizing explicit list-based key-value models (`AttributeItem`) to adhere to provider-level structured decoding constraints.

4. **Standalone Sales Analyst (`src/agents/sales_analyst.py`)**
   Aggregates high-volume sales transactions using Pandas vectorized operations before issuing an executive summarization prompt to extract catalog health, velocity, and inventory recommendations.

---

## Bottlenecks & Engineering Solutions

Building an agentic workflow against free-tier infrastructure presents concrete production constraints. Below are the core bottlenecks encountered during development and the engineering solutions implemented to resolve them.

### 1. Free-Tier Rate Limits (8,000 Tokens Per Minute Ceiling)

- **The Bottleneck:** On-demand developer tiers enforce a strict 8,000 Tokens-Per-Minute (TPM) ceiling. Concatenating up to 20 ragged vendor bullet points created prompt payloads exceeding 1,200 characters per SKU. Processing SKUs sequentially exhausted the token bucket within 1–2 cycles, causing `RateLimitError (TPM limit exceeded)` exceptions and hanging retry loops.

- **The Solution (Front-Loaded Truncation & Pacing):**
  - **Information Density Optimization:** In retail catalog management, primary value propositions (materials, core mechanics, structural dimensions) are concentrated in the first 3 to 6 bullet points. Truncating the concatenated vendor copy to 600 characters provided the LLM with the exact facts needed while stripping low-signal filler.
  - **Hallucination Prevention:** Removing trailing filler prevented the LLM from becoming overwhelmed by redundant phrases, yielding higher-quality feature bullets.
  - **Pacing & Exponential Backoff:** Combined the 600-character payload reduction with a 3-second inter-SKU cooldown and a 6-attempt exponential backoff in `tenacity` (ranging from 3s to 20s), allowing token buckets to replenish without crashing the pipeline.

### 2. Strict JSON Schema Validation (`additionalProperties: false`)

- **The Bottleneck:** Defining product attributes as open key-value maps (`attributes: Dict[str, str]`) caused provider-level validation failures: `invalid JSON schema for response_format: additionalProperties:false must be set on every object`. Groq's constrained JSON decoding engine strictly rejects open-ended dictionary objects without predefined keys.

- **The Solution:** Refactored the schema into an explicit list of strongly typed models (`List[AttributeItem]`, where each item contains explicit `name` and `value` fields). This complies with strict schema validators while preserving flexible attribute extraction across varied furniture types.

### 3. LLM Generation Truncation & Schema Fail-Safes

- **The Bottleneck:** During high-context sales analysis, the LLM occasionally terminated generation before emitting the final `recommendations` array, causing strict Pydantic validation to reject the entire report despite valid executive summaries and insights.

- **The Solution:** Implemented schema fail-safes using Pydantic's `default_factory=list` on the `recommendations` field, complemented by defensive fallback objects within agent nodes. If a provider drops a field, the system captures all successfully generated insights rather than failing the execution cycle.

### 4. Search Scraper Rate Limiting & Anti-Bot Blocking

- **The Bottleneck:** Rapid sequential scraping across 25 SKUs via standard search endpoints triggered anti-bot rate limits, causing empty search payloads (`No search results found`).

- **The Solution:** Migrated from legacy scraper bindings to the updated `ddgs` client, introduced a mandatory 3-second delay prior to each query, and implemented an algorithmic fallback (derived benchmark price + 10% market variance) to guarantee complete competitive reports even under full network blocks.

---

## Assumptions & Data Treatment

1. **Vendor & Sales SKU Disconnect (Reference Price Derivation):**
   - The 25 vendor catalog SKUs do not have matching transaction records in the historical sales sheet.
   - To establish an objective benchmark for competitive intelligence, the pipeline computes a global average realized sales price across all non-cancelled historical sales ($229.91) and binds it as each vendor product's reference baseline (`our_price`).

2. **Sales Order Status Filtering:**
   - Orders marked `orderStatus == 'Cancelled'` are filtered out entirely to avoid inflating realized transaction volume or revenue figures.
   - Orders marked `orderStatus == 'Pending'` are preserved as active pipeline demand.

3. **Ragged Bullet Point Normalization:**
   - Raw vendor bullet points distributed across ragged columns (`Bullet 1` through `Bullet 20`) are dynamically extracted, stripped of empty values/NaNs, and concatenated into a unified string.

4. **Dimension and Weight Formatting:**
   - Missing, non-numeric, or null dimension fields (`Length1`, `Width1`, `Height1`, `Weight1`) default to `0.0` and are normalized into standard imperial strings (`{weight} lbs, {length}L x {width}W x {height}H`).

5. **Image Generation Quota Management:**
   - To prevent IP throttling, connection drops, and prolonged runtimes on free image generation endpoints, an environment-controlled threshold (`IMAGE_GENERATION_LIMIT=3`) is enforced. The pipeline processes all 25 vendor records, generates visual assets for the initial batch, and sets remaining image paths to `null` while preserving full text and competitive analysis.

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- Virtual environment tool (`venv`)
- A free Groq API key from [GroqCloud](https://console.groq.com/)

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone <repository-url>
cd ecommerce_listing_agent

# Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Populate `.env` with your API credentials:

```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
IMAGE_GENERATION_LIMIT=3
LOG_LEVEL=INFO
ENVIRONMENT=development 
MAX_RETRIES=3 
REQUEST_TIMEOUT_SECONDS=30
```

### 4. Place Input Data

Place the source workbook at `data/test_data.xlsx` (must contain vendor catalog data on sheet 1 and sales transactions on sheet 2).

---

## Running the Pipeline

Execute the end-to-end pipeline with the single entry point command:

```bash
python main.py --input data/test_data.xlsx
```

### Execution Lifecycle

1. **Data Load & Cleaning:** Extracts and cleans the vendor catalog and sales transaction sheets using Pandas with automatic resource stream closure.

2. **Sales Intelligence (Task 4):** Calculates revenue and unit volume aggregations, identifies top and bottom performers, and writes executive business insights to `output/reports/sales_analysis_report.json`.

3. **SKU Graph Execution (Tasks 1, 2, 3):** Compiles and invokes the LangGraph state machine sequentially for each SKU:
   - Formulates title, copy, features, and specs.
   - Generates lifestyle imagery for the initial quota batch.
   - Queries competitor pricing and calculates market variance.

4. **Final Export:** Serializes the consolidated SKU deliverables to `output/content/vendor_content_and_competitors.json`.

---

## Output Deliverables

All generated assets are exported to the `/output` folder:

| Deliverable | Path |
|---|---|
| Product Content & Competitor Benchmarks | `output/content/vendor_content_and_competitors.json` |
| Sales Intelligence Report | `output/reports/sales_analysis_report.json` |
| Generated Lifestyle Images | `output/images/{SKU}_lifestyle.png` |
| System Execution Logs | `pipeline.log` |