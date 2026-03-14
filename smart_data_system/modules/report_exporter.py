"""
modules/report_exporter.py
--------------------------
📤 Smart Report Exporter — generates a fully self-contained HTML report
with all statistics, insights, health score, and embedded charts.

Unique Feature #3:
  The exported report is a single .html file that can be:
    - Opened in any browser without an internet connection
    - Shared via email
    - Printed to PDF from the browser

Concepts used:
  - os, sys, datetime, math modules
  - json serialization (embed data as JSON inside HTML)
  - Generator (yields report sections lazily)
  - Mixin (SerializableMixin for metadata)
  - base64 encoding to embed chart images directly in the HTML
"""

import os
import sys
import json
import base64
import datetime
import math
from utils.mixins import SerializableMixin
from utils.generators import chunk_dataset
from utils.decorators import timer, log_call

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "reports"))
os.makedirs(REPORTS_DIR, exist_ok=True)


def _encode_image(path: str) -> str:
    """Base64-encode a PNG so it can be embedded in an <img src='data:...'> tag."""
    full = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", path))
    if not os.path.exists(full):
        return ""
    with open(full, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def _section_generator(stats: dict, insights: list, health: dict,
                        chart_paths: list, user: dict):
    """
    Generator that yields HTML section strings lazily.
    Each yield = one fully rendered section of the report.
    """
    # ── Section 1: Header ────────────────────────────────────────────────────
    yield f"""
    <div class="rpt-header">
      <div class="rpt-logo">⬡ SmartData<span>OS</span></div>
      <h1>Dataset Analysis Report</h1>
      <p class="rpt-meta">
        Prepared for: <strong>{user.get('name','—')}</strong> ·
        {user.get('email','—')} ·
        Generated: {datetime.datetime.now().strftime('%d %b %Y, %H:%M')}
      </p>
      <p class="rpt-meta">Python {sys.version.split()[0]} · SmartDataOS Report Engine</p>
    </div>"""

    # ── Section 2: Health Score ───────────────────────────────────────────────
    if health:
        bd = health.get("breakdown", {})
        bars_html = ""
        for name, val in bd.items():
            pct = round(val["score"] / val["max"] * 100)
            bars_html += f"""
            <div class="hb-row">
              <span class="hb-label">{name}</span>
              <div class="hb-track">
                <div class="hb-fill" style="width:{pct}%;background:{health['badge_color']}"></div>
              </div>
              <span class="hb-val">{val['score']}/{val['max']}</span>
            </div>"""
        yield f"""
    <div class="rpt-section">
      <h2>📊 Dataset Health Score</h2>
      <div class="health-row">
        <div class="grade-circle" style="border-color:{health['badge_color']};color:{health['badge_color']}">
          {health['grade']}
        </div>
        <div>
          <div class="grade-score">{health['score']}/100</div>
          <div class="grade-summary">{health['summary']}</div>
        </div>
      </div>
      <div class="health-bars">{bars_html}</div>
    </div>"""

    # ── Section 3: Column Statistics ─────────────────────────────────────────
    col_stats = stats.get("column_stats", {})
    if col_stats:
        rows_html = ""
        for col, s in col_stats.items():
            rows_html += f"""
            <tr>
              <td class="cn">{col}</td>
              <td>{s['count']}</td><td>{s['mean']}</td><td>{s['median']}</td>
              <td>{s['std']}</td><td>{s['min']}</td><td>{s['max']}</td>
            </tr>"""
        yield f"""
    <div class="rpt-section">
      <h2>📈 Statistical Summary</h2>
      <table class="rpt-table">
        <thead><tr>
          <th>Column</th><th>Count</th><th>Mean</th><th>Median</th>
          <th>Std Dev</th><th>Min</th><th>Max</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>"""

    # ── Section 4: AI Insights ────────────────────────────────────────────────
    if insights:
        icons_map = {"critical":"🚨","warning":"⚠️","good":"✅","insight":"💡","info":"ℹ️"}
        items_html = ""
        for ins in insights:
            sev   = ins.get("severity","info")
            items_html += f"""
            <div class="ins-item ins-{sev}">
              <span class="ins-icon">{ins['icon']}</span>
              <div>
                <strong>{ins['title']}</strong>
                <p>{ins['detail']}</p>
              </div>
            </div>"""
        yield f"""
    <div class="rpt-section">
      <h2>🧠 AI Analyst Insights</h2>
      <div class="insights-list">{items_html}</div>
    </div>"""

    # ── Section 5: Charts (base64 embedded) ──────────────────────────────────
    if chart_paths:
        charts_html = ""
        labels = {
            "bar":  "Bar Chart — Column Means",
            "line": "Line Chart — Chunk Means",
            "dist": "Distribution Histogram",
        }
        for path in chart_paths:
            b64 = _encode_image(path)
            if not b64:
                continue
            kind  = next((k for k in labels if k in path), "chart")
            label = labels.get(kind, path)
            charts_html += f"""
            <div class="rpt-chart-wrap">
              <img src="{b64}" alt="{label}" />
              <p class="chart-caption">{label}</p>
            </div>"""
        yield f"""
    <div class="rpt-section">
      <h2>📉 Visualizations</h2>
      <div class="rpt-charts">{charts_html}</div>
    </div>"""

    # ── Section 6: Footer ─────────────────────────────────────────────────────
    yield f"""
    <div class="rpt-footer">
      <p>Generated by SmartDataOS · Advanced Python Project ·
         {datetime.datetime.now().year}</p>
      <p style="margin-top:.3rem;opacity:.6;font-size:.75rem">
        Python {sys.version.split()[0]} ·
        os.name={os.name} · cpu_count={os.cpu_count()} ·
        math.pi={round(math.pi,5)}
      </p>
    </div>"""


@log_call
@timer
def generate_report(user: dict, stats: dict, insights: list,
                    health: dict, chart_paths: list,
                    record_id: str) -> str:
    """
    Assemble and write a self-contained HTML report.
    Returns the relative URL path to the saved report.
    """
    # Collect all sections using the generator
    sections = list(_section_generator(stats, insights, health, chart_paths, user))
    body     = "\n".join(sections)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>SmartDataOS Report — {user.get('name','')}</title>
  <style>
    :root{{--blue:#2563EB;--blue-light:#60A5FA;--bg:#0F172A;--surface:#1E293B;
          --text:#E2E8F0;--muted:#94A3B8;--border:rgba(59,130,246,.2);}}
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);
          color:var(--text);padding:2rem;line-height:1.6}}
    .rpt-header{{text-align:center;padding:2rem;border-bottom:1px solid var(--border);
                 margin-bottom:2rem}}
    .rpt-logo{{font-size:1.4rem;font-weight:800;color:var(--blue-light);margin-bottom:.5rem}}
    .rpt-logo span{{color:var(--blue)}}
    h1{{font-size:1.8rem;margin-bottom:.5rem}}
    .rpt-meta{{color:var(--muted);font-size:.85rem;margin-top:.3rem}}
    .rpt-section{{background:var(--surface);border:1px solid var(--border);
                  border-radius:12px;padding:1.5rem;margin-bottom:1.5rem}}
    .rpt-section h2{{font-size:1.1rem;margin-bottom:1rem;color:var(--blue-light)}}
    .health-row{{display:flex;align-items:center;gap:1.5rem;margin-bottom:1rem}}
    .grade-circle{{width:72px;height:72px;border-radius:50%;border:3px solid;
                   display:flex;align-items:center;justify-content:center;
                   font-size:1.8rem;font-weight:800;flex-shrink:0}}
    .grade-score{{font-size:1.5rem;font-weight:700;color:var(--blue-light)}}
    .grade-summary{{color:var(--muted);font-size:.85rem}}
    .health-bars{{display:flex;flex-direction:column;gap:.5rem;margin-top:.8rem}}
    .hb-row{{display:flex;align-items:center;gap:.8rem}}
    .hb-label{{width:110px;font-size:.8rem;color:var(--muted);flex-shrink:0}}
    .hb-track{{flex:1;height:8px;background:rgba(255,255,255,.07);border-radius:99px;overflow:hidden}}
    .hb-fill{{height:100%;border-radius:99px;transition:width .4s}}
    .hb-val{{font-size:.78rem;color:var(--muted);width:45px;text-align:right}}
    .rpt-table{{width:100%;border-collapse:collapse;font-size:.82rem}}
    .rpt-table th{{background:rgba(30,58,95,.5);color:var(--blue-light);
                   padding:.5rem .8rem;text-align:left;white-space:nowrap}}
    .rpt-table td{{padding:.45rem .8rem;border-bottom:1px solid rgba(59,130,246,.07)}}
    .rpt-table .cn{{color:var(--blue-light);font-weight:600}}
    .insights-list{{display:flex;flex-direction:column;gap:.6rem}}
    .ins-item{{display:flex;gap:.8rem;padding:.7rem;border-radius:8px;
               border:1px solid var(--border);align-items:flex-start}}
    .ins-critical{{border-color:rgba(239,68,68,.4);background:rgba(239,68,68,.05)}}
    .ins-warning{{border-color:rgba(251,146,60,.3);background:rgba(251,146,60,.05)}}
    .ins-good{{border-color:rgba(34,197,94,.3);background:rgba(34,197,94,.05)}}
    .ins-insight{{border-color:rgba(59,130,246,.3);background:rgba(59,130,246,.05)}}
    .ins-info{{border-color:var(--border)}}
    .ins-icon{{font-size:1.2rem;flex-shrink:0}}
    .ins-item strong{{font-size:.88rem;display:block;margin-bottom:.2rem}}
    .ins-item p{{font-size:.8rem;color:var(--muted)}}
    .rpt-charts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}}
    .rpt-chart-wrap img{{width:100%;border-radius:8px;border:1px solid var(--border)}}
    .chart-caption{{font-size:.75rem;color:var(--muted);text-align:center;margin-top:.3rem}}
    .rpt-footer{{text-align:center;padding:1.5rem;color:var(--muted);font-size:.8rem;
                 border-top:1px solid var(--border);margin-top:1rem}}
    @media print{{body{{background:#fff;color:#000}}
      .rpt-section{{border:1px solid #ccc}}}}
  </style>
</head>
<body>
{body}
</body>
</html>"""

    filename    = f"report_{record_id}.html"
    output_path = os.path.join(REPORTS_DIR, filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return f"reports/{filename}"
