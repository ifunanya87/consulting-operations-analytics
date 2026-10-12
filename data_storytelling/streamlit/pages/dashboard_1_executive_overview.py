import pandas as pd
import streamlit as st
import plotly.express as px

from utils.d1_utils import (
    compute_executive_kpis,
    load_d1_tables_from_duckdb,
    plot_margin_waterfall,
    plot_revenue_trend,
)
from utils.helper_functions import calculate_rf_feature_importance


st.title("Executive Financial & Performance Overview")
st.markdown(
    "### High-level revenue performance, gross margin leakage, and regional breakdown."
)

# Load Data
projects_df, invoices_df = load_d1_tables_from_duckdb()

# INTERACTIVE SIDEBAR SLICERS
st.sidebar.header("Filter Options")
provinces = sorted(projects_df["Province"].dropna().unique())
selected_provinces = st.sidebar.multiselect(
    "Select Province:", options=provinces, default=provinces
)

industries = sorted(projects_df["Industry"].dropna().unique())
selected_industries = st.sidebar.multiselect(
    "Select Industry:", options=industries, default=industries
)

service_lines = sorted(projects_df["Service_Line"].dropna().unique())
selected_servicelines = st.sidebar.multiselect(
    "Select Service Line:", options=service_lines, default=service_lines
)

# Project Status Filter (Excludes 'Cancelled' by default to align with AR logic)
project_statuses = sorted([p for p in projects_df["Project_Status"].dropna().unique()])
default_project_statuses = [p for p in project_statuses if p.lower() != "cancelled"]

selected_project_statuses = st.sidebar.multiselect(
    "Select Project Status:",
    options=project_statuses,
    default=default_project_statuses
)

# Filter Data
filt_projects = projects_df[
    (projects_df["Province"].isin(selected_provinces))
    & (projects_df["Industry"].isin(selected_industries))
    & (projects_df["Service_Line"].isin(selected_servicelines))
    & (projects_df["Project_Status"].isin(selected_project_statuses))
]

filt_invoices = invoices_df[
    (invoices_df["Province"].isin(selected_provinces))
    & (invoices_df["Industry"].isin(selected_industries))
    & (invoices_df["Service_Line"].isin(selected_servicelines))
    & (invoices_df["Project_Status"].isin(selected_project_statuses))
]

# Calculate KPIs & Regression
kpis = compute_executive_kpis(filt_projects, filt_invoices)

# EXECUTIVE KPI CARDS
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Invoiced Revenue", f"${kpis['invoiced_revenue_pretax']/1e6:.2f}M")
col2.metric("Gross Profit", f"${kpis['total_gross_profit']/1e6:.2f}M")
col3.metric(
    label="Gross Margin %",
    value=f"{kpis['gross_margin_pct']:.1f}%",
    delta=f"{kpis['margin_delta']:+.1f}% vs Target (35%)",
    delta_color="normal",
)
col4.metric(
    "Total Outstanding AR",
    f"${kpis['total_outstanding_ar']/1e6:.2f}M",
    delta="Cash Flow Risk",
    delta_color="inverse",
)
col5.metric("Total Projects", f"{kpis['project_count']}")

st.markdown("---")

# CHARTS SECTION
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
  st.subheader("Monthly Revenue Stability (Invoiced vs 3M SMA)")
  st.plotly_chart(plot_revenue_trend(filt_invoices), use_container_width=True)

with row1_col2:
  st.subheader("Gross Margin Leakage Bridge")
  if kpis["OLS_model"] is not None and kpis["delay_p_val"] < 0.05:
    st.caption(
        f"OLS Active: Schedule delay significant (p = {kpis['delay_p_val']:.3f})."
    )
  else:
    st.caption(
        f"OLS Inactive: Schedule delay non-significant (p ="
        f" {kpis['delay_p_val']:.3f}). 100% leakage attributed to labor hours."
    )

  fig_waterfall = plot_margin_waterfall(
      kpis["gross_margin_pct"], kpis["schedule_impact"], kpis["cost_overrun_impact"]
  )
  st.plotly_chart(fig_waterfall, use_container_width=True)

