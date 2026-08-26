/*
  Model: silver_projects
  Layer: Silver
  Description: Standardizes project metadata and pre-calculates raw project 
                delay metrics (schedule_delay_days).
  Why: Pre-computing schedule_delay_days upstream offloads row-by-row DATEDIFF 
                calculations from Power BI DAX.
*/

with projects as (
    select * from {{ ref('stg_projects') }}
)
select
    Project_ID,
    Project_Name,
    Client_ID,
    Project_Manager_ID,
    Contract_Value_CAD,
    Budgeted_Cost_CAD,
    Start_Date,
    Planned_End_Date,
    Actual_End_Date,
    Project_Status,
    
    -- Pre-calculated Schedule Delay Days
    case 
        when Actual_End_Date is not null and Planned_End_Date is not null
        then datediff('day', Planned_End_Date, Actual_End_Date)
        else null 
    end as Schedule_Delay_Days
from projects
