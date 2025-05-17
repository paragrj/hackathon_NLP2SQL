import streamlit as st
import sqlite3
import json
import os
import logging
import io
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# Setup environment variables and OpenAI client (same as before)
DeploymentName = os.getenv("DeploymentName")
EndPoint_URL = os.getenv("EndPoint_URL")
EndPoint_KEY = os.getenv("EndPoint_KEY")

client = AzureOpenAI(
    azure_endpoint=EndPoint_URL,
    api_key=EndPoint_KEY,
    api_version='2024-12-01-preview',
)

# Load DB metadata
with open('databaseMetaData.sql', 'r') as file:
    db_file = file.read().replace('\n', '')

context = f'''Generate a SQL query ready to run 
on sqlite database based on the 
following database metadata{db_file}
that will be used to answer the user question.
Answer with a SQL query only.
'''

st.title("NLP to SQL Query Generator")

# Connect to DB
con = sqlite3.connect('database.db')

# Initialize session state variables if they don't exist
if 'user_input' not in st.session_state:
    st.session_state.user_input = ''

if 'query' not in st.session_state:
    st.session_state.query = ''

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

if 'message' not in st.session_state:
    st.session_state.message = ''

# Input form
with st.form('nlp_form'):
    user_input = st.text_area('Ask a question in natural language:', value=st.session_state.user_input)
    submit = st.form_submit_button('Submit')

if submit:
    if user_input.strip() == '':
        st.error("Please enter a valid question.")
    else:
        st.session_state.user_input = user_input

        # Call Azure OpenAI
        with st.spinner('Generating SQL query...'):
            completion = client.chat.completions.create(
                model=DeploymentName,
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.5,
                max_tokens=1000,
            )

        answer = json.loads(completion.to_json())
        message = answer['choices'][0]['message']['content']

        # Extract SQL query
        selectPos = message.upper().find("SELECT")
        semicolonPos = message[selectPos:].find(";") + selectPos
        query = message[selectPos:semicolonPos+1]

        if query == '':
            st.error("No SQL query generated. Try rephrasing your question.")
        else:
            st.session_state.query = query
            st.session_state.message = message

            # Execute query
            try:
                result = con.execute(query)
                rows = result.fetchall()
                columns = [desc[0] for desc in result.description]
                df = pd.DataFrame(rows, columns=columns)
                st.session_state.df = df
            except Exception as e:
                st.error(f"SQL execution error: {e}")

# If we have a query and df, show results and plotting
if st.session_state.query and not st.session_state.df.empty:
    tabs = st.tabs(["SQL Query", "Results Table", "Chart & Downloads"])

    with tabs[0]:
        st.subheader("Generated SQL Query")
        st.code(st.session_state.query)

    with tabs[1]:
        st.subheader("Query Results")
        st.dataframe(st.session_state.df, use_container_width=True)

    with tabs[2]:
        st.subheader("Data Visualization and Downloads")

        chart_type = st.selectbox("Select chart type", ["None", "Bar", "Line", "Area"])

        df = st.session_state.df

        if df.shape[1] == 2 and chart_type != "None":
            label_col, value_col = df.columns[0], df.columns[1]
            if pd.api.types.is_numeric_dtype(df[value_col]):
                chart_df = df.set_index(label_col)
                fig, ax = plt.subplots()

                if chart_type == "Bar":
                    chart_df.plot(kind='bar', ax=ax, legend=False)
                elif chart_type == "Line":
                    chart_df.plot(kind='line', ax=ax, legend=False)
                elif chart_type == "Area":
                    chart_df.plot(kind='area', ax=ax, legend=False)

                st.pyplot(fig)

                # Save image for download
                img_buf = io.BytesIO()
                fig.savefig(img_buf, format='png', bbox_inches='tight')
                img_buf.seek(0)
                st.download_button("📸 Download Chart as PNG", data=img_buf, file_name="chart.png", mime="image/png")

            else:
                st.info("Second column must be numeric for charting.")
        elif chart_type != "None":
            st.info("Charting requires exactly 2 columns.")

        # Prepare CSV and Excel downloads
        csv_data = df.to_csv(index=False).encode('utf-8')

        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
        excel_buffer.seek(0)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download Result as CSV", data=csv_data, file_name="query_result.csv", mime='text/csv')
        with col2:
            st.download_button("📥 Download Result as Excel", data=excel_buffer, file_name="query_result.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

con.close()
