import os
import pyodbc
import streamlit as st
import google.generativeai as genai

# ========== CONFIGURATION ==========
# Hardcoded API Key (only for local testing)
api_key = 'AIzaSyCcSDXlQVJQMgEe1RvNrhRj9eD0DrlH9Nc'

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# SQL Server connection string
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=dcdocstgdb01.dc68032.easn.morningstar.com;"
    "Database=DocumentAcquisition;"
    "UID=DocuUser;"
    "PWD=StagTest@1"
)

@st.cache_resource
def get_db_connection():
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as e:
        st.error(f"❌ Database connection failed: {e}")
        return None

def generate_sql_from_nl(nl_query):
    try:
        prompt = f"Convert this natural language query into a valid SQL statement for SQL Server: {nl_query}"
        response = model.generate_content(prompt)
        generated = response.text.strip()
        if not generated.lower().startswith("select") or "from" not in generated.lower():
            raise ValueError("Generated SQL doesn't look valid.")
        return generated
    except Exception as e:
        return f"❌ Error generating SQL: {e}"

def execute_sql(conn, sql_query):
    if sql_query.startswith("❌"):
        return sql_query
    try:
        cursor = conn.cursor()
        cursor.execute(sql_query)
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        return columns, results
    except Exception as e:
        return f"❌ Error executing query: {e}"

# ========== STREAMLIT UI ==========

st.set_page_config(page_title="Gemini SQL Assistant", layout="wide")
st.title("💬 Gemini SQL Assistant")
st.markdown("Convert natural language to SQL and run queries on your SQL Server database.")

# Natural Language Query Input
nl_query = st.text_input("🧠 Enter your question:", placeholder="e.g., show top 10 documents created in last week")

if st.button("Generate & Run Query"):
    if nl_query.strip() == "":
        st.warning("Please enter a query.")
    else:
        with st.spinner("Thinking with Gemini..."):
            sql_query = generate_sql_from_nl(nl_query)
        st.code(sql_query, language='sql')

        conn = get_db_connection()
        if conn:
            with st.spinner("Executing SQL..."):
                result = execute_sql(conn, sql_query)

            if isinstance(result, str):  # error
                st.error(result)
            else:
                columns, rows = result
                if rows:
                    st.success("✅ Query executed successfully!")
                    st.dataframe([dict(zip(columns, row)) for row in rows])
                else:
                    st.info("No data returned from the query.")
