# This is the one ------------------------------------------------------------------------->

# Task - 1 -->

# from flask import Flask, jsonify, render_template, request
# from services.region_superadminid_scores import get_topic_best_worst_by_region_all_rms

# app = Flask(__name__, template_folder="../frontend")


# @app.route("/", methods=["GET"])
# def home():
#     return render_template("index.html")


# @app.route("/rm-topic-scores", methods=["GET"])
# def rm_scores():
#     region = request.args.get("region") or "Mumbai"
#     superadmin_id = request.args.get("superadmin_id") or "SAB001"

#     response, status_code = get_topic_best_worst_by_region_all_rms(
#         region, superadmin_id
#     )

#     return jsonify(response), status_code


# @app.errorhandler(404)
# def not_found(_):
#     return jsonify({"error": "Endpoint not found"}), 404


# if __name__ == "__main__":
#     app.run(debug=True)




# Task - 2 Report -->
from flask import Flask, request, jsonify


from services.rm_report_service import generate_report_api

app = Flask(__name__)


# ---------------- RM-SPECIFIC REPORT ----------------

@app.route("/rm-report", methods=["GET"])
def rm_report():
    try:
        rm_id = request.args.get("rm_id")
        start_date = request.args.get("start_date")  # YYYY-MM-DD
        end_date = request.args.get("end_date")      # YYYY-MM-DD

        if not rm_id:
            return jsonify({"error": "rm_id is required"}), 400

        result, status_code = generate_report_api(start_date, end_date)

        return jsonify(result), status_code

    except Exception:
        return jsonify({"error": "Internal Server Error"}), 500


# ---------------- ALL RM FULL REPORT ----------------

@app.route("/rm-full-report", methods=["GET"])
def rm_full_report():
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        result, status = generate_report_api(start_date, end_date)
        return jsonify(result), status

    except Exception:
        return jsonify({"error": "Internal Server Error"}), 500


# ---------------- RUN SERVER ----------------

if __name__ == "__main__":
    app.run(debug=True)


