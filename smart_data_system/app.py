"""
app.py — Flask entry point with all 4 unique features wired in.
"""
import os, sys, io, json, datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from modules.validation        import UserFormValidator
from modules.processing        import DataProcessor
from modules.serialization     import save_result, load_all_results, load_result_by_id, delete_result
from modules.threading_tasks   import run_threaded_processing
from modules.insights_engine   import InsightsEngine
from modules.comparison_engine import ComparisonEngine, DatasetSnapshot
from modules.report_exporter   import generate_report

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER      = os.path.join(BASE_DIR, "data", "uploads")
ALLOWED_EXTENSIONS = {"csv", "json"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "static", "reports"), exist_ok=True)

validator       = UserFormValidator()
insights_engine = InsightsEngine()
comp_engine     = ComparisonEngine()


def allowed_file(f):
    return "." in f and f.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _load_dp(file_storage):
    ext    = file_storage.filename.rsplit(".", 1)[1].lower()
    fbytes = io.BytesIO(file_storage.read())
    name   = secure_filename(file_storage.filename.rsplit(".", 1)[0])
    dp     = DataProcessor(name=name)
    dp.load(fbytes, filetype=ext)
    return dp


@app.route("/")
def index():
    return render_template("index.html", rules=validator.get_rules())


@app.route("/process", methods=["POST"])
def process():
    form_data = {k: request.form.get(k, "").strip()
                 for k in ("name", "email", "phone", "password")}

    validation = validator.validate(form_data)
    if not validation["valid"]:
        return render_template("index.html", errors=validation["errors"],
                               form_data=form_data, rules=validator.get_rules())

    stats = {}; chart_paths = []; threading_result = {}
    preview_rows = []; insights = []; health = {}; report_path = ""

    file = request.files.get("dataset")
    if file and file.filename and allowed_file(file.filename):
        try:
            dp           = _load_dp(file)
            stats        = dp.compute_statistics()
            chart_paths  = dp.generate_charts()
            preview_rows = dp.get_preview(rows=8)
            threading_result = run_threaded_processing(
                dp.df.head(200).to_dict("records"), num_threads=4)
            insights = insights_engine.analyse(dp.df, stats)
            health   = insights_engine.health_score(dp.df, stats)
        except Exception as e:
            import traceback
            traceback.print_exc()
            stats = {"error": str(e)}
    else:
        threading_result = {"status": "no_dataset_provided"}

    record_id = save_result(form_data["name"], stats, chart_paths, form_data)

    if stats and not stats.get("error"):
        try:
            os.makedirs(os.path.join(BASE_DIR, "static", "reports"), exist_ok=True)
            report_path = generate_report(
                user=form_data, stats=stats, insights=insights,
                health=health, chart_paths=chart_paths, record_id=record_id)
        except Exception as e:
            import traceback
            traceback.print_exc()
            report_path = ""

    return render_template("dashboard.html",
        user=form_data, stats=stats, chart_paths=chart_paths,
        threading_result=threading_result, preview_rows=preview_rows,
        record_id=record_id,
        generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        insights=insights, health=health, report_path=report_path)


@app.route("/compare", methods=["GET", "POST"])
def compare():
    if request.method == "GET":
        return render_template("compare.html")
    fa, fb = request.files.get("dataset_a"), request.files.get("dataset_b")
    errors = []
    if not fa or not fa.filename or not allowed_file(fa.filename):
        errors.append("Upload Dataset A (CSV or JSON).")
    if not fb or not fb.filename or not allowed_file(fb.filename):
        errors.append("Upload Dataset B (CSV or JSON).")
    if errors:
        return render_template("compare.html", errors=errors)
    try:
        snap_a = DatasetSnapshot(_load_dp(fa).df, fa.filename.rsplit(".",1)[0])
        snap_b = DatasetSnapshot(_load_dp(fb).df, fb.filename.rsplit(".",1)[0])
        result = snap_a - snap_b   # __sub__ operator overloading
        return render_template("compare.html", result=result)
    except Exception as e:
        return render_template("compare.html", errors=[str(e)])


@app.route("/history")
def history():
    return render_template("history.html", records=load_all_results())


@app.route("/history/delete/<record_id>", methods=["POST"])
def delete_record(record_id):
    delete_result(record_id)
    return redirect(url_for("history"))


@app.route("/api/stats")
def api_stats():
    return jsonify(load_all_results())


@app.route("/api/validate", methods=["POST"])
def api_validate():
    return jsonify(validator.validate(request.get_json(force=True) or {}))


@app.route("/api/health", methods=["POST"])
def api_health():
    file = request.files.get("dataset")
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "No valid file"}), 400
    try:
        dp    = _load_dp(file)
        stats = dp.compute_statistics()
        return jsonify(insights_engine.health_score(dp.df, stats))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/static/reports/<path:filename>")
def serve_report(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static", "reports"), filename)


@app.route("/static/charts/<path:filename>")
def serve_chart(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static", "charts"), filename)


if __name__ == "__main__":
    print(f"Python {sys.version}")
    app.run(debug=True, port=5000)
