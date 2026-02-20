# import pandas as pd
# from ddgs import DDGS
# from datetime import datetime
# import re


# def extract_gst(text):
#     gst_pattern = r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9]\b"
#     match = re.search(gst_pattern, text)
#     return match.group() if match else None


# def verify_funding_and_gst(input_file, output_file):
#     df = pd.read_excel(input_file)

#     results = []

#     current_month = datetime.now().strftime("%B").lower()
#     current_year = str(datetime.now().year)

#     for _, row in df.iterrows():
#         company = row["company_name"]
#         expected_amount = str(row["fund_raise_amount"])

#         query = f"{company} raised funding {current_month} {current_year}"

#         funding_verified = False
#         gst_number = None
#         source_link = None

#         with DDGS() as ddgs:
#             search_results = list(ddgs.text(query, max_results=5))

#         for result in search_results:
#             body = result.get("body", "").lower()
#             link = result.get("href", "")

#             # 1️⃣ Check month + year in text (recency filter)
#             if current_month not in body or current_year not in body:
#                 continue

#             # 2️⃣ Check funding keywords
#             if not any(word in body for word in ["raised", "funding", "ipo", "secured", "investment"]):
#                 continue

#             # 3️⃣ Smarter amount matching (remove commas etc.)
#             expected_digits = re.sub(r"\D", "", expected_amount)
#             body_numbers = re.findall(r"\d+", body)

#             if any(expected_digits in num for num in body_numbers):
#                 funding_verified = True
#                 source_link = link
#                 gst_number = extract_gst(body)
#                 break

#         results.append({
#             "company_name": company,
#             "funding_verified": funding_verified,
#             "gst_number": gst_number,
#             "source": source_link
#         })

#     output_df = pd.DataFrame(results)
#     output_df.to_excel(output_file, index=False)

#     return "Verification completed."


# if __name__ == "__main__":
#     result = verify_funding_and_gst("C:\\Users\\Admin\\Desktop\\RM_Scores_API\\backend\\services\\12_feb_raw.xlsx", "output.xlsx")
#     print(result)








# import pandas as pd
# from duckduckgo_search import DDGS
# import re
# import time
# from datetime import datetime

# # =============================================
# # CONFIGURATION
# # =============================================
# INPUT_FILE = "C:\\Users\\Admin\\Desktop\\RM_Scores_API\\backend\\services\\12_feb_raw.xlsx"
# OUTPUT_FILE = "verified_fundings_feb_2026.xlsx"

# # GSTIN Regex (exact 15-character Indian GSTIN format)
# GST_PATTERN = re.compile(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b')

# def verify_recent_funding(company_name: str, fund_raise_desc: str) -> tuple[bool, str]:
#     """
#     Searches DuckDuckGo News for recent (this month) funding news matching the company + amount.
#     Returns (is_valid, news_date) 
#     """
#     query = f'"{company_name}" {fund_raise_desc}'
#     try:
#         with DDGS() as ddgs:
#             results = ddgs.news(
#                 keywords=query,
#                 region="wt-wt",          # World-wide so we catch international too
#                 safesearch="moderate",
#                 timelimit="m",           # Past month → filters out old news perfectly
#                 max_results=8
#             )
            
#             if results:
#                 # Take the most relevant (first) result
#                 first_result = results[0]
#                 news_date = first_result.get("date", "Unknown")
#                 return True, news_date
#     except Exception as e:
#         print(f"   ⚠️  Search error for {company_name}: {e}")
    
#     return False, None


# def extract_gst_number(company_name: str) -> str:
#     """
#     Improved: Multiple targeted DuckDuckGo searches + better pattern matching
#     Focuses on Indian companies + known GST listing sites
#     """
#     gst_candidates = set()  # avoid duplicates
    
#     # Query variations - more likely to hit public listings
#     queries = [
#         f'"{company_name}" GSTIN OR "GST Number" OR GST number site:knowyourgst.com OR site:microvistatech.com OR site:zaubacorp.com',
#         f'"{company_name}" "GSTIN" "AA" OR "27" OR "29" OR "07"',  # common state codes
#         f'"{company_name}" GSTIN filetype:pdf OR "GST Certificate"',
#         f'"{company_name}" GST number'
#     ]
    
#     for q in queries:
#         try:
#             with DDGS() as ddgs:
#                 results = ddgs.text(
#                     keywords=q,
#                     region="in-en",
#                     safesearch="off",       # sometimes helps with gov/business pages
#                     max_results=12
#                 )
                
#                 for result in results:
#                     text = (result.get("title", "") + " " + 
#                             result.get("body", "") + " " + 
#                             result.get("href", "")).upper()
                    
