import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="GenAI Bootcamp Apps",
    page_icon="🏠",
)


def master_page():
    st.title("GenAI Bootcamp Apps")
    st.write(
        "This homepage provides access to the applications built during the "
        "GenAI Bootcamp. Use the sidebar on the left to explore the available "
        "apps.\n\n"
        "1. Database Querying: An app that allows you to query a database using natural language.\n"
        "2. Data Chat: An app that enables you to chat with your data, asking questions and receiving insights.\n"
    )


PAGE_NAMES = {
    "data_querying.py": "Data Querying",
    "data_chating.py": "Data Chat",
    "database_assisstant.py": "Database Assistant",
}

PAGE_ORDER = ["data_querying.py", "data_chating.py", "database_assisstant.py"]

pages_dir = Path(__file__).parent / "pages"

app_pages = []

for page_name in PAGE_ORDER:
    page_path = pages_dir / page_name

    if page_path.exists():
        app_pages.append(
            st.Page(
                str(page_path),
                title=PAGE_NAMES.get(
                    page_name,
                    page_path.stem.replace("_", " ").title(),
                ),
            )
        )

navigation = st.navigation(
    {
        "GenAI Bootcamp Apps": [
            st.Page(
                master_page,
                title="GenAI Bootcamp Apps",
                icon="🏠",
                default=True,
            ),
            *app_pages,
        ]
    }
)

navigation.run()
