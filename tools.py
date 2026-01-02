from db import get_schema
from llm import llm

ALLOWED_TABLES = {"users"}

# -------- SAFETY --------
def is_safe_sql(sql: str) -> bool:
    sql_upper = sql.upper()

    if not sql_upper.startswith("SELECT"):
        return False

    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]
    if any(word in sql_upper for word in forbidden):
        return False

    for token in sql_upper.split():
        if token in {"FROM", "JOIN"}:
            table = sql_upper.split(token)[1].strip().split()[0]
            if table.lower() not in ALLOWED_TABLES:
                return False

    return True


def needs_database(question: str) -> bool:
    prompt = f"""
Does this question require querying a database?
Answer only YES or NO.

Question: {question}
"""
    return "YES" in llm(prompt).upper()


def generate_sql(question: str) -> str:
    prompt = f"""
You are an expert SQL assistant.

Database schema:
{get_schema()}

Write a SQL query to answer:
{question}

Return ONLY the SQL query.
"""
    return llm(prompt)


def answer_with_data(question: str, data):
    prompt = f"""
Answer the question using ONLY the data below.

Question: {question}
Data: {data}
"""
    return llm(prompt)
