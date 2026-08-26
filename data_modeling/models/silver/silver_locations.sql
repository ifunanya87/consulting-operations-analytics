/*
  Model: silver_locations
  Layer: Silver
  Description: Integrates branch locations with standardized province mappings and tax rates.
  Why: Standardizes regional names across branches and attaches provincial tax rates 
        directly to location metadata.
*/


with locations as (
    select * from {{ ref('stg_locations') }}
),
province_map as (
    select * from {{ ref('stg_provincemap') }}
),
tax_rates as (
    select * from {{ ref('stg_taxrates') }}
)
select
    l.Branch_Id,
    l.City,
    pm.Standard_Province as Province,
    l.Region,
    l.Office_Open_Date,
    l.Branch_Manager,
    tr.Tax_Name,
    tr.Tax_Rate
from locations l
left join province_map pm 
    on l.Province = pm.Standard_Province
left join tax_rates tr 
    on pm.Standard_Province = tr.Province
