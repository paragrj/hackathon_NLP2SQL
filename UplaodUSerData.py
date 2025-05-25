import streamlit as st
import pandas as pd
import sqlite3
import io

st.title("📥 Excel to SQLite Table Uploader")

# Upload Excel file
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    # Read all sheets
    excel_data = pd.read_excel(uploaded_file, sheet_name=None)

    # Connect to SQLite DB
    con = sqlite3.connect("uploaded_data.db")
    cursor = con.cursor()

    st.success(f"Loaded {len(excel_data)} sheets. Creating tables...")

    for sheet_name, df in excel_data.items():
        # Sanitize table name
        table_name = sheet_name.strip().replace(" ", "_")

        # Create table
        df.columns = [col.strip().replace(" ", "_") for col in df.columns]
        df.to_sql(table_name, con, if_exists="replace", index=False)

        st.write(f"✅ Table created: `{table_name}` ({len(df)} rows)")
        st.dataframe(df.head())

    con.close()
    st.success("All tables created and data inserted successfully!")
