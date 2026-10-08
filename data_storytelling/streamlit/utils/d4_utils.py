import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go

DB_PATH = "/workspaces/consulting-operations-analytics/data_modeling/dev.duckdb"

def load_d4_data_from_duckdb():
    """Fetches tables from DuckDB and merges fact_client_feedback into fact_project_performance on Project_ID."""
    conn = duckdb.connect(DB_PATH, read_only=True)

    dc = conn.execute("SELECT * FROM main.dim_consultants").fetchdf()
    fts = conn.execute("SELECT * FROM main.fact_timesheets").fetchdf()
    ds = conn.execute("SELECT * FROM main.dim_servicelines").fetchdf()
    fpp = conn.execute("SELECT * FROM main.fact_project_performance").fetchdf()
    fcf = conn.execute("SELECT * FROM main.fact_client_feedback").fetchdf()

    conn.close()

    # Lookup merging for Consultants
    dc_merged = dc.merge(
        ds[["Service_Line_ID", "Service_Line", "Target_Utilization_Pct"]], 
        on="Service_Line_ID", 
        how="left"
    )

    # Join ALL client feedback metrics on Project_ID
    if "Project_ID" in fpp.columns and "Project_ID" in fcf.columns:
        fpp = fpp.merge(
            fcf.drop_duplicates(subset=["Project_ID"]), 
            on="Project_ID", 
            how="left",
            suffixes=("", "_feedback")
        )
    
    fts["Work_Date"] = pd.to_datetime(fts["Work_Date"])

    return dc_merged, fts, ds, fpp


def prepare_filtered_timesheets(fact_timesheets, fact_performance, filtered_consultants, include_cancelled=False):
    """Filters timesheets by selected consultants and calculates non-billable hours using Billable_Flag strings."""
    filtered_consultant_ids = filtered_consultants["Consultant_ID"].unique()
    filtered_fts = fact_timesheets[fact_timesheets["Consultant_ID"].isin(filtered_consultant_ids)].copy()

    # Default exclusion of cancelled projects
    if not include_cancelled and "Project_Status" in fact_performance.columns:
        active_project_ids = fact_performance[
            fact_performance["Project_Status"] != "Cancelled"
        ]["Project_ID"].unique()
        
        filtered_fts = filtered_fts[filtered_fts["Project_ID"].isin(active_project_ids)]

    # Derived time & calculation metrics
    filtered_fts["Year_Month"] = filtered_fts["Work_Date"].dt.to_period("M")
    filtered_fts["Year"] = filtered_fts["Work_Date"].dt.year.astype(str)
    
    # Calculate non-billable hours based on 'Non-Billable' string label
    if "Billable_Flag" in filtered_fts.columns:
        is_non_billable = filtered_fts["Billable_Flag"] == "Non-Billable"
        filtered_fts["Non_Billable_Hours"] = filtered_fts["Hours_Worked"].where(is_non_billable, 0)
    else:
        filtered_fts["Non_Billable_Hours"] = filtered_fts["Hours_Worked"] - filtered_fts["Billable_Hours"]

    return filtered_fts


def get_monthly_concurrency(filtered_fts, filtered_consultants):
    """Calculates peak monthly project concurrency across history for each consultant."""
    monthly_projects = (
        filtered_fts.groupby(["Consultant_ID", "Year_Month"])["Project_ID"]
        .nunique()
        .reset_index(name="Concurrent_Projects")
    )
    cons_alloc = (
        monthly_projects.groupby("Consultant_ID")["Concurrent_Projects"]
        .max()
        .reset_index(name="Active_Projects")
    )
    cons_alloc = cons_alloc.merge(
        filtered_consultants[["Consultant_ID", "Consultant_Name", "Seniority"]], 
        on="Consultant_ID", 
        how="left"
    )
    return cons_alloc


def create_allocations_chart(cons_alloc):
    """Builds Chart A: Peak Concurrent Project Allocations per Consultant."""
    top_alloc = cons_alloc.sort_values(
        "Active_Projects", ascending=False
    ).head(15)

    fig_alloc = px.bar(
        top_alloc,
        x="Active_Projects",
        y="Consultant_Name",
        orientation="h",
        color_discrete_sequence=["#2B6CB0"],
        text_auto=True,
        labels={
            "Active_Projects": "Peak Concurrent Projects",
            "Consultant_Name": "Consultant",
        },
    )

    fig_alloc.add_vline(
        x=4,
        line_dash="dash",
        line_color="red",
        annotation_text="Upper Cap (4 Projects)",
        annotation_position="top right",
    )

    fig_alloc.update_layout(
        showlegend=False,
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20, r=20, t=30, b=20),
    )
    return fig_alloc