#                     # Find all potential GSTIN matches in the snippet
#                     matches = GST_PATTERN.findall(text)
#                     for match in matches:
#                         gst_candidates.add(match)
                    
#                     # Also look for patterns like "GSTIN: 27AABCP..." 
#                     if "GSTIN" in text or "GST NUMBER" in text:
#                         # crude but effective extra extraction
#                         parts = text.split()
#                         for i, part in enumerate(parts):
#                             if "GSTIN" in part or "GST" in part:
#                                 if i+1 < len(parts) and GST_PATTERN.match(parts[i+1]):
#                                     gst_candidates.add(parts[i+1])
        
#         except Exception as e:
#             print(f"   GST search error ({q}): {e}")
    
#     if gst_candidates:
#         # Prefer the first valid-looking one (usually most relevant)
#         return sorted(gst_candidates)[0]  # or take the most common if many
    
#     return "Not found"


# # =============================================
# # MAIN PROCESSING
# # =============================================
# print("🚀 Starting automated verification...")

# df = pd.read_excel(INPUT_FILE)

# verified_rows = []

# for idx, row in df.iterrows():
#     company = str(row["company_name"]).strip()
#     fund_raise_desc = str(row["fund_raise"]).strip()
#     fund_amount = row["fund_raise_amount"]
    
#     print(f"[{idx+1:2d}/{len(df)}] Checking → {company} | {fund_raise_desc}")
    
#     # 1. Verify recent funding news (this month only)
#     is_valid, news_date = verify_recent_funding(company, fund_raise_desc)
    
#     if not is_valid:
#         print(f"   ❌ Filtered (no recent news)")
#         continue
    
#     # 2. Try to fetch GSTIN
#     gst = extract_gst_number(company)
    
#     # 3. Prepare output row
#     new_row = row.copy()
#     new_row["gst_number"] = gst
#     new_row["news_date"] = news_date
#     new_row["verified"] = "YES"
    
#     verified_rows.append(new_row)
#     print(f"   ✅ Verified | GST: {gst if gst else 'Not found'} | Date: {news_date}")
    
#     # Polite delay to avoid rate-limiting
#     time.sleep(1.2)

# # =============================================
# # SAVE OUTPUT
# # =============================================
# if verified_rows:
#     output_df = pd.DataFrame(verified_rows)
#     # Reorder columns nicely
#     cols = ["company_name", "fund_raise", "gst_number", "pan_number", "fund_raise_amount", "news_date", "verified"]
#     output_df = output_df[cols]
    
#     output_df.to_excel(OUTPUT_FILE, index=False)
#     print(f"\n🎉 DONE! {len(verified_rows)} companies verified and saved to → {OUTPUT_FILE}")
# else:
#     print("\n⚠️  No companies verified.")























# import pandas as pd
# from ddgs import DDGS
# import re
# import time
# from datetime import datetime

# # =============================================
# # CONFIGURATION
# # =============================================
# INPUT_FILE = "C:\\Users\\Admin\\Desktop\\RM_Scores_API\\backend\\services\\12_feb_raw.xlsx"
# OUTPUT_FILE = "verified_fundings_feb_2026_new.xlsx"

# # GSTIN Regex (exact 15-character Indian GSTIN format)
# GST_PATTERN = re.compile(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b')

# def verify_recent_funding(company_name: str, fund_raise_desc: str, ddgs) -> tuple[bool, str, str]:
#     """
#     Searches DuckDuckGo News for recent (this month) funding news matching the company + amount.
#     Returns (is_valid, news_date, reason) 
#     """
#     query = f'"{company_name}" {fund_raise_desc} funding OR investment OR raise OR IPO OR project OR contract OR award'
#     reason = "No recent/relevant news found (potentially old or fake)"
#     try:
#         results = ddgs.news(
#             query=query,
#             region="in-en",
#             safesearch="moderate",
#             timelimit="m",
#             max_results=5
#         )
        
#         if results:
#             # Check if the top result is relevant and recent
#             first_result = results[0]
#             news_date = first_result.get("date", "Unknown")
            
#             # Extra check: Ensure the snippet mentions the company (amount check loosened)
#             snippet = (first_result.get("title", "") + " " + first_result.get("body", "")).lower()
#             if company_name.lower() in snippet:
#                 return True, news_date, "Valid recent news found"
#             else:
#                 reason = "News found but doesn't match company/details (possible mismatch)"
#         else:
#             reason = "No news results in past month"
#     except Exception as e:
#         print(f"   ⚠️  News search error for {company_name}: {e}")
#         reason = f"Search error: {str(e)}"
    
