/*
  Model: stg_timesheets
  Layer: Staging
  Description: Cleans timesheet entries, standardizes key identifiers and dates, 
                casts logged hours to decimals, backfills missing billable flags using 
                task category lookup rules, and deduplicates the final staging output.
*/

{{ config(materialized='view') }}


with source as (
    select * from {{ source('raw_data', 'Timesheets') }}
),
task_rules as (
    select * from {{ ref('stg_taskcategoryrules') }}
),
joined_and_filled as (
    select
        upper(trim(t.Timesheet_ID)) as Timesheet_ID,
        try_cast(nullif(trim(cast(t.Work_Date as varchar)), '') as date) as Work_Date,
        upper(trim(t.Project_ID)) as Project_ID,
        upper(trim(t.Consultant_ID)) as Consultant_ID,
        trim(t.Task_Category) as Task_Category,
        cast(t.Hours_Worked as decimal(5,1)) as Hours_Worked,
        coalesce(
            nullif(trim(cast(t.Billable_Flag as varchar)), ''), 
            r.Default_Billable_Flag
        ) as Billable_Flag,
        trim(cast(t.Approved_Flag as varchar)) as Approved_Flag
    from source t
    left join task_rules r 
        on lower(trim(t.Task_Category)) = lower(trim(r.Task_Category))
)

select distinct * from joined_and_filled
