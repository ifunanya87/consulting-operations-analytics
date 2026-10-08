import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

DB_PATH = "/workspaces/consulting-operations-analytics/data_modeling/dev.duckdb"

# DATA LOADING & MERGING
def load_dashboard_3_data():
    """Loads and merges DuckDB tables (Invoices, Clients, Projects, Payments) for Dashboard 3."""
    conn = duckdb.connect(DB_PATH, read_only=True)

    fi = conn.execute("SELECT * FROM main.fact_invoices").fetchdf()
    dc = conn.execute("SELECT * FROM main.dim_clients").fetchdf()
    fpp = conn.execute("SELECT * FROM main.fact_project_performance").fetchdf()
    fp = conn.execute("SELECT * FROM main.fact_payments").fetchdf()
    dp = conn.execute("SELECT * FROM main.dim_projects").fetchdf()

    conn.close()

    # Join Client metadata
    fi_merged = fi.merge(
        dc[["Client_ID", "Client_Name", "Industry", "Province", "Region", "Payment_Terms_Days", "Client_Priority"]], 
        on="Client_ID", 
        how="left"
    )

    # Join Project Name from dim_projects
    fi_merged = fi_merged.merge(
        dp[["Project_ID", "Project_Name"]],
        on="Project_ID",
        how="left"
    )

    # Join Project Performance status
    fi_merged = fi_merged.merge(
        fpp[["Project_ID", "Project_Status"]],
        on="Project_ID",
        how="left"
    )

    # Join Payment records
    fi_merged = fi_merged.merge(
        fp[["Invoice_ID", "Payment_Date", "Payment_Amount_CAD"]],
        on="Invoice_ID",
        how="left"
    )

    # Format Datetime Columns
    fi_merged["Invoice_Date"] = pd.to_datetime(fi_merged["Invoice_Date"])
    fi_merged["Due_Date"] = pd.to_datetime(fi_merged["Due_Date"])
    if "Payment_Date" in fi_merged.columns:
        fi_merged["Payment_Date"] = pd.to_datetime(fi_merged["Payment_Date"])

    return fi_merged, dc, fpp


def create_client_risk_matrix(client_summary):
    """
    Chart A: 2x2 Client Risk Scatter Plot (Revenue vs Outstanding AR)
    Accepts pre-aggregated client_summary DataFrame.
    """
    if client_summary.empty:
        return px.scatter(title="No Outstanding AR Data")

    # Calculate Quadrant Thresholds (Medians)
    rev_median = client_summary["Total_Invoiced"].median()
    ar_median = client_summary["Outstanding_AR"].median()

    # Assign Quadrant Label
    def assign_quadrant(row):
        if row["Total_Invoiced"] >= rev_median and row["Outstanding_AR"] >= ar_median:
            return "Critical Exposure (High Rev / High AR)"
        elif row["Total_Invoiced"] < rev_median and row["Outstanding_AR"] >= ar_median:
            return "High Debt / Low Revenue"
        elif row["Total_Invoiced"] >= rev_median and row["Outstanding_AR"] < ar_median:
            return "Healthy Key Accounts (High Rev / Low AR)"
        else:
            return "Low Exposure (Low Rev / Low AR)"

    matrix_df = client_summary.copy()
    matrix_df["Quadrant"] = matrix_df.apply(assign_quadrant, axis=1)

    # Define Quadrant Colors
    quadrant_colors = {
        "Critical Exposure (High Rev / High AR)": "#DC3545",     # Red
        "High Debt / Low Revenue": "#FD7E14",                    # Orange
        "Healthy Key Accounts (High Rev / Low AR)": "#28A745",   # Green
        "Low Exposure (Low Rev / Low AR)": "#6C757D"             # Gray
    }

    # Scatter Plot
    fig_matrix = px.scatter(
        matrix_df,
        x="Total_Invoiced",
        y="Outstanding_AR",
        color="Quadrant",
        color_discrete_map=quadrant_colors,
        hover_name="Client_Name",
        hover_data={
            "Client_Name": False,
            "Total_Invoiced": ":$,.0f",
            "Outstanding_AR": ":$,.0f",
            "Max_Days_Overdue": ":.0f",
            "Quadrant": True,
            "Client_ID": True
        },
        size="Outstanding_AR",
        size_max=18,
        labels={
            "Total_Invoiced": "Total Pre-Tax Invoiced (CAD)",
            "Outstanding_AR": "Outstanding Balance (CAD)",
            "Max_Days_Overdue": "Max Days Overdue",
            "Client_ID": "Client ID"
        }
    )

    # Add Median Threshold Lines
    fig_matrix.add_hline(y=ar_median, line_dash="dash", line_color="gray", opacity=0.7)
    fig_matrix.add_vline(x=rev_median, line_dash="dash", line_color="gray", opacity=0.7)

    # Explicit logarithmic ticks
    fig_matrix.update_xaxes(
        type="log",
        tickvals=[20000, 50000, 100000, 200000, 500000, 1000000, 2000000],
        ticktext=["20k", "50k", "100k", "200k", "500k", "1M", "2M"]
    )

    fig_matrix.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title=None
        )
    )
    return fig_matrix


