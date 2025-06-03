import streamlit as st
import pandas as pd
import numpy as np
import sqlite3

# --- Color formatting logic ---
def color_cells(val):
    val_str = str(val).lower()
    if "elite" in val_str:
        return "background-color: lightgreen"
    elif "strong" in val_str:
        return "background-color: lightblue"
    elif "low" in val_str:
        return "background-color: #f8d7da"
    return ""

# --- Arrow logic for changes ---
def arrow_for_change(old_val, new_val):
    try:
        old_num = float(old_val)
        new_num = float(new_val)
        if new_num > old_num:
            return f"{new_val} ▲"
        elif new_num < old_num:
            return f"{new_val} ▼"
        else:
            return str(new_val)
    except:
        if str(old_val).strip() != str(new_val).strip():
            return f"{new_val} →"
        else:
            return str(new_val)

# --- Comparison logic with MultiIndex rebuild ---
def mark_changes_multiindex(df_old, df_new, key_col):
    flat_old = df_old.copy()
    flat_old.columns = ['__'.join(col).strip() if col[0] else col[1] for col in df_old.columns]

    flat_new = df_new.copy()
    flat_new.columns = ['__'.join(col).strip() if col[0] else col[1] for col in df_new.columns]

    merged = pd.merge(flat_old, flat_new, on=key_col[1], how='outer', suffixes=('_old', '_new'))

    result = pd.DataFrame()
    result[key_col[1]] = merged[key_col[1]]

    for col in flat_new.columns:
        if col == key_col[1]:
            continue
        old_col = col + '_old'
        new_col = col + '_new'

        def get_cell(row):
            old_val = row.get(old_col, np.nan)
            new_val = row.get(new_col, np.nan)
            if pd.isna(old_val):
                return str(new_val)
            if pd.isna(new_val):
                return str(old_val) + " (removed)"
            return arrow_for_change(old_val, new_val)

        result[col] = merged.apply(get_cell, axis=1)

    new_columns = []
    for col in result.columns:
        if col == key_col[1]:
            new_columns.append(('', col))
        elif '__' in col:
            parts = col.split('__')
            new_columns.append((parts[0], parts[1]))
        else:
            new_columns.append(('', col))

    result.columns = pd.MultiIndex.from_tuples(new_columns)
    return result

# --- Streamlit App ---
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    .main, .block-container, .stApp {
        background-color: white !important;
        color: black !important;
    }
    th, td {
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Application Ratings Dashboard (May - July 2025)")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded_file:
    excel = pd.ExcelFile(uploaded_file)

    conn = sqlite3.connect(":memory:")

    def save_to_sql(sheet_name, table_name):
        df = excel.parse(sheet_name)
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
        df.columns = [str(c).strip() for c in df.columns]
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        return table_name

    save_to_sql("Sheet1", "May2025")
    save_to_sql("Sheet2", "June2025")
    save_to_sql("Sheet3", "July2025")

    def load_from_db(table):
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)

    def apply_multiindex(df):
        df.columns = pd.MultiIndex.from_tuples([
            ('', 'Application Id'),
            ('DORA', 'Lead Time'),
            ('DORA', 'Deplay Frequency'),
            ('DORA', '%Successful CR'),
            ('DORA', 'Major Incident MTTD'),
            ('Predictability', 'Backlog health'),
            ('Predictability', 'Definition of done Quality'),
            ('Predictability', 'Scope Churn'),
            ('Predictability', 'Sprint Velocity'),
            ('Predictability', 'Say Vs Do Ratio'),
            ('Developer Experience', '%Code Coverage'),
            ('Developer Experience', 'Build Breakers MTTR'),
            ('Developer Experience', 'Medial Build MTTR'),
            ('Platform Engineering', 'Observability'),
            ('Platform Engineering', 'Gitlab adoption timeline')
        ])
        return df

    may_df = apply_multiindex(load_from_db("May2025"))
    june_df = apply_multiindex(load_from_db("June2025"))
    july_df = apply_multiindex(load_from_db("July2025"))

    # Add target row
    target_row = pd.DataFrame([[
        'N/A', '1', 'Daily', '95%', '1h', 'Healthy', 'High', '<5%', 'Consistent', '>=1.0',
        '80%', '<30m', '<15m', 'Integrated', '100%'
    ]], columns=may_df.columns)
    target_row.index = ['TARGET']

    # Concatenate TARGET row to all tabs
    key_col = ('', 'Application Id')
    may_df_display = pd.concat([target_row, may_df], ignore_index=False)

    june_diff = mark_changes_multiindex(may_df, june_df, key_col)
    june_diff_display = pd.concat([target_row, june_diff], ignore_index=False)

    july_diff = mark_changes_multiindex(june_df, july_df, key_col)
    july_diff_display = pd.concat([target_row, july_diff], ignore_index=False)

    tab1, tab2, tab3 = st.tabs(["May 2025", "June 2025 (Deviation)", "July 2025 (Deviation)"])

    with tab1:
        st.subheader("May 2025 Data")
        st.dataframe(may_df_display.style.applymap(color_cells), use_container_width=True)

    with tab2:
        st.subheader("June 2025 Deviations from May")
        st.dataframe(june_diff_display.style.applymap(color_cells), use_container_width=True)

    with tab3:
        st.subheader("July 2025 Deviations from June")
        st.dataframe(july_diff_display.style.applymap(color_cells), use_container_width=True)
