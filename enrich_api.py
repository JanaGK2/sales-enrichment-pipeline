import pandas as pd
from openai import OpenAI
import time
import os


# ================= CONFIGURATION =================
# PASTE YOUR KEY HERE
api_key = "PERPLEXITY KEY" 


# FILES
input_file = "Enriched_Customers.csv"      # The file from Step 1
output_file = "Final_Enriched_Customers.csv" # The file we are building


# MODEL
MODEL_NAME = "sonar-pro"


# STARTING POINT
# If you want to restart from zero, set this to 0.
# If it crashed at row 50, set this to 50.
START_FROM_ROW = 0 


# =================================================


# 1. THE STRICT INDUSTRY LIST
# This list must be exactly what you want the AI to output.
INDUSTRY_LIST = """
11 - Agriculture
21 - Oil & Gas
21 - Other Mining
22 - Utilities, Waste Management (56) (Incl. public)
23 - Construction
31 - Food, Beverage & Tobacco Manufacturing
31 - Textiles, Apparel, Leather
32 - Wood, Paper, Printing
32 - Petroleum, Chemical, Plastics & Rubber
33 - Materials & General Machinery, Furniture, Other
33 - Electronics, Electrical Equipment, Transport Equipment
42 - Merchant Wholesalers, Durable Goods
42 - Merchant Wholesalers, Nondurable Goods
44 - Motor Vehicle & Parts Dealers
44 - Home & Electronics (Furniture, Electronics, Building Materials)
44 - Food, Beverage, Health & Gas Retail
44 - Apparel, Sporting Goods, Hobby, Book & Music
45 - General Merchandise & Nonstore Retail (incl. e-commerce)
48 - Air, Rail, Water Transport
48 - Trucking & Support Activities for Transportation
49 - Postal Service, Couriers, Warehousing & Storage
51 - Publishing, Media, Entertainment
51 - Telecommunication
51 - Data Processing, Hosting, Other Information Services
52 - Monetary Authorities & Credit Intermediation
52 - Securities, Commodities, Investments
52 - Insurance Carriers & Related Activities
53 - Real Estate & Rental & Leasing
54 - Professional, Scientific & Technical Services
56 - Administrative & Support (excl. public)
61 - Educational Services (incl. public)
62 - Health Care Providers (incl. public)
71 - Arts, Entertainment & Recreation
72 - Accommodation
72 - Food Services
81 - Other Services (except Public Administration)
92 - Government administration & permitting
92 - Defense & national security
92 - Public safety & emergency services
92 - Taxation, benefits, and social programs
92 - Other
"""


# 2. SETUP CLIENT
client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")


# 3. LOAD DATA
print(f"Loading {input_file}...")
df = pd.read_csv(input_file)


# Create columns if missing
if 'Fiscal Year End' not in df.columns:
    df['Fiscal Year End'] = ''
if 'AI_Raw_Response' not in df.columns:
    df['AI_Raw_Response'] = ''


# Filter to find work to do
# We process rows where 'Predicted Industry' is 'Unknown' 
# OR where we previously failed (Industry is empty)
rows_indices = df.index[df['Predicted Industry'] == 'Unknown'].tolist()


print(f"Found {len(rows_indices)} 'Unknown' rows to process.")
print(f"Skipping the first {START_FROM_ROW} rows as requested...")


# 4. THE AI FUNCTION
def get_ai_enrichment(company_name, region):
    system_msg = """
    You are a strict data classification assistant.
    You are provided with a FIXED list of Industries.
    You MUST classify the given company into one of these industries.
    You must output the EXACT industry name from the provided list.
    NO variations. NO new categories.
    """
    
    prompt = f"""
    Analyze this customer:
    Name: {company_name}
    Region: {region}
    
    Step 1: Search the web to identify what this company does.
    Step 2: Search the web for their Fiscal Year End (MM-DD).
    Step 3: Match them to the SINGLE BEST category from the list below.
    
    REQUIRED OUTPUT FORMAT:
    Industry: [Copy the exact string from the list below]
    Fiscal Year End: [MM-DD or "Unknown"]
    
    === VALID INDUSTRY LIST ===
    {INDUSTRY_LIST}
    ===========================
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API Error: {e}")
        return "Error"


# 5. MAIN LOOP
process_counter = 0


for i in rows_indices:
    # SKIP LOGIC
    if process_counter < START_FROM_ROW:
        process_counter += 1
        continue


    # GET DATA
    company = df.at[i, 'Customer Name']
    region = df.at[i, 'Region']
    
    print(f"Processing [{process_counter+1}/{len(rows_indices)}]: {company}...")
    
    # CALL API
    result = get_ai_enrichment(company, region)
    
    # SAVE RAW RESULT
    df.at[i, 'AI_Raw_Response'] = result
    
    # OPTIONAL: Try to stick it in the industry column immediately 
    # This is a simple parser. It looks for "Industry: " and grabs the line.
    try:
        for line in result.split('\n'):
            if "Industry:" in line:
                # Grab everything after "Industry:" and strip whitespace
                clean_industry = line.split("Industry:")[1].strip()
                # Remove any markdown bolding like **Industry Name**
                clean_industry = clean_industry.replace('*', '')
                df.at[i, 'Predicted Industry'] = clean_industry
            
            if "Fiscal Year End:" in line:
                 clean_date = line.split("Fiscal Year End:")[1].strip().replace('*', '')
                 df.at[i, 'Fiscal Year End'] = clean_date
    except:
        pass # If parsing fails, we still have the raw response saved
        
    # INCREMENT
    process_counter += 1
    
    # SAVE BATCH
    if process_counter % 5 == 0:
        df.to_csv(output_file, index=False)
        print(f"   [Saved progress to {output_file}]")
    
    # SLEEP (Be nice to the API)
    time.sleep(1.0)


# FINAL SAVE
df.to_csv(output_file, index=False)
print("Done! All rows processed.")