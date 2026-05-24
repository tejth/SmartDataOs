"""
modules/comparison_engine.py
----------------------------
🔁 Dataset Comparison Engine — Upload two CSVs and get a side-by-side
statistical diff with an overlap/divergence chart.

Unique Feature #2:
  - Column-by-column statistical comparison
  - Detects which columns appear in one dataset but not the other
  - Computes % change in mean, std, and range between two datasets
  - Generates a comparison radar/bar chart
  - Returns a structured diff report

Concepts used:
  - Abstract class → concrete ComparisonEngine
  - Operator overloading (__sub__ to compute dataset diff)
  - Mixin inheritance
  - numpy for stats
  - matplotlib for comparison chart
"""

import os
import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod

from utils.decorators import timer, log_call
from utils.mixins import SerializableMixin, ReprMixin

CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)


class BaseComparator(ABC):
    @abstractmethod
    def compare(self, df_a: pd.DataFrame, df_b: pd.DataFrame, name_a: str, name_b: str) -> dict: ...


class ComparisonEngine(BaseComparator, SerializableMixin, ReprMixin):
    """
    Compares two Pandas DataFrames and returns a detailed diff report.

    Operator overloading:  engine_a - engine_b  →  diff dict
    (here implemented as __sub__ on a wrapper DatasetSnapshot)
    """

    BLUE_A = "#3B82F6"    # Dataset A colour
    BLUE_B = "#60A5FA"    # Dataset B colourr

    @log_call
    @timer
    def compare(self, df_a: pd.DataFrame, df_b: pd.DataFrame,
                name_a: str = "Dataset A", name_b: str = "Dataset B") -> dict:
        """
        Full comparison: shape, shared columns, per-column stats diff,
        overlap analysis, and comparison chart.
        """
        shared_cols = [c for c in df_a.columns if c in df_b.columns]
        only_in_a   = [c for c in df_a.columns if c not in df_b.columns]
        only_in_b   = [c for c in df_b.columns if c not in df_a.columns]

        # Numeric shared columns
        num_shared = [
            c for c in shared_cols
            if pd.api.types.is_numeric_dtype(df_a[c]) and pd.api.types.is_numeric_dtype(df_b[c])
        ]

        col_diffs = {}
        for col in num_shared:
            a_vals = df_a[col].dropna().values.astype(float)
            b_vals = df_b[col].dropna().values.astype(float)

            def pct_change(a, b):
                return round((b - a) / abs(a) * 100, 1) if a != 0 else None

            a_mean, b_mean = float(np.mean(a_vals)), float(np.mean(b_vals))
            a_std,  b_std  = float(np.std(a_vals)),  float(np.std(b_vals))
            a_min,  b_min  = float(np.min(a_vals)),  float(np.min(b_vals))
            a_max,  b_max  = float(np.max(a_vals)),  float(np.max(b_vals))

            col_diffs[col] = {
                name_a: {"mean": round(a_mean,3), "std": round(a_std,3),
                         "min":  round(a_min,3),  "max": round(a_max,3), "count": len(a_vals)},
                name_b: {"mean": round(b_mean,3), "std": round(b_std,3),
                         "min":  round(b_min,3),  "max": round(b_max,3), "count": len(b_vals)},
                "mean_change_pct": pct_change(a_mean, b_mean),
                "std_change_pct":  pct_change(a_std,  b_std),
                "verdict": self._verdict(a_mean, b_mean, a_std, b_std),
            }

        chart_path = self._generate_comparison_chart(col_diffs, name_a, name_b)

        return {
            "name_a": name_a,
            "name_b": name_b,
            "shape_a": list(df_a.shape),
            "shape_b": list(df_b.shape),
            "shared_columns": shared_cols,
            "only_in_a": only_in_a,
            "only_in_b": only_in_b,
            "numeric_compared": num_shared,
            "column_diffs": col_diffs,
            "chart_path": chart_path,
            "similarity_score": self._similarity_score(col_diffs, df_a, df_b),
        }

    def _verdict(self, a_mean, b_mean, a_std, b_std) -> str:
        """Plain-English verdict for a single column comparison."""
        mean_diff_pct = abs(b_mean - a_mean) / abs(a_mean) * 100 if a_mean != 0 else 0
        if mean_diff_pct < 5 and abs(b_std - a_std) / max(a_std, 0.001) < 0.1:
            return "Nearly identical distributions"
        elif mean_diff_pct < 20:
            direction = "higher" if b_mean > a_mean else "lower"
            return f"B has slightly {direction} mean (+{mean_diff_pct:.1f}%)"
        else:
            direction = "much higher" if b_mean > a_mean else "much lower"
            return f"B is {direction} mean ({mean_diff_pct:.1f}% shift)"

    def _similarity_score(self, col_diffs: dict, df_a, df_b) -> int:
        """0–100 similarity score between the two datasets."""
        if not col_diffs:
            return 0
        scores = []
        for col, d in col_diffs.items():
            keys = list(d.keys())
            na, nb = keys[0], keys[1]
            ma, mb = d[na]["mean"], d[nb]["mean"]
            pct = abs(mb - ma) / max(abs(ma), 0.001) * 100
            scores.append(max(0, 100 - pct))
        # Column overlap bonus
        col_overlap = len(col_diffs) / max(len(df_a.columns), len(df_b.columns), 1)
        base = sum(scores) / len(scores)
        return min(100, int(base * col_overlap + col_overlap * 20))

    def _generate_comparison_chart(self, col_diffs: dict, name_a: str, name_b: str) -> str:
        """Grouped bar chart comparing means of shared numeric columns."""
        if not col_diffs:
            return ""

        cols  = list(col_diffs.keys())[:8]
        means_a = [col_diffs[c][name_a]["mean"] for c in cols]
        means_b = [col_diffs[c][name_b]["mean"] for c in cols]

        x     = np.arange(len(cols))
        width = 0.38

        fig, ax = plt.subplots(figsize=(max(8, len(cols)*1.4), 5), facecolor="#0F172A")
        ax.set_facecolor("#0F172A")

        bars_a = ax.bar(x - width/2, means_a, width, label=name_a,
                        color=self.BLUE_A, alpha=0.9, edgecolor="#1E3A5F")
        bars_b = ax.bar(x + width/2, means_b, width, label=name_b,
                        color=self.BLUE_B, alpha=0.9, edgecolor="#1E3A5F")

        ax.set_xticks(x)
        ax.set_xticklabels(cols, color="#94A3B8", fontsize=9, rotation=20, ha="right")
        ax.tick_params(colors="#94A3B8")
        ax.spines[:].set_color("#1E3A5F")
        ax.set_title("Dataset Comparison — Column Means", color="#60A5FA",
                     fontsize=13, fontweight="bold", pad=12)
        ax.legend(facecolor="#1E293B", edgecolor="#1E3A5F", labelcolor="#94A3B8", fontsize=9)

        fig.tight_layout()
        path = os.path.join(CHARTS_DIR, "comparison_chart.png")
        fig.savefig(path, dpi=120, bbox_inches="tight", facecolor="#0F172A")
        plt.close(fig)
        return "charts/comparison_chart.png"


# ── DatasetSnapshot with __sub__ operator overloading ─────────────────────────
class DatasetSnapshot(SerializableMixin, ReprMixin):
    """
    Wraps a DataFrame so two snapshots can be 'subtracted' to get a diff.

    snapshot_a - snapshot_b  →  comparison dict
    Concept: Operator overloading (__sub__)
    """

    def __init__(self, df: pd.DataFrame, name: str):
        self.df   = df
        self.name = name
        self._engine = ComparisonEngine()

    def __sub__(self, other: "DatasetSnapshot") -> dict:
        if not isinstance(other, DatasetSnapshot):
            return NotImplemented
        return self._engine.compare(self.df, other.df, self.name, other.name)

    def __repr__(self):
        return f"DatasetSnapshot(name={self.name!r}, shape={self.df.shape})"
