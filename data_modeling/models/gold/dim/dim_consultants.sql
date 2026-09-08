/*
  Model: dim_consultants
  Layer: Gold
  Description: Unifies consultant profile data, including branch location, employment status, work capacity, and billing rates.
  Why: The master source for tracking consultant availability, costs, and performance across teams and seniority levels.
*/


{{ config(materialized='table') }}

SELECT
    con.Consultant_ID,
    con.Consultant_Name,
    con.Home_Branch_ID,
    con.Service_Line_ID,
    con.Seniority,
    con.Hire_Date,
    con.Termination_Date,
    con.Employment_Status,
    con.Hourly_Cost_Rate,
    con.Standard_Bill_Rate,
    con.Cost_Multiplier,
    con.Bill_Rate_Multiplier,
    con.Expected_Annual_Available_Hours,
    con.Rule_Default_Cost_Rate,
    con.Rule_Default_Bill_Rate
FROM {{ ref('silver_consultants') }} con
