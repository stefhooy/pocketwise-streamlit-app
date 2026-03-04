import streamlit as st
import pandas as pd
from pathlib import Path

from pocketwise.io import stream_transactions_csv
from pocketwise.rules import RuleSet, RegexRule
from pocketwise.engine import Categorizer
from pocketwise.reporting import summarize_by_month_and_category


st.set_page_config(page_title="PocketWise Finance", layout="wide")

# --- Sidebar: quick-start guide ---
with st.sidebar:
    st.title("How to use PocketWise")
    st.markdown(
        """
        **Step 1 — Upload your CSV**
        Your file must have these columns:
        - `date` (format: `YYYY-MM-DD`)
        - `description`
        - `amount`

        **Step 2 — Set categorization rules**
        Each rule maps a keyword/regex pattern to a spending category.
        You can edit the defaults or add your own rows.

        **Step 3 — View results**
        Once your file is uploaded, you'll see:
        - Categorized transactions
        - A monthly summary table
        - A category breakdown chart
        """
    )
    st.divider()
    st.caption("PocketWise Finance · demo app")


# --- Header ---
st.title("PocketWise Finance Dashboard")
st.markdown(
    "Upload your bank transactions and PocketWise will automatically categorize them "
    "and produce a monthly spending summary. Follow the three steps below to get started."
)

st.divider()

# --- Step 1: File upload ---
st.subheader("Step 1 — Upload your transactions CSV")
uploaded_file = st.file_uploader(
    "Drag and drop or click to browse",
    type=["csv"],
    help="Required columns: date (YYYY-MM-DD), description, amount",
)

st.divider()

# --- Step 2: Categorization rules ---
st.subheader("Step 2 — Categorization rules")
st.caption(
    "Each row maps a spending category to a regex pattern matched against the transaction description. "
    "You can edit existing rows or add new ones."
)

with st.expander("Edit rules", expanded=False):
    default_rules = [
        ("Groceries",     r"carrefour|mercadona|aldi|lidl"),
        ("Transport",     r"uber|bolt|metro|renfe|cabify"),
        ("Subscriptions", r"netflix|spotify|prime|hbo"),
        ("Eating Out",    r"restaurant|cafe|starbucks|mcdonald"),
    ]
    rules_df = pd.DataFrame(default_rules, columns=["category", "pattern"])
    edited_rules_df = st.data_editor(
        rules_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "category": st.column_config.TextColumn("Category", help="e.g. Groceries"),
            "pattern":  st.column_config.TextColumn("Regex pattern", help="e.g. carrefour|lidl"),
        },
    )
    st.caption("Tip: patterns are case-insensitive. Use `|` to match multiple keywords in one rule.")

ruleset = RuleSet()
for _, row in edited_rules_df.iterrows():
    cat = str(row["category"]).strip()
    pat = str(row["pattern"]).strip()
    if cat and pat:
        ruleset.add(RegexRule(cat, pat))

categorizer = Categorizer(ruleset)

st.divider()

# --- Step 3: Results ---
st.subheader("Step 3 — Results")

if uploaded_file is None:
    st.info(
        "No file uploaded yet. Complete Step 1 above to see your categorized transactions and spending summary.",
        icon="👆",
    )
else:
    df = pd.read_csv(uploaded_file)

    # Save temporarily to reuse the package loader (Path-based generator)
    temp_path = Path("temp_transactions.csv")
    df.to_csv(temp_path, index=False)

    txs = list(stream_transactions_csv(temp_path))
    categorized = categorizer.categorize_all(txs)

    categorized_df = pd.DataFrame(
        [
            {
                "Date":        t.tx_date.isoformat(),
                "Description": t.description,
                "Amount":      t.amount,
                "Currency":    t.currency,
                "Category":    t.category if t.category else "Uncategorized",
            }
            for t in categorized
        ]
    )

    # KPI metric cards
    total_txns    = len(categorized_df)
    total_spend   = categorized_df["Amount"].sum()
    n_categories  = categorized_df["Category"].nunique()
    uncategorized = (categorized_df["Category"] == "Uncategorized").sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total transactions", total_txns)
    k2.metric("Total spend", f"{total_spend:,.2f}")
    k3.metric("Categories found", n_categories)
    k4.metric("Uncategorized", uncategorized, help="Transactions that didn't match any rule")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Categorized transactions**")
        st.dataframe(
            categorized_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Amount": st.column_config.NumberColumn(format="%.2f"),
            },
        )

    with col2:
        summary = summarize_by_month_and_category(categorized)
        summary_df = pd.DataFrame(summary).T.fillna(0)
        st.markdown("**Monthly summary by category**")
        st.dataframe(
            summary_df.style.format("{:.2f}"),
            use_container_width=True,
        )

    st.divider()
    st.markdown("**Category totals by month**")
    st.bar_chart(summary_df)

    with st.expander("Raw data preview"):
        st.dataframe(df, use_container_width=True, hide_index=True)
