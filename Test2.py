import streamlit as st
import sqlite3
import json
import os
import openai
import logging
import io
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI

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

# Load metadata
with open('databaseMetaData.sql', 'r') as file:
    db_file = file.read().replace('\n', '')

context = f'''Generate a SQL query ready to run on sqlite database based on this metadata:\n{db_file}\nReturn ONLY SQL, no explanation.'''

# App title
st.set_page_config(page_title="🏦 NLP SQL Explorer", layout="wide")
st.title("💡 Insight Squads: Your AI Lens into Risk Data")
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

# Connect to DB
con = sqlite3.connect('database.db')
df = pd.DataFrame()

# Upload Excel to database
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Upload Excel to Database")
uploaded_file = st.sidebar.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        for sheet_name in xls.sheet_names:
            df_sheet = xls.parse(sheet_name)

            # Sanitize table name
            table_name = sheet_name.strip().replace(" ", "_").replace("-", "_")
            table_name = ''.join(char for char in table_name if char.isalnum() or char == '_')

            # Replace table if exists
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

# NLP to SQL
with st.form("sql_form"):
    user_input = st.text_area("💬 Ask a question about your banking data:")
    submit_btn = st.form_submit_button("Submit")

if submit_btn and user_input:
    try:
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
            try:
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
                st.error(f"SQL execution error: {e}")
                logger.error(f"SQL execution error: {e}")

    except Exception as e:
        logger.error(f"SQL processing error: {e}")
        st.error(f"Something went wrong: {e}")

# Export options
if 'original_df' in st.session_state:
    excel_buffer = io.BytesIO()
    st.session_state['original_df'].to_excel(excel_buffer, index=False, engine='xlsxwriter')
    st.download_button("📥 Download Excel", data=excel_buffer, file_name="query_results.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Visualization
if 'original_df' in st.session_state:
    chart_type = st.selectbox("📈 Visualize results", ["None", "Bar", "Line", "Area"])
    df = st.session_state['original_df']
    if df.shape[1] == 2 and pd.api.types.is_numeric_dtype(df[df.columns[1]]):
        chart_df = df.set_index(df.columns[0])
        fig, ax = plt.subplots()
        if chart_type == "Bar":
            chart_df.plot(kind='bar', ax=ax, legend=False)
        elif chart_type == "Line":
            chart_df.plot(kind='line', ax=ax, legend=False)
        elif chart_type == "Area":
            chart_df.plot(kind='area', ax=ax, legend=False)
        st.pyplot(fig)

con.close()
