"""
modules/insights_engine.py
--------------------------
🧠 AI Data Analyst — Automatically generates human-readable English insights
from statistical analysis of a dataset.

Unique Feature #1:
  Scans statistics and produces intelligent observations like:
    - "salary has extreme right skew — a few very high earners pull the mean up"
    - "age and experience are strongly correlated (r=0.91)"
    - "score has 3 outliers above the upper fence (Q3 + 1.5×IQR)"
    - "Potential data quality issue: 'phone' column is 18% missing"

Concepts used:
  - Advanced OOP (abstract class → concrete InsightsEngine)
  - Generator (yields insights one at a time)
  - Closures (threshold factory)
  - numpy for statistical calculations
  - re for pattern detection in column names
"""

import re
import math
import numpy as np
from abc import ABC, abstractmethod
from utils.decorators import timer, log_call
from utils.generators import stats_stream


# ── Threshold factory (closure) ───────────────────────────────────────────────
def make_threshold_checker(low: float, high: float):
    """
    Closure factory: returns a function that checks if a value is
    outside [low, high].

    Concept: Closure — the returned lambda captures low/high from
    the enclosing scope of make_threshold_checker.
    """
    def check(value: float) -> str:
        if value < low:  return "low"
        if value > high: return "high"
        return "normal"
    return check


# ── Abstract base ─────────────────────────────────────────────────────────────
class BaseInsightsEngine(ABC):
    @abstractmethod
    def analyse(self, df, stats: dict) -> list: ...

    @abstractmethod
    def health_score(self, df, stats: dict) -> dict: ...


