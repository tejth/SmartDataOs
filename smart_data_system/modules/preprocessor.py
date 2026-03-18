"""
modules/preprocessor.py
-----------------------
Data Preprocessing Engine — cleans and transforms datasets.

Concepts demonstrated:
  - Abstract Base Class (ABC) + @abstractmethod
  - Multiple Inheritance (BasePreprocessor + SerializableMixin + LoggableMixin + ReprMixin)
  - @log_call and @timer decorators
  - Generator function (cleaned_row_generator)
  - os, datetime modules
  - NumPy + Pandas operations
"""

import os
import io
import datetime
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

from utils.mixins     import SerializableMixin, LoggableMixin, ReprMixin
from utils.decorators import log_call, timer


class BasePreprocessor(ABC):
    """Abstract contract every preprocessor must follow."""

    @abstractmethod
    def fit(self, df: pd.DataFrame) -> dict:
        """Scan the DataFrame and return an issue report."""
        ...

    @abstractmethod
    def transform(self, df: pd.DataFrame, options: dict) -> tuple:
        """Apply selected preprocessing steps. Returns (cleaned_df, change_log)."""
        ...


class DataPreprocessor(BasePreprocessor, SerializableMixin, LoggableMixin, ReprMixin):
    """
    Full data preprocessing pipeline.
    Inherits: BasePreprocessor · SerializableMixin · LoggableMixin · ReprMixin
    """

    def __init__(self):
        LoggableMixin.__init__(self)
        self.original_shape = None
        self.cleaned_shape  = None
        self.steps_applied  = []

    # ── fit ───────────────────────────────────────────────────────────────────
    @log_call
    @timer
    def fit(self, df: pd.DataFrame) -> dict:
        """Scan the DataFrame for missing values, outliers, duplicates."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        text_cols    = df.select_dtypes(exclude=[np.number]).columns.tolist()

        # Missing values per column
        missing = {}
        for col in df.columns:
            n = int(df[col].isnull().sum())
            if n > 0:
                missing[col] = {
                    "count":     n,
                    "pct":       round(n / len(df) * 100, 1),
                    "dtype":     str(df[col].dtype),
                    "suggested": "mean" if col in numeric_cols else "mode",
                }

        # Outliers per numeric column (IQR method)
        outliers = {}
        for col in numeric_cols:
            q25 = float(df[col].quantile(0.25))
            q75 = float(df[col].quantile(0.75))
            iqr = q75 - q25
            lo, hi = q25 - 1.5 * iqr, q75 + 1.5 * iqr
            n = int(((df[col] < lo) | (df[col] > hi)).sum())
            if n > 0:
                outliers[col] = {
                    "count":       n,
                    "pct":         round(n / len(df) * 100, 1),
                    "lower_fence": round(lo, 2),
                    "upper_fence": round(hi, 2),
                }

        # Column info
        col_info = {}
        for col in df.columns:
            col_info[col] = {
                "dtype":   str(df[col].dtype),
                "missing": int(df[col].isnull().sum()),
                "unique":  int(df[col].nunique()),
                "numeric": col in numeric_cols,
            }

        report = {
            "shape":        list(df.shape),
            "numeric_cols": numeric_cols,
            "text_cols":    text_cols,
            "missing":      missing,
            "outliers":     outliers,
            "duplicates":   int(df.duplicated().sum()),
            "col_info":     col_info,
            "total_issues": len(missing) + (1 if df.duplicated().sum() else 0) + len(outliers),
        }
        self.log_event(f"fit() — {report['total_issues']} issues found in {df.shape}")
        return report

    # ── transform ─────────────────────────────────────────────────────────────
    @log_call
    @timer
    def transform(self, df: pd.DataFrame, options: dict) -> tuple:
        """
        Apply selected preprocessing operations.
        Returns (cleaned_df, change_log).
        """
        df = df.copy()
        self.original_shape = df.shape
        change_log = []

        # 1. Drop duplicates
        if options.get("drop_duplicates"):
            before = len(df)
            df = df.drop_duplicates()
            n = before - len(df)
            if n:
                change_log.append({"step": "Drop Duplicates",
                                   "detail": f"Removed {n} duplicate rows",
                                   "icon": "🔁"})
            self.steps_applied.append("drop_duplicates")

        # 2. Handle missing values
        strategy = options.get("fill_missing")
        if strategy:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            text_cols    = df.select_dtypes(exclude=[np.number]).columns.tolist()
            total = 0
            if strategy == "drop":
                before = len(df)
                df = df.dropna()
                change_log.append({"step": "Drop Missing Rows",
                                   "detail": f"Removed {before - len(df)} rows containing nulls",
                                   "icon": "🗑️"})
            else:
                for col in numeric_cols:
                    n = int(df[col].isnull().sum())
                    if n:
                        if strategy == "mean":
                            df[col] = df[col].fillna(round(df[col].mean(), 4))
                        elif strategy == "median":
                            df[col] = df[col].fillna(df[col].median())
                        elif strategy == "mode":
                            df[col] = df[col].fillna(df[col].mode()[0])
                        elif strategy == "zero":
                            df[col] = df[col].fillna(0)
                        total += n
                for col in text_cols:
                    n = int(df[col].isnull().sum())
                    if n:
                        df[col] = df[col].fillna(
                            df[col].mode()[0] if not df[col].mode().empty else "Unknown")
                        total += n
                if total:
                    change_log.append({"step": f"Fill Missing ({strategy})",
                                       "detail": f"Filled {total} missing values using {strategy}",
                                       "icon": "✏️"})
            self.steps_applied.append(f"fill_{strategy}")

        # 3. Remove outliers (IQR)
        if options.get("remove_outliers"):
            before = len(df)
            for col in df.select_dtypes(include=[np.number]).columns:
                q25, q75 = df[col].quantile(0.25), df[col].quantile(0.75)
                iqr = q75 - q25
                df = df[(df[col] >= q25 - 1.5*iqr) & (df[col] <= q75 + 1.5*iqr)]
            n = before - len(df)
            if n:
                change_log.append({"step": "Remove Outliers (IQR)",
                                   "detail": f"Removed {n} rows outside IQR fences",
                                   "icon": "📍"})
            self.steps_applied.append("remove_outliers")

        # 4. Drop selected columns
        raw = options.get("drop_cols", "")
        drop_cols = [c.strip() for c in raw.split(",") if c.strip() in df.columns]
        if drop_cols:
            df = df.drop(columns=drop_cols)
            change_log.append({"step": "Drop Columns",
                               "detail": f"Dropped: {', '.join(drop_cols)}",
                               "icon": "✂️"})
            self.steps_applied.append("drop_cols")

        # 5. Scaling / Normalisation
        scale = options.get("scale")
        if scale:
            raw_sc = options.get("scale_cols", "")
            scale_cols = [c.strip() for c in raw_sc.split(",") if c.strip() in df.columns]
            if not scale_cols:
                scale_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            applied = []
            for col in scale_cols:
                if pd.api.types.is_numeric_dtype(df[col]):
                    if scale == "minmax":
                        mn, mx = df[col].min(), df[col].max()
                        if mx != mn:
                            df[col] = round((df[col] - mn) / (mx - mn), 6)
                            applied.append(col)
                    elif scale == "zscore":
                        mu, sigma = df[col].mean(), df[col].std()
                        if sigma > 0:
                            df[col] = round((df[col] - mu) / sigma, 6)
                            applied.append(col)
            if applied:
                label = "Min-Max (0-1)" if scale == "minmax" else "Z-Score"
                change_log.append({"step": f"Scale: {label}",
                                   "detail": f"Applied to {len(applied)} columns: {', '.join(applied[:4])}{'...' if len(applied)>4 else ''}",
                                   "icon": "📏"})
            self.steps_applied.append(f"scale_{scale}")

        self.cleaned_shape = df.shape
        change_log.append({
            "step":   "Summary",
            "detail": f"Shape: {self.original_shape[0]}×{self.original_shape[1]} → {self.cleaned_shape[0]}×{self.cleaned_shape[1]}",
            "icon":   "✅",
        })
        self.log_event(f"transform() — {len(change_log)} steps, final shape {self.cleaned_shape}")
        return df, change_log

    # ── Generator: lazy row streaming ─────────────────────────────────────────
    def cleaned_row_generator(self, df: pd.DataFrame):
        """Generator — yields cleaned rows one at a time (lazy evaluation)."""
        for _, row in df.iterrows():
            yield row.to_dict()

    # ── Export ────────────────────────────────────────────────────────────────
    def to_csv_bytes(self, df: pd.DataFrame) -> bytes:
        """Serialize cleaned DataFrame to UTF-8 CSV bytes for download."""
        buf = io.StringIO()
        df.to_csv(buf, index=False, encoding="utf-8")
        return buf.getvalue().encode("utf-8")
