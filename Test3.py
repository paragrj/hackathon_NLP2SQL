import streamlit as st
import sqlite3
import json
import os
import openai
import logging
import io
import matplotlib.pyplot as plt
import pandas as pd
import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI
from pandas.errors import ParserError

# Load environment variables
load_dotenv()

# Set up credentials
DeploymentName = os.getenv("DeploymentName")
EndPoint_URL = os.getenv("EndPoint_URL")
EndPoint_KEY = os.getenv("EndPoint_KEY")

# Logging configuration
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info("App started")

# Azure OpenAI client initialization
client = AzureOpenAI(
    azure_endpoint=EndPoint_URL,
    api_key=EndPoint_KEY,
    api_version='2024-12-01-preview',
)

# Connect to SQLite
con = sqlite3.connect('database.db')

# Utility: Refresh database metadata
def refresh_metadata():
    table_info = ""
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for (table,) in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        cols = cursor.fetchall()
        columns = ", ".join([f"{col[1]} ({col[2]})" for col in cols])
        table_info += f"Table {table}: {columns}\n"
    return table_info

def convert_possible_dates(df):
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_datetime(df[col], format="%Y-%m-%d", errors='raise')
            except (ParserError, ValueError):
                try:
                    df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors='raise')
                except (ParserError, ValueError):
                    continue
        elif pd.api.types.is_numeric_dtype(df[col]):
            if df[col].between(20000, 60000).all():  # likely Excel date serials
                try:
                    df[col] = df[col].apply(lambda x: datetime.datetime(1899, 12, 30) + datetime.timedelta(days=x))
                except:
                    pass
    return df

# App title
st.set_page_config(page_title="🏦 NLP SQL Explorer", layout="wide")
st.title("💡 Insight Squads: Your AI Lens into your Data")
st.markdown(
    "<div style='font-size:16px; color:blue;'>Empowering decision-makers through smart, natural language analytics</div>",
    unsafe_allow_html=True
)

# Sidebar Dashboards
st.sidebar.header("📊 Business Dashboards")
dashboard_option = st.sidebar.selectbox("Choose a Dashboard", (
    "None",
    "Customer Loan Summary",
    "Impairment by Type",
    "Monthly Loan Payments",
    "Top 5 Customers by Loan Amount",
    "Loans with Impairments"
))

# Upload Excel to database
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Upload Excel to Database")
uploaded_file = st.sidebar.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        for sheet_name in xls.sheet_names:
            df_sheet = xls.parse(sheet_name, parse_dates=True)
            df_sheet = convert_possible_dates(df_sheet)

            table_name = sheet_name.strip().replace(" ", "_").replace("-", "_")
            table_name = ''.join(char for char in table_name if char.isalnum() or char == '_')

            df_sheet.to_sql(table_name, con, if_exists='replace', index=False)
            st.sidebar.success(f"✅ Table '{table_name}' loaded.")
        logger.info("Excel data uploaded and imported into SQLite.")
    except Exception as e:
        st.sidebar.error(f"❌ Failed to import: {e}")
        logger.error(f"Excel import error: {e}")

# Dashboard Queries
predefined_queries = {
    "Customer Loan Summary": """
        SELECT 
        C.customer_id,
        C.first_name || ' ' || C.last_name AS FullName,
        COUNT(L.loan_id) AS TotalLoans,
        SUM(L.loan_amount) AS TotalLoanAmount
        FROM Customers C
        JOIN Loans L ON C.customer_id = L.customer_id
        GROUP BY C.customer_id, FullName
        ORDER BY TotalLoanAmount DESC;
    """,
    "Impairment by Type": """
        SELECT impairment_type, SUM(impairment_amount) AS total_impairment
        FROM Loan_Impairments
        GROUP BY impairment_type
        ORDER BY total_impairment DESC;
    """,
    "Monthly Loan Payments": """
        SELECT 
        strftime('%Y-%m', payment_date) AS Month,
        SUM(payment_amount) AS TotalPayments
        FROM Loan_Payments
        GROUP BY Month
        ORDER BY Month;
    """,
    "Top 5 Customers by Loan Amount": """
        SELECT 
        C.customer_id,
        C.first_name || ' ' || C.last_name AS FullName,
        SUM(L.loan_amount) AS TotalLoanAmount
        FROM Customers C
        JOIN Loans L ON C.customer_id = L.customer_id
        GROUP BY C.customer_id, FullName
        ORDER BY TotalLoanAmount DESC
        LIMIT 5;
    """,
    "Loans with Impairments": """
        SELECT 
        L.loan_id,
        C.first_name || ' ' || C.last_name AS FullName,
        L.loan_amount,
        SUM(I.impairment_amount) AS TotalImpairment
        FROM Loans L
        JOIN Customers C ON L.customer_id = C.customer_id
        JOIN Loan_Impairments I ON L.loan_id = I.loan_id
        GROUP BY L.loan_id, FullName, L.loan_amount
        ORDER BY TotalImpairment DESC;
    """
}

