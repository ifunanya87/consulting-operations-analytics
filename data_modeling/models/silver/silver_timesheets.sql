/*
  Model: silver_timesheets
  Layer: Silver
  Description: Integrates consultant daily time entries with task utilization rules.
  Why: Attaches the include_in_utilization flag to each timesheet record without 
        altering granular log rows.
*/


with timesheets as (
    select * from {{ ref('stg_timesheets') }}
),
task_rules as (
    select * from {{ ref('stg_taskcategoryrules') }}
)
select
    t.Timesheet_Id,
    t.Work_Date,
    t.Project_Id,
    t.Consultant_Id,
    t.Task_Category,
    t.Hours_Worked,
    t.Billable_Flag,
    t.Approved_Flag,
    tr.Include_In_Utilization
from timesheets t
left join task_rules tr 
    on t.Task_Category = tr.Task_Category