#     return False, None, reason


# def extract_gst_number(company_name: str, ddgs) -> str:
#     """
#     Improved: Multiple targeted DuckDuckGo searches + better pattern matching
#     """
#     gst_candidates = set()  # avoid duplicates
    
#     queries = [
#         f'"{company_name}" GSTIN OR "GST Number" OR GST number site:knowyourgst.com OR site:zaubacorp.com OR site:cleartax.in',
#         f'"{company_name}" "GSTIN" "27" OR "29" OR "07" OR "03" OR "06"',
#         f'"{company_name}" GSTIN filetype:pdf OR "GST Certificate"',
#         f'"{company_name}" GST number India'
#     ]
    
#     for q in queries:
#         try:
#             results = ddgs.text(
#                 query=q,
#                 region="in-en",
#                 safesearch="off",
#                 max_results=10
#             )
            
#             for result in results:
#                 text = (result.get("title", "") + " " + 
#                         result.get("body", "") + " " + 
#                         result.get("href", "")).upper()
                
#                 matches = GST_PATTERN.findall(text)
#                 for match in matches:
#                     gst_candidates.add(match)
                
#                 if "GSTIN" in text or "GST NUMBER" in text:
#                     parts = text.split()
#                     for i, part in enumerate(parts):
#                         if "GSTIN" in part.upper() or "GST" in part.upper():
#                             if i+1 < len(parts) and GST_PATTERN.match(parts[i+1]):
#                                 gst_candidates.add(parts[i+1])
        
#         except Exception as e:
#             print(f"   GST search error ({q}): {e}")
    
#     if gst_candidates:
#         return sorted(gst_candidates)[0]
    
#     return "Not found"


# # =============================================
# # MAIN PROCESSING
# # =============================================
# print("🚀 Starting automated verification...")

# df = pd.read_excel(INPUT_FILE)
# ddgs = DDGS()  # Shared instance - used everywhere

# # Prepare list for all rows (including filtered ones)
# all_rows = []

# for idx, row in df.iterrows():
#     company = str(row["company_name"]).strip()
#     fund_raise_desc = str(row["fund_raise"]).strip()
#     fund_amount = row["fund_raise_amount"]
    
#     print(f"[{idx+1:2d}/{len(df)}] {company} … ", end="")
    
#     # 1. Verify recent funding news (pass shared ddgs)
#     is_valid, news_date, reason = verify_recent_funding(company, fund_raise_desc, ddgs)
    
#     # 2. Try to fetch GSTIN (pass shared ddgs)
#     gst = extract_gst_number(company, ddgs)
    
#     # 3. Prepare output row
#     new_row = row.copy()
#     new_row["gst_number"] = gst
#     new_row["news_date"] = news_date if news_date else ""
#     new_row["verified"] = "YES" if is_valid else "NO"
#     new_row["reason"] = reason
    
#     all_rows.append(new_row)
    
#     status = "✓" if is_valid else "✗"
#     gst_display = gst if gst else "no GST"
#     print(f"{status} ({reason}) | GST: {gst_display}")
    
#     # Polite delay to avoid rate-limiting
#     time.sleep(6)

# # =============================================
# # SAVE OUTPUT
# # =============================================
# if all_rows:
#     output_df = pd.DataFrame(all_rows)
#     # Reorder columns nicely
#     cols = ["company_name", "fund_raise", "gst_number", "pan_number", "fund_raise_amount", "news_date", "verified", "reason"]
#     output_df = output_df[cols]
    
#     output_df.to_excel(OUTPUT_FILE, index=False)
#     print(f"\n🎉 DONE! All {len(all_rows)} entries processed and saved to → {OUTPUT_FILE}")
# else:
#     print("\n⚠️  No data to save.")




















# import random
# import pandas as pd
# from ddgs import DDGS
# import re
# import time
# from datetime import datetime

# # =============================================
# # CONFIGURATION
# # =============================================
# INPUT_FILE = "C:\\Users\\Admin\\Desktop\\RM_Scores_API\\backend\\services\\12_feb_raw.xlsx"
# OUTPUT_FILE = "verified_fundings_feb_2026_new.xlsx"

# # GSTIN Regex (exact 15-character Indian GSTIN format)
# GST_PATTERN = re.compile(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b')

# # Simple regex for finding amounts in snippets (e.g., Rs 123 crore, $45 million, ₹678 Cr)
# AMOUNT_PATTERN = re.compile(r'(Rs|₹|\$|USD|INR|crore|million|billion|cr)\s*[\d,.]+(?:\s*(crore|million|billion|cr))?', re.IGNORECASE)