# MODEL DIAGNOSTICS
with st.expander(
    "**Advanced Statistical & Machine Learning Model Diagnostics**",
    expanded=False,
):
  tab_ols, tab_rf = st.tabs(
      ["OLS Regression Parameters", "Random Forest Feature Importance"]
  )

  with tab_ols:
    if kpis["OLS_model"] is not None:
      m_col1, m_col2, m_col3 = st.columns(3)
      m_col1.metric(
          "Slope (Delay_Years)",
          f"{kpis['OLS_model'].params.get('Delay_Years', 0.0):.4f}",
      )
      m_col2.metric("R-Squared (R²)", f"{kpis['OLS_model'].rsquared:.3f}")
      m_col3.metric("p-value", f"{kpis['delay_p_val']:.4f}")

      st.markdown("**Parameters Breakdown:**")
      params_df = pd.DataFrame({
          "Coefficient": kpis["OLS_model"].params,
          "Std Error": kpis["OLS_model"].bse,
          "t-value": kpis["OLS_model"].tvalues,
          "p-value": kpis["OLS_model"].pvalues,
      })
      st.dataframe(params_df.style.format("{:.4f}"), use_container_width=True)
      st.text("Full OLS Summary Output:")
      st.code(str(kpis["OLS_model"].summary()), language="text")
    else:
      st.warning(
          "Insufficient data points in current filter selection to fit an OLS"
          " model."
      )

  with tab_rf:
    try:
      rf_model, importance_df = calculate_rf_feature_importance(
          filt_projects, filt_invoices
      )
      if importance_df is not None:
        rf_col1, rf_col2 = st.columns([1, 1])
        with rf_col1:
          st.markdown("### Operational Leakage Attribution")
          st.write(
              "While Linear Regression tests individual statistical impact,"
              "**Random Forest captures complex, non-linear patterns across variables**. "
              "This breakdown shows the percentage of margin leakage caused by each operational factor."
          )
          st.dataframe(
              importance_df.sort_values(
                  by="Importance_Pct", ascending=False
              ).style.format({"Importance_Pct": "{:.1f}%"}),
              use_container_width=True,
          )

        with rf_col2:
          fig_rf = px.bar(
              importance_df,
              x="Importance_Pct",
              y="Feature",
              orientation="h",
              text=importance_df["Importance_Pct"].apply(lambda x: f"{x:.1f}%"),
              title="Margin Leakage Drivers (% Contribution)",
              labels={"Importance_Pct": "Importance Score (%)", "Feature": ""},
          )
          fig_rf.update_traces(
              marker_color="#1E64C8", textposition="outside", cliponaxis=False
          )
          fig_rf.update_layout(
              showlegend=False,
              height=320,
              margin=dict(l=150, r=50, t=50, b=40),
              xaxis=dict(
                  range=[0, max(importance_df["Importance_Pct"]) * 1.25]
              ),
          )
          st.plotly_chart(fig_rf, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Key Takeaways")
        col_a, col_b, col_c = st.columns(3)

        st.markdown(
            """**1. Labor Effort (35.0%)**  
            *Primary Leakage Driver*  
            Margin loss is directly caused by unbilled team hours, not calendar duration."""
        )

        with col_b:
            st.markdown(
                """**2. Budget Scale (33.9%)**  
                *Risk Buffer*  
                Larger contracts absorb scope creep better than small fixed-fee engagements."""
            )

        with col_c:
            st.markdown(
                """**3. Schedule Delay (31.1%)**  
                *Indirect Catalyst*  
                Delays don't burn cash on their own—they give staff more time to over-burn hours."""
            )
        st.info(
            "**Executive Summary:** Calendar delays alone do not erode margin."
            " A delayed project that stays strictly within budgeted hours"
            " preserves its target margin, whereas any project that over-burns"
            " labor hours loses margin regardless of delivery speed."
        )
      else:
        st.warning(
            "Not enough project rows selected to run Random Forest feature"
            " attribution."
        )
    except Exception as rf_err:
      st.error(
          "Random Forest model calculation could not run with current filter"
          f" selection: {rf_err}"
      )

st.markdown("---")

# ROW 2: GEOGRAPHIC & SECTOR DISTRIBUTIONS
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
  st.subheader("Geographic Revenue Distribution (Provinces)")
  prov_df = (
      filt_invoices.groupby("Province")["Invoice_Subtotal_CAD"]
      .sum()
      .reset_index()
      .sort_values(by="Invoice_Subtotal_CAD", ascending=True)
  )
  fig_prov = px.bar(
      prov_df, x="Invoice_Subtotal_CAD", y="Province", orientation="h", text_auto=".2s"
  )
  fig_prov.update_traces(marker_color="#1E64C8")
  fig_prov.update_layout(
      showlegend=False,
      xaxis_title="Total Invoiced Revenue (CAD)",
      margin=dict(l=20, r=20, t=30, b=20),
  )
  st.plotly_chart(fig_prov, use_container_width=True)

with row2_col2:
  st.subheader("Revenue by Industry Sector")
  ind_df = (
      filt_invoices.groupby("Industry")["Invoice_Subtotal_CAD"]
      .sum()
      .reset_index()
      .sort_values(by="Invoice_Subtotal_CAD", ascending=False)
  )
  fig_ind = px.bar(
      ind_df, x="Industry", y="Invoice_Subtotal_CAD", text_auto=".2s"
  )
  fig_ind.update_traces(marker_color="#1E64C8")
  fig_ind.update_layout(
      showlegend=False,
      yaxis_title="Total Invoiced Revenue (CAD)",
      margin=dict(l=20, r=20, t=30, b=20),
  )
  st.plotly_chart(fig_ind, use_container_width=True)


# INSIGHTS
st.markdown("---")
st.markdown("#### Key Takeaways")

row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
  st.markdown(
      "**1. Solid Revenue Foundation**<br>"
      "*\\$35.98M Invoiced Revenue*<br>"
      "The business generated \\$35.98M across 238 completed projects. "
      "Monthly revenue shows steady long-term growth, though short-term "
      "billing fluctuates between \\$0.5M and \\$1.6M.",
      unsafe_allow_html=True,
  )

with row1_col2:
  st.markdown(
      "**2. Labor Overruns Erode Margins**<br>"
      "*7.0% Gross Margin Leakage*<br>"
      "Delivered gross margin stands at 28.0%, falling short of the 35.0% "
      "target benchmark. OLS regression confirms 100% of this "
      "leakage is caused by excess labor hours rather than schedule delays.",
      unsafe_allow_html=True,
  )

with row1_col3:
  st.markdown(
      "**3. High Outstanding Receivables**<br>"
      "*\\$7.21M Cash Flow Risk*<br>"
      "Over 20% of total invoiced revenue remains uncollected in outstanding "
      "accounts receivable (\\$7.21M), creating substantial cash flow "
      "drag and working capital exposure.",
      unsafe_allow_html=True,
  )

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
  st.markdown(
      "**4. Regional Market Concentration**<br>"
      "*Ontario Leads Delivery*<br>"
      "Ontario generates the largest share of revenue at \\$14M, "
      "followed by Quebec (\\$7.3M), Alberta (\\$6.2M), and "
      "British Columbia (\\$6.1M), while Atlantic/Midwest markets "
      "lag behind.",
      unsafe_allow_html=True,
  )

with row2_col2:
  st.markdown(
      "**5. Sector-Driven Diversification**<br>"
      "*Tech & Energy Lead Portfolio*<br>"
      "Revenue is well spread across key industries, led by Technology "
      "(\\$6.9M), Energy & Utilities (\\$5.2M), and Government "
      "(\\$5.0M), with lower exposure in Manufacturing (\\$870k) "
      "and Insurance (\\$470k).",
      unsafe_allow_html=True,
  )

st.info(
    "**Summary:** Total invoiced revenue reached \\$35.98M across 238 projects, "
    "with strong regional performance led by Ontario (\\$14M) and industry demand "
    "concentrated in Technology (\\$6.9M), Energy (\\$5.2M), and Public Sector (\\$5.0M). "
    "However, profitability is strained as delivered gross margin fell to 28.0% against "
    "a 35.0% target. This 7.0% margin gap is entirely driven by "
    "unbilled labor hour overruns rather than schedule delays. "
    "Additionally, cash flow is constrained by \\$7.21M in outstanding accounts "
    "receivable. Management should enforce stricter budget controls "
    "on project labor hours and strengthen collections to recover outstanding cash."
)
