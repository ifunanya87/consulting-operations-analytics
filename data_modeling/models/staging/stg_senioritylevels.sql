/*
  Model: stg_senioritylevels
  Layer: Staging
  Description: Cleans seniority level reference data, standardizes seniority text fields, 
                formats cost and billing rate multipliers, and casts expected annual 
                available hours to integers.
*/

{{ config(materialized='view') }}


select
    trim(Seniority) as Seniority,
    cast(Cost_Multiplier as decimal(4,2)) as Cost_Multiplier,
    cast(Bill_Rate_Multiplier as decimal(4,2)) as Bill_Rate_Multiplier,
    cast(Expected_Annual_Available_Hours as integer) as Expected_Annual_Available_Hours
from {{ source('raw_data', 'SeniorityLevels') }}
