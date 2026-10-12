import streamlit as st
import pandas as pd
from utils.d3_utils import (
    load_dashboard_3_data,
    create_client_risk_matrix,
    create_ar_aging_schedule,
    create_top10_ar_clients_chart,
    create_industry_payment_delays_chart,
    create_true_dso_collection_trend
)


st.title("Working Capital, Accounts Receivable & Financing Drag")
st.markdown("### Tracking capital cost exposure, aging receivables, and client credit risk.")

# Load dataset
fi_merged, dc, fpp = load_dashboard_3_data()

# SIDEBAR FILTERS
st.sidebar.header("Filter Options")

# Date range filter based on Invoice_Date
min_date = fi_merged["Invoice_Date"].min().date()
max_date = fi_merged["Invoice_Date"].max().date()

start_date, end_date = st.sidebar.date_input(
    "Invoice Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Filter by Province
provinces = sorted([p for p in fi_merged["Province"].dropna().unique()])
selected_provinces = st.sidebar.multiselect("Select Province:", options=provinces, default=provinces)

# Filter by Industry
industries = sorted([i for i in fi_merged["Industry"].dropna().unique()])
selected_industries = st.sidebar.multiselect("Select Industry:", options=industries, default=industries)

# Filter by Invoice Status
statuses = sorted([s for s in fi_merged["Invoice_Status"].dropna().unique()])
selected_statuses = st.sidebar.multiselect("Select Invoice Status:", options=statuses, default=statuses)

# Filter by Project Status (Excludes 'Cancelled' by default to isolate active debt)
project_statuses = sorted([p for p in fi_merged["Project_Status"].dropna().unique()])
default_project_statuses = [p for p in project_statuses if p.lower() != "cancelled"]

selected_project_statuses = st.sidebar.multiselect(
    "Select Project Status:", 
    options=project_statuses, 
    default=default_project_statuses
)

# Apply Slicers
filtered_fi = fi_merged[
    (fi_merged["Invoice_Date"].dt.date >= start_date) & 
    (fi_merged["Invoice_Date"].dt.date <= end_date) &
    (fi_merged["Province"].isin(selected_provinces)) &
    (fi_merged["Industry"].isin(selected_industries)) &
    (fi_merged["Invoice_Status"].isin(selected_statuses)) &
    (fi_merged["Project_Status"].isin(selected_project_statuses))
].copy()

# EXECUTIVE KPI CARDS
total_invoiced = filtered_fi["Invoice_Subtotal_CAD"].sum()
total_outstanding_ar = filtered_fi["Outstanding_Balance"].sum()
overdue_ar = filtered_fi[filtered_fi["Days_Past_Due"] > 0]["Outstanding_Balance"].sum()

avg_days_past_due = filtered_fi[filtered_fi["Outstanding_Balance"] > 0]["Days_Past_Due"].mean()
avg_days_past_due = avg_days_past_due if not pd.isna(avg_days_past_due) else 0.0

annual_interest_rate = 0.075
capital_cost = overdue_ar * annual_interest_rate

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Invoiced", f"${total_invoiced/1e6:.2f}M")
col2.metric("Outstanding AR", f"${total_outstanding_ar/1e6:.2f}M", delta="Working Capital Lock")
col3.metric("Overdue AR (>0 Days)", f"${overdue_ar/1e6:.2f}M", delta="Credit Risk", delta_color="inverse")
col4.metric("Avg Days Past Due", f"{avg_days_past_due:.1f} Days", delta="Target: <30 Days", delta_color="inverse")
col5.metric("Financing Cost of Overdue AR", f"${capital_cost/1e3:.1f}K/yr", delta="@ 7.5% Hurdle Rate", delta_color="inverse")

st.markdown("---")

# PREPARE CLIENT SUMMARY FOR CHARTS A & C
client_summary = filtered_fi.groupby(["Client_ID", "Client_Name"]).agg(
    Total_Invoiced=("Invoice_Subtotal_CAD", "sum"),
    Outstanding_AR=("Outstanding_Balance", "sum"),
    Max_Days_Overdue=("Days_Past_Due", "max")
).reset_index()

client_summary = client_summary[client_summary["Outstanding_AR"] > 0]

# ROW 1 CHARTS
row1_col1, row1_col2 = st.columns(2)

# CHART A: 2x2 Risk Matrix
with row1_col1:
    st.subheader("Client Risk Matrix: Revenue vs. Outstanding AR")
    st.caption("Identifies high-revenue clients carrying significant unpaid balances.")

    fig_matrix = create_client_risk_matrix(client_summary)
    st.plotly_chart(fig_matrix, use_container_width=True)

# CHART B: AR Aging Schedule
with row1_col2:
    st.subheader("Accounts Receivable Aging Schedule")
    st.caption("Tracks unpaid balances by how long payments are overdue.")

    fig_aging = create_ar_aging_schedule(filtered_fi)
    st.plotly_chart(fig_aging, use_container_width=True)

# ROW 2 CHARTS
row2_col1, row2_col2 = st.columns(2)

# CHART C: Pareto Analysis (Analyzing the data to test whether the Pareto Principle holds true for overdue receivables)
with row2_col1:
    st.subheader("Top 10 High-Risk Clients")
    st.caption("Top 10 accounts holding the highest unpaid balances.")

    fig_pareto = create_top10_ar_clients_chart(client_summary)
    st.plotly_chart(fig_pareto, use_container_width=True)

# CHART D: Payment Terms vs Delays by Industry Sector
with row2_col2:
    st.subheader("Payment Friction & Delays by Industry Sector")
    st.caption("Compares standard payment terms against actual overdue days across industries.")

    fig_ind_ar = create_industry_payment_delays_chart(filtered_fi)
    st.plotly_chart(fig_ind_ar, use_container_width=True)


# ROW 3: HISTORY OF COLLECTION EFFICIENCY & CASH INFLOW
st.markdown("---")
st.subheader("Historical Collection Efficiency & Cash Inflow")
st.caption(
    "Tracks actual cash collected month-by-month along with the average days taken to receive payment, "
    "highlighting seasonal cash flow delays and collection efficiency trends."
)

fig_trend = create_true_dso_collection_trend(filtered_fi)
st.plotly_chart(fig_trend, use_container_width=True)

# INSIGHTS
st.markdown("---")
st.markdown("#### Key Takeaways")

row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    st.markdown(
        """**1. High Overdue Balance**  
        *\\$7.21M Unpaid Debt*  
        Out of \\$8.25M in open balances, 87.4% is past due. Over 76% (\\$6.3M) is more than 90 days late, including \\$4.2M overdue by more than a year."""
    )

with row1_col2:
    st.markdown(
        """**2. High Cost of Delayed Cash**  
        *\\$540.5K Annual Financing Drag*  
        Holding \\$7.21M in late payments costs the business \\$540.5K every year in interest under our 7.5% funding rate."""
    )

with row1_col3:
    st.markdown(
        """**3. Spread Across Multiple Clients**  
        *Broad Credit Risk*  
        Unpaid balances are spread across many mid-sized accounts rather than one failing client. The top 10 clients make up 41.8% (\\$3.45M) of total unpaid bills."""
    )

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown(
        """**4. Industry-Specific Delays**  
        *Key Sectors Lagging Behind*  
        Manufacturing clients take the longest to pay (over 600 days late), followed by significant delays in Education, Logistics, and Energy."""
    )

with row2_col2:
    st.markdown(
        """**5. Active Collections vs. Old Debt**  
        *Two Different Cash Flows*  
        Newer invoices are collected steadily within 40 to 65 days. The high average delay (410.5 days) is driven mostly by older, uncollected debt."""
    )
st.info(
    "**Summary:** Cash flow is heavily limited by \\$7.21M in overdue payments, which creates an annual \\$540.5K interest drag. "
    "These delays are not caused by client bankruptcies, but by weak collection follow-ups across several industries, especially "
    "Manufacturing, Education, and Logistics. While recent invoices are collected within 40 to 65 days, \\$4.2M in old debt "
    "has been left unpaid for over a year. It is recommended that management review accounts past 365 days for potential write-offs "
    "and evaluate establishing a stop-work policy on active projects with balances over 90 days past due."
)
