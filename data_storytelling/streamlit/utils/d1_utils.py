import duckdb
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from .helper_functions import calculate_delay_multiplier


DB_PATH = (
    "/workspaces/consulting-operations-analytics/data_modeling/dev.duckdb"
)


@st.cache_data
def load_d1_tables_from_duckdb(db_path=DB_PATH):
  """Fetches raw tables independently from DuckDB and performs lightweight,

  in-memory dimension lookups using Pandas.
  """
  conn = duckdb.connect(db_path, read_only=True)

  fpp = conn.execute("SELECT * FROM main.fact_project_performance").fetchdf()
  fi = conn.execute("SELECT * FROM main.fact_invoices").fetchdf()
  dc = conn.execute("SELECT * FROM main.dim_clients").fetchdf()
  ds = conn.execute("SELECT * FROM main.dim_servicelines").fetchdf()

  conn.close()

  # Enrich PROJECT FACT TABLE
  projects_df = fpp.merge(
      dc[["Client_ID", "Client_Name", "Industry", "Province", "Region"]],
      on="Client_ID",
      how="left",
  )
  projects_df = projects_df.merge(
      ds[["Service_Line_ID", "Service_Line", "Target_Margin_Pct"]],
      on="Service_Line_ID",
      how="left",
  )

  projects_df["Start_Date"] = pd.to_datetime(projects_df["Start_Date"])
  projects_df["Planned_End_Date"] = pd.to_datetime(
      projects_df["Planned_End_Date"]
  )
  projects_df["Actual_End_Date"] = pd.to_datetime(
      projects_df["Actual_End_Date"]
  )

  # Enrich INVOICE FACT TABLE
  invoices_df = fi.merge(
      dc[["Client_ID", "Province", "Industry"]], on="Client_ID", how="left"
  )
  invoices_df = invoices_df.merge(
      projects_df[["Project_ID", "Service_Line"]].drop_duplicates(),
      on="Project_ID",
      how="left",
  )

  invoices_df["Invoice_Date"] = pd.to_datetime(invoices_df["Invoice_Date"])

  return projects_df, invoices_df


def plot_revenue_trend(filt_invoices):
  monthly_df = (
      filt_invoices.set_index("Invoice_Date")
      .resample("ME")["Invoice_Subtotal_CAD"]
      .sum()
      .reset_index()
  )
  monthly_df["3M_SMA"] = (
      monthly_df["Invoice_Subtotal_CAD"].rolling(window=3).mean()
  )

  fig = go.Figure()
  fig.add_trace(
      go.Scatter(
          x=monthly_df["Invoice_Date"],
          y=monthly_df["Invoice_Subtotal_CAD"],
          mode="lines+markers",
          name="Monthly Invoiced",
          line=dict(color="#1E64C8", width=2.5),
      )
  )
  fig.add_trace(
      go.Scatter(
          x=monthly_df["Invoice_Date"],
          y=monthly_df["3M_SMA"],
          mode="lines",
          name="3-Month Moving Avg",
          line=dict(dash="dash", color="#22A355", width=2),
      )
  )
  fig.update_layout(
      xaxis_title="Timeline",
      yaxis_title="Invoiced Revenue (CAD)",
      legend=dict(
          orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
      ),
      margin=dict(l=20, r=20, t=30, b=20),
  )
  return fig


def plot_margin_waterfall(gross_margin_pct, schedule_impact, cost_overrun_impact, target_margin_pct=35.0):
  actual_margin = float(gross_margin_pct) if gross_margin_pct else 0.0

  fig = go.Figure(
      go.Waterfall(
          name="Margin Erosion",
          orientation="v",
          measure=["absolute", "relative", "relative", "total"],
          x=[
              "Target Benchmark",
              "Schedule Delay Impact",
              "Labour Overrun Impact",
              "Delivered Gross Margin",
          ],
          textposition="outside",
          text=[
              f"{target_margin_pct:.1f}%",
              f"{schedule_impact:.1f}%",
              f"{cost_overrun_impact:.1f}%",
              f"{actual_margin:.1f}%",
          ],
          y=[
              target_margin_pct,
              schedule_impact,
              cost_overrun_impact,
              actual_margin,
          ],
          connector={"line": {"color": "#A0AEC0", "width": 1.5}},
          decreasing={"marker": {"color": "#E03E3E"}},
          increasing={"marker": {"color": "#22A355"}},
          totals={"marker": {"color": "#1E64C8"}},
      )
  )

  y_max = max(target_margin_pct, actual_margin) * 1.15
  fig.update_layout(
      yaxis=dict(title="Margin Percentage (%)", range=[0, y_max]),
      margin=dict(l=20, r=20, t=30, b=20),
      showlegend=False,
  )
  return fig


def compute_executive_kpis(
    filt_projects, filt_invoices, target_margin=35.0, default_multiplier=0.5
):
  invoiced_revenue_pretax = filt_invoices["Invoice_Subtotal_CAD"].sum()
  total_labour_cost = filt_projects["Total_Actual_Labour_Cost"].sum()
  total_gross_profit = invoiced_revenue_pretax - total_labour_cost
  gross_margin_pct = (
      (total_gross_profit / invoiced_revenue_pretax * 100)
      if invoiced_revenue_pretax > 0
      else 0
  )
  margin_delta = gross_margin_pct - target_margin
  total_outstanding_ar = filt_invoices["Outstanding_Balance"].sum()
  project_count = filt_projects["Project_ID"].nunique()

  # Leakage calculations
  total_margin_leakage = gross_margin_pct - target_margin
  dynamic_multiplier, OLS_model = calculate_delay_multiplier(
      filt_projects, filt_invoices, default_multiplier=default_multiplier
  )

  delay_p_val = (
      OLS_model.pvalues.get("Delay_Years", 1.0)
      if OLS_model is not None
      else 1.0
  )

  if OLS_model is not None and delay_p_val < 0.05:
    delayed_projects = filt_projects[filt_projects["Schedule_Delay_Days"] > 0]
    total_delay_impact = (
        delayed_projects["Schedule_Delay_Days"].sum() / 365.0
    ) * dynamic_multiplier
    schedule_impact = -round(
        min(total_delay_impact, abs(total_margin_leakage)), 1
    )
  else:
    schedule_impact = 0.0

  cost_overrun_impact = round(total_margin_leakage - schedule_impact, 1)

  return {
      "invoiced_revenue_pretax": invoiced_revenue_pretax,
      "total_gross_profit": total_gross_profit,
      "gross_margin_pct": gross_margin_pct,
      "margin_delta": margin_delta,
      "total_outstanding_ar": total_outstanding_ar,
      "project_count": project_count,
      "schedule_impact": schedule_impact,
      "cost_overrun_impact": cost_overrun_impact,
      "OLS_model": OLS_model,
      "delay_p_val": delay_p_val,
  }
