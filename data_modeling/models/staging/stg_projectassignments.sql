/*
  Model: stg_projectassignments
  Layer: Staging
  Description: Cleans consultant project allocation records, standardizes assignment, project, 
                and consultant identifiers, casts lifecycle assignment dates, parses decimal 
                allocations and billing rates, and normalizes assignment statuses.
*/

{{ config(materialized='view') }}


with source as (
    select * from {{ source('raw_data', 'ProjectAssignments') }}
)

select
    upper(trim(Assignment_ID)) as Assignment_ID,
    upper(trim(Project_ID)) as Project_ID,
    upper(trim(Consultant_ID)) as Consultant_ID,
    trim(Role_On_Project) as Role_On_Project,
    try_cast(nullif(trim(cast(Assigned_Start_Date as varchar)), '') as date) as Assigned_Start_Date,
    try_cast(nullif(trim(cast(Assigned_End_Date as varchar)), '') as date) as Assigned_End_Date,
    cast(Allocation_Pct as decimal(4,2)) as Allocation_Pct,
    cast(
        replace(
            replace(cast(Bill_Rate_CAD as varchar), '$', ''), 
            ',', ''
        ) as decimal(10,2)
    ) as Bill_Rate_CAD,
    lower(trim(Assignment_Status)) as Assignment_Status
from source