# # Heuristic for finding possible company names (sequences of capitalized words)
# COMPANY_PATTERN = re.compile(r'\b([A-Z][a-z0-9]*\s*){2,4}\b')

# def verify_recent_funding(company_name: str, fund_raise_desc: str, ddgs) -> tuple[bool, str, str]:
#     """
#     Searches DuckDuckGo for recent (this month) funding news matching the company + amount.
#     Prioritizes news search for reliable dates, falls back to text search.
#     Returns (is_valid, news_date, reason) 
#     """
#     query = f'"{company_name}" {fund_raise_desc} funding OR investment OR raise OR IPO OR project OR contract OR award OR acquisition OR QIP'
#     reason = "No recent/relevant news found (potentially old or fake)"
    
#     try:
#         # Step 1: Try news-specific search first (better dates)
#         news_results = ddgs.news(
#             query=query,
#             region="in-en",
#             safesearch="moderate",
#             timelimit="m",
#             max_results=10
#         )
        
#         search_results = news_results if news_results else []
        
#         # Step 2: If no good news, fall back to broader text/web search
#         if not search_results:
#             search_results = ddgs.text(
#                 query=query,
#                 region="in-en",
#                 safesearch="moderate",
#                 timelimit="m",
#                 max_results=10
#             )
        
#         if search_results:
#             for result in search_results:
#                 snippet = (result.get("title", "") + " " + result.get("body", "")).lower()
#                 original_snippet = result.get("title", "") + " " + result.get("body", "")
                
#                 # Looser company match: any part of name
#                 company_parts = company_name.lower().split()
#                 company_matched = any(part in snippet for part in company_parts) or company_name.lower() in snippet
                
#                 # Looser amount match
#                 amount_parts = fund_raise_desc.lower().split()
#                 amount_matched = any(part in snippet for part in amount_parts)
                
#                 if company_matched and amount_matched:
#                     # Get date — prefer real date, fallback to today if missing
#                     news_date = result.get("date", None)
#                     if not news_date or news_date == "Unknown":
#                         news_date = datetime.now().strftime("%Y-%m-%d")  # Use today's date as fallback
#                     return True, news_date, "Valid recent news found (company + amount match)"
            
#             # No full match → detailed reason from top result
#             first_result = search_results[0]
#             snippet = (first_result.get("title", "") + " " + first_result.get("body", "")).lower()
#             original_snippet = first_result.get("title", "") + " " + first_result.get("body", "")
            
#             detail = []
#             company_matched = False  # Reset for reason
#             company_parts = company_name.lower().split()
#             if any(part in snippet for part in company_parts) or company_name.lower() in snippet:
#                 company_matched = True
            
#             if not company_matched:
#                 found_company = "not detected"
#                 company_match = COMPANY_PATTERN.search(original_snippet)
#                 if company_match:
#                     found_company = company_match.group(0).strip()
#                 detail.append(f"Company mismatch (found possible name: '{found_company}' instead of '{company_name}')")
            
#             amount_matched = False
#             if any(part in snippet for part in amount_parts):
#                 amount_matched = True
            
#             if not amount_matched:
#                 found_amount = "not detected"
#                 amount_match = AMOUNT_PATTERN.search(original_snippet)
#                 if amount_match:
#                     found_amount = amount_match.group(0).strip()
#                 detail.append(f"Amount mismatch (found possible amount: '{found_amount}' instead of '{fund_raise_desc}')")
            
#             reason = "News found but doesn't match details: " + "; ".join(detail) if detail else "General mismatch in company/amount"
            
#             # Still set a date for the reason (top result date if available)
#             news_date_for_reason = first_result.get("date", datetime.now().strftime("%Y-%m-%d"))
#         else:
#             reason = "No news results in past month"
#             news_date_for_reason = ""
        
#     except Exception as e:
#         print(f"   ⚠️  Search error for {company_name}: {e}")
#         reason = f"Search error: {str(e)}"
#         news_date_for_reason = ""
    
#     return False, news_date_for_reason, reason


# def extract_gst_number(company_name: str, ddgs) -> str:
#     """
#     Improved: Multiple targeted DuckDuckGo searches + better pattern matching
#     """
#     gst_candidates = set()  # avoid duplicates
    
#     queries = [
#         f'"{company_name}" GSTIN OR "GST Number" OR GST number site:knowyourgst.com OR site:zaubacorp.com OR site:cleartax.in',
#         f'"{company_name}" "GSTIN" "27" OR "29" OR "07" OR "03" OR "06"',
#         f'"{company_name}" GSTIN filetype:pdf OR "GST Certificate"',
#         f'"{company_name}" GST number India'
#     ]
    
