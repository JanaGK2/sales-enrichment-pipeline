import pandas as pd
from openai import OpenAI
import time
import concurrent.futures
import threading


# ================= CONFIGURATION =================
api_key = "PERPLEXITY KEY HERE"   # <--- PASTE KEY HERE


# INPUT: Use the OUTPUT from the previous step
input_file = "Research_Results_Fast.csv" 
output_file = "Final_Leads_With_Contacts.csv"


MODEL_NAME = "sonar-pro"
MAX_WORKERS = 5 


# JOB TITLES TO FALL BACK ON
TARGET_ROLES = "Head of AI, Chief Data Officer, Director of Data Science, Digital Transformation Lead"
# =================================================


client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
save_lock = threading.Lock()


print("Loading research results...")
try:
    df = pd.read_csv(input_file)
except FileNotFoundError:
    print(f"Error: Could not find {input_file}. Run research_parallel.py first!")
    exit()


if 'Key_Contacts' not in df.columns:
    df['Key_Contacts'] = ''


# ---------------------------------------------------------
# FILTER LOGIC: ONLY process rows that have valid AI projects
# We skip rows where AI_Projects_Found is empty, "NO_DATA", or "Error"
# ---------------------------------------------------------
def has_projects(text):
    if not isinstance(text, str): return False
    text = text.upper()
    if "NO_DATA" in text or "ERROR" in text or len(text) < 10:
        return False
    return True


# Create a list of "Worthwhile" rows
# We use a boolean mask to filter the original dataframe
mask = df['AI_Projects_Found'].apply(has_projects)
todos_indices = df[mask].index.tolist()


# === TEST MODE: UNCOMMENT LINE BELOW TO TEST ON JUST 10 PEOPLE ===
# todos_indices = todos_indices[:10] 


print(f"Found {len(todos_indices)} companies with AI projects to find contacts for.")


def get_contacts_safe(idx, row):
    company = row['Customer Name']
    project_text = str(row['AI_Projects_Found'])[:300] # Use first 300 chars (Project names usually at top)
    
    prompt = f"""
    Find the key leader for AI initiatives at: "{company}".
    
    CONTEXT: They are working on:
    {project_text}
    
    TASK: 
    1. Identify who is leading these specific projects (Project Manager, Lead, etc).
    2. If specific project leaders are not public, find the "{TARGET_ROLES}".
    
    OUTPUT RULES:
    - Strict Limit: Max 2 people.
    - Format: "[Name] ([Job Title])"
    - If no one found, output "No specific contact found".
    """


    try:
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a helpful sales researcher."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return idx, response.choices[0].message.content
            except Exception as e:
                if "429" in str(e):
                    time.sleep(5 * (attempt + 1))
                    continue
                else:
                    return idx, "Error"
        return idx, "Error (Rate Limit)"
    except:
        return idx, "Error"


# PARALLEL EXECUTION
completed = 0
print("Starting People Search...")


with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit tasks for only the filtered indices
    futures = {executor.submit(get_contacts_safe, idx, df.iloc[idx]): idx for idx in todos_indices}
    
    for future in concurrent.futures.as_completed(futures):
        idx, result = future.result()
        
        # Update DataFrame
        df.at[idx, 'Key_Contacts'] = result
        
        completed += 1
        print(f"[{completed}/{len(todos_indices)}] Found contact for row {idx}")
        
        if completed % 10 == 0:
            with save_lock:
                df.to_csv(output_file, index=False)


# Final Save
df.to_csv(output_file, index=False)
print("Done! Contacts found.")