/*
  Model: stg_clients
  Layer: Bronze / Staging
  Description: Cleans, standardizes, and type-casts raw client data.
*/

{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw_data', 'Clients') }}
)

select 
    Client_ID,
    Client_Name,
    Industry,
    City,
    case
        when lower(trim(Province)) in ('on', 'ontario') then 'ON'
        when lower(trim(Province)) in ('ns', 'nova scotia') then 'NS'
        when lower(trim(Province)) in ('qc', 'quebec') then 'QC'
        when lower(trim(Province)) in ('bc', 'british columbia') then 'BC'
        when lower(trim(Province)) in ('ab', 'alberta') then 'AB'
        when lower(trim(Province)) in ('mb', 'manitoba') then 'MB'
        else trim(Province)
    end as Province,
    Region,
    Client_Size,
    Account_Manager_ID,
    try_cast(nullif(trim(Client_Start_Date), '') as date) as Client_Start_Date,
    Active_Status 
from source
