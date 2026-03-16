import streamlit as st
import pandas as pd
from pathlib import Path

#import the pocketwise library functions we need
from pocketwise.io import stream_transactions_csv
from pocketwise.rules import RuleSet, RegexRule
from pocketwise.engine import Categorizer
from pocketwise.reporting import summarize_by_month_and_category


#set the browser tab title and use a wide layout so tables don't get cramped
st.set_page_config(page_title="PocketWise Finance", layout="wide")

#--- Sidebar: quick-start guide ---
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


#--- Header ---
st.title("PocketWise Finance Dashboard")
st.markdown(
    "Upload your bank transactions and PocketWise will automatically categorize them "
    "and produce a monthly spending summary. Follow the three steps below to get started."
)

st.divider()

#--- Step 1: File upload ---
st.subheader("Step 1 — Upload your transactions CSV")
#file_uploader shows a drag-and-drop box and only accepts CSV files
uploaded_file = st.file_uploader(
    "Drag and drop or click to browse",
    type=["csv"],
    help="Required columns: date (YYYY-MM-DD), description, amount",
)

st.divider()

#--- Step 2: Categorization rules ---
st.subheader("Step 2 — Categorization rules")
st.caption(
    "Each row maps a spending category to a regex pattern matched against the transaction description. "
    "You can edit existing rows or add new ones."
)

#wrap the rule editor inside an expander so it doesn't take up too much space by default
with st.expander("Edit rules", expanded=False):
    #default rules: each tuple is (category, regex pattern)
    #the pipe | in regex means "or", so "carrefour|lidl" matches either word
    default_rules = [
        ("Groceries",     r"carrefour|mercadona|aldi|lidl"),
        ("Transport",     r"uber|bolt|metro|renfe|cabify"),
        ("Subscriptions", r"netflix|spotify|prime|hbo"),
        ("Eating Out",    r"restaurant|cafe|starbucks|mcdonald"),
    ]
    #convert to a DataFrame so we can display it as an editable table
    rules_df = pd.DataFrame(default_rules, columns=["category", "pattern"])
    #data_editor lets the user modify, add, or delete rows directly in the browser
    edited_rules_df = st.data_editor(
        rules_df,
        use_container_width=True,
        num_rows="dynamic",  #"dynamic" allows adding and deleting rows
        column_config={
            "category": st.column_config.TextColumn("Category", help="e.g. Groceries"),
            "pattern":  st.column_config.TextColumn("Regex pattern", help="e.g. carrefour|lidl"),
        },
    )
    st.caption("Tip: patterns are case-insensitive. Use `|` to match multiple keywords in one rule.")

#build a RuleSet from whatever the user has in the table (edited or default)
ruleset = RuleSet()
for _, row in edited_rules_df.iterrows():
    cat = str(row["category"]).strip()
    pat = str(row["pattern"]).strip()
    #only add the rule if both fields are filled in (skip empty rows)
    if cat and pat:
        ruleset.add(RegexRule(cat, pat))

#wrap the ruleset in a Categorizer so we can apply it to transactions
categorizer = Categorizer(ruleset)

st.divider()

#--- Step 3: Results ---
st.subheader("Step 3 — Results")

if uploaded_file is None:
    #show a friendly message if the user hasn't uploaded anything yet
    st.info(
        "No file uploaded yet. Complete Step 1 above to see your categorized transactions and spending summary.",
        icon="👆",
    )
else:
    #read the uploaded CSV into a pandas DataFrame
    df = pd.read_csv(uploaded_file)

    #the pocketwise loader expects a file path, so we save the upload to a temp file first
    temp_path = Path("temp_transactions.csv")
    df.to_csv(temp_path, index=False)

    #stream_transactions_csv is a generator — we convert it to a list to use it multiple times
    txs = list(stream_transactions_csv(temp_path))

    #apply the categorization rules to every transaction
    categorized = categorizer.categorize_all(txs)

    #convert the list of Transaction objects into a DataFrame for display
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

    #--- KPI metric cards at the top ---
    total_txns    = len(categorized_df)
    total_spend   = categorized_df["Amount"].sum()         #sum of all amounts (income + expenses)
    n_categories  = categorized_df["Category"].nunique()   #how many distinct categories were found
    uncategorized = (categorized_df["Category"] == "Uncategorized").sum()  #how many rows didn't match any rule

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total transactions", total_txns)
    k2.metric("Total spend", f"{total_spend:,.2f}")
    k3.metric("Categories found", n_categories)
    k4.metric("Uncategorized", uncategorized, help="Transactions that didn't match any rule")

    st.divider()

    #split the results into two side-by-side columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Categorized transactions**")
        #show the full transaction table with formatted amounts
        st.dataframe(
            categorized_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Amount": st.column_config.NumberColumn(format="%.2f"),
            },
        )

    with col2:
        #summarize_by_month_and_category returns a nested dict: { "2026-03": { "Groceries": -120.0, ... } }
        summary = summarize_by_month_and_category(categorized)
        #transpose so months are rows and categories are columns, fill missing combos with 0
        summary_df = pd.DataFrame(summary).T.fillna(0)
        st.markdown("**Monthly summary by category**")
        st.dataframe(
            summary_df.style.format("{:.2f}"),
            use_container_width=True,
        )

    st.divider()

    #bar chart: x-axis = months, bars = spending per category
    st.markdown("**Category totals by month**")
    st.bar_chart(summary_df)

    #raw data preview hidden in a collapsible section
    with st.expander("Raw data preview"):
        st.dataframe(df, use_container_width=True, hide_index=True)
