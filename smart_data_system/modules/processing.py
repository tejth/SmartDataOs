"""
modules/processing.py
---------------------
Core dataset processing using Pandas and NumPy.

Concepts covered:
  - Advanced OOP: abstract class → concrete subclass
  - Multiple inheritance with Mixins
  - Operator overloading (__add__ to merge two DataProcessor objects)
  - External libraries: numpy, pandas
  - Decorators: @timer, @log_call applied to processing methods
  - Custom Iterator used during row-level processing
  - Generator used for chunked processing
"""

import io
import os
import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend (server-side)
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from abc import ABC, abstractmethod

from utils.decorators import timer, log_call
from utils.mixins import SerializableMixin, LoggableMixin, ReprMixin
from utils.iterators import DatasetRowIterator
from utils.generators import chunk_dataset, stats_stream

CHARTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "charts"))
os.makedirs(CHARTS_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# Abstract base for all processors
# ══════════════════════════════════════════════════════════════════════════════
class AbstractDataProcessor(ABC):
    """
    Abstract class that defines the processing contract.

    Concept covered: Abstract Classes + @abstractmethod
    """

    @abstractmethod
    def load(self, source) -> None:
        """Load data from a file-like object or filepath."""
        ...

    @abstractmethod
    def compute_statistics(self) -> dict:
        """Return descriptive statistics for the loaded dataset."""
        ...

    @abstractmethod
    def generate_charts(self) -> list:
        """Generate charts and return a list of saved file paths."""
        ...


# ══════════════════════════════════════════════════════════════════════════════
# Concrete processor
# Multiple Inheritance: AbstractDataProcessor + SerializableMixin
#                        + LoggableMixin + ReprMixin
# ══════════════════════════════════════════════════════════════════════════════
class DataProcessor(AbstractDataProcessor, SerializableMixin, LoggableMixin, ReprMixin):
    """
    Loads CSV/JSON datasets, computes statistics, and generates charts.

    Operator overloading:
      processor_a + processor_b  →  merged DataProcessor
    """

    BLUE_PALETTE = ["#1E3A5F", "#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE"]

    def __init__(self, name: str = "dataset"):
        self.name = name
        self.df: pd.DataFrame = pd.DataFrame()
        self.stats: dict = {}
        self.chart_paths: list = []

    # ── load ─────────────────────────────────────────────────────────────────
    @log_call
    @timer
    def load(self, source, filetype: str = "csv") -> None:
        """Load a CSV or JSON file-like object into a Pandas DataFrame."""
        try:
            if filetype == "csv":
                self.df = pd.read_csv(source)
            else:
                self.df = pd.read_json(source)
            self.log_event(f"Loaded {filetype.upper()} – shape {self.df.shape}")
        except Exception as e:
            raise ValueError(f"Failed to load dataset: {e}")

    # ── statistics ────────────────────────────────────────────────────────────
    @log_call
    @timer
    def compute_statistics(self) -> dict:
        """
        Compute descriptive statistics for all numeric columns.

        Uses:
          - numpy for mean, median, std, percentiles
          - Generator (stats_stream) for running stats
          - Custom Iterator (DatasetRowIterator) to walk rows
        """
        if self.df.empty:
            return {}

        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        result = {
            "shape": list(self.df.shape),
            "columns": self.df.columns.tolist(),
            "numeric_columns": numeric_cols,
            "missing_values": int(self.df.isnull().sum().sum()),
            "column_stats": {},
        }

        for col in numeric_cols:
            values = self.df[col].dropna().tolist()
            arr = np.array(values, dtype=float)

            # numpy statistics
            col_stats = {
                "mean":   round(float(np.mean(arr)), 4),
                "median": round(float(np.median(arr)), 4),
                "std":    round(float(np.std(arr)), 4),
                "min":    round(float(np.min(arr)), 4),
                "max":    round(float(np.max(arr)), 4),
                "q25":    round(float(np.percentile(arr, 25)), 4),
                "q75":    round(float(np.percentile(arr, 75)), 4),
                "count":  len(values),
            }

            # generator-based running stats (last entry = final stats)
            running = list(stats_stream(values))
            if running:
                col_stats["running_final"] = running[-1]

            result["column_stats"][col] = col_stats

        # Demonstrate custom iterator: walk rows in batches of 10
        row_iter = DatasetRowIterator(self.df.to_dict("records"), batch_size=10)
        batch_count = sum(1 for _ in row_iter)
        result["row_batches_processed"] = batch_count

        self.stats = result
        self.log_event("Statistics computed")
        return result

    # ── charts ────────────────────────────────────────────────────────────────
    @log_call
    @timer
    def generate_charts(self) -> list:
        """Generate bar chart, line chart, and distribution histograms."""
        if self.df.empty:
            return []

        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            return []

        paths = []
        col = numeric_cols[0]          # use first numeric column for demos
        values = self.df[col].dropna().values

        plt.style.use("dark_background")

        # ── Chart 1 : Bar chart (column means) ───────────────────────────────
        means = {c: float(self.df[c].mean()) for c in numeric_cols[:6]}
        fig, ax = plt.subplots(figsize=(8, 4), facecolor="#0F172A")
        ax.set_facecolor("#0F172A")
        bars = ax.bar(
            means.keys(), means.values(),
            color=self.BLUE_PALETTE[:len(means)], edgecolor="#1E3A5F", linewidth=0.8
        )
        ax.bar_label(bars, fmt="%.2f", color="#93C5FD", fontsize=8, padding=3)
        ax.set_title("Column Means", color="#60A5FA", fontsize=13, fontweight="bold")
        ax.tick_params(colors="#94A3B8")
        ax.spines[:].set_color("#1E3A5F")
        fig.tight_layout()
        p = os.path.join(CHARTS_DIR, f"{self.name}_bar.png")
        fig.savefig(p, dpi=120, bbox_inches="tight", facecolor="#0F172A")
        plt.close(fig)
        paths.append(f"charts/{self.name}_bar.png")

        # ── Chart 2 : Line chart (first numeric column values, chunked) ───────
        chunks = list(chunk_dataset(values.tolist(), chunk_size=max(1, len(values)//20)))
        chunk_means = [float(np.mean(c)) for c in chunks]
        fig, ax = plt.subplots(figsize=(8, 4), facecolor="#0F172A")
        ax.set_facecolor("#0F172A")
        ax.plot(chunk_means, color="#3B82F6", linewidth=2, marker="o",
                markersize=4, markerfacecolor="#60A5FA")
        ax.fill_between(range(len(chunk_means)), chunk_means, alpha=0.15, color="#3B82F6")
        ax.set_title(f"'{col}' – Chunk Means (Line)", color="#60A5FA", fontsize=13, fontweight="bold")
        ax.tick_params(colors="#94A3B8")
        ax.spines[:].set_color("#1E3A5F")
        fig.tight_layout()
        p = os.path.join(CHARTS_DIR, f"{self.name}_line.png")
        fig.savefig(p, dpi=120, bbox_inches="tight", facecolor="#0F172A")
        plt.close(fig)
        paths.append(f"charts/{self.name}_line.png")

        # ── Chart 3 : Distribution histogram ─────────────────────────────────
        fig, ax = plt.subplots(figsize=(8, 4), facecolor="#0F172A")
        ax.set_facecolor("#0F172A")
        n, bins, patches = ax.hist(values, bins=20, edgecolor="#1E3A5F", linewidth=0.6)
        # Colour bars by frequency (gradient blue)
        norm = mcolors.Normalize(vmin=n.min(), vmax=n.max())
        for patch, val in zip(patches, n):
            patch.set_facecolor(plt.cm.Blues(0.3 + 0.7 * norm(val)))
        ax.set_title(f"'{col}' Distribution", color="#60A5FA", fontsize=13, fontweight="bold")
        ax.tick_params(colors="#94A3B8")
        ax.spines[:].set_color("#1E3A5F")
        fig.tight_layout()
        p = os.path.join(CHARTS_DIR, f"{self.name}_dist.png")
        fig.savefig(p, dpi=120, bbox_inches="tight", facecolor="#0F172A")
        plt.close(fig)
        paths.append(f"charts/{self.name}_dist.png")

        self.chart_paths = paths
        self.log_event(f"Generated {len(paths)} charts")
        return paths

    # ── operator overloading : __add__ ────────────────────────────────────────
    def __add__(self, other: "DataProcessor") -> "DataProcessor":
        """
        Merge two DataProcessor objects by concatenating their DataFrames.

        Concept covered: Operator overloading (__add__)
        Allows: merged = processor_a + processor_b
        """
        if not isinstance(other, DataProcessor):
            return NotImplemented
        merged = DataProcessor(name=f"{self.name}+{other.name}")
        merged.df = pd.concat([self.df, other.df], ignore_index=True)
        merged.log_event(f"Merged '{self.name}' and '{other.name}'")
        return merged

    # ── helpers ───────────────────────────────────────────────────────────────
    def get_preview(self, rows: int = 5) -> list:
        """Return the first `rows` rows as a list of dicts."""
        return self.df.head(rows).to_dict("records")

    def get_column_names(self) -> list:
        return self.df.columns.tolist()
