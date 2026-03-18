# SmartDataOS — Advanced Python Project

**Smart Data Processing & Validation Dashboard**

A full-stack Python web application built with Flask that demonstrates every advanced Python concept required by the assignment specification.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Folder Structure](#folder-structure)
3. [Technology Stack](#technology-stack)
4. [Setup & Installation](#setup--installation)
5. [How to Run](#how-to-run)
6. [Python Concepts Explained](#python-concepts-explained)
7. [Module Descriptions](#module-descriptions)
8. [Evaluation Criteria Coverage](#evaluation-criteria-coverage)

---

## Project Overview

SmartDataOS lets a user:
- Submit a validated form (name, email, phone, password) with live regex checking
- Upload a CSV or JSON dataset
- View computed statistics (mean, median, std, percentiles) from NumPy/Pandas
- See three auto-generated Matplotlib charts
- Observe concurrent processing via `threading` and `multiprocessing`
- Browse all previous results stored in `data/datasets.json`

---

## Folder Structure

```
smart_data_system/
│
├── app.py                          ← Flask entry point
├── requirements.txt
├── README.md
│
├── templates/
│   ├── index.html                  ← Landing / form page
│   ├── dashboard.html              ← Results page
│   └── history.html                ← All saved records
│
├── static/
│   ├── style.css                   ← Blue-theme dark design
│   ├── script.js                   ← Client-side validation & UX
│   └── charts/                     ← Matplotlib chart outputs
│
├── data/
│   ├── datasets.json               ← JSON-serialized results store
│   ├── app.log                     ← Decorator log output
│   └── uploads/                    ← Temporary upload storage
│
├── modules/
│   ├── __init__.py
│   ├── validation.py               ← Regex validator + Abstract class
│   ├── processing.py               ← Pandas/NumPy DataProcessor
│   ├── threading_tasks.py          ← threading.Thread concurrent processing
│   ├── multiprocessing_tasks.py    ← multiprocessing.Pool parallel stats
│   └── serialization.py            ← JSON data storage CRUD
│
└── utils/
    ├── __init__.py
    ├── decorators.py               ← @log_call, @timer, @validate_input
    ├── iterators.py                ← DatasetRowIterator, RangeStepIterator
    ├── generators.py               ← chunk_dataset, stats_stream, json_record_generator
    └── mixins.py                   ← SerializableMixin, LoggableMixin, ReprMixin
```

---

## Technology Stack

| Layer     | Technology                              |
|-----------|-----------------------------------------|
| Backend   | Python 3.11+, Flask 3.0                 |
| Data      | Pandas 2.1, NumPy 1.26                  |
| Charts    | Matplotlib 3.8 (Agg backend)            |
| Frontend  | HTML5, CSS3, Vanilla JavaScript         |
| Storage   | JSON (via Python `json` module)         |

---

## Setup & Installation

### Step 1 — Clone / create the project folder
```bash
mkdir smart_data_system && cd smart_data_system
# Place all project files here
```

### Step 2 — Create and activate a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

---

## How to Run

```bash
python app.py
```

Then open your browser at: **http://127.0.0.1:5000**

### API Endpoints
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Landing / form page |
| `/process` | POST | Submit form + dataset |
| `/history` | GET | All saved records |
| `/api/stats` | GET | All records as JSON |
| `/api/validate` | POST | Live field validation |

---

## Python Concepts Explained

### 1. Iterators (`utils/iterators.py`)
```python
class DatasetRowIterator:
    def __iter__(self): return self
    def __next__(self):
        if self._index >= len(self._rows): raise StopIteration
        ...
```
Implements `__iter__` and `__next__` — the iterator protocol. Walks dataset rows in batches.

### 2. Generators (`utils/generators.py`)
```python
def chunk_dataset(data, chunk_size=100):
    for i in range(0, len(data), chunk_size):
        yield data[i: i + chunk_size]
```
Uses `yield` for lazy, memory-efficient chunking. `stats_stream` computes running statistics using Welford's algorithm.

### 3. Decorators & Closures (`utils/decorators.py`)
```python
def log_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        _write_log(f"CALL {func.__name__}()")
        result = func(*args, **kwargs)
        _write_log(f"RETURN {result!r}")
        return result
    return wrapper
```
`wrapper` is a **closure** — it captures `func` from the enclosing `log_call` scope.
`@timer` measures execution time. `@validate_input` is a decorator factory.

### 4. Abstract Classes (`modules/validation.py`)
```python
from abc import ABC, abstractmethod

class BaseValidator(ABC):
    @abstractmethod
    def validate(self, data: dict) -> dict: ...
    @abstractmethod
    def get_rules(self) -> dict: ...
```
Forces every subclass to implement `validate()` and `get_rules()`.

### 5. Multiple Inheritance & MRO
```python
class UserFormValidator(BaseValidator, SerializableMixin, LoggableMixin, ReprMixin):
    ...
```
Python resolves methods using **C3 linearisation** (MRO). Use `UserFormValidator.__mro__` to inspect the chain.

### 6. Operator Overloading (`modules/processing.py`)
```python
def __add__(self, other):
    merged = DataProcessor()
    merged.df = pd.concat([self.df, other.df])
    return merged
```
Allows `merged = processor_a + processor_b`.

### 7. Mixin Classes (`utils/mixins.py`)
- `SerializableMixin` → `to_dict()`, `to_json()`, `from_dict()`
- `LoggableMixin` → `log_event()`, `get_log()`
- `ReprMixin` → `__repr__`, `__str__`, `__eq__`

### 8. Regular Expressions (`modules/validation.py`)
```python
re.compile(r"^[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")  # email
re.compile(r"^\+?[\d\s\-\(\)]{7,15}$")              # phone
```
Pre-compiled patterns checked with `.fullmatch()`.

### 9. Threading (`modules/threading_tasks.py`)
```python
t = threading.Thread(target=_process_chunk, args=(chunk, idx, shared_results))
t.start()
...
t.join()  # wait for completion
```
`threading.Lock` ensures thread-safe writes to the shared result list.

### 10. Multiprocessing (`modules/multiprocessing_tasks.py`)
```python
with multiprocessing.Pool(processes=4) as pool:
    results = pool.map(_compute_stats_worker, indexed_chunks)
```
`Pool.map` distributes CPU-bound work across separate processes, bypassing the GIL.

### 11. JSON Serialization (`modules/serialization.py`)
```python
json.dump(records, f, indent=2, default=str)   # write
json.load(f)                                    # read
```
Complete CRUD operations on `data/datasets.json`.

### 12. Core Library Modules
| Module | Usage |
|--------|-------|
| `os` | `os.path`, `os.makedirs`, `os.cpu_count()` |
| `sys` | `sys.path.insert`, `sys.version` |
| `datetime` | Record timestamps, log entries |
| `math` | `math.sqrt`, `math.factorial` in worker |
| `re` | Compiled regex patterns |
| `json` | Serialization / deserialization |
| `abc` | Abstract base class infrastructure |
| `functools` | `@functools.wraps` in decorators |
| `threading` | Thread, Lock |
| `multiprocessing` | Pool, get_context |

---

## Evaluation Criteria Coverage

| Criterion | Marks | Implementation |
|-----------|-------|----------------|
| Python Concepts | 30 | All 12 concepts (iterators, generators, decorators, OOP, regex, threading, multiprocessing, JSON, os/sys/datetime/math) |
| Backend Implementation | 20 | Flask routes, form handling, file upload, REST API |
| Data Processing | 15 | Pandas + NumPy statistics on uploaded CSV/JSON |
| Visualization | 10 | 3 Matplotlib charts (bar, line, histogram) |
| Code Structure | 10 | 5 modules, 4 utils, clean separation of concerns |
| Documentation | 10 | This README + inline docstrings in every file |
| Innovation | 5 | Live client-side regex validation, drag-and-drop upload, running statistics generator, operator overloading for dataset merging |

**Total: 100 marks**

---

## Sample Dataset (for testing)

Create a file `sample.csv`:
```
age,salary,experience,score
25,45000,2,78
30,65000,5,85
35,80000,8,90
28,52000,3,72
42,95000,15,95
```

Upload this on the form page to see all charts and statistics generated.

---

## Author Notes

- All regex patterns are compiled once at class instantiation for performance
- The `@log_call` decorator writes to `data/app.log` — check this file to see every function call
- The threading demo processes the first 200 rows of your dataset in 4 parallel threads
- The multiprocessing module uses `spawn` context for cross-platform compatibility
