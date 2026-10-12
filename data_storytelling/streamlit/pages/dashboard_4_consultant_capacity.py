import streamlit as st
from utils.d4_utils import (
    load_d4_data_from_duckdb,
    prepare_filtered_timesheets,
    get_monthly_concurrency,
    create_allocations_chart,
    create_task_drag_chart,
    create_seniority_utilization_chart,
    create_capacity_comparison_chart,
    create_csat_vs_utilization_chart,
    create_csat_deepdive_chart
)


st.title("Consultant Workload, Capacity & Dependency Risk")
st.markdown("### Tracking talent allocation efficiency, single-point dependency detection, and non-billable leakage.")

# Load dataset
@st.cache_data
def load_data():
    return load_d4_data_from_duckdb()

dim_consultants, fact_timesheets, dim_servicelines, fact_performance = load_data()

# INTERACTIVE SIDEBAR SLICERS
st.sidebar.header("Filter Options")

service_lines = sorted([s for s in dim_consultants["Service_Line"].dropna().unique()])
selected_servicelines = st.sidebar.multiselect("Select Service Line:", options=service_lines, default=service_lines)

seniority_levels = sorted([s for s in dim_consultants["Seniority"].dropna().unique()])
selected_seniority = st.sidebar.multiselect("Select Seniority:", options=seniority_levels, default=seniority_levels)

statuses = sorted([st_val for st_val in dim_consultants["Employment_Status"].dropna().unique()])
selected_statuses = st.sidebar.multiselect("Select Employment Status:", options=statuses, default=statuses)

# Toggle for excluding 'Cancelled' by default
include_cancelled = st.sidebar.checkbox("Include Cancelled Projects", value=False)

# Apply Slicers
filtered_consultants = dim_consultants[
    (dim_consultants["Service_Line"].isin(selected_servicelines)) &
    (dim_consultants["Seniority"].isin(selected_seniority)) &
    (dim_consultants["Employment_Status"].isin(selected_statuses))
]

filtered_fts = prepare_filtered_timesheets(
    fact_timesheets=fact_timesheets,
    fact_performance=fact_performance,
    filtered_consultants=filtered_consultants,
    include_cancelled=include_cancelled
)

# EXECUTIVE CAPACITY KPIS
total_consultants = filtered_consultants["Consultant_ID"].nunique()
total_hours = filtered_fts["Hours_Worked"].sum()
billable_hours = filtered_fts["Billable_Hours"].sum()
non_billable_hours = total_hours - billable_hours
overall_utilization = (billable_hours / total_hours * 100) if total_hours > 0 else 0.0

cons_alloc = get_monthly_concurrency(filtered_fts, filtered_consultants)
overallocated_consultants = cons_alloc[cons_alloc["Active_Projects"] > 4]["Consultant_ID"].nunique()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Active Consultants", f"{total_consultants}")
col2.metric("Billable Utilization", f"{overall_utilization:.1f}%", delta="Target: 75.0%", delta_color="normal")
col3.metric("Over-Allocated (>4 Prj)", f"{overallocated_consultants}", delta="Dependency Risk", delta_color="inverse")
col4.metric("Total Worked Hours", f"{total_hours:,.0f} hrs")
col5.metric("Non-Billable Drag", f"{non_billable_hours:,.0f} hrs", delta=f"{100 - overall_utilization:.1f}% Non-Billable", delta_color="inverse")

st.markdown("---")

# CHARTS SECTION
row1_col1, row1_col2 = st.columns(2)

# CHART A: Single-Point Dependency
with row1_col1:
    st.subheader("Consultant Workload & Single-Point Dependency")
    st.caption("Highlights peak monthly project concurrency across history to detect key-person risks.")
    fig_alloc = create_allocations_chart(cons_alloc)
    st.plotly_chart(fig_alloc, use_container_width=True)

# CHART B: Utilization Spread
with row1_col2:
    st.subheader("Utilization Rate Distribution by Seniority")
    st.caption("Evaluates capacity distribution across management vs delivery tiers.")
    fig_util_box = create_seniority_utilization_chart(filtered_fts, filtered_consultants)
    st.plotly_chart(fig_util_box, use_container_width=True)

row2_col1, row2_col2 = st.columns(2)

# CHART C: Non-Billable Hours Breakdown by Task Category
with row2_col1:
    st.subheader("Non-Billable Labour Drag by Task Category")
    st.caption("Itemized breakdown of non-billable hours.")
    fig_task = create_task_drag_chart(filtered_fts)
    st.plotly_chart(fig_task, use_container_width=True)

# CHART D: Total Billable Hours vs Expected Capacity by Service Line
with row2_col2:
    st.subheader("Annual Capacity Delivery Efficiency by Service Line")
    fig_cap = create_capacity_comparison_chart(filtered_fts, filtered_consultants)
    st.plotly_chart(fig_cap, use_container_width=True)

st.markdown("---")
st.subheader("Capacity vs. Quality Analysis")

row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    fig_corr = create_csat_vs_utilization_chart(
        filtered_fts, 
        filtered_consultants, 
        fact_performance
    )
    st.plotly_chart(fig_corr, use_container_width=True)

with row3_col2:
    selected_sl = st.selectbox(
        "Select Service Line to Inspect CSAT:",
        options=filtered_consultants["Service_Line"].unique(),
        index=0
    )
    fig_deepdive = create_csat_deepdive_chart(
        fact_performance, 
        filtered_consultants, 
        target_service_line=selected_sl
    )
    st.plotly_chart(fig_deepdive, use_container_width=True)


# INSIGHTS
st.markdown("---")
st.markdown("#### Key Takeaways")

row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    st.markdown(
        """**1. Strong Utilization Rate**  
        *85.9% Overall Utilization*  
        Across 80 active consultants, billable utilization comfortably beats the 75.0% target. Execution is led by Senior Consultants and Analysts at 90%–92% utilization."""
    )

with row1_col2:
    st.markdown(
        """**2. Severe Key-Person Dependency**  
        *7 Consultants Over-Allocated*  
        7 consultants exceed the 4-project upper cap, led by Abigail Bennett on 8 concurrent projects and 6 others on 5 projects, exposing key accounts to delivery risk."""
    )

with row1_col3:
    st.markdown(
        """**3. Heavy Non-Billable Drag**  
        *41,692 Hours Lost (14.1%)*  
        Non-billable leakage is dominated by Sales Support at 20,000 hours, indicating senior delivery staff are heavily burdened with presales and proposal work."""
    )

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown(
        """**4. Communication Drives CSAT**  
        *Updates Protect Project Quality*  
        High utilization alone does not erode client satisfaction. Overall CSAT drops to historic lows specifically when Communication Scores fall to approximately 3.0."""
    )

with row2_col2:
    st.markdown(
        """**5. Strategic Allocation Gap**  
        *Underutilized Talent Buffer*  
        While senior delivery tiers are stretched thin, junior tier utilization drops as low as 68%, highlighting a clear opportunity to rebalance active project workloads."""
    )

st.info(
    "**Summary:** The organization demonstrates strong performance with an "
    "85.9% billable utilization rate across 80 active consultants, exceeding "
    "the 75.0% benchmark. However, growth is threatened by critical reliance "
    "on key staff, led by Abigail Bennett managing 8 projects, and a 14.1% "
    "non-billable drag (41,692 hours). Additionally, client satisfaction is "
    "highly sensitive to communication quality during peak delivery phases. "
    "It is recommended that management reassign projects to under-utilized "
    "staff, deploy dedicated sales engineering support to reduce presales "
    "burden, and standardize client communication protocols to stabilize "
    "CSAT scores. "
)
