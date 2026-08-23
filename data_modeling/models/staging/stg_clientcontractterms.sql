/*
  Model: stg_clientcontractterms
  Layer: Bronze / Staging
  Description: Raw passthrough for client contract terms data.
*/

{{ config(materialized='view') }}

select * 
from {{ source('raw_data', 'ClientContractTerms') }}
