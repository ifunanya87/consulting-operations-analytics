/*
  Model: stg_consultants
  Layer: Staging
  Description: Cleans consultant profile records, standardizes hire and termination dates, 
                and backfills missing hourly cost and billing rates using default rates from 
                seniority rate rules.
*/

{{ config(materialized='view') }}


with source as (
    select * from {{ source('raw_data', 'Consultants') }}
),
seniority_rules as (
    select * from {{ source('raw_data', 'SeniorityRateRules') }}
)

select
    c.Consultant_ID,
    c.Consultant_Name,
    c.Home_Branch_ID,
    c.Service_Line_ID,
    c.Seniority,
    coalesce(c.Hourly_Cost_Rate, s.Default_Hourly_Cost_Rate) as Hourly_Cost_Rate,
    coalesce(c.Standard_Bill_Rate, s.Default_Bill_Rate) as Standard_Bill_Rate,
    try_cast(nullif(trim(cast(c.Hire_Date as varchar)), '') as date) as Hire_Date,
    try_cast(nullif(trim(cast(c.Termination_Date as varchar)), '') as date) as Termination_Date,
    c.Employment_Status
from source c
left join seniority_rules s
    on c.Service_Line_ID = s.Service_Line_ID
    and c.Seniority = s.Seniority
