# PocketWise Streamlit Demo

A Streamlit app that uses the [`pocketwise-finance`](https://test.pypi.org/project/pocketwise-finance/) package to categorize bank transactions and produce monthly spending summaries.

> The purpose of this project is to demonstrate that the PocketWise library (published on TestPyPI) can be installed and reused in a separate application.

---

## Setup

### 1. Create a virtual environment and install dependencies

```bash
uv venv
uv sync
```

### 2. Install `pocketwise-finance` from TestPyPI

```bash
uv pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple pocketwise-finance
```

### 3. Run the app

```bash
uv run streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`.

---

## How to use

The dashboard walks you through three steps:

1. **Upload a CSV** file containing your transactions.
2. **Review or edit the categorization rules** (regex patterns mapped to spending categories).
3. **View results** — categorized transactions, a monthly summary table, and a bar chart.

---

## Expected CSV format

Your file must include the following columns:

| Column        | Format       | Example              |
|---------------|--------------|----------------------|
| `date`        | `YYYY-MM-DD` | `2026-03-01`         |
| `description` | free text    | `Mercadona purchase` |
| `amount`      | number       | `-35.60`             |

Sample CSV:

```csv
date,description,amount
2026-03-01,Mercadona purchase,-35.60
2026-03-02,Netflix subscription,-12.99
2026-03-03,Salary,2500.00
```

> Negative amounts are treated as expenses; positive amounts as income.

---

## Sample data

A ready-to-use example file is included in the `sample_data_example/` folder:

```
sample_data_example/
└── sample_transactions.csv
```

It contains 6 months of transactions (Jan – Jun 2026) across categories including Groceries, Transport, Subscriptions, and Eating Out. Upload it directly in Step 1 to see the app in action without needing your own bank export.
