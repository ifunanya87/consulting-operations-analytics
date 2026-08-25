/*
  Model: stg_taskcategoryrules
  Layer: Staging
  Description: Cleans task category lookup rules, standardizing task category descriptions 
                and trimming flags for default billability and utilization tracking.
*/

{{ config(materialized='view') }}


select
    trim(Task_Category) as Task_Category,
    trim(cast(Default_Billable_Flag as varchar)) as Default_Billable_Flag,
    trim(cast(Include_In_Utilization as varchar)) as Include_In_Utilization
from {{ source('raw_data', 'TaskCategoryRules') }}
