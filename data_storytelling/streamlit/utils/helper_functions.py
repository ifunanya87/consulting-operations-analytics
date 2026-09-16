import statsmodels.formula.api as smf
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import numpy as np


def calculate_delay_multiplier(projects_df, invoices_df, default_multiplier=0.5):
  """Calculates the empirical schedule delay multiplier using a Multiple Linear Regression model
  controlling for project scale (revenue) and labor effort.
  """
  # Aggregate invoice subtotals to project grain
  inv_agg = invoices_df.groupby("Project_ID", as_index=False)[
      "Invoice_Subtotal_CAD"
  ].sum()

  # Merge aggregated invoices with project performance data
  df = projects_df.merge(inv_agg, on="Project_ID", how="left")
  df["Invoice_Subtotal_CAD"] = df["Invoice_Subtotal_CAD"].fillna(0)

  # Calculate target profit (35%), actual profit, and margin variance
  df["Target_Profit"] = df["Invoice_Subtotal_CAD"] * 0.35
  df["Actual_Profit"] = (
      df["Invoice_Subtotal_CAD"] - df["Total_Actual_Labour_Cost"]
  )
  df["Margin_Variance_CAD"] = (
      df["Target_Profit"] - df["Actual_Profit"]
  )  # Positive value indicates unfavorable leakage

  # Filter for delayed projects with positive revenue AND positive margin variance (actual leakage)
  reg_data = df[
      (df["Schedule_Delay_Days"] > 0)
      & (df["Invoice_Subtotal_CAD"] > 0)
      & (df["Margin_Variance_CAD"] > 0)
  ].copy()

  # Debug prints for reg_data filtering criteria
  print("\n--- OLS DATASET FILTER DEBUG ---")
  print(f"Total merged rows: {len(df)}")
  print(f"1. Schedule_Delay_Days > 0: {(df['Schedule_Delay_Days'] > 0).sum()}")
  print(f"2. Invoice_Subtotal_CAD > 0: {(df['Invoice_Subtotal_CAD'] > 0).sum()}")
  print(f"3. Margin_Variance_CAD > 0:  {(df['Margin_Variance_CAD'] > 0).sum()}")
  print(f"Final reg_data rows (ALL conditions met): {len(reg_data)}")
  print("--------------------------------\n")

  if len(reg_data) < 5:  # Minimum sample threshold for multivariable stability
    return default_multiplier, None

  # Prepare variables for Multivariable OLS
  reg_data["Delay_Years"] = reg_data["Schedule_Delay_Days"] / 365.0
  reg_data["Margin_Drop_Pct"] = (
      reg_data["Margin_Variance_CAD"] / reg_data["Invoice_Subtotal_CAD"]
  ) * 100.0
  reg_data["Log_Invoice"] = np.log1p(reg_data["Invoice_Subtotal_CAD"])

  # Rescale hours to thousands to improve matrix condition number
  reg_data["hours_k"] = reg_data["Total_Hours_Worked"] / 1000.0

  # Fit Multiple Linear Regression
  try:
    formula = (
        "Margin_Drop_Pct ~ Delay_Years + Log_Invoice + hours_k"
    )
    model = smf.ols(formula=formula, data=reg_data).fit()

    multiplier = model.params.get("Delay_Years", default_multiplier)

    if pd.isna(multiplier) or multiplier <= 0:
      print(f"Fallback triggered: Multiplier is {multiplier}")
      return default_multiplier, model

    return float(multiplier), model
  except Exception as e:
    print(f"\n OLS REGRESSION ERROR: {e}\n")
    return default_multiplier, None



def calculate_rf_feature_importance(projects_df, invoices_df):
  """Trains a Random Forest Regressor to measure relative feature importance

  for Margin Loss. Scale invariant, but protected against NaN/Inf values.
  """
  try:
    # Aggregate invoice subtotals
    inv_agg = invoices_df.groupby("Project_ID", as_index=False)[
        "Invoice_Subtotal_CAD"
    ].sum()
    df = projects_df.merge(inv_agg, on="Project_ID", how="left")
    df["Invoice_Subtotal_CAD"] = df["Invoice_Subtotal_CAD"].fillna(0)

    # Financial target & variance
    df["Target_Profit"] = df["Invoice_Subtotal_CAD"] * 0.35
    df["Actual_Profit"] = (
        df["Invoice_Subtotal_CAD"] - df["Total_Actual_Labour_Cost"]
    )
    df["Margin_Variance_CAD"] = df["Target_Profit"] - df["Actual_Profit"]

    # Filter criteria (same grain as OLS)
    reg_data = df[
        (df["Schedule_Delay_Days"] > 0)
        & (df["Invoice_Subtotal_CAD"] > 0)
        & (df["Margin_Variance_CAD"] > 0)
    ].copy()

    # Feature Engineering
    reg_data["Delay_Years"] = reg_data["Schedule_Delay_Days"] / 365.0
    reg_data["Margin_Drop_Pct"] = (
        reg_data["Margin_Variance_CAD"] / reg_data["Invoice_Subtotal_CAD"]
    ) * 100.0
    reg_data["Log_Invoice"] = np.log1p(reg_data["Invoice_Subtotal_CAD"])

    feature_cols = ["Total_Hours_Worked", "Log_Invoice", "Delay_Years"]

    # Drop any NaN or Infinite values to keep fit() stable
    clean_data = reg_data[feature_cols + ["Margin_Drop_Pct"]].replace(
        [np.inf, -np.inf], np.nan
    ).dropna()

    if len(clean_data) < 5:
      return None, None

    X = clean_data[feature_cols]
    y = clean_data["Margin_Drop_Pct"]

    # Train Model (max_depth limits overfitting on small datasets)
    rf_model = RandomForestRegressor(
        n_estimators=100, max_depth=5, random_state=42
    )
    rf_model.fit(X, y)

    # Format Feature Importances
    importance_df = pd.DataFrame({
        "Feature": [
            "Total Hours Worked",
            "Invoice Scale (Log)",
            "Schedule Delay (Years)",
        ],
        "Importance_Pct": rf_model.feature_importances_ * 100.0,
    }).sort_values(by="Importance_Pct", ascending=True)

    return rf_model, importance_df

  except Exception as e:
    print(f"\n RANDOM FOREST ERROR: {e}\n")
    return None, None
  