def create_ar_aging_schedule(filtered_fi):
    """
    Chart B: Accounts Receivable Aging Schedule Bar Chart
    """
    aging_order = ["Current", "1-30 Days", "31-90 Days", "91-365 Days", ">365 Days"]
    
    aging_df = filtered_fi.groupby("Aging_Bucket")["Outstanding_Balance"].sum().reset_index()
    aging_df = aging_df[aging_df["Outstanding_Balance"] > 0]
    aging_df["Aging_Bucket"] = pd.Categorical(aging_df["Aging_Bucket"], categories=aging_order, ordered=True)
    aging_df = aging_df.sort_values("Aging_Bucket").dropna()

    fig_aging = px.bar(
        aging_df,
        x="Aging_Bucket",
        y="Outstanding_Balance",
        text_auto=".2s",
        labels={"Outstanding_Balance": "Outstanding Balance (CAD)", "Aging_Bucket": "Aging Bucket"}
    )
    
    fig_aging.update_traces(marker_color="#8B0000")

    fig_aging.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=20, b=10)
    )
    return fig_aging


def create_top10_ar_clients_chart(client_summary):
    """
    Chart C: Horizontal Bar Chart of Top 10 Clients by Outstanding AR
    """
    top_ar_clients = client_summary.sort_values("Outstanding_AR", ascending=False).head(10)

    fig_pareto = px.bar(
        top_ar_clients,
        x="Outstanding_AR",
        y="Client_Name",
        orientation="h",
        text_auto=".2s",
        labels={"Outstanding_AR": "Outstanding AR (CAD)", "Client_Name": "Client Name"}
    )
    
    fig_pareto.update_traces(
        marker_color="#DC3545"
    )

    fig_pareto.update_layout(
        showlegend=False,
        yaxis=dict(autorange="reversed", title=""),
        margin=dict(l=180, r=20, t=10, b=20)
    )
    return fig_pareto


def create_industry_payment_delays_chart(filtered_fi):
    """
    Chart D: Bar + Line Combo Chart (Payment Terms vs Days Overdue by Industry)
    """
    industry_ar = filtered_fi[filtered_fi["Outstanding_Balance"] > 0].groupby("Industry").agg(
        Outstanding_AR=("Outstanding_Balance", "sum"),
        Avg_Days_Overdue=("Days_Past_Due", "mean"),
        Avg_Payment_Terms=("Payment_Terms_Days", "mean")
    ).reset_index()

    fig_ind_ar = go.Figure()
    
    fig_ind_ar.add_trace(go.Bar(
        x=industry_ar["Industry"],
        y=industry_ar["Avg_Days_Overdue"],
        name="Avg Days Overdue",
        marker_color="#DC3545"
    ))
    
    fig_ind_ar.add_trace(go.Scatter(
        x=industry_ar["Industry"],
        y=industry_ar["Avg_Payment_Terms"],
        name="Standard Payment Terms (Days)",
        mode="lines+markers",
        line=dict(color="#007BFF", width=3)
    ))

    fig_ind_ar.update_layout(
        yaxis_title="Days",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis=dict(tickangle=-30)
    )
    return fig_ind_ar


def create_true_dso_collection_trend(filtered_fi):
    """
    Chart E: True Historical Collection Efficiency & Cash Inflow Trend
    Groups paid invoices by Payment_Date to show actual turnaround time and cash collected.
    """
    if "Payment_Date" not in filtered_fi.columns:
        fig = go.Figure()
        fig.add_annotation(text="Payment Date column not found in dataset.", showarrow=False)
        return fig

    # Paid records with valid payment dates
    paid_df = filtered_fi[filtered_fi["Payment_Date"].notna()].copy()

    if paid_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No Paid Invoice Records Found", showarrow=False)
        return fig

    # Actual payment turnaround time (Payment_Date - Invoice_Date)
    paid_df["Days_To_Pay"] = (paid_df["Payment_Date"] - paid_df["Invoice_Date"]).dt.days
    paid_df["Payment_Month"] = paid_df["Payment_Date"].dt.to_period("M").astype(str)

    monthly_trend = paid_df.groupby("Payment_Month").agg(
        Total_Cash_Collected=("Payment_Amount_CAD", "sum"),
        Avg_Days_To_Pay=("Days_To_Pay", "mean")
    ).reset_index().sort_values("Payment_Month")

    fig_trend = go.Figure()

    # Green Bars: Actual Cash Collected
    fig_trend.add_trace(go.Bar(
        x=monthly_trend["Payment_Month"],
        y=monthly_trend["Total_Cash_Collected"],
        name="Cash Collected ($)",
        marker_color="#28A745",
        opacity=0.85
    ))

    # Blue Line: Average Turnaround Time (Days to Pay)
    fig_trend.add_trace(go.Scatter(
        x=monthly_trend["Payment_Month"],
        y=monthly_trend["Avg_Days_To_Pay"],
        name="Avg Days to Pay",
        mode="lines+markers",
        line=dict(color="#007BFF", width=2.5),
        yaxis="y2"
    ))

    fig_trend.update_layout(
        yaxis=dict(title="Cash Collected (CAD)", tickprefix="$"),
        yaxis2=dict(title="Avg Days to Pay", overlaying="y", side="right", ticksuffix=" days"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis=dict(tickangle=-45)
    )

    return fig_trend
