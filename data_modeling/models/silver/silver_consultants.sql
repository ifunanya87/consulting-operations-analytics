/*
  Model: silver_consultants
  Layer: Silver
  Description: Enriches consultant profiles with seniority capacity multipliers and 
                rate rule fallbacks.
  Why: Consolidates consultant rate rules and expected annual billable hours into a 
                single resource table.
*/


with consultants as (
    select * from {{ ref('stg_consultants') }}
),
seniority_levels as (
    select * from {{ ref('stg_senioritylevels') }}
),
rate_rules as (
    select * from {{ ref('stg_seniorityraterules') }}
)
select
    c.Consultant_Id,
    c.Consultant_Name,
    c.Home_Branch_Id,
    c.Service_Line_Id,
    c.Seniority,
    c.Hire_Date,
    c.Termination_Date,
    c.Employment_Status,
    c.Hourly_Cost_Rate,
    c.Standard_Bill_Rate,
    sl.Cost_Multiplier,
    sl.Bill_Rate_Multiplier,
    sl.Expected_Annual_Available_Hours,
    rr.Default_Hourly_Cost_Rate as Rule_Default_Cost_Rate,
    rr.Default_Bill_Rate as Rule_Default_Bill_Rate
from consultants c
left join seniority_levels sl 
    on c.Seniority = sl.Seniority
left join rate_rules rr 
    on c.Service_Line_Id = rr.Service_Line_Id 
   and c.Seniority = rr.Seniority
