import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

st.set_page_config(page_title="Simple Auto Finance App", page_icon="💰", layout="wide")

category_file = "categories.json"

if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": []
    }

if os.path.exists(category_file):
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)

def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)

def categories_transactions(df):
    df["Category"] = "Uncategorized"

    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue

        lowered_keywords = [keyword.lower().strip() for keyword in keywords]

        for idx, row in df.iterrows():
            details = row["Details"].lower().strip()
            if details in lowered_keywords:
                df.at[idx, "Category"] = category
    return df

def load_transactions(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]
        df["Amount"] = df["Amount"].str.replace(",", "").astype(float)
        df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y")

        st.write(df)
        return categories_transactions(df)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False

def main():
    st.title("Simple Finance Dashboard")

    st.markdown("""
        ### How to Download a ".csv" Bank Statement
        1. Log in to your bank's online portal.
        2. Navigate to 'Statements' or 'Transaction History'.
        3. Select your account and desired date range.
        4. Choose 'CSV' as the download format (if available).
        5. Save the file to your computer and upload it below.
        """)

    uploaded_file = st.file_uploader("Upload your transaction CSV file", type=["csv"])

    st.markdown("""
                        ### OR
                        Use the Sample Bank Statement
                        """)
    if st.button('Press to use Sample Bank Statement'):
        st.session_state.uploaded_file = "sample_bank_statement.csv"

    current_file = uploaded_file if uploaded_file is not None else st.session_state.get("uploaded_file")


    if current_file is not None:
        df = load_transactions(current_file)

        if df is not None:
            debits_df = df[df["Debit/Credit"] == "Debit"].copy()
            credits_df = df[df["Debit/Credit"] == "Credit"].copy()

            st.session_state.debits_df = debits_df.copy()
            st.session_state.credits_df = credits_df.copy()

            tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])
            with tab1:
                new_category = st.text_input("New Category Name")
                add_button = st.button("Add Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()

                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.debits_df[["Date","Details","Amount","Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="MM/DD/YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f AED"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"
                )

                save_button = st.button("Apply Changes", type="primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]
                        if row["Category"] == st.session_state.debits_df.at[idx, "Category"]:
                            continue

                        details = row["Details"]
                        st.session_state.debits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details)

                st.subheader('Expense Summary')
                category_totals = st.session_state.debits_df.groupby("Category")["Amount"].sum().reset_index()
                category_totals = category_totals.sort_values("Amount", ascending=False)

                st.dataframe(
                    category_totals,
                    column_config={
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f AED")
                    },
                    use_container_width=True,
                    hide_index=True
                )

                st.subheader("Pie Chart")
                fig_pie = px.pie(
                    category_totals,
                    values="Amount",
                    names="Category",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
                fig_pie.update_traces(textinfo="percent+label", hovertemplate="%{label}: %{value:.2f} AED")
                fig_pie.update_layout(margin=dict(t=30, l=25, r=25, b=25))
                st.plotly_chart(fig_pie, use_container_width=True)

                st.subheader("Bar Chart")
                fig_bar = px.bar(
                    category_totals,
                    x="Category",
                    y="Amount",
                    color="Amount",
                    color_continuous_scale="Blues",
                    text="Amount",
                    height=500
                )
                fig_bar.update_traces(texttemplate="%{text:.2f} AED", textposition="auto")
                fig_bar.update_layout(
                    xaxis_title="Category",
                    yaxis_title="Amount (AED)",
                    xaxis_tickangle=45,
                    showlegend=False,
                    margin=dict(t=30, l=25, r=25, b=100)
                )
                st.plotly_chart(fig_bar, use_container_width=True)


            with tab2:
                st.subheader("Payment Summary")
                total_payments = credits_df["Amount"].sum()
                st.metric("Total Payment", f"{total_payments:,.2f} AED")
                st.write(credits_df)

main()