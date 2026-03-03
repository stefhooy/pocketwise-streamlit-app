import streamlit as st
import pandas as pd
from pathlib import Path

from pocketwise.io import stream_transactions_csv
from pocketwise.rules import RuleSet, RegexRule
from pocketwise.engine import Categorizer
from pocketwise.reporting import summarize_by_month_and_category


st.set_page_config(page_title="PocketWise Finance", layout="wide")
st.title("PocketWise Finance Dashboard")

st.write(
    "This Streamlit app is a small demo project that installs the PocketWise Finance package from TestPyPI "
    "and uses it to categorize transactions and generate monthly summaries."
)

st.subheader("1) Upload a CSV file")
uploaded_file = st.file_uploader(
    "CSV must contain: date, description, amount (date format: YYYY-MM-DD)",
    type=["csv"],
)

st.divider()
st.subheader("2) Categorization rules (regex based)")

default_rules = [
    ("Groceries", r"carrefour|mercadona|aldi|lidl"),
    ("Transport", r"uber|bolt|metro|renfe|cabify"),
    ("Subscriptions", r"netflix|spotify|prime|hbo"),
    ("Eating Out", r"restaurant|cafe|starbucks|mcdonald"),
]

rules_df = pd.DataFrame(default_rules, columns=["category", "pattern"])
edited_rules_df = st.data_editor(
    rules_df,
    use_container_width=True,
    num_rows="dynamic",
)

ruleset = RuleSet()
for _, row in edited_rules_df.iterrows():
    cat = str(row["category"]).strip()
    pat = str(row["pattern"]).strip()
    if cat and pat:
        ruleset.add(RegexRule(cat, pat))

categorizer = Categorizer(ruleset)

st.divider()
st.subheader("3) Results")

if uploaded_file is None:
    st.info("Upload a CSV file to see results.")
else:
    df = pd.read_csv(uploaded_file)
    st.write("Raw data preview:")
    st.dataframe(df.head(20), use_container_width=True)

    # Save temporarily to reuse the package loader (Path based generator)
    temp_path = Path("temp_transactions.csv")
    df.to_csv(temp_path, index=False)

    # Package output: list[Transaction] then categorized list[Transaction]
    txs = list(stream_transactions_csv(temp_path))
    categorized = categorizer.categorize_all(txs)

    # Show categorized transactions as a dataframe
    categorized_df = pd.DataFrame(
        [
            {
                "date": t.tx_date.isoformat(),
                "description": t.description,
                "amount": t.amount,
                "currency": t.currency,
                "category": t.category,
            }
            for t in categorized
        ]
    )

    col1, col2 = st.columns(2)

    with col1:
        st.write("Categorized transactions:")
        st.dataframe(categorized_df, use_container_width=True)

    with col2:
        summary = summarize_by_month_and_category(categorized)
        st.write("Monthly summary (package output):")
        st.json(summary)

    # Chart
    summary_df = pd.DataFrame(summary).T.fillna(0)
    st.subheader("4) Category totals by month")
    st.bar_chart(summary_df)