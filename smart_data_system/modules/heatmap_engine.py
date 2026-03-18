"""
modules/heatmap_engine.py
-------------------------
Correlation Heatmap Engine — generates a Matplotlib correlation heatmap.

Features:
  - Pearson correlation matrix for all numeric columns
  - Color-coded heatmap (blue=positive, red=negative)
  - Annotated with correlation values
  - Highlights strong correlations (|r| >= 0.7)
  - Returns correlation pairs sorted by strength

Concepts used:
  - Abstract Base Class + @abstractmethod
  - @log_call, @timer decorators
  - SerializableMixin, LoggableMixin, ReprMixin
  - NumPy correlation computation
  - Matplotlib heatmap with annotations
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod

from utils.mixins     import SerializableMixin, LoggableMixin, ReprMixin
from utils.decorators import log_call, timer

CHARTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "charts"))
os.makedirs(CHARTS_DIR, exist_ok=True)


class BaseHeatmapEngine(ABC):
    @abstractmethod
    def generate(self, df: pd.DataFrame) -> dict:
        ...


class CorrelationHeatmapEngine(BaseHeatmapEngine, SerializableMixin, LoggableMixin, ReprMixin):
    """Computes Pearson correlations and generates a heatmap PNG."""

    def __init__(self):
        LoggableMixin.__init__(self)

    @log_call
    @timer
    def generate(self, df: pd.DataFrame, dataset_name: str = "dataset") -> dict:
        """
        Compute correlation matrix, generate heatmap, return analysis.
        """
        numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.shape[1] < 2:
            return {"error": "Need at least 2 numeric columns for correlation."}

        corr = numeric_df.corr(method="pearson")
        cols = list(corr.columns)
        n    = len(cols)

        # Build correlation pairs (upper triangle)
        pairs = []
        for i in range(n):
            for j in range(i+1, n):
                r = round(float(corr.iloc[i, j]), 4)
                pairs.append({
                    "col_a": cols[i],
                    "col_b": cols[j],
                    "r":     r,
                    "abs_r": abs(r),
                    "label": ("Strong positive" if r >= 0.7
                              else "Strong negative" if r <= -0.7
                              else "Moderate" if abs(r) >= 0.4
                              else "Weak"),
                    "color": ("#4ade80" if r >= 0.7
                              else "#f87171" if r <= -0.7
                              else "#fbbf24" if abs(r) >= 0.4
                              else "#94A3B8"),
                })

        pairs.sort(key=lambda x: x["abs_r"], reverse=True)

        # Generate heatmap
        chart_path = self._draw_heatmap(corr, dataset_name)

        result = {
            "cols":       cols,
            "n_cols":     n,
            "pairs":      pairs,
            "strong":     [p for p in pairs if p["abs_r"] >= 0.7],
            "chart_path": chart_path,
            "matrix":     {c: {c2: round(float(corr.loc[c, c2]), 4)
                               for c2 in cols} for c in cols},
        }
        self.log_event(f"generate() — {n} cols, {len(pairs)} pairs, {len(result['strong'])} strong")
        return result

    def _draw_heatmap(self, corr: pd.DataFrame, name: str) -> str:
        """Draw and save the correlation heatmap PNG."""
        n = len(corr)
        fig_size = max(6, n * 0.8)
        fig, ax = plt.subplots(figsize=(fig_size, fig_size * 0.85), facecolor="#0F172A")
        ax.set_facecolor("#0F172A")

        data = corr.values
        cols = list(corr.columns)

        # Custom colormap: red -> white -> blue
        from matplotlib.colors import LinearSegmentedColormap
        cmap = LinearSegmentedColormap.from_list(
            "rw_b",
            ["#EF4444", "#1E293B", "#3B82F6"], N=256
        )

        im = ax.imshow(data, cmap=cmap, vmin=-1, vmax=1, aspect="auto")

        # Annotations
        for i in range(n):
            for j in range(n):
                val = data[i, j]
                color = "#F1F5F9" if abs(val) < 0.5 else ("#0F172A" if abs(val) > 0.85 else "#F1F5F9")
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        color=color, fontsize=max(5, 9 - n//3),
                        fontweight="bold" if abs(val) >= 0.7 else "normal")

        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(cols, rotation=45, ha="right",
                           color="#94A3B8", fontsize=max(6, 9 - n//4))
        ax.set_yticklabels(cols, color="#94A3B8",
                           fontsize=max(6, 9 - n//4))
        ax.set_title("Pearson Correlation Matrix", color="#93C5FD",
                     fontsize=11, fontweight="bold", pad=12)

        cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.04)
        cbar.ax.tick_params(colors="#94A3B8", labelsize=7)

        for spine in ax.spines.values():
            spine.set_color("#1E3A5F")
        ax.tick_params(colors="#475569")
        fig.tight_layout()

        fname = f"heatmap_{name}.png"
        fig.savefig(os.path.join(CHARTS_DIR, fname), dpi=110,
                    bbox_inches="tight", facecolor="#0F172A")
        plt.close(fig)
        return f"charts/{fname}"
