import pandas as pd
from ddgs import DDGS
import re
import time
from datetime import datetime

# =============================================
# CONFIGURATION
# =============================================
INPUT_FILE = "C:\\Users\\Admin\\Desktop\\RM_Scores_API\\backend\\services\\13_14_15_feb_raw.xlsx"
OUTPUT_FILE = "verified_fundings_13_14_15_feb_2026.xlsx"

# GSTIN Regex (exact 15-character Indian GSTIN format)
GST_PATTERN = re.compile(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b')

def verify_recent_funding(company_name: str, fund_raise_desc: str, ddgs) -> tuple[bool, str, str]:
    """
    Searches DuckDuckGo News for recent (this month) funding news matching the company + amount.
    Returns (is_valid, news_date, reason) 
    """
    query = f'"{company_name}" {fund_raise_desc} funding OR investment OR raise OR IPO OR project OR contract OR award'
    reason = "No recent/relevant news found (potentially old or fake)"
    try:
        results = ddgs.news(
            query=query,
            region="in-en",
            safesearch="moderate",
            timelimit="m",
            max_results=5
        )
        
        if results:
            # Check if the top result is relevant and recent
            first_result = results[0]
            news_date = first_result.get("date", "Unknown")
            
            # Extra check: Ensure the snippet mentions the company (amount check loosened)
            snippet = (first_result.get("title", "") + " " + first_result.get("body", "")).lower()
            if company_name.lower() in snippet:
                return True, news_date, "Valid recent news found"
            else:
                reason = "News found but doesn't match company/details (possible mismatch)"
        else:
            reason = "No news results in past month"
    except Exception as e:
        print(f"   ⚠️  News search error for {company_name}: {e}")
        reason = f"Search error: {str(e)}"
    
    return False, None, reason


def extract_gst_number(company_name: str, ddgs) -> str:
    """
    Improved: Multiple targeted DuckDuckGo searches + better pattern matching
    """
    gst_candidates = set()  # avoid duplicates
    
    queries = [
        f'"{company_name}" GSTIN OR "GST Number" OR GST number site:knowyourgst.com OR site:zaubacorp.com OR site:cleartax.in',
        f'"{company_name}" "GSTIN" "27" OR "29" OR "07" OR "03" OR "06"',
        f'"{company_name}" GSTIN filetype:pdf OR "GST Certificate"',
        f'"{company_name}" GST number India'
    ]
    
    for q in queries:
        try:
            results = ddgs.text(
                query=q,
                region="in-en",
                safesearch="off",
                max_results=10
            )
            
            for result in results:
                text = (result.get("title", "") + " " + 
                        result.get("body", "") + " " + 
                        result.get("href", "")).upper()
                
                matches = GST_PATTERN.findall(text)
                for match in matches:
                    gst_candidates.add(match)
                
                if "GSTIN" in text or "GST NUMBER" in text:
                    parts = text.split()
                    for i, part in enumerate(parts):
                        if "GSTIN" in part.upper() or "GST" in part.upper():
                            if i+1 < len(parts) and GST_PATTERN.match(parts[i+1]):
                                gst_candidates.add(parts[i+1])
        
        except Exception as e:
            print(f"   GST search error ({q}): {e}")
    
    if gst_candidates:
        return sorted(gst_candidates)[0]
    
    return "Not found"


# =============================================
# MAIN PROCESSING
# =============================================
print("🚀 Starting automated verification...")

df = pd.read_excel(INPUT_FILE)
ddgs = DDGS()  # Shared instance - used everywhere

# Prepare list for all rows (including filtered ones)
all_rows = []

for idx, row in df.iterrows():
    company = str(row["company_name"]).strip()
    fund_raise_desc = str(row["fund_raise"]).strip()
    fund_amount = row.get("fund_raise_amount", "")  # Use get() in case column missing
    
    print(f"[{idx+1:2d}/{len(df)}] {company} … ", end="")
    
    # 1. Verify recent funding news (pass shared ddgs)
    is_valid, news_date, reason = verify_recent_funding(company, fund_raise_desc, ddgs)
    
    # 2. Try to fetch GSTIN (pass shared ddgs)
    gst = extract_gst_number(company, ddgs)
    
    # 3. Prepare output row (copy all original columns)
    new_row = row.copy()
    new_row["gst_number"] = gst if pd.isna(new_row.get("gst_number")) else new_row["gst_number"]  # Prefer existing if present
    new_row["news_date"] = news_date if news_date else ""
    new_row["verified"] = "YES" if is_valid else "NO"
    new_row["reason"] = reason
    
    all_rows.append(new_row)
    
    status = "✓" if is_valid else "✗"
    gst_display = gst if gst else "no GST"
    print(f"{status} ({reason}) | GST: {gst_display}")
    
    # Polite delay to avoid rate-limiting
    time.sleep(6)

# =============================================
# SAVE OUTPUT
# =============================================
if all_rows:
    output_df = pd.DataFrame(all_rows)
    # Reorder columns nicely (put new ones at end)
    cols = list(df.columns) + ["news_date", "verified", "reason"]
    output_df = output_df[cols]
    
    output_df.to_excel(OUTPUT_FILE, index=False)
    print(f"\n🎉 DONE! All {len(all_rows)} entries processed and saved to → {OUTPUT_FILE}")
else:
    print("\n⚠️  No data to save.")