def create_seniority_utilization_chart(filtered_fts, filtered_consultants):
    """Builds Chart B: Utilization Spread by Seniority Tier (Box Plot)."""
    ind_util = filtered_fts.groupby("Consultant_ID").agg(
        Tot_H=("Hours_Worked", "sum"),
        Bil_H=("Billable_Hours", "sum")
    ).reset_index()
    ind_util["Utilization_Pct"] = (ind_util["Bil_H"] / ind_util["Tot_H"]) * 100
    ind_util = ind_util.merge(
        filtered_consultants[["Consultant_ID", "Seniority", "Consultant_Name"]], 
        on="Consultant_ID"
    )

    fig_util_box = px.box(
        ind_util,
        x="Seniority",
        y="Utilization_Pct",
        color="Seniority",
        points="all",
        hover_name="Consultant_Name",
        labels={"Utilization_Pct": "Utilization Rate (%)", "Seniority": "Seniority Tier"}
    )
    
    fig_util_box.add_hline(y=75.0, line_dash="dash", line_color="green", annotation_text="Target Benchmark (75%)")
    fig_util_box.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    return fig_util_box


def create_task_drag_chart(filtered_fts):
    """Builds Chart C: Non-Billable Hours Breakdown by Task Category."""
    # Filter explicitly by the 'Non-Billable' label or non-zero Non_Billable_Hours
    non_billable_df = (
        filtered_fts[filtered_fts["Billable_Flag"] == "Non-Billable"]
        if "Billable_Flag" in filtered_fts.columns
        else filtered_fts[filtered_fts["Non_Billable_Hours"] > 0]
    )

    task_drag = (
        non_billable_df.groupby("Task_Category")["Hours_Worked"]
        .sum()
        .reset_index(name="Non_Billable_Hours")
        .sort_values("Non_Billable_Hours", ascending=False)
    )

    if task_drag.empty:
        fig_task = px.bar(
            title="No Non-Billable Hours Recorded for Current Selection"
        )
        return fig_task

    fig_task = px.bar(
        task_drag,
        x="Non_Billable_Hours",
        y="Task_Category",
        orientation="h",
        text_auto=".2s",
        color_discrete_sequence=["#2B6CB0"],
        labels={
            "Non_Billable_Hours": "Non-Billable Hours",
            "Task_Category": "Task Category",
        },
    )

    fig_task.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis=dict(autorange="reversed"),
    )
    return fig_task


def create_capacity_comparison_chart(filtered_fts, filtered_consultants):
    """Builds Chart D: Actual Billable Hours vs Expected Target Billable Capacity per Service Line."""

    # Aggregate yearly actual billable hours by Service Line
    sl_actuals_yearly = (
        filtered_fts.merge(
            filtered_consultants[["Consultant_ID", "Service_Line"]],
            on="Consultant_ID",
        )
        .groupby(["Service_Line", "Year"])["Billable_Hours"]
        .sum()
        .reset_index()
    )

    # Convert Year column to string to ensure reliable discrete color mapping
    sl_actuals_yearly["Year"] = sl_actuals_yearly["Year"].astype(str)

    # Calculate Expected Target Billable Capacity directly from filtered_consultants
    # Each consultant's target hours = Expected_Annual_Available_Hours * Target_Utilization_Pct
    sl_capacity = (
        filtered_consultants.assign(
            Consultant_Target_Hours=filtered_consultants[
                "Expected_Annual_Available_Hours"
            ]
            * filtered_consultants["Target_Utilization_Pct"]
        )
        .groupby("Service_Line")["Consultant_Target_Hours"]
        .sum()
        .reset_index(name="Target_Billable_Capacity")
        .sort_values("Service_Line")
    )

    # 3. Merge actuals with target capacity and sort
    sl_comparison = sl_actuals_yearly.merge(
        sl_capacity, on="Service_Line"
    ).sort_values(["Service_Line", "Year"])
    service_line_order = sl_capacity["Service_Line"].tolist()

    # Color mapping
    blue_year_map = {
        "2023": "#2B6CB0",  # Muted Steel Blue
        "2024": "#4A90E2",  # Balanced Mid-Blue
        "2025": "#8ECAE6",  # Light Sky Blue
    }

    # Grouped Bar Chart
    fig_cap = px.bar(
        sl_comparison,
        x="Service_Line",
        y="Billable_Hours",
        color="Year",
        barmode="group",
        color_discrete_map=blue_year_map,
        labels={
            "Billable_Hours": "Actual Billable Hours",
            "Service_Line": "Service Line",
            "Year": "Year",
        },
        category_orders={"Service_Line": service_line_order},
    )

    # Overlay red dashed lines matching target billable capacity
    for idx, row in sl_capacity.iterrows():
        x_pos = service_line_order.index(row["Service_Line"])

        fig_cap.add_shape(
            type="line",
            x0=x_pos - 0.4,
            x1=x_pos + 0.4,
            y0=row["Target_Billable_Capacity"],
            y1=row["Target_Billable_Capacity"],
            line=dict(color="Red", width=2, dash="dash"),
        )

    fig_cap.update_layout(
        yaxis_title="Hours",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        margin=dict(l=20, r=20, t=30, b=20),
    )

    return fig_cap


