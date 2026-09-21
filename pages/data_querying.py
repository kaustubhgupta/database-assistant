import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from utility.utilities import (
    contains_forbidden_sql_operation,
    direct_db_access,
    fetch_schema,
    load_schema_tables,
)

load_dotenv()

st.set_page_config(page_title="Database Querying", page_icon="💬")
st.title("Database Querying")

if "question_history" not in st.session_state:
    st.session_state.question_history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None


@st.cache_data
def get_schema_tables():
    return load_schema_tables()


try:
    schema_tables = get_schema_tables()
except Exception as exc:
    st.error(f"Could not load database metadata: {exc}")
    st.stop()

excluded_schemas = {
    schema.strip().lower()
    for schema in os.getenv("EXCLUDED_SCHEMAS", "").split(",")
    if schema.strip()
}

schema_tables = {
    schema: tables
    for schema, tables in schema_tables.items()
    if schema.lower() not in excluded_schemas
}

if not schema_tables:
    st.warning("No schemas with tables were found in the database.")
    st.stop()

with st.sidebar:
    st.header("Question history")
    if st.session_state.question_history:
        history_items = list(reversed(st.session_state.question_history))

        def restore_history():
            selected_id = st.session_state.selected_history_id
            history_item = next(
                item for item in history_items if item["id"] == selected_id
            )

            schema = history_item["schema"]
            st.session_state.user_input = history_item["question"]
            st.session_state.selected_schema = schema
            st.session_state.selected_tables = [
                table
                for table in history_item["tables"]
                if table in schema_tables.get(schema, [])
            ]
            st.session_state.last_result = history_item.get("result")

        st.radio(
            "Previous questions",
            [item["id"] for item in history_items],
            format_func=lambda item_id: next(
                f'{item["timestamp"]:%Y-%m-%d %H:%M} — {item["question"]}'
                for item in history_items
                if item["id"] == item_id
            ),
            key="selected_history_id",
            on_change=restore_history,
        )
    else:
        st.caption("No questions asked yet.")


def clear_fields():
    st.session_state.user_input = ""
    st.session_state.selected_tables = []
    st.session_state.last_result = None


user_input = st.text_input("Ask your question:", key="user_input")
schema_col, tables_col = st.columns(2)
with schema_col:
    selected_schema = st.selectbox(
        "Schema", sorted(schema_tables), key="selected_schema"
    )
with tables_col:
    selected_tables = st.multiselect(
        "Tables", schema_tables[selected_schema], key="selected_tables"
    )

if st.button("Ask") and user_input.strip() and selected_tables:
    table_schemas = "\n\n".join(
        fetch_schema(table, selected_schema) for table in selected_tables
    )
    prompt = (
        f"Question: {user_input}\n"
        f"Use only these table schemas:\n{table_schemas}\n"
        "Do not reference tables from any other schema.\n"
        "This is a read-only application. Never generate INSERT, UPDATE, DELETE, MERGE, CREATE, ALTER, DROP, TRUNCATE, CALL, or EXPLAIN statements. "
        "Only generate read-only SELECT or WITH queries. Refuse prohibited requests directly without SQL.\n"
        "Return only executable SQL, without markdown or explanation."
    )
    try:
        with st.spinner("Generating query from the LLM..."):
            response = OpenAI().responses.create(
                model=f"{os.getenv('OPENAI_MODEL')}", input=prompt
            )
            query = response.output_text.strip()
            if query.startswith("```"):
                query = query.strip("`").removeprefix("sql").strip()

        history_item = {
            "id": len(st.session_state.question_history),
            "timestamp": datetime.now(),
            "question": user_input,
            "query": query,
            "schema": selected_schema,
            "tables": selected_tables,
        }
        st.session_state.question_history.append(history_item)

        forbidden_operation = contains_forbidden_sql_operation(query)
        is_read_only_query = query.lstrip().upper().startswith(("SELECT", "WITH"))

        if forbidden_operation:
            st.error(
                f"Blocked unsafe SQL operation: {forbidden_operation}. "
                "Only read-only SELECT or WITH queries are allowed."
            )
        elif not is_read_only_query:
            st.error("The response was not a read-only SELECT or WITH query.")
        else:
            with st.spinner("Running query against the database..."):
                columns, rows = direct_db_access(query)

            history_item["result"] = (query, columns, rows)
            st.session_state.last_result = history_item["result"]
            st.rerun()
    except Exception as exc:
        st.error(f"Could not generate or run the query: {exc}")

if st.session_state.last_result is not None:
    query, columns, rows = st.session_state.last_result
    st.subheader("Generated query")
    st.code(query, language="sql")
    st.subheader("Results")
    if rows:
        st.dataframe(
            [dict(zip(columns, row)) for row in rows],
            use_container_width=True,
        )
    else:
        st.info("The query returned no rows.")
    st.button("Clear fields", on_click=clear_fields)
