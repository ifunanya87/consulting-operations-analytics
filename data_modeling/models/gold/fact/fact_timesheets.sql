/*
  Model: fact_timesheets
  Layer: Gold
  Description: Tracks daily work logs with pay and billing rates to calculate total 
                work costs and billable hours.
  Why: Helps track employee work hours, labor costs, and project spending.
*/

{{ config(materialized='table') }}

select
    t.Timesheet_ID,
    t.Work_Date,
    t.Project_ID,
    t.Consultant_ID,
    t.Task_Category,
    t.Hours_Worked,
    t.Billable_Flag,
    t.Approved_Flag,
    t.Include_In_Utilization,
    -- Calculate billable hours
    case 
        when t.Billable_Flag = 'Billable' then t.Hours_Worked 
        else 0 
    end as Billable_Hours,
    -- Calculate actual delivery labor cost
    (t.Hours_Worked * coalesce(c.Hourly_Cost_Rate, c.Rule_Default_Cost_Rate, 0)) as Actual_Labour_Cost,
    -- Calculate estimated billable value using assigned or standard rate
    (t.Hours_Worked * coalesce(pa.Bill_Rate_CAD, c.Standard_Bill_Rate, 0)) as Estimated_Billable_Amount_CAD
from {{ ref('silver_timesheets') }} t
left join {{ ref('silver_consultants') }} c 
    on t.Consultant_ID = c.Consultant_ID
left join {{ ref('silver_projectassignments') }} pa 
    on t.Project_ID = pa.Project_ID 
   and t.Consultant_ID = pa.Consultant_ID