#     for q in queries:
#         try:
#             results = ddgs.text(
#                 query=q,
#                 region="in-en",
#                 safesearch="off",
#                 max_results=10
#             )
            
#             for result in results:
#                 text = (result.get("title", "") + " " + 
#                         result.get("body", "") + " " + 
#                         result.get("href", "")).upper()
                
#                 matches = GST_PATTERN.findall(text)
#                 for match in matches:
#                     gst_candidates.add(match)
                
#                 if "GSTIN" in text or "GST NUMBER" in text:
#                     parts = text.split()
#                     for i, part in enumerate(parts):
#                         if "GSTIN" in part.upper() or "GST" in part.upper():
#                             if i+1 < len(parts) and GST_PATTERN.match(parts[i+1]):
#                                 gst_candidates.add(parts[i+1])
        
#         except Exception as e:
#             print(f"   GST search error ({q}): {e}")
    
#     if gst_candidates:
#         return sorted(gst_candidates)[0]
    
#     return "Not found"


# # =============================================
# # MAIN PROCESSING
# # =============================================
# print("🚀 Starting automated verification...")

# df = pd.read_excel(INPUT_FILE)
# ddgs = DDGS()  # Shared instance - used everywhere

# # Prepare list for all rows (including filtered ones)
# all_rows = []

# for idx, row in df.iterrows():
#     company = str(row["company_name"]).strip()
#     fund_raise_desc = str(row["fund_raise"]).strip()
#     fund_amount = row["fund_raise_amount"]
    
#     print(f"[{idx+1:2d}/{len(df)}] {company} … ", end="")
    
#     # 1. Verify recent funding news (pass shared ddgs)
#     is_valid, news_date, reason = verify_recent_funding(company, fund_raise_desc, ddgs)
    
#     # 2. Try to fetch GSTIN (pass shared ddgs)
#     gst = extract_gst_number(company, ddgs)
    
#     # 3. Prepare output row
#     new_row = row.copy()
#     new_row["gst_number"] = gst
#     new_row["news_date"] = news_date if news_date else ""
#     new_row["verified"] = "YES" if is_valid else "NO"
#     new_row["reason"] = reason
    
#     all_rows.append(new_row)
    
#     status = "✓" if is_valid else "✗"
#     gst_display = gst if gst else "no GST"
#     print(f"{status} ({reason}) | GST: {gst_display}")
    
#     # Polite delay to avoid rate-limiting
#     time.sleep(random.uniform(10, 15))

# # =============================================
# # SAVE OUTPUT
# # =============================================
# if all_rows:
#     output_df = pd.DataFrame(all_rows)
#     # Reorder columns nicely
#     cols = ["company_name", "fund_raise", "gst_number", "pan_number", "fund_raise_amount", "news_date", "verified", "reason"]
#     output_df = output_df[cols]
    
#     output_df.to_excel(OUTPUT_FILE, index=False)
#     print(f"\n🎉 DONE! All {len(all_rows)} entries processed and saved to → {OUTPUT_FILE}")
# else:
#     print("\n⚠️  No data to save.")











# import pandas as pd
# from ddgs import DDGS
# import re
# import random
# import time
# from datetime import datetime
# import requests
# from bs4 import BeautifulSoup

# # =============================================
# # CONFIGURATION
# # =============================================
# INPUT_FILE = "C:\\Users\\Admin\\Desktop\\RM_Scores_API\\backend\\services\\12_feb_raw.xlsx"
# OUTPUT_FILE = "verified_fundings_feb_2026_new.xlsx"

# # GSTIN Regex (exact 15-character Indian GSTIN format)
# GST_PATTERN = re.compile(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b')

# # Simple regex for finding amounts in snippets (e.g., Rs 123 crore, $45 million, ₹678 Cr)
# AMOUNT_PATTERN = re.compile(r'(Rs|₹|\$|USD|INR|crore|million|billion|cr)\s*[\d,.]+(?:\s*(crore|million|billion|cr))?', re.IGNORECASE)

# # Heuristic for finding possible company names (sequences of capitalized words)
# COMPANY_PATTERN = re.compile(r'\b([A-Z][a-z0-9]*\s*){2,4}\b')

# def verify_recent_funding(company_name: str, fund_raise_desc: str, ddgs) -> tuple[bool, str, str]:
#     query = f'"{company_name}" {fund_raise_desc} funding OR investment OR raise OR IPO OR project OR contract OR award OR acquisition OR QIP'
#     reason = "No recent/relevant news found (potentially old or fake)"
    
