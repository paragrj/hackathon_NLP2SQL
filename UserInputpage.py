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



load_dotenv()

try:
    DeploymentName = os.environ["DeploymentName"]
    EndPoint_URL = os.environ["EndPoint_URL"]
    EndPoint_KEY = os.environ["EndPoint_KEY"]

except KeyError as e:
    print(f"Environment variable {e} not found. Please check your .env file.")
    st.error(f"Environment variable {e} not found. Please check your .env file.")
    exit()

logger = logging.getLogger(__name__)
logging.basicConfig(filename='app.log', level=logging.INFO)
logger.info("Starting the NLP to SQL App")
# Set up the OpenAI client

try:
    client = AzureOpenAI(
    azure_endpoint=EndPoint_URL,
    api_key=EndPoint_KEY,
    api_version='2024-12-01-preview',
)
except Exception as e:
    print(f"Error initializing AzureOpenAI client: {e}")
    st.error(f"Error initializing AzureOpenAI client: {e}")
    exit()


with open('databaseMetaData.sql', 'r') as file:
    db_file = file.read().replace('\n', '')

context = f'''Generate a SQL query ready to run 
on sqlite database based on the 
following database metadata{db_file}
that will be used to answer the user question.
Answer with a SQL query only.

'''

st.title("NLP to SQL App")

try:
    con = sqlite3.connect('database.db')
except:
    print("Error connecting to the database. Please check if the database file exists.")
    st.error("Error connecting to the database. Please check if the database file exists.")
    exit

with st.form(key='NLP input form'):
    user_input = st.text_area('Ask a question')

    submit_button = st.form_submit_button('Submit')


    if submit_button:
        if len(user_input) == 0:
            st.error("Please enter a valid  natural language.")
            exit()

    try:
        completion = client.chat.completions.create(
    model=DeploymentName,  # Use your deployment name as the model
    messages=[
        {
            "role": "system",
            "content": context
        },
        {
            "role": "user",
            "content": user_input
        }
    ],
    temperature=0.5,
    max_tokens=1000,
)


        # completion = client.chat.completions.create(
        #       messages=[{
        #                 "role": "system",
        #                 "content": context
        #             },
        #             {   
        #                 "role": "user",
        #                 "content": user_input

        #             }
        #         ],
        #         temperature=0.5,
        #         max_tokens=1000,
        #         deployment_id=DeploymentName,
        #     )

    except Exception as e:
        print(f"Error generating SQL query:or while sending request to open AI {e}")
        st.error(f"Error generating SQL query: {e}")
        exit()

    answer = json.loads(completion.to_json())

#Preprocess the answer to get the SQL query
    Message = answer['choices'][0]['message']['content']
    selectPos = Message.upper().find("SELECT")
    # semicolonPos = Message.selectPos.find(";") + selectPos
    semicolonPos = Message[selectPos:].find(";") + selectPos
    query= Message[selectPos:semicolonPos+1]

    if len(query) == 0:
        st.error("Error: No SQL query generated.try rephasing your question.")
        exit()
    try:
        result = con.execute(query)
        resultSet= result.fetchall()
    except :
        st.error("Error executing the SQL query. Please check the query syntax.")
        exit()

    
    # with st.expander("SQL Query"):
    #     st.write('The query generated is:')
    #     st.code(query)

    #     column_names = {index+1: item[0] for index, item in enumerate(result.description)}
       
    # st.write('Result')
    # st.dataframe(resultSet,column_config=column_names, use_container_width=True)


    with st.expander("SQL Query"):
        st.write('The query generated is:')
        st.code(query)

column_names = [item[0] for item in result.description]
df = pd.DataFrame(resultSet, columns=column_names)

st.write("Result:")
st.dataframe(df, use_container_width=True)

csv_data = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Result as CSV", data=csv_data, file_name="query_result.csv", mime='text/csv')

excel_buffer = io.BytesIO()
df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
st.download_button("📥 Download Result as Excel", data=excel_buffer, file_name="query_result.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

logger.info("User input: %s", user_input)
logger.info("Message from API/Answer from API: %s", Message)
logger.info("Generated SQL query: %s", query)
logger.info("Query result: %s", resultSet)
logger.info(f'Description of the result: {result.description}')
logger.info("Execution completed successfully.")
# Close the database connection


#Graphical representation of the result


# df = pd.DataFrame(resultSet, columns=column_names)

# st.write("Result:")
# st.dataframe(df)

# Try auto-plotting if numeric data is available
# if df.shape[1] == 2:
#     label_col = df.columns[0]
#     value_col = df.columns[1]
#     if pd.api.types.is_numeric_dtype(df[value_col]):
#         st.bar_chart(df.set_index(label_col))

chart_type = st.selectbox("Select chart type", ["None", "Bar", "Line", "Area"])

if df.shape[1] == 2:
    label_col, value_col = df.columns[0], df.columns[1]
    if pd.api.types.is_numeric_dtype(df[value_col]):
        chart_df = df.set_index(label_col)
        if chart_type == "Bar":
            st.bar_chart(chart_df)
        elif chart_type == "Line":
            st.line_chart(chart_df)
        elif chart_type == "Area":
            st.area_chart(chart_df)




if df.shape[1] == 2:
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

        # Save figure to buffer
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png')
        img_buf.seek(0)

        st.download_button("📸 Download Chart as PNG", data=img_buf, file_name="chart.png", mime="image/png")




con.close()