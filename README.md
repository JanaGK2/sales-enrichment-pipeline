# sales-enrichment-pipeline
AI-powered tool to enrich B2B leads using Perplexity API.
Here is a professional `README.md` ready for you to use. You can simply save this as a file named `README.md` in your project folder (GitHub renders it automatically).

I have structured it to highlight the **business value** and the **technical implementation**, which is exactly what recruiters or peers want to see.

***

# AI-Powered Sales Enrichment Pipeline

An automated Python pipeline that transforms a raw list of customer names into a fully enriched sales intelligence database. It leverages the **Perplexity AI API (`sonar-pro`)** to perform live web research at scale, replacing weeks of manual analyst work with a few hours of automated processing.

## 🚀 Business Value
Sales and Marketing teams often spend 40%+ of their time on manual research. This tool automates the "grunt work" of account research:
*   **Standardization:** Classifies companies into a fixed taxonomy (41 Industries) and finds Fiscal Year Ends.
*   **Deep Research:** Identifies specific, confirmed AI/Data initiatives (e.g., *"Project Cortex: Predictive Maintenance Pilot"*).
*   **Lead Gen:** Finds key decision-makers (Head of AI, CDO) *only* for accounts with active projects, optimizing budget.
*   **Scale:** Processed 3,500+ companies in <3 hours using parallel execution.

## 🛠️ Tech Stack
*   **Python 3.13+**
*   **Pandas:** Data manipulation and merging.
*   **Perplexity API:** Used via `openai` SDK for real-time web search and synthesis.
*   **Concurrent Futures:** Thread-based parallelism to handle 5+ concurrent API requests.
*   **Prompt Engineering:** Dynamic context injection based on industry verticals.

## 📂 Project Structure

| File | Description |
| :--- | :--- |
| `enrich_api.py` | **Step 1:** Classifies "Unknown" industries and finds Fiscal Year End dates. |
| `research_parallel.py` | **Step 2:** The core research engine. Runs multi-threaded web searches to find specific projects. |
| `find_people_parallel.py` | **Step 3:** targeted people search. Filters for companies with valid projects and finds the specific owners. |
| `Industry_UseCase_Mapping.csv`| **Config:** Maps 41 industries to specific "Search Keywords" (e.g., *Oil & Gas* -> *"Seismic Data Analysis"*). |
| `requirements.txt` | List of python dependencies. |

## ⚙️ How It Works

### Phase 1: Classification & Hygiene
The script first ingests a raw CSV. It uses a strict "System Prompt" to force the LLM to classify companies into one of 41 pre-defined NAICS-based industries and find their Fiscal Year End (critical for sales timing).

### Phase 2: Smart Research (Parallelized)
Instead of generic searches, the script loads `Industry_UseCase_Mapping.csv`.
*   *If Company is "Bank" -> Search for "Fraud Detection", "Algorithmic Trading".*
*   *If Company is "Retail" -> Search for "Personalization", "Inventory Forecasting".*
    
It uses `ThreadPoolExecutor` to run 5 concurrent workers, drastically reducing runtime while handling Rate Limits (HTTP 429) with automatic backoff/retries.

### Phase 3: Sniper Targeting
To save costs, the final script only runs on companies where **Step 2 found valid data**. It searches specifically for the leaders of the *identified projects* (e.g., *"Who runs the 'LUMI Supercomputer' project at Sigma2?"*) rather than generic "CIO" searches.

## 🔧 Setup & Usage

1.  **Clone the repo**
    ```bash
    git clone https://github.com/yourusername/sales-enrichment-pipeline.git
    cd sales-enrichment-pipeline
    ```

2.  **Install Dependencies**
    ```bash
    pip install pandas openai
    ```

3.  **Set API Key**
    Open the scripts and replace `YOUR_PPLX_KEY_HERE` with your Perplexity API key.
    *(Recommended: Use `os.getenv('PERPLEXITY_API_KEY')` for production)*.

4.  **Run the Pipeline**
    ```bash
    # Step 1: Industry & Fiscal Year
    python enrich_api.py
    
    # Step 2: Deep Project Research
    python research_parallel.py
    
    # Step 3: Find Contacts
    python find_people_parallel.py
    ```

## ⚠️ Note on Cost & Rate Limits
*   This tool uses paid API tokens.
*   Estimated cost: ~$0.04 per company for full deep research.
*   The script includes `time.sleep()` and retry logic to respect API rate limits, but you can adjust `MAX_WORKERS` in the config section.

## 📜 License
MIT License. Feel free to use and modify for your own sales ops workflows.
