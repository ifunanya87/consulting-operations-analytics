# Consulting Operations & Financial Analytics Storytelling

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![dbt](https://img.shields.io/badge/dbt-Core-orange?logo=dbt)](https://www.getdbt.com/)
[![DuckDB](https://img.shields.io/badge/Database-DuckDB-yellow?logo=duckdb)](https://duckdb.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?logo=streamlit)](https://streamlit.io/)
[![Power BI DAX](https://img.shields.io/badge/Power_BI-DAX_Measures-yellow?logo=powerbi)](./data_storytelling/Powerbi_dax_measures.md)
[![Status](https://img.shields.io/badge/Status-In_Progress-yellowgreen)](#-project-status)

This is a data analysis and storytelling project focused on the operational and financial performance of a consulting firm. It cleans, models, and explores operational data to discover what drives **margin leakage**, **project delays**, **consultant availability**, and **invoice collections** using Streamlit for interactive web storytelling and DAX measures for Power BI reporting.

> **Project Status:** The interactive Streamlit analytics suite is fully complete and live. I am currently expanding this project into Power BI to showcase cross-platform dashboard design and uncover deeper analytical trends.

---

## Problem

Consulting firms can easily lose money without noticing. Even when overall revenue looks good, problems like **untracked project delays**, **profit loss**, and **underused consultants** can hurt the business. Without clear data, it is hard for leadership to see how much delivery delays actually reduce profits or slow down cash collection.

---

## Solution

This project implements an end-to-end data engineering and advanced analytics solution:

1. **Data Cleaning & Modeling (dbt + DuckDB):** Transforms raw data into clean, structured Bronze, Silver, and Gold relational models optimized for analytical performance.
2. **Statistical Modeling & ML Diagnostics:** Uses Ordinary Least Squares (OLS) regression (`statsmodels`) to quantify project delay impacts on gross margins (evaluating R² score, slope, and p-values), paired with Random Forest Feature Importance to isolate root drivers of margin leakage.
3. **Interactive Visualizations & Cross-Platform BI:** Delivers an interactive **Streamlit** suite for executive web storytelling, while automatically exporting curated Gold datasets and standardized **DAX measures** (`Powerbi_dax_measures.md`) for seamless deployment in **Power BI**.

---

## Key Insights & Dashboard Storytelling

### 1. Executive Financial Overview
* **Focus:** High-Level Revenue Growth, Gross Margin Leakage & Regional Performance
* **Revenue Performance:** Achieved **$35.98M in invoiced revenue** across 238 completed projects, driven by strong core demand in **Ontario ($14M)**, **Technology ($6.9M)**, and **Energy ($5.2M)**.
* **Margin Leakage Root Cause:** Delivered gross margin fell to **28.0%** (vs. 35.0% target). OLS regression analysis isolated **100% of margin erosion to excess unbilled labor hours**, proving schedule delays alone do not drive margin loss.
* **Strategic Recommendation:** Enforce strict labor hour caps and trigger automated management alerts when project engagements hit 85% of their budgeted labor threshold.

### 2. Operations & Delivery Performance
* **Focus:** Client Satisfaction Drivers, Intake Risk Calibration & Delivery Bottlenecks
* **Communication Buffer Effect:** Schedule delays do not erode client trust if communication remains proactive. Maintaining high communication scores (>= 4.0) acts as a **+0.75 CSAT safety net**, keeping satisfaction above target (4.16) during project slippage.
* **Capacity Bottlenecks:** High consultant utilization (**83%–89%**) starves engagement leads of time required for routine client touchpoints, directly impacting CSAT when communication drops below 3.0.
* **Strategic Recommendation:** Protect dedicated weekly non-billable client management hours for delivery leads during project delay phases.

### 3. Working Capital & Accounts Receivable
* **Focus:** Cash Flow Optimization, Aging AR Analysis & Capital Drag
* **Capital Exposure:** Identified **$7.21M in overdue accounts receivable** (87.4% of total open balances), with **$4.2M sitting over 365 days past due**, generating a **$540.5K annual interest/financing drag** (at 7.5% cost of capital).
* **Concentration & Delay Profiles:** Credit risk is spread across mid-sized accounts rather than concentrated in single bankruptcies, led by severe payment lags in **Manufacturing (600+ days late)** and **Education**.
* **Strategic Recommendation:** Institute automated stop-work triggers for accounts exceeding 90 days past due and initiate formal collections or write-offs for the $4.2M sitting past 365 days.

### 4. Consultant Capacity & Workload Allocation
* **Focus:** Resource Allocation, Key-Person Risk & Presales Overhead
* **Utilization vs. Key-Person Risk:** Achieved an **85.9% overall billable utilization** across 80 consultants (beating the 75.0% target). However, severe over-allocation exists, with **7 consultants exceeding project capacity limits** (e.g., managing up to 8 concurrent projects).
* **Non-Billable Drag:** Identified **41,692 non-billable hours lost (14.1%)**, heavily driven by senior delivery staff absorbing **20,000 hours in sales support/proposal work**.
* **Strategic Recommendation:** Rebalance workloads to junior consultants (currently underutilized at 68%) and introduce dedicated sales engineers to relieve senior staff of presales overhead.

---

## Quick Start & How to Run

Follow these steps to launch the interactive Streamlit dashboards in GitHub Codespaces with zero local setup required:

### 1. Launch in GitHub Codespaces
1. Fork or clone this repository.
2. Click the **Code** button on GitHub, select the **Codespaces** tab, and click **Create codespace on main**.
3. Wait for the cloud environment to finish initializing.

### 2. Run the Application
Once the terminal opens in Codespaces, run:

```bash
make run
```

> **Note:** `make run` automatically executes the full end-to-end pipeline: syncs dependencies via `uv`, builds the **dbt** models (Bronze/Silver/Gold), exports the curated Gold tables for Power BI reporting, and launches the **Streamlit** suite.

---

### Useful Commands

| Command | Description |
| :--- | :--- |
| `make run` | Runs full pipeline sequentially (setup → dbt → export → Streamlit) |
| `make app` | Launches the Streamlit dashboard directly |
| `make setup` | Syncs environment dependencies via `uv` |
| `make dbt` | Compiles and executes dbt models independently |
| `make export` | Exports Gold tables for Power BI report execution |
| `make clean` | Cleans temporary build files, caches, and dbt artifacts |
| `make help` | Displays all available Makefile commands |

---

## Repository Structure

```text
├── .devcontainer/           # DevContainer configuration for instant cloud setup
├── data/                    # Raw dataset files (CSV) & exported Gold tables
├── data_modeling/           # dbt project transformation pipeline
│   ├── models/              # Bronze (Raw), Silver (Clean), Gold (Final) analytics layers
│   ├── dbt_packages/        # Installed dbt packages
│   └── dbt_project.yml      # dbt core configuration
├── data_storytelling/       # Visual reporting and analytics assets
|   ├── Powerbi_dax_measures/ # DAX measures documented across .md files for Power BI implementation
│   ├── streamlit/           # Multi-page interactive Streamlit app
│   │   ├── app.py           # Main application entry point
│   │   ├── pages/           # Individual executive dashboard pages
│   │   └── utils/           # Modular utility scripts and analytics helpers
│   └── export_gold_tables.py # Python script exporting Gold models for BI
├── Makefile                 # Automated workspace management commands
├── pyproject.toml           # Python dependency definitions (uv)
└── README.md                # Project documentation
```