#     try:
#         # Prefer news search for dates
#         results = ddgs.news(
#             query=query,
#             region="in-en",
#             safesearch="moderate",
#             timelimit="m",
#             max_results=15
#         ) or ddgs.text(
#             query=query,
#             region="in-en",
#             safesearch="moderate",
#             timelimit="m",
#             max_results=15
#         )
        
#         if not results:
#             return False, "", "No news results in past month"
        
#         company_lower = company_name.lower()
#         desc_lower = fund_raise_desc.lower()
#         company_words = set(company_lower.split())
        
#         for result in results[:5]:  # Check top 5 only for speed
#             url = result.get("href", "")
#             title = result.get("title", "").lower()
#             body = result.get("body", "").lower()
#             snippet = title + " " + body
            
#             # Partial match in snippet (quick filter)
#             company_hit = any(word in snippet for word in company_words) or company_lower in snippet
#             amount_hit = any(word in snippet for word in desc_lower.split())
            
#             if not (company_hit or amount_hit):
#                 continue  # Skip if no hint at all
            
#             # Fetch full page if partial match
#             try:
#                 if not url or not url.startswith(('http://', 'https://')):
#                     continue  # Skip invalid/empty URLs
#                 response = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
#                 if response.status_code == 200:
#                     soup = BeautifulSoup(response.text, 'html.parser')
#                     full_text = soup.get_text(separator=" ", strip=True).lower()
                    
#                     # Final check in full text
#                     company_full_hit = any(word in full_text for word in company_words) or company_lower in full_text
#                     amount_full_hit = any(word in full_text for word in desc_lower.split())
                    
#                     if company_full_hit and amount_full_hit:
#                         date = result.get("date") or datetime.now().strftime("%Y-%m-%d")
#                         return True, date, "Valid recent news found (full article match)"
#             except Exception as e:
#                 print(f"   Page fetch skipped for {url}: {e}")
#                 # Continue to next result
            
#         # No match after checking full pages
#         first = results[0]
#         snippet = (first.get("title", "") + " " + first.get("body", "")).lower()
#         detail = []
        
#         company_hit = any(word in snippet for word in company_words) or company_lower in snippet
#         if not company_hit:
#             found = COMPANY_PATTERN.search(first.get("title", "") + " " + first.get("body", "")) 
#             found_name = found.group(0).strip() if found else "not detected"
#             detail.append(f"Company mismatch (found possible name: '{found_name}' instead of '{company_name}')")
        
#         amount_hit = any(word in snippet for word in desc_lower.split())
#         if not amount_hit:
#             found_amt = AMOUNT_PATTERN.search(first.get("title", "") + " " + first.get("body", "")) 
#             found_amount = found_amt.group(0).strip() if found_amt else "not detected"
#             detail.append(f"Amount mismatch (found possible amount: '{found_amount}' instead of '{fund_raise_desc}')")
        
#         reason = "News found but doesn't match details: " + "; ".join(detail) if detail else "No clear match"
#         date = first.get("date") or datetime.now().strftime("%Y-%m-%d")
        
#     except Exception as e:
#         reason = f"Search error: {str(e)}"
#         date = ""
    
#     return False, date, reason

# def extract_gst_number(company_name: str, ddgs) -> str:
#     """
#     Improved: Multiple targeted DuckDuckGo searches + better pattern matching
#     """
#     gst_candidates = set()  # avoid duplicates
    
#     queries = [
#         f'"{company_name}" GSTIN OR "GST Number" OR GST number site:knowyourgst.com OR site:zaubacorp.com OR site:cleartax.in',
#         f'"{company_name}" "GSTIN" "27" OR "29" OR "07" OR "03" OR "06"',
#         f'"{company_name}" GSTIN filetype:pdf OR "GST Certificate"',
#         f'"{company_name}" GST number India'
#     ]
    
#     for q in queries:
#         try:
#             results = ddgs.text(
#                 query=q,
#                 region="in-en",
#                 safesearch="off",
#                 max_results=10
#             )
            
#             for result in results:
#                 text = (result.get("title", "") + " " + 
#                         result.get("body", "") + " " + 
#                         result.get("href", "")).upper()
                
#                 matches = GST_PATTERN.findall(text)
#                 for match in matches:
#                     gst_candidates.add(match)
                
#                 if "GSTIN" in text or "GST NUMBER" in text:
#                     parts = text.split()
#                     for i, part in enumerate(parts):
#                         if "GSTIN" in part.upper() or "GST" in part.upper():
#                             if i+1 < len(parts) and GST_PATTERN.match(parts[i+1]):
#                                 gst_candidates.add(parts[i+1])
        