# Dashboard Output
df = pd.DataFrame()
if dashboard_option != "None":
    try:
        result = con.execute(predefined_queries[dashboard_option])
        df = pd.DataFrame(result.fetchall(), columns=[desc[0] for desc in result.description])
        st.subheader(f"📊 {dashboard_option}")
        st.dataframe(df, use_container_width=True)

        if df.shape[1] == 2 and pd.api.types.is_numeric_dtype(df[df.columns[1]]):
            chart_df = df.set_index(df.columns[0])
            st.bar_chart(chart_df)

    except Exception as e:
        logger.error(f"Dashboard query error: {e}")
        st.error(f"Dashboard error: {e}")

# Context Prompt with live metadata
context = f"""Generate a SQL query ready to run on sqlite database based on this metadata:\n{refresh_metadata()}\nReturn ONLY SQL, no explanation."""

# NLP to SQL
with st.form("sql_form"):
    user_input = st.text_area("💬 Ask a question about your data:")
    submit_btn = st.form_submit_button("Submit")

if submit_btn and user_input:
    try:
        with st.spinner("Generating SQL and fetching results..."):
            completion = client.chat.completions.create(
                model=DeploymentName,
                messages=[{"role": "system", "content": context}, {"role": "user", "content": user_input}],
                temperature=0.5,
                max_tokens=1000,
            )
            sql_text = json.loads(completion.to_json())['choices'][0]['message']['content'].strip()

            if not sql_text.strip().upper().startswith("SELECT"):
                st.warning("🤖 I couldn't understand your request as a SQL question. Please try rephrasing.")
                logger.warning(f"Non-SQL response received: {sql_text}")
            else:
                sql_query = sql_text.split(";")[0].strip() + ';'
                result = con.execute(sql_query)
                df = pd.DataFrame(result.fetchall(), columns=[desc[0] for desc in result.description])
                st.session_state['original_df'] = df

                st.subheader("📋 Results")
                st.dataframe(df, use_container_width=True)
                with st.expander("🧠 Generated SQL"):
                    st.code(sql_query)

                logger.info(f"User query: {user_input}")
                logger.info(f"Generated SQL: {sql_query}")

    except Exception as e:
        logger.error(f"SQL processing error: {e}")
        st.error(f"Something went wrong: {e}")

# Export
if 'original_df' in st.session_state:
    excel_buffer = io.BytesIO()
    st.session_state['original_df'].to_excel(excel_buffer, index=False, engine='xlsxwriter')
    st.download_button("📥 Download Excel", data=excel_buffer, file_name="query_results.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

import seaborn as sns
sns.set_theme(style="whitegrid")  # Optional: adds cleaner visuals

# Visualization
if 'original_df' in st.session_state:
    st.subheader("📈 Visualization")
    df = st.session_state['original_df']

    chart_type = st.selectbox("📊 Choose chart type", ["None", "Bar", "Line", "Area"])

    if chart_type != "None":
        try:
            fig, ax = plt.subplots(figsize=(10, 5))  # Consistent size for all charts

            # Case 1: Simple 2-column chart (e.g., Category vs Value)
            if df.shape[1] == 2 and pd.api.types.is_numeric_dtype(df[df.columns[1]]):
                chart_df = df.set_index(df.columns[0])
                if chart_type == "Bar":
                    chart_df.plot(kind='bar', ax=ax, legend=False, color="#4e79a7")
                elif chart_type == "Line":
                    chart_df.plot(kind='line', ax=ax, legend=False, marker='o', color="#f28e2b")
                elif chart_type == "Area":
                    chart_df.plot(kind='area', ax=ax, legend=False, color="#59a14f")

                ax.set_title("Chart: " + df.columns[1], fontsize=16)
                ax.set_xlabel(df.columns[0], fontsize=12)
                ax.set_ylabel(df.columns[1], fontsize=12)
                plt.xticks(rotation=45)
                fig.tight_layout()
                st.pyplot(fig)

            # Case 2: Pivoted 3-column multi-series chart
            elif df.shape[1] == 3:
                pivot_df = df.pivot(index=df.columns[1], columns=df.columns[0], values=df.columns[2])
                pivot_df = pivot_df.sort_index()

                if chart_type == "Bar":
                    pivot_df.plot(kind='bar', stacked=True, ax=ax)
                elif chart_type == "Line":
                    pivot_df.plot(kind='line', ax=ax, marker='o')
                elif chart_type == "Area":
                    pivot_df.plot(kind='area', ax=ax)

                ax.set_title("Chart: " + df.columns[2], fontsize=16)
                ax.set_xlabel(df.columns[1], fontsize=12)
                ax.set_ylabel(df.columns[2], fontsize=12)
                plt.xticks(rotation=45)
                fig.tight_layout()
                st.pyplot(fig)

            else:
                st.info("ℹ️ Please ensure your data has either 2 columns (Category + Value) or 3 columns (Category, Time, Value) to visualize.")

        except Exception as e:
            st.warning(f"⚠️ Could not render chart: {e}")



con.close()
