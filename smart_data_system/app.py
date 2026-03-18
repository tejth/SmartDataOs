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
from modules.preprocessor      import DataPreprocessor
from modules.profiler          import DataProfiler
from modules.filter_engine     import SmartFilterEngine
from modules.merger            import DatasetMerger
from modules.heatmap_engine    import CorrelationHeatmapEngine

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER      = os.path.join(BASE_DIR, "data", "uploads")
ALLOWED_EXTENSIONS = {"csv", "json"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "static", "reports"), exist_ok=True)

validator       = UserFormValidator()
insights_engine = InsightsEngine()
comp_engine     = ComparisonEngine()
preprocessor    = DataPreprocessor()
profiler        = DataProfiler()
filter_engine   = SmartFilterEngine()
merger          = DatasetMerger()
heatmap_engine  = CorrelationHeatmapEngine()


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




# ══════════════════════════════════════════════════════════════════════════════
# PREPROCESSING ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/preprocess", methods=["GET", "POST"])
def preprocess():
    if request.method == "GET":
        return render_template("preprocess.html")

    file = request.files.get("dataset")
    if not file or not file.filename or not allowed_file(file.filename):
        return render_template("preprocess.html",
                               error="Please upload a valid CSV or JSON file.")
    try:
        dp      = _load_dp(file)
        report  = preprocessor.fit(dp.df)
        preview = dp.df.head(5).to_dict("records")
        cols    = list(dp.df.columns)
        return render_template("preprocess.html",
                               report=report, preview=preview,
                               cols=cols, dataset_name=dp.name)
    except Exception as e:
        import traceback; traceback.print_exc()
        return render_template("preprocess.html", error=str(e))


@app.route("/preprocess/transform", methods=["POST"])
def preprocess_transform():
    file = request.files.get("dataset")
    if not file or not file.filename or not allowed_file(file.filename):
        return render_template("preprocess.html",
                               error="Please re-upload the dataset.")
    options = {
        "drop_duplicates": request.form.get("drop_duplicates") == "on",
        "fill_missing":    request.form.get("fill_missing") or None,
        "remove_outliers": request.form.get("remove_outliers") == "on",
        "drop_cols":       request.form.get("drop_cols", ""),
        "scale":           request.form.get("scale") or None,
        "scale_cols":      request.form.get("scale_cols", ""),
    }
    try:
        dp = _load_dp(file)
        df = dp.df
        fit_report          = preprocessor.fit(df)
        cleaned_df, log     = preprocessor.transform(df, options)
        preview_before      = df.head(5).to_dict("records")
        preview_after       = cleaned_df.head(5).to_dict("records")
        cols_before         = list(df.columns)
        cols_after          = list(cleaned_df.columns)

        # Save cleaned CSV to uploads folder
        clean_name = f"cleaned_{dp.name}.csv"
        clean_path = os.path.join(BASE_DIR, "data", "uploads", clean_name)
        os.makedirs(os.path.dirname(clean_path), exist_ok=True)
        with open(clean_path, "wb") as f:
            f.write(preprocessor.to_csv_bytes(cleaned_df))

        return render_template("preprocess.html",
                               report=fit_report,
                               change_log=log,
                               preview_before=preview_before,
                               preview_after=preview_after,
                               cols_before=cols_before,
                               cols_after=cols_after,
                               dataset_name=dp.name,
                               cleaned_name=clean_name,
                               options=options,
                               transformed=True)
    except Exception as e:
        import traceback; traceback.print_exc()
        return render_template("preprocess.html", error=str(e))


@app.route("/preprocess/download/<filename>")
def download_cleaned(filename):
    from flask import send_file
    safe = secure_filename(filename)
    path = os.path.join(BASE_DIR, "data", "uploads", safe)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True,
                     download_name=safe, mimetype="text/csv")



