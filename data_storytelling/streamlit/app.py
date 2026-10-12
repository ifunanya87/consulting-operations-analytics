import streamlit as st

# Global page configuration
st.set_page_config(
    page_title="Executive Multi-Dashboard Suite",
    page_icon="📊",
    layout="wide",
)

# Pages
page_1 = st.Page(
    "pages/dashboard_1_executive_overview.py",
    title="Executive Overview",
    icon="📊",
    default=True,
)

page_2 = st.Page(
    "pages/dashboard_2_operations.py",
    title="Operations",
    icon="⚙️",
)

page_3 = st.Page(
    "pages/dashboard_3_working_capital_and_ar.py",
    title="Working Capital & AR",
    icon="💰",
)

page_4 = st.Page(
    "pages/dashboard_4_consultant_capacity.py",
    title="Consultant Capacity",
    icon="👥",
)

# Navigation menu
pg = st.navigation(
    {
        "Dashboards": [page_1, page_2, page_3, page_4]
    }
)

# Run active page
pg.run()
