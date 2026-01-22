from psycopg2.extras import RealDictCursor
from db_config import get_db_connection
import json


def get_region_score_summary(region, exclude_rm_id, superadmin_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT
            ri.score_json
        FROM investigen.transaction_info ti
        JOIN investigen.user_master um ON ti.rm_id = um.rm_id
        JOIN investigen.recorded_info ri ON ti.record_id = ri.record_id
        WHERE um.region = %s
          AND um.rm_id <> %s
          AND um.superadminid = %s
          AND ri.score_json IS NOT NULL;
    """

    cur.execute(query, (region, exclude_rm_id, superadmin_id))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    scores = []

    for row in rows:
        try:
            score_json = row["score_json"]

            # Parse JSON if stored as string
            if isinstance(score_json, str):
                score_json = json.loads(score_json)

            final_score = (
                score_json
                    .get("summery_score", {})
                    .get("data", {})
                    .get("final_score")
            )

            if not final_score:
                continue

            # Handle "13/20" or "15"
            if isinstance(final_score, str) and "/" in final_score:
                score = float(final_score.split("/")[0])
            else:
                score = float(final_score)

            scores.append(score)

        except Exception:
            continue

    if not scores:
        return {
            "region": region,
            "message": "No valid scores found"
        }

    return {
        "region": region,
        "average_score": round(sum(scores) / len(scores), 2),
        "best_score": max(scores),
        "worst_score": min(scores)
    }


if __name__ == "__main__":
    print(
        get_region_score_summary("Mumbai", "SAB001", "SAB001")
    )
