import sys
import os
import json
from psycopg2.extras import RealDictCursor
from db_config import get_db_connection

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def get_topic_best_worst_by_region_all_rms(region=None, superadmin_id=None):
    """
    Fetches the single best topic for each RM with its best and worst scores.
    superadmin_id is REQUIRED and validated.
    """

    # -------------------- 🔐 AUTH CHECK --------------------
    if not superadmin_id:
        return {"error": "superadmin_id is required"}, 401

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT 1
            FROM investigen.user_master
            WHERE superadminid = %s
            LIMIT 1
            """,
            (superadmin_id,)
        )

        auth_exists = cur.fetchone()
        cur.close()
        conn.close()

    except Exception:
        return {"error": "Authorization check failed"}, 500

    if not auth_exists:
        return {"error": "Unauthorized superadmin_id"}, 401
    
    # -------------------- ❌ BAD REQUEST CHECK --------------------
    if region is not None and not region.strip():
        return {"error": "Invalid region parameter"}, 400


    # -------------------- 📊 DATA QUERY --------------------
    query = """
        SELECT 
            um.region,
            um.rm_id,
            ri.score_json
        FROM investigen.transaction_info ti
        JOIN investigen.user_master um ON ti.rm_id = um.rm_id
        JOIN investigen.recorded_info ri ON ti.record_id = ri.record_id
        WHERE ri.score_json IS NOT NULL
          AND um.superadminid = %s
    """
    params = [superadmin_id]

    if region:
        query += " AND um.region = %s"
        params.append(region)

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        return {"error": "Database connection or query failed"}, 500

    if not rows:
        return {"error": "No RM data found"}, 200

    # -------------------- 🧠 PROCESSING --------------------
    rm_topic_scores = {}
    valid_row_count = 0

    for row in rows:
        rm_id = row.get("rm_id")
        score_json = row.get("score_json")
        region_name = row.get("region")

        if not rm_id or not score_json:
            continue

        if isinstance(score_json, str):
            try:
                score_json = json.loads(score_json)
            except json.JSONDecodeError:
                continue

        sections = score_json.get("summery_score", {}).get("sections", [])
        if not sections:
            continue

        valid_row_count += 1

        if rm_id not in rm_topic_scores:
            rm_topic_scores[rm_id] = {"region": region_name, "topics": {}}

        for section in sections:
            topic = section.get("topic")
            score_raw = section.get("score")

            if not topic or not score_raw:
                continue

            try:
                score = float(score_raw.split("/")[0])
            except (ValueError, AttributeError):
                continue
            # print(traceback format_exc())

            if topic not in rm_topic_scores[rm_id]["topics"]:
                rm_topic_scores[rm_id]["topics"][topic] = {
                    "best_score": score,
                    "worst_score": score,
                    "has_real_score": score != 0
                }
            else:
                current = rm_topic_scores[rm_id]["topics"][topic]
                if current["has_real_score"]:
                    current["best_score"] = max(current["best_score"], score)
                    current["worst_score"] = min(current["worst_score"], score)
                elif score != 0:
                    current["best_score"] = score
                    current["worst_score"] = score
                    current["has_real_score"] = True

    # -------------------- 🎯 FINAL RESULT --------------------
    results = {}

    for rm_id, data in rm_topic_scores.items():
        topics = data["topics"]
        if not topics:
            continue

        best_topic_name = max(topics, key=lambda t: topics[t]["best_score"])
        best_topic_data = topics[best_topic_name]

        results[rm_id] = {
            "region": data["region"],
            "best_topic": {
                "topic": best_topic_name,
                "best_score": best_topic_data["best_score"],
                "worst_score": best_topic_data["worst_score"]
            }
        }

    response_payload = {"results": results}

    if valid_row_count < len(rows):
        response_payload["warning"] = "Partial data processed"
        return response_payload, 206

    return response_payload, 200
