/*
  Model: stg_seniorityraterules
  Layer: Staging
  Description: Cleans seniority rate lookup rules, standardizes service line identifiers 
                and seniority titles, and formats default hourly cost and bill rates into 
                standard decimal values.
*/

{{ config(materialized='view') }}


select
    upper(trim(Service_Line_ID)) as Service_Line_ID,
    trim(Seniority) as Seniority,
    cast(Default_Hourly_Cost_Rate as decimal(10,2)) as Default_Hourly_Cost_Rate,
    cast(Default_Bill_Rate as decimal(10,2)) as Default_Bill_Rate
from {{ source('raw_data', 'SeniorityRateRules') }}
