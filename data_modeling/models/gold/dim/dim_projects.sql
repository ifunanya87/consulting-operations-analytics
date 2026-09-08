/*
  Model: dim_projects
  Layer: Gold
  Description: Standardizes engagement metadata, contract parameters, 
                commercial project structures, baseline timelines, and schedule variances.
  Why: The primary source dimension for delivery tracking, risk assessment, 
                schedule overrun evaluation, and engagement-level profitability reporting.
*/


{{ config(materialized='table') }}

SELECT
    p.Project_ID,
    p.Project_Name,
    p.Client_ID,
    p.Service_Line_ID,
    p.Project_Manager_ID,
    p.Contract_Value_CAD,
    p.Budgeted_Cost_CAD,
    p.Start_Date,
    p.Planned_End_Date,
    p.Actual_End_Date,
    p.Project_Status,
    p.Schedule_Delay_Days,
    p.Initial_Risk_Level,
    p.Project_Type
FROM {{ ref('silver_projects') }} p
