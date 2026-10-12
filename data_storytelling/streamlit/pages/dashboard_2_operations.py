import streamlit as st
from utils.d2_utils import (
    load_d2_data_from_duckdb,
    compute_dashboard_kpis,
    compute_communication_kpis,
    create_industry_contract_breakdown,
    create_utilization_benchmark_chart,
    create_csat_dropoff_box_plot,
    create_intake_risk_chart,
    create_comm_vs_csat_scatter,
    create_comm_buffer_box_plot
)



st.title("Operational Execution & Schedule Delay Analysis")
st.markdown("### Diagnostic tracking of delivery delays, customer satisfaction thresholds, and intake risk scores.")

# LOAD DATA
@st.cache_data
def get_cached_data():
    return load_d2_data_from_duckdb()

df, fts, dim_servicelines = get_cached_data()

# INTERACTIVE SIDEBAR SLICERS
st.sidebar.header("Filter Options")

# Project Status Filter (Excludes 'Cancelled' by default to align with Dashboard 1 & 3)
all_statuses = sorted([s for s in df["Project_Status"].dropna().unique()])
default_statuses = [s for s in all_statuses if s.lower() != "cancelled"]
selected_statuses = st.sidebar.multiselect("Select Project Status:", options=all_statuses, default=default_statuses)

service_lines = sorted([s for s in df["Service_Line"].dropna().unique()])
selected_servicelines = st.sidebar.multiselect("Select Service Line:", options=service_lines, default=service_lines)

project_types = sorted([t for t in df["Project_Type"].dropna().unique()])
selected_project_types = st.sidebar.multiselect("Select Project Type:", options=project_types, default=project_types)

risk_levels = sorted([r for r in df["Initial_Risk_Level"].dropna().unique()])
selected_risk_levels = st.sidebar.multiselect("Select Initial Risk Level:", options=risk_levels, default=risk_levels)

# Filter data
filtered_df = df[
    (df["Project_Status"].isin(selected_statuses)) &
    (df["Service_Line"].isin(selected_servicelines)) &
    (df["Project_Type"].isin(selected_project_types)) &
    (df["Initial_Risk_Level"].isin(selected_risk_levels))
]

# EXECUTIVE OPERATIONAL KPIS
kpis = compute_dashboard_kpis(filtered_df)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Projects", f"{kpis['total_projects']}")
col2.metric("Avg Schedule Delay", f"{kpis['avg_delay']:.1f} Days", delta="Threshold: 14 Days", delta_color="inverse")
col3.metric("Severe Delays (>14d)", f"{kpis['severe_delay_pct']:.1f}%", f"{kpis['severe_delays']} Projects", delta_color="inverse")
col4.metric("Avg Client CSAT", f"{kpis['avg_satisfaction']:.2f} / 5.0")
col5.metric("False Low-Risk Failures", f"{kpis['low_risk_failures']}", delta="Intake Mismatch", delta_color="inverse")

st.markdown("---")

# CHARTS SECTION
# ROW 1: INDUSTRY & CONTRACTING RISK ANALYSIS
st.subheader("Industry → Contract Model Delay Breakdown")
st.caption("Industry sectors grouped strictly by their primary contract type.")

fig_subplot = create_industry_contract_breakdown(filtered_df)
st.plotly_chart(fig_subplot, use_container_width=True)

st.markdown("---")

# ROW 2: BILLABLE UTILIZATION BENCHMARKING
st.subheader("Billable Utilization vs Target Benchmark")
fig_util = create_utilization_benchmark_chart(filtered_df, fts, dim_servicelines, selected_servicelines)
st.plotly_chart(fig_util, use_container_width=True)

# ROW 3: INTAKE & CLIENT SATISFACTION (CSAT) DIAGNOSTICS
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Client Satisfaction Drop-off across Delay Cohorts")
    fig_box = create_csat_dropoff_box_plot(filtered_df)
    st.plotly_chart(fig_box, use_container_width=True)

with row2_col2:
    st.subheader("Severe Delays by Initial Risk Level")
    fig_intake = create_intake_risk_chart(filtered_df)
    st.plotly_chart(fig_intake, use_container_width=True)

st.markdown("---")

# DIAGNOSTIC: COMMUNICATION IMPACT DURING DELAYS
st.subheader("Diagnostic: Communication Impact During Project Delays")
st.caption("Investigating whether high communication buffers client satisfaction drop-offs when delays set in.")

clean_comm_df, avg_high, avg_low, csat_delta = compute_communication_kpis(filtered_df)

m_col1, m_col2, m_col3 = st.columns(3)
m_col1.metric("Delayed Projects Avg CSAT (High Comm)", f"{avg_high:.2f} / 5.0")
m_col2.metric("Delayed Projects Avg CSAT (Low Comm)", f"{avg_low:.2f} / 5.0")
m_col3.metric("Communication CSAT Buffer", f"+{csat_delta:.2f} Pts", "CSAT Protection", delta_color="normal")

col_left, col_right = st.columns(2)

with col_left:
    fig_comm_csat = create_comm_vs_csat_scatter(clean_comm_df)
    st.plotly_chart(fig_comm_csat, use_container_width=True)

with col_right:
    fig_buffer = create_comm_buffer_box_plot(clean_comm_df)
    st.plotly_chart(fig_buffer, use_container_width=True)

# INSIGHTS
st.markdown("---")
st.markdown("#### Key Takeaways")

row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    st.markdown(
        """**1. Intake Model Calibration**  
        *Assessment Gap*  
        Projects classified as 'low-risk' still experience delivery delays, indicating a need to refine our initial intake evaluation."""
    )

with row1_col2:
    st.markdown(
        """**2. Communication Drives Sentiment**  
        *Primary CSAT Factor*  
        Proactive communication influences client satisfaction far more than minor schedule slippages."""
    )

with row1_col3:
    st.markdown(
        """**3. Strategic CSAT Buffer**  
        *+0.75 Rating Safety Net*  
        Delayed projects with strong communication maintain a 4.16 CSAT versus 3.41 when communication is weak."""
    )

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown(
        """**4. Execution Speed Limitations**  
        *Quality Over Timing*  
        On-time delivery yields low ratings when communication is lacking, proving speed cannot compensate for silent delivery."""
    )

with row2_col2:
    st.markdown(
        """**5. High Capacity Bottlenecks**  
        *Operational Root Cause*  
        Elevated utilization (83%–89%) reduces available non-billable hours, constraining engagement leads' ability to maintain regular updates."""
    )

st.info(
    "**Summary:** Schedule delays do not erode client trust—poor communication does. "
    "Operating at 83%–89% billable utilization starves delivery leads of the time needed to maintain client updates. "
    "However, maintaining consistent communication (>= 4.0) acts as a critical buffer (+0.75 CSAT impact), "
    "keeping satisfaction above our 3.8 target (at 4.16) during project delays. "
    "Project managers must protect dedicated time for weekly client touchpoints whenever schedule friction arises."
)
