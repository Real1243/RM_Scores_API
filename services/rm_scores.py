from psycopg2.extras import RealDictCursor
from db_config import get_db_connection
from collections import defaultdict
import json


def get_rm_scores_with_extremes():
    query = """
    SELECT
        r.rm_id,
        r.score_json,
        um.zone,
        um.region
    FROM investigen.recorded_info r
    JOIN investigen.user_master um
        ON r.rm_id = um.rm_id
    WHERE r.score_json IS NOT NULL
      AND um.zone IS NOT NULL
      AND um.region IS NOT NULL;
    """

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    scores = []

    for row in rows:
        try:
            score_json = row["score_json"]

            if isinstance(score_json, str):
                score_json = json.loads(score_json)

            final_score = score_json["summery_score"]["data"]["final_score"]

            if isinstance(final_score, str) and "/" in final_score:
                score = float(final_score.split("/")[0])
            else:
                score = float(final_score)

            scores.append(score)

        except Exception:
            continue

    if not scores:
        return {
            "message": "No valid scores found"
        }

    return {
        "region": rows[0]["region"],
        "average_score": round(sum(scores) / len(scores), 2),
        "best_score": max(scores),
        "worst_score": min(scores)
    }
