# PocketWise Streamlit Demo

This repository is a small Streamlit project that uses the `pocketwise-finance` Python package published on TestPyPI.

The purpose is to demonstrate that the library can be installed and reused in a separate application.

## Setup

Create a virtual environment with uv and install dependencies:

```bash
uv venv
uv sync
```
Install the package from TestPyPI (and dependencies from PyPI):
```bash
uv pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple pocketwise-finance
#Run the app
uv run streamlit run main.py
```
Expected CSV format

The app expects a CSV file with these columns:

date (YYYY-MM-DD)

description

amount


## 4) Run it
From the Streamlit repo root:

```powershell
uv run streamlit run main.py

Upload a sample CSV like:

date,description,amount
2026-03-01,Mercadona purchase,-35.60
2026-03-02,Netflix subscription,-12.99
2026-03-03,Salary,2500.00