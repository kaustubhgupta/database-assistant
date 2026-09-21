import streamlit as st
from pathlib import Path

st.set_page_config(page_title="GenAI Bootcamp Apps", page_icon="🏠")


def master_page():
    st.title("GenAI Bootcamp Apps")
    st.write("Use the sidebar on the left to navigate to applications.")


# Add or update entries to customize the names shown in the sidebar.
PAGE_NAMES = {
    "database_querying.py": "Database Querying",
    "data_chating.py": "Data Chat",
}

pages_dir = Path(__file__).parent / "pages"
app_pages = [
    st.Page(
        str(page),
        title=PAGE_NAMES.get(page.name, page.stem.replace("_", " ").title()),
    )
    for page in sorted(pages_dir.glob("*.py"))
]

navigation = st.navigation(
    {
        "GenAI Bootcamp Apps": [
            st.Page(master_page, title="GenAI Bootcamp Apps", icon="🏠", default=True),
            *app_pages,
        ]
    }
)
navigation.run()
