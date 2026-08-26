/*
  Model: silver_projectassignments
  Layer: Silver
  Description: Standardizes consultant project staffing entries and assignment durations.
  Why: Captures resource allocation dates and assignment days for capacity planning analysis.
*/


with assignments as (
    select * from {{ ref('stg_projectassignments') }}
)
select
    Assignment_ID,
    Project_ID,
    Consultant_ID,
    Role_On_Project,
    Assigned_Start_Date,
    Assigned_End_Date,
    Allocation_Pct,
    Bill_Rate_CAD,
    Assignment_Status,
    
    -- Calculated Assignment Duration
    case 
        when Assigned_End_Date is not null and Assigned_Start_Date is not null 
        then datediff('day', Assigned_Start_Date, Assigned_End_Date)
        else null 
    end as Assigned_Days
from assignments
