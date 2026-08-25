/*
  Model: stg_locations
  Layer: Staging
  Description: Cleans office branch records, standardizes branch identifiers and provincial codes, 
                formats geographic and manager text fields, and casts office open dates to 
                standard date format.
*/

{{ config(materialized='view') }}


with source as (
    select * from {{ source('raw_data', 'Locations') }}
)

select
    upper(trim(Branch_ID)) as Branch_ID,
    trim(City) as City,
    upper(trim(Province)) as Province,
    trim(Region) as Region,
    try_cast(nullif(trim(cast(Office_Open_Date as varchar)), '') as date) as Office_Open_Date,
    trim(Branch_Manager) as Branch_Manager
from source
