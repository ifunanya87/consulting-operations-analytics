import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DB_PATH = "/workspaces/consulting-operations-analytics/data_modeling/dev.duckdb"

# DATA LOADING & PREPROCESSING
def assign_delay_tier(row):
    if row.get("Project_Status") == "Cancelled":
        return "Cancelled"
    elif pd.isna(row.get("Schedule_Delay_Days")):
        return "Unscheduled"
    elif row["Schedule_Delay_Days"] <= 0:
        return "Early / On-Time"
    elif row["Schedule_Delay_Days"] <= 14:
        return "1–14 Days Delay"
    elif row["Schedule_Delay_Days"] <= 30:
        return "15–30 Days Delay"
    else:
        return ">30 Days Severe Delay"


def load_d2_data_from_duckdb(db_path=DB_PATH):
    conn = duckdb.connect(db_path, read_only=True)

    fpp = conn.execute("SELECT * FROM main.fact_project_performance").fetchdf()
    fts = conn.execute("SELECT * FROM main.fact_timesheets").fetchdf()
    fcf = conn.execute("SELECT * FROM main.fact_client_feedback").fetchdf()
    dp = conn.execute("SELECT * FROM main.dim_projects").fetchdf()
    dc = conn.execute("SELECT * FROM main.dim_clients").fetchdf()
    ds = conn.execute("SELECT * FROM main.dim_servicelines").fetchdf()

    conn.close()

    df = fpp.merge(dc[["Client_ID", "Client_Name", "Industry", "Province"]], on="Client_ID", how="left")
    df = df.merge(ds[["Service_Line_ID", "Service_Line", "Target_Utilization_Pct"]], on="Service_Line_ID", how="left")
    df = df.merge(dp[["Project_ID", "Initial_Risk_Level"]], on="Project_ID", how="left")
    df = df.merge(
        fcf[["Project_ID", "Overall_Satisfaction_Score", "Delivery_Quality_Score", "Communication_Score"]], 
        on="Project_ID", 
        how="left"
    )

    df["Delay_Tier"] = df.apply(assign_delay_tier, axis=1)
    df["Start_Date"] = pd.to_datetime(df["Start_Date"])
    df["Planned_End_Date"] = pd.to_datetime(df["Planned_End_Date"])
    df["Actual_End_Date"] = pd.to_datetime(df["Actual_End_Date"])

    return df, fts, ds

# METRIC CALCULATIONS
def compute_dashboard_kpis(filtered_df):
    total_projects = filtered_df["Project_ID"].nunique()
    avg_delay = filtered_df["Schedule_Delay_Days"].mean()
    severe_delays = filtered_df[filtered_df["Schedule_Delay_Days"] > 14]["Project_ID"].nunique()
    severe_delay_pct = (severe_delays / total_projects * 100) if total_projects > 0 else 0
    avg_satisfaction = filtered_df["Overall_Satisfaction_Score"].mean()
    
    low_risk_failures = filtered_df[
        (filtered_df["Initial_Risk_Level"] == "Low") & 
        ((filtered_df["Schedule_Delay_Days"] > 14) | (filtered_df["Project_Status"] == "Cancelled"))
    ]["Project_ID"].nunique()

    return {
        "total_projects": total_projects,
        "avg_delay": avg_delay,
        "severe_delays": severe_delays,
        "severe_delay_pct": severe_delay_pct,
        "avg_satisfaction": avg_satisfaction,
        "low_risk_failures": low_risk_failures
    }

def compute_communication_kpis(filtered_df):
    comm_cols = ["Communication_Score", "Schedule_Delay_Days", "Overall_Satisfaction_Score"]
    clean_comm_df = filtered_df.dropna(subset=comm_cols).copy()

    delayed_df = clean_comm_df[clean_comm_df["Schedule_Delay_Days"] > 0].copy()
    delayed_df["Comm_Tier"] = delayed_df["Communication_Score"].apply(
        lambda x: "High Comm (≥ 4.0)" if x >= 4.0 else "Low/Mod Comm (< 4.0)"
    )

    avg_csat_high_comm = delayed_df[delayed_df["Comm_Tier"] == "High Comm (≥ 4.0)"]["Overall_Satisfaction_Score"].mean() if not delayed_df.empty else 0.0
    avg_csat_low_comm = delayed_df[delayed_df["Comm_Tier"] == "Low/Mod Comm (< 4.0)"]["Overall_Satisfaction_Score"].mean() if not delayed_df.empty else 0.0
    csat_delta = avg_csat_high_comm - avg_csat_low_comm if not delayed_df.empty else 0.0

    return clean_comm_df, avg_csat_high_comm, avg_csat_low_comm, csat_delta

