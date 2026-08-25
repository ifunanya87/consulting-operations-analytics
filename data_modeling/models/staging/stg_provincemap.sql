/*
  Model: stg_provincemap
  Layer: Staging
  Description: Normalizes raw provincial names and variations to full province labels and 
                standardizes target provincial ISO codes.
*/

{{ config(materialized='view') }}


with source as (
    select * from {{ source('raw_data', 'ProvinceMap') }}
)

select
    case 
        when upper(trim(Raw_Province_Value)) in ('ON', 'ONTARIO') then 'Ontario'
        when upper(trim(Raw_Province_Value)) in ('BC', 'BRITISH COLUMBIA') then 'British Columbia'
        when upper(trim(Raw_Province_Value)) in ('AB', 'ALBERTA') then 'Alberta'
        when upper(trim(Raw_Province_Value)) in ('QC', 'QUEBEC') then 'Quebec'
        when upper(trim(Raw_Province_Value)) in ('NS', 'NOVA SCOTIA') then 'Nova Scotia'
        when upper(trim(Raw_Province_Value)) in ('MB', 'MANITOBA') then 'Manitoba'
        else trim(Raw_Province_Value)
    end as Raw_Province_Value,
    upper(trim(Standard_Province)) as Standard_Province
from source
