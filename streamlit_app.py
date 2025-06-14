import os
import pyodbc
import google.generativeai as genai

# Set your API key
api_key = 'AIzaSyCcSDXlQVJQMgEe1RvNrhRj9eD0DrlH9Nc'

if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is not set.")

# Configure Gemini
genai.configure(api_key=api_key)

# Correct model reference
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# SQL Server connection string
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=dcdocstgdb01.dc68032.easn.morningstar.com;"
    "Database=DocumentAcquisition;"
    "UID=DocuUser;"
    "PWD=StagTest@1"
)

# Connect to DB
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
except pyodbc.Error as e:
    print(f"❌ Database connection failed: {e}")
    exit(1)

def generate_sql_from_nl(nl_query):
    """
    Uses Gemini to convert NL query to SQL.
    """
    try:
        prompt = f"Convert this natural language query into a valid SQL statement for SQL Server: {nl_query}"
        response = model.generate_content(prompt)
        generated = response.text.strip()

        # Optional: basic validation
        if not generated.lower().startswith("select") and "from" not in generated.lower():
            raise ValueError("Generated SQL doesn't look valid.")

        return generated
    except Exception as e:
        return f"❌ Error generating SQL: {e}"

def execute_sql(sql_query):
    """
    Executes SQL and returns results.
    """
    if sql_query.startswith("❌"):
        return sql_query
    try:
        cursor.execute(sql_query)
        return cursor.fetchall()
    except Exception as e:
        return f"❌ Error executing query: {e}"

def main():
    print("✅ Welcome to the AI-powered Data Query Tool (Gemini Edition)")
    nl_query = input("🧠 Enter your natural language query: ")
    sql_query = generate_sql_from_nl(nl_query)
    print(f"\n📝 Generated SQL:\n{sql_query}")
    results = execute_sql(sql_query)
    print("\n📊 Query Results:")
    if isinstance(results, str):  # Error
        print(results)
    else:
        for row in results:
            print(row)

if __name__ == "__main__":
    try:
        main()
    finally:
        cursor.close()
        conn.close()