# PLOTLY CHART BUILDERS
def create_industry_contract_breakdown(filtered_df):
    color_map = {
        "Early / On-Time": "#28A745",
        "1–14 Days Delay": "#FFC107",
        "15–30 Days Delay": "#FD7E14",
        ">30 Days Severe Delay": "#DC3545",
        "Cancelled / Unscheduled": "#6C757D"
    }
    tier_order = [
        "Early / On-Time", 
        "1–14 Days Delay", 
        "15–30 Days Delay", 
        ">30 Days Severe Delay", 
        "Cancelled / Unscheduled"
    ]
    contract_industry_map = {
        "Fixed Fee": ["Government/Public Sector", "Banking & Financial Services", "Education"],
        "Time & Materials": ["Technology", "Retail", "Healthcare", "Logistics & Transportation"],
        "Retainer": ["Manufacturing", "Energy & Utilities", "Insurance"]
    }

    fig_subplot = make_subplots(
        rows=2, cols=3, 
        row_heights=[0.18, 0.82],
        shared_xaxes=False,
        subplot_titles=(
            "Fixed Fee Contracts", "Retainer Contracts", "Time & Materials Contracts",
            "", "", ""
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.08
    )

    project_types = ["Fixed Fee", "Retainer", "Time & Materials"]

    for col_idx, p_type in enumerate(project_types, start=1):
        allowed_industries = contract_industry_map[p_type]
        pt_df = filtered_df[
            (filtered_df["Project_Type"] == p_type) & 
            (filtered_df["Industry"].isin(allowed_industries))
        ]
        
        top_summary = pt_df.groupby("Delay_Tier").size().reindex(tier_order, fill_value=0)
        for tier in tier_order:
            val = top_summary.get(tier, 0)
            if val > 0:
                fig_subplot.add_trace(
                    go.Bar(
                        y=[p_type], x=[val], name=tier, orientation="h",
                        marker_color=color_map[tier], showlegend=(col_idx == 1)
                    ),
                    row=1, col=col_idx
                )
                
        bot_summary = pt_df.groupby(["Industry", "Delay_Tier"]).size().reset_index(name="Count")
        for tier in tier_order:
            tier_data = bot_summary[bot_summary["Delay_Tier"] == tier]
            if not tier_data.empty:
                fig_subplot.add_trace(
                    go.Bar(
                        x=tier_data["Industry"], y=tier_data["Count"], name=tier,
                        marker_color=color_map[tier], showlegend=False
                    ),
                    row=2, col=col_idx
                )

    fig_subplot.update_layout(
        barmode="stack", height=500,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="right", x=1)
    )
    fig_subplot.update_xaxes(tickangle=-25, row=2)
    return fig_subplot

