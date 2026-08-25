/*
  Model: stg_clientcontractterms
  Layer: Staging
  Description: Raw passthrough for client contract terms data.
*/

{{ config(materialized='view') }}

select * 
from {{ source('raw_data', 'ClientContractTerms') }}