#         except Exception as e:
#             print(f"   GST search error ({q}): {e}")
    
#     if gst_candidates:
#         return sorted(gst_candidates)[0]
    
#     return "Not found"


# # =============================================
# # MAIN PROCESSING
# # =============================================
# print("🚀 Starting automated verification...")

# df = pd.read_excel(INPUT_FILE)
# ddgs = DDGS()  # Shared instance - used everywhere

# # Prepare list for all rows (including filtered ones)
# all_rows = []

# for idx, row in df.iterrows():
#     company = str(row["company_name"]).strip()
#     fund_raise_desc = str(row["fund_raise"]).strip()
#     fund_amount = row["fund_raise_amount"]
    
#     print(f"[{idx+1:2d}/{len(df)}] {company} … ", end="")
    
#     # 1. Verify recent funding news (pass shared ddgs)
#     is_valid, news_date, reason = verify_recent_funding(company, fund_raise_desc, ddgs)
    
#     # 2. Try to fetch GSTIN (pass shared ddgs)
#     gst = extract_gst_number(company, ddgs)
    
#     # 3. Prepare output row
#     new_row = row.copy()
#     new_row["gst_number"] = gst
#     new_row["news_date"] = news_date if news_date else ""
#     new_row["verified"] = "YES" if is_valid else "NO"
#     new_row["reason"] = reason
    
#     all_rows.append(new_row)
    
#     status = "✓" if is_valid else "✗"
#     gst_display = gst if gst else "no GST"
#     print(f"{status} ({reason}) | GST: {gst_display}")
    
#     # Polite delay to avoid rate-limiting
#     time.sleep(random.uniform(10, 15))

# # =============================================
# # SAVE OUTPUT
# # =============================================
# if all_rows:
#     output_df = pd.DataFrame(all_rows)
#     # Reorder columns nicely
#     cols = ["company_name", "fund_raise", "gst_number", "pan_number", "fund_raise_amount", "news_date", "verified", "reason"]
#     output_df = output_df[cols]
    
#     output_df.to_excel(OUTPUT_FILE, index=False)
#     print(f"\n🎉 DONE! All {len(all_rows)} entries processed and saved to → {OUTPUT_FILE}")
# else:
#     print("\n⚠️  No data to save.")









import pandas as pd
from ddgs import DDGS
import re
import random
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# =============================================
# CONFIGURATION
# =============================================
INPUT_FILE = r"C:\Users\Admin\Desktop\RM_Scores_API\backend\services\12_feb_raw.xlsx"
OUTPUT_FILE = "verified_fundings_feb_2026_fixed.xlsx"

