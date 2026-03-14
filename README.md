# 📊 SmartDataOS — Smart Data Processing & Validation Dashboard

> A full-stack Flask web application demonstrating 19+ advanced Python concepts — regex validation, NumPy/Pandas statistics, Matplotlib visualizations, concurrent threading, AI insights engine, dataset health scoring, comparison engine, and auto-generated HTML reports.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?style=flat-square&logo=flask)
![Pandas](https://img.shields.io/badge/Pandas-2.1-blue?style=flat-square&logo=pandas)
![NumPy](https://img.shields.io/badge/NumPy-1.26-013243?style=flat-square&logo=numpy)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.8-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🖥️ Screenshots

| Home Page 





---

## ✨ Features

- 🔐 **Form Validation** — All fields validated with pre-compiled `re.compile()` regex patterns (name, email, phone, password)
- 📈 **Statistical Analysis** — Full NumPy statistics (mean, median, std, percentiles, Q25/Q75) for every numeric column
- 📊 **Visualizations** — 3 Matplotlib charts auto-generated: bar chart, line chart, distribution histogram
- ⚡ **Concurrent Threading** — Dataset split across multiple `threading.Thread` workers with `Lock` for thread safety
- 🧠 **AI Insights Engine** — Auto-generates 80+ plain-English findings: skewness, outliers (IQR fencing), Pearson correlations
- 🏥 **Health Score** — Grades dataset A+ to F across 5 dimensions: Completeness, Uniqueness, Size, Consistency, Diversity
- 🔀 **Dataset Comparison** — Compare two CSVs side-by-side using `__sub__` operator overloading (`snap_a - snap_b`)
- 📄 **Smart Report** — Auto-generates a self-contained 137KB HTML report with base64-embedded charts, printable to PDF
- 🗂️ **History** — All results persisted to `data/datasets.json` with full CRUD via Python's `json` module

---

## 🐍 Python Concepts Demonstrated

| # | Concept | File |
|---|---|---|
| 01 | Custom Iterator (`__iter__`, `__next__`) | `utils/iterators.py` |
| 02 | Generator functions (`yield`) | `utils/generators.py` |
| 03 | Decorator `@log_call` | `utils/decorators.py` |
| 04 | Decorator `@timer` | `utils/decorators.py` |
| 05 | Decorator factory `@validate_input` | `utils/decorators.py` |
| 06 | Closure (`make_threshold_checker`) | `modules/insights_engine.py` |
| 07 | Abstract Base Classes (`ABC`) | `modules/validation.py` |
| 08 | Multiple Inheritance | `modules/validation.py` |
| 09 | MRO (C3 Linearisation) | All multi-inherit classes |
| 10 | Operator Overloading `__add__` | `modules/processing.py` |
| 11 | Operator Overloading `__sub__` | `modules/comparison_engine.py` |
| 12 | Mixin Classes (×3) | `utils/mixins.py` |
| 13 | Regular Expressions | `modules/validation.py` |
| 14 | Multithreading (`Thread + Lock`) | `modules/threading_tasks.py` |
| 15 | Multiprocessing (`Pool.map`) | `modules/multiprocessing_tasks.py` |
| 16 | JSON Serialization (CRUD) | `modules/serialization.py` |
| 17 | `os` · `sys` · `datetime` · `math` | Throughout |
| 18 | NumPy statistical operations | `modules/processing.py` |
| 19 | Pandas DataFrame operations | `modules/processing.py` |
| 20 | Matplotlib visualizations | `modules/processing.py` |

---

## 📁 Project Structure

```
smart_data_system/
├── app.py                        # Flask entry point — all routes
├── requirements.txt
├── README.md
│
├── modules/
│   ├── validation.py             # UserFormValidator (ABC + regex)
│   ├── processing.py             # DataProcessor (NumPy + Pandas + Matplotlib)
│   ├── threading_tasks.py        # Concurrent threading with Lock
│   ├── multiprocessing_tasks.py  # Pool.map() multiprocessing
│   ├── serialization.py          # JSON CRUD — datasets.json
│   ├── insights_engine.py        # AI insights + health score (Unique Feature)
│   ├── comparison_engine.py      # Dataset comparison + __sub__ (Unique Feature)
│   └── report_exporter.py        # Self-contained HTML report (Unique Feature)
│
├── utils/
│   ├── decorators.py             # @log_call, @timer, @validate_input
│   ├── iterators.py              # DatasetRowIterator
│   ├── generators.py             # chunk_dataset, stats_stream
│   └── mixins.py                 # SerializableMixin, LoggableMixin, ReprMixin
│
├── templates/
│   ├── index.html                # Home page
│   ├── dashboard.html            # Results dashboard
│   ├── compare.html              # Dataset comparison
│   └── history.html              # Processing history
│
├── static/
│   ├── style.css
│   ├── script.js
│   ├── charts/                   # Auto-generated Matplotlib PNGs
│   └── reports/                  # Auto-generated HTML reports
│
└── data/
    ├── datasets.json             # Persistent JSON store
    ├── employee_dataset.csv      # Sample dataset (50 rows × 17 cols)
    ├── it_dept.csv               # Sample subset for comparison
    └── finance_dept.csv          # Sample subset for comparison
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/smart-data-os.git
cd smart-data-os/smart_data_system
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

### 5. Open in browser

```
http://127.0.0.1:5000
```

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

## 🗺️ Pages & Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Home page — form + file upload |
| `/process` | POST | Validate form, process dataset, generate report |
| `/compare` | GET / POST | Upload two datasets and compare |
| `/history` | GET | View all past processing records |
| `/history/delete/<id>` | POST | Delete a record from JSON store |
| `/api/stats` | GET | Raw JSON API — all records |
| `/api/validate` | POST | Live field validation endpoint |
| `/api/health` | POST | Dataset health score endpoint |

---

## 🔬 Unique Features

### 1. 🧠 AI Insights Engine
Automatically analyses your dataset and generates plain-English findings with zero external APIs — pure Python + NumPy:
- Skewness detection using closure factory `make_threshold_checker(low, high)`
- Outlier detection using IQR fencing (Q25 − 1.5×IQR, Q75 + 1.5×IQR)
- Pearson correlation scan — flags r ≥ 0.85 as strongly correlated

### 2. 🏥 Dataset Health Score
Grades your dataset A+ to F across 5 dimensions:

| Dimension | Max | Rule |
|---|---|---|
| Completeness | 30 | 30 − (missing% × 1.5) |
| Uniqueness | 25 | 25 − (duplicate% × 2) |
| Size | 20 | 20 if ≥1000 rows, 10 if ≥50 |
| Consistency | 15 | 15 − (zero-variance cols × 5) |
| Diversity | 10 | 10 if both numeric + text cols |

### 3. 🔀 Dataset Comparison Engine
Uses Python operator overloading so comparison reads like natural syntax:
```python
snap_a = DatasetSnapshot(df_a, "IT_Dept")
snap_b = DatasetSnapshot(df_b, "Finance_Dept")
result = snap_a - snap_b   # __sub__ triggers ComparisonEngine.compare()
```

### 4. 📄 Smart Report Exporter
Generates a fully self-contained 137KB HTML file with:
- Base64-embedded chart images (no external files needed)
- Health score, statistics, and all AI insights
- Printable to PDF directly from any browser
- Viewable offline — no internet connection required

---

## 📊 Sample Output (employee_dataset.csv)

```
Shape          : 50 rows × 17 columns
Numeric cols   : 12
Missing values : 0
Health Score   : A+ (90/100)
AI Insights    : 87 findings generated
Threading      : 5 threads, 50 rows, ~0.019s
Top finding    : experience ↔ joined_year  r = -1.000 (perfect inverse)
```

---

## 👤 Author

**Tejendra Pal Singh**
- 📧 ptejendra91@gmail.com
- 🐙 GitHub: https://github.com/tejth

---



---

<p align="center">Made with ❤️ as an Advanced Python Project</p>
