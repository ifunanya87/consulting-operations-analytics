/*
  Model: dim_servicelines
  Layer: Gold
  Description: Stores team information, including department groups, profit goals, 
              standard pricing, and work-hour targets.
  Why: lets leadership compare actual business performance against their set goals.
*/


{{ config(materialized='table') }}

SELECT
    sl.Service_Line_ID,
    sl.Service_Line,
    sl.Department,
    sl.Target_Margin_Pct,
    sl.Standard_Bill_Rate,
    sl.Target_Utilization_Pct
FROM {{ ref('silver_servicelines') }} sl
