import pandas as pd
from openai import OpenAI
import time
import concurrent.futures
import threading


# ================= CONFIGURATION =================
api_key = "PERPLEXITY KEY HERE   # <--- PASTE KEY HERE


input_customer_file = "Final_Enriched_Customers.csv"
input_mapping_file = "Industry_UseCase_Mapping.csv"
output_file = "Research_Results_Fast.csv"


MODEL_NAME = "sonar-pro"
MAX_WORKERS = 5  # Runs 5 searches at the same time. Safe for Pro accounts.
# =================================================


client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
save_lock = threading.Lock() # Prevents two threads from writing to file at same time


# LOAD DATA
print("Loading files...")
df_customers = pd.read_csv(input_customer_file)
df_mapping = pd.read_csv(input_mapping_file)


# MAP KEYWORDS
df_mapping['Industry Name'] = df_mapping['Industry Name'].str.strip()
industry_map = pd.Series(df_mapping.Search_Keywords.values, index=df_mapping['Industry Name']).to_dict()


if 'AI_Projects_Found' not in df_customers.columns:
    df_customers['AI_Projects_Found'] = ''


# Identify rows to do
# (Optional: Filter for empty rows only if restarting)
# todos = df_customers[df_customers['AI_Projects_Found'].isna() | (df_customers['AI_Projects_Found'] == '')]
todos = df_customers  # Run ALL rows


print(f"Starting Parallel Research on {len(todos)} rows with {MAX_WORKERS} threads...")


def get_ai_research_safe(row_tuple):
    index, row = row_tuple
    company = row['Customer Name']
    industry = str(row['Predicted Industry']).strip()
    keywords = industry_map.get(industry, "AI, GenAI, Machine Learning, Data Optimization")
    
    prompt = f"""
    Perform deep market research on the company: "{company}" (Industry: {industry}).
    OBJECTIVE: Identify specific AI, GenAI, or Data Science projects.
    SEARCH HINTS: Look for: {keywords}. Also "GenAI pilots", "Process Automation".
    SOURCES: Annual Reports (2023-2025), Tech Blogs, Press Releases.
    OUTPUT RULES:
    1. Max 3 bullet points total.
    2. Max 20 words per bullet point.
    3. Format: "- [Project Name]: [Brief Description] (Status)"
    4. If NO projects found, output "NO_DATA".
    """


    try:
        # Retry logic for rate limits
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a concise researcher."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return index, response.choices[0].message.content
            except Exception as e:
                if "429" in str(e): # Rate limit error
                    time.sleep(5 * (attempt + 1)) # Wait 5s, then 10s...
                    continue
                else:
                    return index, "Error"
        return index, "Error (Rate Limit)"
    except:
        return index, "Error"


# PARALLEL EXECUTION
completed = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit all tasks
    # We turn the dataframe rows into a list of tuples (index, row)
    futures = {executor.submit(get_ai_research_safe, (idx, row)): idx for idx, row in todos.iterrows()}
    
    for future in concurrent.futures.as_completed(futures):
        idx, result = future.result()
        
        # Save result to dataframe
        df_customers.at[idx, 'AI_Projects_Found'] = result
        
        completed += 1
        print(f"[{completed}/{len(todos)}] Finished row {idx}")
        
        # Periodic Save (Thread safe)
        if completed % 10 == 0:
            with save_lock:
                df_customers.to_csv(output_file, index=False)


# Final Save
df_customers.to_csv(output_file, index=False)
print("Done! Fast research complete.")