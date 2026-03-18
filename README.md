<div align="center">

# 🔬 SmartDataOS

### Smart Data Processing & Validation Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Pandas](https://img.shields.io/badge/Pandas-2.1-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![NumPy](https://img.shields.io/badge/NumPy-1.26-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.8-11557C?style=for-the-badge&logo=python&logoColor=white)](https://matplotlib.org)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

**A full-stack data analytics web application built with pure Python.**  
Upload any CSV or JSON dataset — get statistics, charts, AI insights, health scores,  
correlation heatmaps, preprocessing tools, filtering, merging and downloadable reports.

<br/>

[Features](#-features) · [Demo](#-screenshots) · [Getting Started](#-getting-started) · [Concepts](#-python-concepts) · [Routes](#-api-routes) · [Structure](#-project-structure)

</div>



---

## ✨ Features

| Feature | Page | Description |
|---|---|---|
| 🔐 **Form Validation** | `/` | Real-time regex validation on all 4 fields as you type |
| ⚡ **Process & Analyse** | `/process` | Full statistical analysis, 3 charts, threading, AI insights, health score + HTML report |
| 🔧 **Preprocessing** | `/preprocess` | Fill missing values, remove outliers, drop columns, normalise, standardise, download CSV |
| 📊 **Data Profiler** | `/profile` | Deep per-column profile — skewness, kurtosis, value counts, mini charts for every column |
| 🔍 **Filter & Search** | `/filter` | Multi-condition filtering, global text search, sort any column, download filtered CSV |
| 🌡️ **Correlation Heatmap** | `/heatmap` | Pearson correlation matrix with annotated Matplotlib heatmap — detect multicollinearity |
| 🔗 **Dataset Merger** | `/merge` | Inner / Left / Right / Outer join two datasets on any common key column |
| 📋 **Compare Datasets** | `/compare` | Side-by-side statistical diff with similarity score — uses `__sub__` operator overloading |
| 🗂️ **History** | `/history` | All past records stored in `data/datasets.json` — view, browse and delete |
| 🔌 **REST API** | `/api/*` | JSON endpoints for stats, live validation and health scoring |

---

## 🖥️ Screenshots


<img width="1021" height="934" alt="1" src="https://github.com/user-attachments/assets/37dea329-9de1-4965-9620-e32513ddf888" />                    
<img width="1012" height="894" alt="2" src="https://github.com/user-attachments/assets/e2107288-a012-4d78-81a1-878ae726474c" />
<img width="798" height="915" alt="10" src="https://github.com/user-attachments/assets/652dfc53-368f-4398-a9d6-d5d0f5a3e92a" />
<img width="960" height="939" alt="9" src="https://github.com/user-attachments/assets/0d546da7-f1da-4f6d-82d7-7ff81af8fd93" />
<img width="960" height="842" alt="7" src="https://github.com/user-attachments/assets/593a98f6-4816-48e8-9d39-44762aa19a0a" />
<img width="984" height="868" alt="5" src="https://github.com/user-attachments/assets/3eb27c9b-5d3a-4dab-9722-82ae0773b739" />
                                                        
                                             

## 🚀 Getting Started

### Prerequisites

- Python **3.10 or higher**
- pip (comes with Python)
- Any modern browser

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/smart-data-os.git
cd smart-data-os/smart_data_system

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the app
python app.py
```

### Open in Browser

```
http://127.0.0.1:5000
```

> ⚠️ **Important:** Always run `python app.py` from **inside** the `smart_data_system/` folder.

---

## 📦 Requirements

```
flask==3.0.0
numpy==1.26.2
pandas==2.1.4
matplotlib==3.8.2
Werkzeug==3.0.1
```

---

## 🐍 Python Concepts

SmartDataOS demonstrates **24 advanced Python concepts** — all implemented with real, working code.

<details>
<summary><b>Click to expand — full concept list</b></summary>

| # | Concept | File | How It's Used |
|---|---|---|---|
| 01 | Custom Iterator | `utils/iterators.py` | `DatasetRowIterator` — `__iter__` + `__next__` walks rows in batches |
| 02 | Generator (×3) | `utils/generators.py` | `chunk_dataset` · `stats_stream` · `json_record_generator` — all use `yield` |
| 03 | Generator (profile) | `modules/profiler.py` | `profile_stream()` — yields one column profile at a time |
| 04 | Generator (filter) | `modules/filter_engine.py` | `filtered_row_generator()` — yields filtered rows lazily |
| 05 | Decorator `@log_call` | `utils/decorators.py` | Logs every function call with args + return value to `app.log` |
| 06 | Decorator `@timer` | `utils/decorators.py` | Measures execution time with `time.perf_counter()` |
| 07 | Decorator factory | `utils/decorators.py` | `@validate_input(*keys)` — returns a decorator that checks required keys |
| 08 | Closure | `modules/insights_engine.py` | `make_threshold_checker(lo, hi)` — returns `check()` that closes over lo/hi |
| 09 | Abstract Base Class | `modules/validation.py` + 7 others | `ABC` + `@abstractmethod` enforces interface on every subclass |
| 10 | Multiple Inheritance | `modules/validation.py` | `UserFormValidator(BaseValidator, SerializableMixin, LoggableMixin, ReprMixin)` |
| 11 | MRO (C3 linearisation) | All multi-inherit classes | Python resolves method order — inspect with `ClassName.__mro__` |
| 12 | Operator Overloading `__add__` | `modules/processing.py` | `processor_a + processor_b` → merges two DataFrames with `pd.concat` |
| 13 | Operator Overloading `__sub__` | `modules/comparison_engine.py` | `snap_a - snap_b` → triggers `ComparisonEngine.compare()` automatically |
| 14 | Mixin: SerializableMixin | `utils/mixins.py` | Adds `to_dict()` · `to_json()` · `from_dict()` to any class |
| 15 | Mixin: LoggableMixin | `utils/mixins.py` | Adds `log_event()` · `get_log()` · `clear_log()` — per-instance event logging |
| 16 | Mixin: ReprMixin | `utils/mixins.py` | Adds `__repr__` · `__str__` · `__eq__` for readable object representation |
| 17 | Regular Expressions | `modules/validation.py` | `re.compile()` pre-compiles all 4 field patterns at class load time |
| 18 | Multithreading | `modules/threading_tasks.py` | `threading.Thread` + `Lock` — 4 threads process row chunks concurrently |
| 19 | Multiprocessing | `modules/multiprocessing_tasks.py` | `Pool.map()` distributes stats across CPU cores with spawn context |
| 20 | JSON Serialization | `modules/serialization.py` | `json.dump()` saves · `json.load()` reads · delete filters and rewrites |
| 21 | `os` · `sys` · `datetime` · `math` | Throughout all modules | File paths, version info, timestamps, `pi` constant, `cpu_count()` |
| 22 | NumPy | `modules/processing.py` | `mean` · `median` · `std` · `percentile` · skewness · kurtosis · `corrcoef` |
| 23 | Pandas | `modules/processing.py` | `read_csv` · `DataFrame` · `merge` · `concat` · `value_counts` · `describe` |
| 24 | Matplotlib | `modules/processing.py` | Bar · Line · Histogram · Heatmap — all Agg backend, saved as PNG |

</details>

---

## 🗺️ API Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Home page — user form + dataset upload |
| `/process` | POST | Validate form, load dataset, run full analysis, render dashboard |
| `/preprocess` | GET / POST | Scan dataset for issues OR return issue report |
| `/preprocess/transform` | POST | Apply transformations, return before/after preview |
| `/preprocess/download/<file>` | GET | Download the cleaned CSV file |
| `/profile` | GET / POST | Upload dataset → full per-column profile with charts |
| `/filter` | GET / POST | Multi-condition filter + global search + sort |
| `/filter/download/<file>` | GET | Download the filtered CSV file |
| `/heatmap` | GET / POST | Upload dataset → Pearson correlation heatmap |
| `/merge` | GET / POST | Scan common columns OR perform the join |
| `/merge/download/<file>` | GET | Download the merged CSV file |
| `/compare` | GET / POST | Upload two datasets → side-by-side statistical comparison |
| `/history` | GET | View all past processing records |
| `/history/delete/<id>` | POST | Delete a record from `datasets.json` |
| `/api/stats` | GET | All processing records as raw JSON |
| `/api/validate` | POST | Live field validation — called by `script.js` as you type |
| `/api/health` | POST | Upload file → returns health score JSON |

---

## 📁 Project Structure

```
smart_data_system/
│
├── app.py                         # Main Flask app — all 23 routes
├── requirements.txt               # flask, pandas, numpy, matplotlib, werkzeug
├── README.md
│
├── modules/                       # Core feature modules (14 files)
│   ├── validation.py              # UserFormValidator — regex + ABC
│   ├── processing.py              # DataProcessor — stats, charts, preview
│   ├── preprocessor.py            # DataPreprocessor — clean, scale, download
│   ├── profiler.py                # DataProfiler — skewness, kurtosis, value counts
│   ├── filter_engine.py           # SmartFilterEngine — multi-condition filter + search
│   ├── heatmap_engine.py          # CorrelationHeatmapEngine — Pearson matrix + chart
│   ├── merger.py                  # DatasetMerger — inner/left/right/outer join
│   ├── comparison_engine.py       # ComparisonEngine + DatasetSnapshot (__sub__)
│   ├── insights_engine.py         # InsightsEngine — AI findings + health score
│   ├── threading_tasks.py         # run_threaded_processing — Thread + Lock
│   ├── multiprocessing_tasks.py   # run_multiprocess_statistics — Pool.map()
│   ├── serialization.py           # save_result / load_all / delete_result — JSON CRUD
│   ├── report_exporter.py         # generate_report() — self-contained HTML report
│   └── __init__.py
│
├── utils/                         # Reusable utilities (4 files)
│   ├── decorators.py              # @log_call  @timer  @validate_input
│   ├── generators.py              # chunk_dataset()  stats_stream()  json_record_generator()
│   ├── iterators.py               # DatasetRowIterator  RangeStepIterator
│   ├── mixins.py                  # SerializableMixin  LoggableMixin  ReprMixin
│   └── __init__.py
│
├── templates/                     # Jinja2 HTML templates (9 pages)
│   ├── index.html                 # Home — form + drag-and-drop upload
│   ├── dashboard.html             # Results — stats, charts, AI insights, live report
│   ├── preprocess.html            # Preprocessing — scan, configure, transform, download
│   ├── profile.html               # Profiler — per-column stats + mini charts
│   ├── filter.html                # Filter & Search — conditions + sort + download
│   ├── heatmap.html               # Heatmap — correlation matrix + pair list
│   ├── merge.html                 # Merger — upload 2 files, pick join type, download
│   ├── compare.html               # Compare — similarity score + column-by-column diff
│   └── history.html               # History — all records from datasets.json
│
├── static/
│   ├── style.css                  # Dark blue theme — all page styling
│   ├── script.js                  # Live validation, dropzone, animated counters
│   ├── charts/                    # Auto-generated Matplotlib PNGs
│   └── reports/                   # Auto-generated self-contained HTML reports
│
└── data/
    ├── datasets.json              # All processing records (JSON array)
    ├── employee_dataset.csv       # Sample data — 50 rows × 17 columns
    ├── it_dept.csv                # IT department subset — 16 rows
    ├── finance_dept.csv           # Finance department subset — 13 rows
    └── uploads/                   # Temp storage for cleaned / filtered / merged CSVs
```

---

## 🔬 Unique Features

### 1. 🧠 AI Insights Engine
Automatically generates **80+ plain-English findings** from your dataset — no external API needed. Pure Python + NumPy:
- Skewness detection using a **closure factory** `make_threshold_checker(low, high)`
- Outlier detection using **IQR fencing** — names specific outlier rows
- Pearson correlation scan — flags `r ≥ 0.85` as strongly correlated with multicollinearity warning
- Column name hints — detects `id`, `date`, `year` patterns using `re.compile()`

### 2. 🏥 Dataset Health Score
Grades your dataset **A+ to F** across 5 dimensions:

| Dimension | Max | Scoring Rule |
|---|---|---|
| Completeness | 30 | `30 − (missing% × 1.5)` |
| Uniqueness | 25 | `25 − (duplicate% × 2)` |
| Size | 20 | 20 if ≥1000 rows · 10 if ≥50 rows |
| Consistency | 15 | `15 − (zero-variance cols × 5)` |
| Diversity | 10 | 10 if both numeric + text columns exist |

### 3. 🔗 Operator Overloading for Comparison
Dataset comparison uses Python's `__sub__` operator — feels like natural syntax:
```python
snap_a = DatasetSnapshot(df_a, "IT_Dept")
snap_b = DatasetSnapshot(df_b, "Finance_Dept")
result = snap_a - snap_b   # __sub__ triggers ComparisonEngine.compare()
```

### 4. 📄 Self-Contained HTML Report
After every analysis, a **~137 KB HTML file** is auto-generated with:
- Base64-embedded chart images — no external files needed
- Health score, statistics table, and all AI insights
- Printable to PDF directly from any browser
- Works completely offline

---

## 📊 Sample Output — employee_dataset.csv

```
Shape           : 50 rows × 17 columns
Numeric columns : 12
Missing values  : 0
Health Score    : A+ (90/100)
AI Insights     : 87 findings generated
Threading       : 5 threads · 50 rows · ~0.019s
Top finding     : experience ↔ joined_year  r = -1.000 (perfect inverse)
Strong corr     : salary ↔ projects_completed  r = +0.997
```

---

## 📂 Sample Datasets Included

| File | Rows | Columns | Use For |
|---|---|---|---|
| `employee_dataset.csv` | 50 | 17 | Main dataset — full company data |
| `it_dept.csv` | 16 | 6 | IT department subset — use in Compare / Merge |
| `finance_dept.csv` | 13 | 6 | Finance department subset — use in Compare / Merge |

---

## 🛠️ How Each Module Works

<details>
<summary><b>modules/validation.py</b></summary>

- Class: `UserFormValidator(BaseValidator, SerializableMixin, LoggableMixin, ReprMixin)`
- Inherits from 4 parents — demonstrates **multiple inheritance**
- All 4 regex patterns pre-compiled at class level with `re.compile()`
- `validate(data)` checks all fields, returns `{"valid": bool, "errors": dict}`

</details>

<details>
<summary><b>modules/processing.py</b></summary>

- Class: `DataProcessor(AbstractDataProcessor, SerializableMixin, LoggableMixin, ReprMixin)`
- `load(source, filetype)` — supports `pd.read_csv()` and `pd.read_json()`
- `compute_statistics()` — NumPy mean/median/std/percentiles for all numeric columns
- `generate_charts()` — 3 Matplotlib charts saved to `static/charts/`
- `__add__` overloading — `dp1 + dp2` merges two DataFrames with `pd.concat`

</details>

<details>
<summary><b>modules/insights_engine.py</b></summary>

- Class: `InsightsEngine(BaseInsightsEngine)`
- `analyse(df, stats)` — runs the `_insight_generator()` **generator**, collects all findings
- `health_score(df, stats)` — grades dataset A+ to F across 5 dimensions
- Uses `make_threshold_checker(lo, hi)` **closure** for skewness thresholds
- Returns 80+ findings on `employee_dataset.csv` including `r = -1.000`

</details>

<details>
<summary><b>modules/comparison_engine.py</b></summary>

- Classes: `ComparisonEngine` + `DatasetSnapshot`
- `DatasetSnapshot.__sub__` — `snap_a - snap_b` triggers `compare()` via **operator overloading**
- `compare()` — per-column statistical diff, % change, plain-English verdict, similarity score
- Generates grouped bar chart comparing both datasets side by side

</details>

<details>
<summary><b>utils/decorators.py</b></summary>

- `@log_call` — closure, wraps any function, logs call + return to `data/app.log` with `encoding="utf-8"`
- `@timer` — closure, measures wall-clock time with `time.perf_counter()`
- `@validate_input(*keys)` — **decorator factory**, returns a decorator that checks required dict keys
- `_write_log()` — opens log file with `encoding="utf-8"` to support emojis on Windows

</details>

---

## 🐛 Known Fix — Windows Encoding

If you get a `UnicodeEncodeError` on Windows, it's already fixed in this version.  
The `_write_log()` function in `utils/decorators.py` uses `encoding="utf-8"` to handle emojis in the insights output:

```python
# Fixed — works on Windows (Python 3.14)
with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write(f"[{timestamp}] {message}\n")
```

---

## 👤 Author

**Tejendra Pal Singh**
- 📧 ptejendra91@gmail.com
- 🐙 GitHub: [@tejth](https://github.com/tejth)


---

<div align="center">

Made with ❤️ as an **Advanced Python Project**

⭐ Star this repo if you found it useful!

</div>