def _clean_year_month(df, date_col_options=["Actual_End_Date", "Feedback_Date", "Work_Date"]):
    """Extracts a clean YYYY-MM string from datetime, numeric, or string date columns.
    """
    for col in date_col_options:
        if col in df.columns:
            # Parse datetime
            parsed_dates = pd.to_datetime(df[col], errors="coerce")
            
            # If successful, convert directly to YYYY-MM
            if parsed_dates.notna().any():
                return parsed_dates.dt.to_period("M").astype(str)
            
            # Fallback for string/float dates
            clean_str = (
                df[col]
                .astype(str)
                .str.replace(r"\.0$", "", regex=True)
                .str.strip()
            )
            return clean_str

    # Final fallback if no standard date column is found
    if "Year" in df.columns:
        return df["Year"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
        
    raise KeyError("Could not find a valid date or Year column to derive Year-Month.")


def create_csat_vs_utilization_chart(filtered_fts, filtered_consultants, fact_performance):
    """Generates a 3x2 faceted scatter plot grid showing CSAT vs Monthly Utilization Rate,
    modulating point size by Communication_Score with individual OLS trendlines per Service Line.
    """
    
    # Merge Timesheets with Consultants & Derive YearMonth
    fts_copy = filtered_fts.copy()
    fts_copy["YearMonth"] = _clean_year_month(fts_copy, date_col_options=["Work_Date", "Actual_End_Date"])
    
    fts_sl = fts_copy.merge(
        filtered_consultants[["Consultant_ID", "Service_Line"]], 
        on="Consultant_ID"
    )
    
    actuals = (
        fts_sl.groupby(["Service_Line", "YearMonth"])["Billable_Hours"]
        .sum()
        .reset_index()
    )

    # Calculate Monthly Target Capacity per Service Line
    capacity = (
        filtered_consultants.assign(
            Monthly_Target_Hours=(
                filtered_consultants["Expected_Annual_Available_Hours"] 
                * filtered_consultants["Target_Utilization_Pct"] 
                / 12.0
            )
        )
        .groupby("Service_Line")["Monthly_Target_Hours"]
        .sum()
        .reset_index(name="Monthly_Capacity_Hours")
    )

    # Calculate Monthly Utilization Rate (%)
    util_df = actuals.merge(capacity, on="Service_Line")
    util_df["Utilization_Pct"] = (util_df["Billable_Hours"] / util_df["Monthly_Capacity_Hours"]) * 100

    # Process Project Feedback and derive YearMonth
    fpp_copy = fact_performance.copy()
    
    if "Service_Line" not in fpp_copy.columns and "Service_Line_ID" in fpp_copy.columns:
        sl_lookup = filtered_consultants[["Service_Line_ID", "Service_Line"]].drop_duplicates()
        fpp_copy = fpp_copy.merge(sl_lookup, on="Service_Line_ID", how="left")

    fpp_copy["YearMonth"] = _clean_year_month(fpp_copy)

    # Ensure Communication_Score exists
    if "Communication_Score" in fpp_copy.columns and not fpp_copy["Communication_Score"].isnull().all():
        # Fill missing entries with the overall average of existing scores
        avg_score = fpp_copy["Communication_Score"].mean()
        fpp_copy["Communication_Score"] = fpp_copy["Communication_Score"].fillna(avg_score)
    else:
        # if missing entirely use neutral fallback (neutral midpoint on a 1–5 scale) 
        fpp_copy["Communication_Score"] = 3.0

    # Aggregate Average CSAT Score AND Communication Score per Service Line & YearMonth
    csat_df = (
        fpp_copy.groupby(["Service_Line", "YearMonth"])
        .agg(
            CSAT_Score=("Overall_Satisfaction_Score", "mean"),
            Comm_Score=("Communication_Score", "mean")
        )
        .reset_index()
    )

    # Combine Datasets
    corr_df = util_df.merge(csat_df, on=["Service_Line", "YearMonth"]).dropna(
        subset=["Utilization_Pct", "CSAT_Score", "Comm_Score"]
    )

    # Scatter Plot with Size Modulated by Communication Score
    fig = px.scatter(
        corr_df,
        x="Utilization_Pct",
        y="CSAT_Score",
        size="Comm_Score",
        size_max=12,
        color="Service_Line",
        facet_col="Service_Line",
        facet_col_wrap=2,
        trendline="ols",
        hover_data={"YearMonth": True, "Comm_Score": ":.2f", "CSAT_Score": ":.2f"},
        title="CSAT vs. Monthly Utilization Rate (%) (Point Size = Communication Score)",
        labels={
            "Utilization_Pct": "Utilization (%)",
            "CSAT_Score": "CSAT Score",
            "Comm_Score": "Avg Comm Score",
            "Service_Line": "Service Line",
            "YearMonth": "Period"
        }
    )

    # Clean up header labels
    fig.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))

    # Overlay 85% Threshold Line across all subplots
    for row in range(1, 4):
        for col in range(1, 3):
            fig.add_vline(
                x=85.0,
                line_dash="dash",
                line_color="red",
                opacity=0.75,
                row=row,
                col=col
            )

    fig.update_xaxes(range=[0, 220])
    fig.update_yaxes(range=[2.8, 4.8])

    fig.update_layout(
        showlegend=False,
        height=620,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig


def create_csat_deepdive_chart(
    fact_performance,
    filtered_consultants=None,
    target_service_line="Cloud & Digital Delivery",
):
    """Compares CSAT (bars) with Communication Score (overlaid line) for a selected service line."""

    fpp_copy = fact_performance.copy()

    if (
        "Service_Line" not in fpp_copy.columns
        and "Service_Line_ID" in fpp_copy.columns
    ):
        if filtered_consultants is not None:
            sl_lookup = filtered_consultants[
                ["Service_Line_ID", "Service_Line"]
            ].drop_duplicates()
            fpp_copy = fpp_copy.merge(sl_lookup, on="Service_Line_ID", how="left")

    fpp_copy["YearMonth"] = _clean_year_month(fpp_copy)

    sl_perf = fpp_copy[fpp_copy["Service_Line"] == target_service_line]

    if "Communication_Score" in sl_perf.columns and not sl_perf["Communication_Score"].isnull().all():
        # Use average of existing scores to impute missing values
        mean_score = sl_perf["Communication_Score"].mean()
        sl_perf["Communication_Score"] = sl_perf["Communication_Score"].fillna(mean_score)
    else:
        # use scale neutral fallback if empty
        sl_perf["Communication_Score"] = 3.0

    monthly_scores = (
        sl_perf.groupby("YearMonth")
        .agg(
            Overall_CSAT=("Overall_Satisfaction_Score", "mean"),
            Communication=("Communication_Score", "mean"),
        )
        .reset_index()
        .dropna(subset=["Overall_CSAT"])
        .sort_values("YearMonth")
    )

    fig_deepdive = go.Figure()

    # Overall CSAT Bars
    fig_deepdive.add_trace(
        go.Bar(
            x=monthly_scores["YearMonth"],
            y=monthly_scores["Overall_CSAT"],
            name="Overall CSAT",
            marker_color="#1f77b4",
            cliponaxis=False,
            hovertemplate="<b>YearMonth</b>: %{x}<br><b>Overall CSAT</b>: %{y:.2f}<extra></extra>",
        )
    )

    # Fixed Y-coordinate at y=2.0 for straight horizontal CSAT label alignment
    fig_deepdive.add_trace(
        go.Scatter(
            x=monthly_scores["YearMonth"],
            y=[2.0] * len(monthly_scores),
            text=monthly_scores["Overall_CSAT"].round(2),
            mode="text",
            textposition="middle center",
            textfont=dict(size=6, color="white", family="Arial Black"),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Communication Score Overlay Line
    fig_deepdive.add_trace(
        go.Scatter(
            x=monthly_scores["YearMonth"],
            y=monthly_scores["Communication"],
            name="Comm Score",
            mode="lines+markers",
            line=dict(color="#FF7F0E", width=3),
            marker=dict(size=8, symbol="circle", color="#FF7F0E"),
            hovertemplate="<b>YearMonth</b>: %{x}<br><b>Comm Score</b>: %{y:.2f}<extra></extra>",
        )
    )

    fig_deepdive.update_xaxes(type="category", tickangle=-45)

    fig_deepdive.update_layout(
        title=dict(
            text=f"<b>{target_service_line}</b>: CSAT & Communication Score Trend",
            x=0,
            xanchor="left",
        ),
        yaxis=dict(title="Score (1-5)", range=[0, 5.2]),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        height=620,
        margin=dict(l=20, r=20, t=70, b=30),
    )

    return fig_deepdive
