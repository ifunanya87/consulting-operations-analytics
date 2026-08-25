/*
  Model: stg_taxrates
  Layer: Staging
  Description: Cleans provincial tax rate reference data, standardizes provincial codes, 
                trims province and tax names, and casts tax rates into standard decimal values.
*/

{{ config(materialized='view') }}


with source as (
    select * from {{ source('raw_data', 'TaxRates') }}
)

select
    upper(trim(Province)) as Province,
    trim(Province_Name) as Province_Name,
    trim(Tax_Name) as Tax_Name,
    cast(Tax_Rate as decimal(7,5)) as Tax_Rate
from source