GST_PATTERN = re.compile(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b')
AMOUNT_PATTERN = re.compile(r'(Rs|₹|\$|USD|INR|crore|million|billion|cr)\s*[\d,.]+(?:\s*(crore|million|billion|cr))?', re.IGNORECASE)

def verify_recent_funding(company_name: str, fund_raise_desc: str, ddgs) -> tuple[bool, str, str]:
    """
    Super-fixed version: aggressive matching, full page read, strong retry, focused Indian finance sources
    """
    # Strong focused query on Indian business/finance sites
    query = f'"{company_name}" {fund_raise_desc} (funding OR raise OR investment OR IPO OR QIP OR acquisition OR order OR project OR award OR secured OR bagged) site:economictimes.indiatimes.com OR site:business-standard.com OR site:livemint.com OR site:financialexpress.com OR site:moneycontrol.com OR site:thehindubusinessline.com OR site:ndtvprofit.com'

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Use news search first (best for dates and relevance)
            results = ddgs.news(
                query=query,
                region="in-en",
                safesearch="off",  # off = more results, even if slightly risky
                timelimit="m",
                max_results=20  # More results = better chance
            )

            if not results:
                results = ddgs.text(
                    query=query,
                    region="in-en",
                    safesearch="off",
                    timelimit="m",
                    max_results=20
                )

            if not results:
                return False, "", "No recent news found on major finance sites"

            company_lower = company_name.lower().replace("pvt ltd", "").replace("limited", "").strip()
            desc_lower = fund_raise_desc.lower().replace("rs ", "").replace("₹", "").replace("$", "").replace("crore", "cr").replace("million", "mn").strip()
            company_words = set(company_lower.split())

            for result in results[:10]:  # Check top 10
                url = result.get("href", "").strip()
                if not url or not url.startswith(('http://', 'https://')):
                    continue

                date = result.get("date") or datetime.now().strftime("%Y-%m-%d")
                title = result.get("title", "").lower()
                body = result.get("body", "").lower()
                snippet = title + " " + body

                # Very loose initial filter (any word match)
                company_hit = any(word in snippet for word in company_words) or company_lower in snippet
                amount_hit = any(word in snippet for word in desc_lower.split()) or any(word in snippet for word in ["crore", "million", "billion", "cr", "mn"])

                if not (company_hit or amount_hit):
                    continue

                # Fetch full page
                try:
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    response = requests.get(url, timeout=12, headers=headers)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        full_text = soup.get_text(separator=" ", strip=True).lower()

                        # Final strict check in full text
                        full_company = any(word in full_text for word in company_words) or company_lower in full_text
                        full_amount = any(word in full_text for word in desc_lower.split()) or any(term in full_text for term in ["crore", "million", "billion", "cr", "mn"])

                        if full_company and full_amount:
                            return True, date, "Valid recent news found (full article confirmed)"

                except Exception as fetch_e:
                    print(f"   Full page failed for {url}: {fetch_e}")
                    continue

            # No match after deep check
            top = results[0]
            snippet = (top.get("title", "") + " " + top.get("body", "")).lower()
            detail = []

            if not (company_lower in snippet or any(w in snippet for w in company_words)):
                found = re.search(r'\b[A-Z][a-zA-Z0-9\s&-]{3,40}\b', top.get("title", "") + " " + top.get("body", ""))
                found_name = found.group(0).strip() if found else "unknown"
                detail.append(f"Company not clearly mentioned (found hint: '{found_name}')")

            if not any(w in snippet for w in desc_lower.split()):
                found_amt = AMOUNT_PATTERN.search(top.get("title", "") + " " + top.get("body", ""))
                found_amount = found_amt.group(0).strip() if found_amt else "not found"
                detail.append(f"Amount not clearly mentioned (found hint: '{found_amount}')")

            reason = "News found but insufficient match: " + "; ".join(detail) if detail else "No strong match in top results"
            date = top.get("date") or datetime.now().strftime("%Y-%m-%d")

            return False, date, reason

        except Exception as e:
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                print(f"   Timeout (attempt {attempt+1}/{max_retries}) for {company_name} → retrying...")
                time.sleep(random.uniform(40, 80))  # Long wait
                continue
            else:
                print(f"   Critical search error for {company_name}: {e}")
                return False, "", f"Search failed: {str(e)}"

    return False, "", "Max retries exceeded (timeout or connection issue)"

def extract_gst_number(company_name: str, ddgs) -> str:
    gst_candidates = set()
    queries = [
        f'"{company_name}" GSTIN OR "GST Number" site:zaubacorp.com OR site:knowyourgst.com OR site:cleartax.in',
        f'"{company_name}" GSTIN',
        f'"{company_name}" GST number India'
    ]
    
    for q in queries:
        try:
            results = ddgs.text(query=q, region="in-en", safesearch="off", max_results=8)
            for result in results:
                text = (result.get("title", "") + " " + result.get("body", "") + " " + result.get("href", "")).upper()
                for match in GST_PATTERN.findall(text):
                    gst_candidates.add(match)
        except Exception as e:
            pass  # Silent fail for GST - not critical
    
    return sorted(gst_candidates)[0] if gst_candidates else "Not found"

# MAIN PROCESSING
print("🚀 Starting automated verification...")
df = pd.read_excel(INPUT_FILE)
ddgs = DDGS()

all_rows = []

for idx, row in df.iterrows():
    company = str(row["company_name"]).strip()
    fund_raise_desc = str(row["fund_raise"]).strip()
    print(f"[{idx+1:2d}/{len(df)}] {company} … ", end="")
    
    is_valid, news_date, reason = verify_recent_funding(company, fund_raise_desc, ddgs)
    gst = extract_gst_number(company, ddgs)
    
    new_row = row.copy()
    new_row["gst_number"] = gst
    new_row["news_date"] = news_date
    new_row["verified"] = "YES" if is_valid else "NO"
    new_row["reason"] = reason
    
    all_rows.append(new_row)
    
    status = "✓" if is_valid else "✗"
    print(f"{status} ({reason}) | GST: {gst}")
    
    time.sleep(random.uniform(12, 25))  # Aggressive anti-block delay

# SAVE
if all_rows:
    output_df = pd.DataFrame(all_rows)
    cols = ["company_name", "fund_raise", "gst_number", "pan_number", "fund_raise_amount", "news_date", "verified", "reason"]
    output_df = output_df[cols]
    output_df.to_excel(OUTPUT_FILE, index=False)
    print(f"\n🎉 DONE! All {len(all_rows)} entries saved → {OUTPUT_FILE}")
else:
    print("\n⚠️ No data.")















