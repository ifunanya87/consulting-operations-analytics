/*
  Model: stg_projects
  Layer: Staging
  Description: Cleans consulting project records, standardizes primary/foreign keys and 
                project metadata, casts lifecycle dates, and derives missing project statuses 
                based on completion and cancellation dates.
*/

{{ config(materialized='view') }}


with source as (
    select * from {{ source('raw_data', 'Projects') }}
),
prep as (
    select 
        upper(trim(Project_ID)) as Project_ID, 
        upper(trim(Client_ID)) as Client_ID, 
        upper(trim(Service_Line_ID)) as Service_Line_ID,
        upper(trim(Branch_ID)) as Branch_ID,
        upper(trim(Project_Manager_ID)) as Project_Manager_ID,  
        trim(Project_Name) as Project_Name,
        Project_Type,
        try_cast(nullif(trim(cast(Start_Date as varchar)), '') as date) as Start_Date,
        try_cast(nullif(trim(cast(Planned_End_Date as varchar)), '') as date) as Planned_End_Date,
        try_cast(nullif(trim(cast(Actual_End_Date as varchar)), '') as date) as Actual_End_Date,
        try_cast(nullif(trim(cast(Cancellation_Date as varchar)), '') as date) as Cancellation_Date,
        nullif(trim(Cancellation_Reason), '') as Cancellation_Reason,
        Contract_Value_CAD,
        Budgeted_Hours, 
        Budgeted_Cost_CAD,
        Initial_Risk_Level 
    from source
)

select 
    *,
    case 
        when Actual_End_Date is not null then 'Completed'
        when Cancellation_Date is not null then 'Cancelled'
        else 'In Progress'
    end as Project_Status
from prep