# ══════════════════════════════════════════════════════════════════════════════
# FEATURE: DATA PROFILER
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "GET":
        return render_template("profile.html")
    file = request.files.get("dataset")
    if not file or not file.filename or not allowed_file(file.filename):
        return render_template("profile.html", error="Please upload a valid CSV or JSON file.")
    try:
        dp     = _load_dp(file)
        result = profiler.profile(dp.df)
        return render_template("profile.html",
                               result=result, dataset_name=dp.name,
                               rows=len(dp.df), cols=len(dp.df.columns))
    except Exception as e:
        import traceback; traceback.print_exc()
        return render_template("profile.html", error=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE: SMART FILTER & SEARCH
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/filter", methods=["GET", "POST"])
def filter_data():
    if request.method == "GET":
        return render_template("filter.html")

    file = request.files.get("dataset")
    if not file or not file.filename or not allowed_file(file.filename):
        return render_template("filter.html", error="Please upload a valid CSV or JSON file.")

    try:
        dp = _load_dp(file)
        df = dp.df

        # Parse filters from form
        filter_cols = request.form.getlist("filter_col")
        filter_ops  = request.form.getlist("filter_op")
        filter_vals = request.form.getlist("filter_val")
        filters = [{"col": c, "op": o, "val": v}
                   for c, o, v in zip(filter_cols, filter_ops, filter_vals)
                   if c and o]

        search   = request.form.get("search", "").strip()
        sort_col = request.form.get("sort_col", "").strip()
        sort_dir = request.form.get("sort_dir", "asc").strip()

        filtered = filter_engine.apply_filters(df, filters, search, sort_col, sort_dir)

        # Save filtered CSV
        fname = f"filtered_{dp.name}.csv"
        fpath = os.path.join(BASE_DIR, "data", "uploads", fname)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, "wb") as f:
            f.write(filter_engine.to_csv_bytes(filtered))

        preview = filtered.head(50).to_dict("records")
        cols    = list(df.columns)

        return render_template("filter.html",
                               preview=preview, cols=cols,
                               dataset_name=dp.name,
                               total_rows=len(df),
                               filtered_rows=len(filtered),
                               filters=filters,
                               search=search,
                               sort_col=sort_col,
                               sort_dir=sort_dir,
                               filtered_name=fname,
                               operators=filter_engine.OPERATORS,
                               has_results=True)
    except Exception as e:
        import traceback; traceback.print_exc()
        return render_template("filter.html", error=str(e))


@app.route("/filter/download/<filename>")
def download_filtered(filename):
    from flask import send_file
    safe = secure_filename(filename)
    path = os.path.join(BASE_DIR, "data", "uploads", safe)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True, download_name=safe, mimetype="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE: DATASET MERGER
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/merge", methods=["GET", "POST"])
def merge_datasets():
    if request.method == "GET":
        return render_template("merge.html")

    fa = request.files.get("dataset_a")
    fb = request.files.get("dataset_b")

    if not fa or not fa.filename or not allowed_file(fa.filename):
        return render_template("merge.html", error="Please upload Dataset A.")
    if not fb or not fb.filename or not allowed_file(fb.filename):
        return render_template("merge.html", error="Please upload Dataset B.")

    try:
        dp_a = _load_dp(fa)
        dp_b = _load_dp(fb)

        # If just scanning for common columns
        if request.form.get("scan_only") == "1":
            common = merger.common_columns(dp_a.df, dp_b.df)
            return render_template("merge.html",
                                   name_a=dp_a.name, name_b=dp_b.name,
                                   cols_a=list(dp_a.df.columns),
                                   cols_b=list(dp_b.df.columns),
                                   common=common,
                                   rows_a=len(dp_a.df), rows_b=len(dp_b.df),
                                   join_types=merger.JOIN_TYPES,
                                   scanned=True)

        key = request.form.get("join_key", "").strip()
        how = request.form.get("join_type", "inner").strip()

        merged_df, summary = merger.merge(dp_a.df, dp_b.df, key, how)
        preview = merged_df.head(10).to_dict("records")
        merged_cols = list(merged_df.columns)

        fname = f"merged_{dp_a.name}_{dp_b.name}.csv"
        fpath = os.path.join(BASE_DIR, "data", "uploads", fname)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, "wb") as f:
            f.write(merger.to_csv_bytes(merged_df))

        return render_template("merge.html",
                               name_a=dp_a.name, name_b=dp_b.name,
                               summary=summary,
                               preview=preview,
                               merged_cols=merged_cols,
                               merged_name=fname,
                               join_types=merger.JOIN_TYPES,
                               merged=True)
    except Exception as e:
        import traceback; traceback.print_exc()
        return render_template("merge.html", error=str(e))


@app.route("/merge/download/<filename>")
def download_merged(filename):
    from flask import send_file
    safe = secure_filename(filename)
    path = os.path.join(BASE_DIR, "data", "uploads", safe)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True, download_name=safe, mimetype="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE: CORRELATION HEATMAP
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/heatmap", methods=["GET", "POST"])
def heatmap():
    if request.method == "GET":
        return render_template("heatmap.html")
    file = request.files.get("dataset")
    if not file or not file.filename or not allowed_file(file.filename):
        return render_template("heatmap.html", error="Please upload a valid CSV or JSON file.")
    try:
        dp     = _load_dp(file)
        result = heatmap_engine.generate(dp.df, dataset_name=dp.name)
        if result.get("error"):
            return render_template("heatmap.html", error=result["error"])
        return render_template("heatmap.html",
                               result=result, dataset_name=dp.name,
                               rows=len(dp.df))
    except Exception as e:
        import traceback; traceback.print_exc()
        return render_template("heatmap.html", error=str(e))

if __name__ == "__main__":
    print(f"Python {sys.version}")
    app.run(debug=True, port=5000)
