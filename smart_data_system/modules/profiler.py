"""
modules/profiler.py
-------------------
Deep Data Profiling Engine — generates a full per-column profile.

Features:
  - Count, missing, unique, dtype for every column
  - Numeric: mean, std, min, max, skewness, kurtosis, percentiles
  - Categorical: top-10 value counts, mode, cardinality
  - Per-column histogram / bar chart saved as PNG

Concepts used:
  - Abstract Base Class + @abstractmethod
  - Multiple Inheritance (SerializableMixin, LoggableMixin, ReprMixin)
  - @log_call + @timer decorators
  - Generator (profile_stream — yields column profiles lazily)
  - NumPy: skew/kurtosis calculations
  - Pandas: value_counts, describe
  - Matplotlib: per-column charts
"""

import os
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from abc import ABC, abstractmethod

from utils.mixins     import SerializableMixin, LoggableMixin, ReprMixin
from utils.decorators import log_call, timer

CHARTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "charts"))
os.makedirs(CHARTS_DIR, exist_ok=True)


class BaseProfiler(ABC):
    @abstractmethod
    def profile(self, df: pd.DataFrame) -> dict:
        ...


class DataProfiler(BaseProfiler, SerializableMixin, LoggableMixin, ReprMixin):
    """
    Generates a comprehensive per-column profile for any DataFrame.
    """

    def __init__(self):
        LoggableMixin.__init__(self)

    # ── Generator: yields column profiles one at a time ───────────────────────
    def profile_stream(self, df: pd.DataFrame):
        """Generator — yields one column profile dict per iteration (lazy)."""
        for col in df.columns:
            yield self._profile_column(col, df[col])

    def _profile_column(self, col: str, series: pd.Series) -> dict:
        """Build a full profile dict for a single column."""
        dtype     = str(series.dtype)
        count     = int(series.count())
        missing   = int(series.isnull().sum())
        missing_p = round(missing / len(series) * 100, 1)
        unique    = int(series.nunique())
        is_num    = pd.api.types.is_numeric_dtype(series)

        p = {
            "col":       col,
            "dtype":     dtype,
            "count":     count,
            "missing":   missing,
            "missing_p": missing_p,
            "unique":    unique,
            "is_num":    is_num,
        }

        if is_num:
            vals = series.dropna().values.astype(float)
            n = len(vals)
            if n > 0:
                mean  = float(np.mean(vals))
                std   = float(np.std(vals))
                # Skewness (Fisher)
                skew = float((np.sum(((vals - mean) / std) ** 3) * n /
                              ((n-1)*(n-2))) if (std > 0 and n > 2) else 0)
                # Kurtosis (excess)
                kurt = float((n*(n+1)/((n-1)*(n-2)*(n-3)) *
                              np.sum(((vals-mean)/std)**4) -
                              3*(n-1)**2/((n-2)*(n-3))) if (std > 0 and n > 3) else 0)
                p.update({
                    "mean":    round(mean, 4),
                    "median":  round(float(np.median(vals)), 4),
                    "std":     round(std, 4),
                    "min":     round(float(vals.min()), 4),
                    "max":     round(float(vals.max()), 4),
                    "q25":     round(float(np.percentile(vals, 25)), 4),
                    "q75":     round(float(np.percentile(vals, 75)), 4),
                    "skew":    round(skew, 4),
                    "kurt":    round(kurt, 4),
                    "skew_label": ("Right-skewed" if skew > 0.5
                                   else "Left-skewed" if skew < -0.5
                                   else "Normal"),
                })
        else:
            vc = series.value_counts().head(8)
            p.update({
                "top_values": [{"val": str(k), "count": int(v),
                                "pct": round(int(v)/len(series)*100, 1)}
                               for k, v in vc.items()],
                "mode": str(series.mode()[0]) if not series.mode().empty else "—",
            })
        return p

    @log_call
    @timer
    def profile(self, df: pd.DataFrame) -> dict:
        """Build full profile for all columns and generate charts."""
        columns  = list(self.profile_stream(df))   # uses generator
        charts   = self._generate_profile_charts(df, columns[:6])  # top 6 numeric
        overview = {
            "rows":         len(df),
            "cols":         len(df.columns),
            "numeric_cols": int(df.select_dtypes(include=[np.number]).shape[1]),
            "text_cols":    int(df.select_dtypes(exclude=[np.number]).shape[1]),
            "total_missing":int(df.isnull().sum().sum()),
            "total_dupes":  int(df.duplicated().sum()),
            "memory_kb":    round(df.memory_usage(deep=True).sum() / 1024, 1),
        }
        self.log_event(f"profile() complete — {len(columns)} columns profiled")
        return {"overview": overview, "columns": columns, "charts": charts}

    def _generate_profile_charts(self, df: pd.DataFrame, col_profiles: list) -> list:
        """Generate a small histogram/bar chart for each column profile."""
        charts = []
        for p in col_profiles:
            col = p["col"]
            if col not in df.columns:
                continue
            try:
                series = df[col].dropna()
                fig, ax = plt.subplots(figsize=(4, 2.8), facecolor="#0F172A")
                ax.set_facecolor("#0F172A")

                if p["is_num"]:
                    vals = series.values.astype(float)
                    n_bins = min(20, max(5, int(len(vals)**0.5)))
                    counts, bins, patches = ax.hist(vals, bins=n_bins, edgecolor="#1E3A5F", lw=0.5)
                    norm = mcolors.Normalize(vmin=counts.min(), vmax=counts.max())
                    for patch, c in zip(patches, counts):
                        patch.set_facecolor(plt.cm.Blues(0.35 + 0.65*norm(c)))
                    ax.axvline(p["mean"], color="#60A5FA", lw=1.2, linestyle="--", alpha=0.8)
                    ax.set_title(f"{col}", color="#93C5FD", fontsize=8, fontweight="bold")
                else:
                    vc = series.value_counts().head(6)
                    bars = ax.barh(range(len(vc)), vc.values,
                                   color=["#3B82F6","#60A5FA","#93C5FD","#1D4ED8","#2563EB","#1E3A5F"][:len(vc)])
                    ax.set_yticks(range(len(vc)))
                    ax.set_yticklabels([str(v)[:12] for v in vc.index],
                                        color="#94A3B8", fontsize=7)
                    ax.set_title(f"{col}", color="#93C5FD", fontsize=8, fontweight="bold")

                ax.tick_params(colors="#475569", labelsize=6)
                for spine in ax.spines.values():
                    spine.set_color("#1E3A5F")
                fig.tight_layout(pad=0.5)
                fname = f"profile_{col}.png"
                fig.savefig(os.path.join(CHARTS_DIR, fname), dpi=90,
                            bbox_inches="tight", facecolor="#0F172A")
                plt.close(fig)
                charts.append({"col": col, "path": f"charts/{fname}"})
            except Exception:
                plt.close("all")
        return charts
