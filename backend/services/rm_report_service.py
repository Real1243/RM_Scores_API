# import sys
# import os
# import json
# import re
# from psycopg2.extras import RealDictCursor

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from db_config import get_db_connection


# # -------------------- HELPERS --------------------

# def clean_text(text):
#     if not text:
#         return ""
#     text = re.sub(r"<.*?>", "", text)
#     text = re.sub(r"\*\*", "", text)
#     return text.strip()


# def normalize_score(raw):
#     try:
#         return float(str(raw).split("/")[0])
#     except Exception:
#         return 0.0


# def extract_scores(score_json):
#     scores = {}
#     soft_skill_total = 0.0
#     knowledge_total = 0.0

#     if isinstance(score_json, str):
#         score_json = json.loads(score_json)

#     summary = score_json.get("summery_score", {})
#     scores["Total_Score_100"] = normalize_score(summary.get("total_score"))

#     sections = summary.get("sections", [])

#     for sec in sections:
#         topic = sec.get("topic", "").strip()
#         score = normalize_score(sec.get("score"))

#         if not topic:
#             continue

#         col = topic.replace(" ", "_") + "_Score_100"
#         scores[col] = score

#         if topic.lower() in ["clarity", "confidence"]:
#             soft_skill_total += score
#         else:
#             knowledge_total += score

#     scores["Soft_Skill_Score_100"] = round(soft_skill_total, 2)
#     scores["Knowledge_Score_100"] = round(knowledge_total, 2)

#     return scores


# # -------------------- API REPORT --------------------

# def generate_report_api(start_date=None, end_date=None):
#     """
#     Uses the exact query provided by task giver
#     and returns browser-friendly JSON
#     """

#     query = """
#         SELECT DISTINCT ON (ri.record_id)
#             um.*, ti.created_date, ki.topic_name,
#             ri.record_id, ri.recorded_data,
#             ri.confidence_analysis, ri.score_json, ri.html_content
#         FROM investigen.user_master um
#         JOIN investigen.transaction_info ti ON um.rm_id = ti.rm_id
#         JOIN investigen.recorded_info ri ON ri.record_id = ti.record_id
#         JOIN investigen.knowledge_info ki ON ki.id = ti.topic_id
#         WHERE ri.score_json IS NOT NULL
#           AND um.rm_id = 'RM017'
#     """

#     params = []

#     # Date selection format (added without changing base query logic)
#     if start_date and end_date:
#         query += " AND ti.created_date BETWEEN %s AND %s"
#         params.extend([start_date, end_date])

#     query += " ORDER BY ri.record_id, ti.created_date DESC"

#     try:
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         cur.execute(query, tuple(params))
#         rows = cur.fetchall()
#         cur.close()
#         conn.close()
#     except Exception as e:
#         return {
#             "error": "Database error",
#             "details": str(e)
#         }, 500

#     if not rows:
#         return {"error": "No data found"}, 404

#     report_rows = []

#     for row in rows:
#         base_row = {}

#         # ---- CORE FIELDS ----
#         for k, v in row.items():
#             if k not in [
#                 "score_json",
#                 "recorded_data",
#                 "confidence_analysis",
#                 "html_content"
#             ]:
#                 base_row[k] = v

#         # ---- CLEAN TEXT ----
#         base_row["Knowledge_Text"] = clean_text(row.get("recorded_data"))
#         base_row["Soft_Skill_Text"] = clean_text(row.get("confidence_analysis"))

#         # ---- SCORES ----
#         score_columns = extract_scores(row.get("score_json"))
#         base_row.update(score_columns)

#         report_rows.append(base_row)

#     return {
#         "rm_id": "RM017",
#         "total_records": len(report_rows),
#         "data": report_rows
#     }, 200












import sys
import os
import json
import re
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


def extract_scores(confidence_text):
    """
    Extracts ONLY:
    - Clarity Score (out of 10)
    - Confidence Score (out of 10)
    From confidence_analysis text
    """

    scores = {
        "Clarity_Score_10": None,
        "Confidence_Score_10": None
    }

    if not confidence_text:
        return scores

    # Confidence Score
    conf_match = re.search(r"Confidence Score:\s*(\d+)\s*/\s*10", confidence_text, re.IGNORECASE)
    if conf_match:
        scores["Confidence_Score_10"] = int(conf_match.group(1))

    # Clarity Score
    clarity_match = re.search(r"Clarity Score:\s*(\d+)\s*/\s*10", confidence_text, re.IGNORECASE)
    if clarity_match:
        scores["Clarity_Score_10"] = int(clarity_match.group(1))

    return scores




def format_rm_record(row):
    return {
        "rm_id": row.get("rm_id"),
        "name": row.get("name"),
        "region": row.get("region"),
        "zone": row.get("zone"),
        "topic": row.get("topic_name"),
        "created_date": row.get("created_date"),

        # ONLY SCORES
        "scores": extract_scores(row.get("confidence_analysis"))
    }



# -------------------- API REPORT --------------------

def generate_report_api(start_date=None, end_date=None):
    

    query = """
        SELECT DISTINCT ON (ri.record_id)
            um.*, ti.created_date, ki.topic_name,
            ri.record_id, ri.recorded_data,
            ri.confidence_analysis, ri.score_json, ri.html_content
        FROM investigen.user_master um
        JOIN investigen.transaction_info ti ON um.rm_id = ti.rm_id
        JOIN investigen.recorded_info ri ON ri.record_id = ti.record_id
        JOIN investigen.knowledge_info ki ON ki.id = ti.topic_id
        WHERE ri.score_json IS NOT NULL
          AND um.rm_id = 'RM017'
    """

    params = []

    if start_date and end_date:
        query += " AND ti.created_date BETWEEN %s AND %s"
        params.extend([start_date, end_date])

    query += " ORDER BY ri.record_id, ti.created_date DESC"

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        return {
            "error": "Database error",
            "details": str(e)
        }, 500

    if not rows:
        return {"error": "No data found"}, 404

    formatted_data = [format_rm_record(row) for row in rows]

    return {
        "rm_id": "RM017",
        "total_records": len(formatted_data),
        "data": formatted_data
    }, 200
