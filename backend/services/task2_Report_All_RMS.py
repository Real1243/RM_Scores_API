import sys
import os
import json
import re
import pandas as pd
from psycopg2.extras import RealDictCursor


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_config import get_db_connection


# -------------------- HELPERS --------------------

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\*\*", "", text)
    return text.strip()


def normalize_score(raw):
    try:
        return float(str(raw).split("/")[0])
    except Exception:
        return 0.0


def extract_scores(score_json):
    scores = {}
    soft_skill_total = 0.0
    knowledge_total = 0.0

    if isinstance(score_json, str):
        score_json = json.loads(score_json)

    summary = score_json.get("summery_score", {})
    scores["Total_Score_100"] = normalize_score(summary.get("total_score"))

    sections = summary.get("sections", [])

    for sec in sections:
        topic = sec.get("topic", "").strip()
        score = normalize_score(sec.get("score"))

        if not topic:
            continue

        col = topic.replace(" ", "_") + "_Score_100"
        scores[col] = score

        if topic.lower() in ["clarity", "confidence"]:
            soft_skill_total += score
        else:
            knowledge_total += score

    scores["Soft_Skill_Score_100"] = round(soft_skill_total, 2)
    scores["Knowledge_Score_100"] = round(knowledge_total, 2)

    return scores


# -------------------- MAIN REPORT --------------------

def generate_report(start_date, end_date, output_file):
    query = """
        SELECT DISTINCT ON (ri.record_id)
        um.*,
        ti.created_date,
        ki.topic_name,
        ri.record_id, 
        ri.recorded_data, 
        ri.confidence_analysis, 
        ri.score_json, 
        ri.html_content 
        FROM investigen.user_master um 
        JOIN investigen.transaction_info ti ON um.rm_id = ti.rm_id 
        JOIN investigen.recorded_info ri ON ri.record_id = ti.record_id 
        JOIN investigen.knowledge_info ki ON ki.id = ti.topic_id WHERE ri.score_json IS NOT NULL AND ti.created_date BETWEEN %s AND %s ORDER BY ri.record_id, ti.created_date DESC;
    """

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, (start_date, end_date))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("No data found")
        return

    report_rows = []

    for row in rows:
        base_row = {}

        # ---- ALL USER_MASTER + QUERY FIELDS ----
        for k, v in row.items():
            if k not in [
                "score_json",
                "recorded_data",
                "confidence_analysis",
                "html_content"
            ]:
                base_row[k] = v

        # ---- CLEAN TEXT ----
        base_row["Knowledge_Text"] = clean_text(row.get("recorded_data"))
        base_row["Soft_Skill_Text"] = clean_text(row.get("confidence_analysis"))

        # ---- SCORES ----
        score_columns = extract_scores(row.get("score_json"))
        base_row.update(score_columns)

        report_rows.append(base_row)

    df = pd.DataFrame(report_rows)

    # ✅ SAFE FILLNA (NO WARNINGS, NO CHAINING)
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].fillna("")

    df.to_excel(output_file, index=False)

    print(f"Excel report generated: {output_file}")


# -------------------- RUN --------------------

if __name__ == "__main__":
    generate_report(
        start_date="2026-01-01",
        end_date="2026-01-31",
        output_file="RM_Full_Normalized_Report_All_RMs.xlsx"
    )
