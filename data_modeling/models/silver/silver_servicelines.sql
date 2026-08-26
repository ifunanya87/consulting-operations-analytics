/*
  Model: silver_servicelines
  Layer: Silver
  Description: Standardizes department service line reference data and target 
                performance metrics.
  Why: Serves as the central reference model for target margin % and target 
                utilization % benchmarks.
*/


with servicelines as (
    select * from {{ ref('stg_servicelines') }}
)
select
    Service_Line_Id,
    Service_Line,
    Department,
    Target_Margin_Pct,
    Standard_Bill_Rate,
    Target_Utilization_Pct
from servicelines
