/*
  Model: stg_servicelines
  Layer: Staging
  Description: Cleans service line reference data, standardizes service line identifiers, 
                trims textual names and departments, and formats target margins, 
                standard bill rates, and utilization percentages into standard decimal values.
*/

{{ config(materialized='view') }}


select
    upper(trim(Service_Line_ID)) as Service_Line_ID,
    trim(Service_Line) as Service_Line,
    trim(Department) as Department,
    cast(Target_Margin_Pct as decimal(4,2)) as Target_Margin_Pct,
    cast(Standard_Bill_Rate as decimal(10,2)) as Standard_Bill_Rate,
    cast(Target_Utilization_Pct as decimal(4,2)) as Target_Utilization_Pct
from {{ source('raw_data', 'ServiceLines') }}
