# Consulting Operations & Financial Analytics Storytelling

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![dbt](https://img.shields.io/badge/dbt-Core-orange?logo=dbt)](https://www.getdbt.com/)
[![DuckDB](https://img.shields.io/badge/Database-DuckDB-yellow?logo=duckdb)](https://duckdb.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?logo=streamlit)](https://streamlit.io/)
[![Power BI DAX](https://img.shields.io/badge/Power_BI-DAX_Measures-yellow?logo=powerbi)](./data_storytelling/Powerbi_dax_measures.md)
[![Status](https://img.shields.io/badge/Status-In_Progress-yellowgreen)](#-project-status)

This is a data analysis and storytelling project focused on the operational and financial performance of a consulting firm. It cleans, models, and explores operational data to discover what drives **margin leakage**, **project delays**, **consultant availability**, and **invoice collections** using Streamlit for interactive web storytelling and DAX measures for Power BI reporting.

---

## Problem

Consulting firms can easily lose money without noticing. Even when overall revenue looks good, problems like **untracked project delays**, **profit loss**, and **underused consultants** can hurt the business. Without clear data, it is hard for leadership to see how much delivery delays actually reduce profits or slow down cash collection.

---

## Solution

This project builds a step-by-step pipeline to clean the data, analyze it, and present clear insights:

1. **Data Cleaning & Modeling (dbt + DuckDB):** Organizes messy raw tables into clean Bronze, Silver, and Gold relational tables ready for analysis.
2. **Statistical Modeling:** Uses Ordinary Least Squares (**OLS**) regression in Python (`statsmodels`) to calculate how project delays impact profit margins using stats metrics like $R^2$, slope, and p-values.
3. **Interactive Visualizations & Modular DAX:** Uses an interactive **Streamlit** app for web-based data storytelling, alongside documented **Power BI DAX measures** (`Powerbi_dax_measures.md`) so the same analytical metrics can be deployed directly into Power BI reports.

---

## Project Status

> **Note:** This project is actively being worked on as I explore more data and uncover new insights.

---

## Repository Folders

```text
├── .devcontainer/            # Setup files for running code in a DevContainer
├── data/                     # Raw dataset files (CSV)
├── data_modeling/            # dbt folder for cleaning and structuring data
│   ├── models/               # Bronze (Raw), Silver (Clean), Gold (Final) tables
│   ├── dbt_packages/         # dbt add-ons
│   ├── target/               # Compiled SQL queries
│   └── dbt_project.yml       # dbt setup file
├── data_storytelling/        # Code and docs for presenting data insights
│   ├── streamlit/            # Interactive Streamlit story pages
│   │   ├── dashboard_1_executive_overview.py
│   │   ├── dashboard_2_operations.py
│   │   ├── dashboard_3_working_capital_and_ar.py
│   │   ├── dashboard_4_consultant_capacity.py
│   │   └── helper_functions.py
│   ├── export_gold_tables.py # Python script for exporting processed models
│   └── Powerbi_dax_measures.md # Key DAX calculations for Power BI reporting
├── .gitattributes            # Controls GitHub language stats
├── .gitignore                # Files ignored by Git tracking
├── .python-version          # Python environment configuration
├── LICENSE                   # Project license
├── pyproject.toml            # Python package dependencies (uv)
├── README.md                 # Project guide
└── uv.lock                   # Exact dependency lockfile