# ── Concrete engine ───────────────────────────────────────────────────────────
class InsightsEngine(BaseInsightsEngine):
    """
    Generates plain-English insights from dataset statistics.
    Uses a generator internally to yield findings lazily.
    """

    # Store as module-level refs to avoid `self` being passed as first arg
    _SKEW_CHECK = staticmethod(make_threshold_checker(-0.5, 0.5))
    _CV_CHECK   = staticmethod(make_threshold_checker(0,    0.3))

    @log_call
    @timer
    def analyse(self, df, stats: dict) -> list:
        """
        Main entry point. Returns a list of insight dicts:
          {type, icon, title, detail, severity}
        """
        insights = list(self._insight_generator(df, stats))
        return insights

    def _insight_generator(self, df, stats: dict):
        """
        Generator that yields insights one at a time.
        Covers: distribution shape, outliers, correlations,
                missing data, duplicates, data types.
        """
        import pandas as pd

        col_stats  = stats.get("column_stats", {})
        num_cols   = stats.get("numeric_columns", [])
        total_rows = stats["shape"][0] if stats.get("shape") else 1

        # ── 1. Dataset overview ───────────────────────────────────────────────
        yield {
            "type": "overview", "icon": "📋",
            "title": f"Dataset has {total_rows:,} rows × {stats['shape'][1]} columns",
            "detail": f"{len(num_cols)} numeric column(s): {', '.join(num_cols[:5])}",
            "severity": "info",
        }

        # ── 2. Missing value warnings ─────────────────────────────────────────
        for col in df.columns:
            missing = int(df[col].isnull().sum())
            pct = round(missing / total_rows * 100, 1) if total_rows else 0
            if pct >= 30:
                yield {"type": "quality", "icon": "🚨",
                       "title": f"Critical: '{col}' is {pct}% missing",
                       "detail": f"{missing} of {total_rows} values are NaN — consider dropping this column.",
                       "severity": "critical"}
            elif pct >= 5:
                yield {"type": "quality", "icon": "⚠️",
                       "title": f"'{col}' has {pct}% missing values",
                       "detail": f"Imputation (mean/median/mode) recommended before modelling.",
                       "severity": "warning"}

        # ── 3. Duplicate rows ──────────────────────────────────────────────────
        dups = int(df.duplicated().sum())
        if dups > 0:
            yield {"type": "quality", "icon": "🔁",
                   "title": f"{dups} duplicate row(s) detected",
                   "detail": f"{round(dups/total_rows*100,1)}% of the dataset is duplicated.",
                   "severity": "warning"}

        # ── 4. Per-column analysis ─────────────────────────────────────────────
        for col in num_cols:
            s   = col_stats.get(col, {})
            arr = df[col].dropna().values.astype(float)
            if len(arr) < 3:
                continue

            mean, std, mn, mx = s["mean"], s["std"], s["min"], s["max"]
            q25, q75 = s["q25"], s["q75"]
            iqr = q75 - q25

            # ── Skewness ──────────────────────────────────────────────────────
            try:
                n   = len(arr)
                skew = (n / ((n-1)*(n-2))) * np.sum(((arr - mean)/std)**3) if std > 0 else 0
            except:
                skew = 0

            skew_check = self._SKEW_CHECK(skew)
            if skew_check == "high":
                yield {"type": "distribution", "icon": "📈",
                       "title": f"'{col}' is right-skewed (skew={skew:.2f})",
                       "detail": "A few very large values pull the mean rightward. Median is a better central measure here.",
                       "severity": "insight"}
            elif skew_check == "low":
                yield {"type": "distribution", "icon": "📉",
                       "title": f"'{col}' is left-skewed (skew={skew:.2f})",
                       "detail": "A few very small values pull the mean leftward. Consider log or square-root transformation.",
                       "severity": "insight"}
            else:
                yield {"type": "distribution", "icon": "✅",
                       "title": f"'{col}' is approximately symmetric (skew={skew:.2f})",
                       "detail": "Mean and median are close — distribution is fairly normal.",
                       "severity": "good"}

            # ── Outliers via IQR fence ────────────────────────────────────────
            if iqr > 0:
                lower_fence = q25 - 1.5 * iqr
                upper_fence = q75 + 1.5 * iqr
                outliers = arr[(arr < lower_fence) | (arr > upper_fence)]
                if len(outliers) > 0:
                    yield {"type": "outlier", "icon": "🎯",
                           "title": f"'{col}' has {len(outliers)} outlier(s)",
                           "detail": f"Values outside [{lower_fence:.2f}, {upper_fence:.2f}] (IQR fence). "
                                     f"Outlier range: {outliers.min():.2f} – {outliers.max():.2f}.",
                           "severity": "warning" if len(outliers) > 3 else "insight"}

            # ── Coefficient of variation (spread) ─────────────────────────────
            cv = (std / abs(mean)) if mean != 0 else 0
            cv_state = self._CV_CHECK(cv)
            if cv_state == "high":
                yield {"type": "spread", "icon": "📡",
                       "title": f"'{col}' is highly variable (CV={cv:.2f})",
                       "detail": f"Std dev is {round(cv*100)}% of the mean — wide spread in data.",
                       "severity": "insight"}

            # ── Range anomaly: column that is all the same value ──────────────
            if mn == mx:
                yield {"type": "quality", "icon": "🔴",
                       "title": f"'{col}' has zero variance — all values are {mn}",
                       "detail": "This column carries no information and should likely be dropped.",
                       "severity": "critical"}

        # ── 5. Correlations ────────────────────────────────────────────────────
        if len(num_cols) >= 2:
            try:
                corr_matrix = df[num_cols].corr()
                for i in range(len(num_cols)):
                    for j in range(i+1, len(num_cols)):
                        r = corr_matrix.iloc[i, j]
                        if abs(r) >= 0.85:
                            label = "perfectly" if abs(r) >= 0.97 else "strongly"
                            direction = "positively" if r > 0 else "negatively"
                            yield {"type": "correlation", "icon": "🔗",
                                   "title": f"'{num_cols[i]}' & '{num_cols[j]}' are {label} {direction} correlated",
                                   "detail": f"Pearson r = {r:.3f}. "
                                             + ("Watch for multicollinearity if using these in a model together."
                                                if abs(r) >= 0.9 else ""),
                                   "severity": "insight"}
                        elif abs(r) >= 0.5:
                            yield {"type": "correlation", "icon": "〰️",
                                   "title": f"Moderate correlation: '{num_cols[i]}' ↔ '{num_cols[j]}' (r={r:.2f})",
                                   "detail": "Some linear relationship exists between these columns.",
                                   "severity": "info"}
            except Exception:
                pass

        # ── 6. Column name pattern hints ──────────────────────────────────────
        id_pattern = re.compile(r'\b(id|index|key|uuid|code)\b', re.IGNORECASE)
        date_pattern = re.compile(r'\b(date|time|year|month|day|timestamp)\b', re.IGNORECASE)
        for col in df.columns:
            if id_pattern.search(col):
                yield {"type": "hint", "icon": "🔑",
                       "title": f"'{col}' looks like an identifier column",
                       "detail": "ID-type columns usually shouldn't be used as features in a model.",
                       "severity": "info"}
            elif date_pattern.search(col):
                yield {"type": "hint", "icon": "📅",
                       "title": f"'{col}' may contain date/time data",
                       "detail": "Consider parsing it with pd.to_datetime() for time-series analysis.",
                       "severity": "info"}

    @log_call
    def health_score(self, df, stats: dict) -> dict:
        """
        Grades the dataset A–F based on:
          - Completeness  (missing values)
          - Uniqueness    (duplicate rows)
          - Consistency   (zero-variance columns)
          - Size          (row count)
          - Balance       (column type diversity)

        Returns {score: int, grade: str, breakdown: dict, badge_color: str}
        """
        total_rows = stats["shape"][0] if stats.get("shape") else 1
        total_cols = stats["shape"][1] if stats.get("shape") else 1
        num_cols   = stats.get("numeric_columns", [])

        scores = {}

        # Completeness (0–30)
        missing_pct = (stats.get("missing_values", 0) / max(total_rows * total_cols, 1)) * 100
        scores["completeness"] = max(0, 30 - int(missing_pct * 1.5))

        # Uniqueness (0–25)
        dup_pct = (int(df.duplicated().sum()) / max(total_rows, 1)) * 100
        scores["uniqueness"] = max(0, 25 - int(dup_pct * 2))

        # Size adequacy (0–20)
        if total_rows >= 1000:   scores["size"] = 20
        elif total_rows >= 200:  scores["size"] = 15
        elif total_rows >= 50:   scores["size"] = 10
        elif total_rows >= 10:   scores["size"] = 5
        else:                    scores["size"] = 2

        # Consistency — penalise zero-variance columns (0–15)
        zero_var = sum(
            1 for c in num_cols
            if stats["column_stats"].get(c, {}).get("std", 1) == 0
        )
        scores["consistency"] = max(0, 15 - zero_var * 5)

        # Column diversity (0–10)
        non_num = total_cols - len(num_cols)
        scores["diversity"] = 10 if (non_num > 0 and len(num_cols) > 0) else 6

        total = sum(scores.values())

        if   total >= 90: grade, color = "A+", "#22c55e"
        elif total >= 80: grade, color = "A",  "#4ade80"
        elif total >= 70: grade, color = "B",  "#86efac"
        elif total >= 60: grade, color = "C",  "#facc15"
        elif total >= 50: grade, color = "D",  "#fb923c"
        else:             grade, color = "F",  "#f87171"

        return {
            "score": total,
            "grade": grade,
            "badge_color": color,
            "breakdown": {
                "Completeness":  {"score": scores["completeness"],  "max": 30},
                "Uniqueness":    {"score": scores["uniqueness"],    "max": 25},
                "Size":          {"score": scores["size"],          "max": 20},
                "Consistency":   {"score": scores["consistency"],   "max": 15},
                "Diversity":     {"score": scores["diversity"],     "max": 10},
            },
            "summary": f"Dataset scored {total}/100 — Grade {grade}",
        }