def create_utilization_benchmark_chart(df, fts, dim_servicelines, selected_servicelines):
    util_by_sl = []
    for sl in selected_servicelines:
        sl_proj_ids = df[df["Service_Line"] == sl]["Project_ID"].unique()
        sl_ts = fts[fts["Project_ID"].isin(sl_proj_ids)]
        
        tot_h = sl_ts["Hours_Worked"].sum()
        bil_h = sl_ts["Billable_Hours"].sum()
        act_util = (bil_h / tot_h * 100) if tot_h > 0 else 0
        
        target_val = dim_servicelines[dim_servicelines["Service_Line"] == sl]["Target_Utilization_Pct"].values
        target_util = (target_val[0] * 100) if len(target_val) > 0 else 75.0
        
        util_by_sl.append({
            "Service_Line": sl,
            "Actual_Utilization": round(act_util, 1),
            "Target_Utilization": round(target_util, 1)
        })

    util_df = pd.DataFrame(util_by_sl).sort_values("Actual_Utilization", ascending=True)

    fig_util = go.Figure()
    fig_util.add_trace(go.Bar(
        y=util_df["Service_Line"], x=util_df["Actual_Utilization"],
        name="Actual Utilization %", orientation="h", marker_color="#4A80C4",
        text=util_df["Actual_Utilization"].astype(str) + "%", textposition="inside"
    ))
    fig_util.add_trace(go.Scatter(
        y=util_df["Service_Line"], x=util_df["Target_Utilization"],
        name="Target Utilization %", mode="markers",
        marker=dict(color="#DC3545", size=12, symbol="line-ns-open")
    ))

    fig_util.update_layout(
        xaxis_title="Utilization Rate (%)",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig_util


def create_csat_dropoff_box_plot(filtered_df):
    tier_order = [
        "Early / On-Time",
        "1–14 Days Delay",
        "15–30 Days Delay",
        ">30 Days Severe Delay",
    ]
    
    # Define fill and border color mappings
    fill_color_map = {
        "Early / On-Time": "#75AADB",
        "1–14 Days Delay": "#BFE1FF",
        "15–30 Days Delay": "#FFA3A3",
        ">30 Days Severe Delay": "#FFD6D6",
    }
    
    border_color_map = {
        "Early / On-Time": "#0052B4",
        "1–14 Days Delay": "#6BB4FF",
        "15–30 Days Delay": "#FF0000",
        ">30 Days Severe Delay": "#FFA3A3",
    }

    box_df = filtered_df[filtered_df["Delay_Tier"].isin(tier_order)].dropna(
        subset=["Overall_Satisfaction_Score"]
    )

    # Box plot with custom fill colors
    fig_box = px.box(
        box_df,
        x="Delay_Tier",
        y="Overall_Satisfaction_Score",
        color="Delay_Tier",
        color_discrete_map=fill_color_map,
        category_orders={"Delay_Tier": tier_order},
        points="outliers",
        labels={
            "Overall_Satisfaction_Score": "CSAT Score (1-5)",
            "Delay_Tier": "Schedule Delay Tier",
        },
    )

    # Distinct border/line colors to each box trace
    fig_box.for_each_trace(
        lambda trace: trace.update(
            line_color=border_color_map.get(trace.name, "#000000")
        )
    )

    # Target hline and layout configurations
    fig_box.add_hline(
        y=3.8,
        line_dash="dash",
        line_color="#FF0000",
        annotation_text="CSAT Target (3.8)",
        annotation_position="top right",
    )
    
    fig_box.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    
    return fig_box

def create_intake_risk_chart(filtered_df):
    intake_df = filtered_df.groupby(["Initial_Risk_Level", "Delay_Tier"]).size().reset_index(name="Project_Count")
    
    # Colour mapping 
    color_map = {
        "Early / On-Time": "#28A745",          # Green
        "1–14 Days Delay": "#FFC107",          # Yellow
        "15–30 Days Delay": "#FD7E14",         # Orange
        ">30 Days Severe Delay": "#DC3545",    # Red
        "Cancelled": "#A71D2A",                # Muted Dark Crimson / Burgundy
        "Unscheduled": "#6C757D"               # Medium Neutral Gray
    }

    # Enforce category display order
    tier_order = [
        "Early / On-Time", 
        "1–14 Days Delay", 
        "15–30 Days Delay", 
        ">30 Days Severe Delay", 
        "Cancelled",
        "Unscheduled"
    ]

    fig_intake = px.bar(
        intake_df, 
        x="Initial_Risk_Level", 
        y="Project_Count", 
        color="Delay_Tier", 
        barmode="group",
        color_discrete_map=color_map,
        category_orders={"Delay_Tier": tier_order},
        labels={"Project_Count": "Project Count", "Initial_Risk_Level": "Intake Risk Tier"}
    )
    
    fig_intake.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    return fig_intake

def create_comm_vs_csat_scatter(clean_comm_df):
    fig_comm_csat = px.scatter(
        clean_comm_df, x="Communication_Score", y="Overall_Satisfaction_Score", color="Delay_Tier",
        trendline="ols", title="1. Communication Score vs. CSAT",
        labels={"Communication_Score": "Communication Score (1-5)", "Overall_Satisfaction_Score": "CSAT Score (1-5)"}
    )
    fig_comm_csat.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    return fig_comm_csat

def create_comm_buffer_box_plot(clean_comm_df):
    delay_cohorts = ["1–14 Days Delay", "15–30 Days Delay", ">30 Days Severe Delay"]
    box_delay_df = clean_comm_df[clean_comm_df["Delay_Tier"].isin(delay_cohorts)].copy()
    box_delay_df["Comm_Group"] = box_delay_df["Communication_Score"].apply(
        lambda x: "Strong Comm (≥ 4.0)" if x >= 4.0 else "Weak Comm (< 4.0)"
    )

    fig_buffer = px.box(
        box_delay_df, x="Delay_Tier", y="Overall_Satisfaction_Score", color="Comm_Group",
        category_orders={"Delay_Tier": delay_cohorts},
        title="2. CSAT Rating when Delay Sets In: Strong vs. Weak Comm",
        labels={"Overall_Satisfaction_Score": "CSAT Score (1-5)", "Delay_Tier": "Schedule Delay Tier", "Comm_Group": "Comm Quality"}
    )
    fig_buffer.add_hline(y=3.8, line_dash="dash", line_color="red", annotation_text="CSAT Target (3.8)", annotation_position="top right")
    fig_buffer.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig_buffer
