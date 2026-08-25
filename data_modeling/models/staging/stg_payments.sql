/*
  Model: stg_payments
  Layer: Staging
  Description: Cleans client payment records, standardizes payment and invoice primary/foreign keys, 
                casts transaction dates, parses currency strings into numeric decimals, 
                and trims payment metadata.
*/

{{ config(materialized='view') }}


with source as (
    select * from {{ source('raw_data', 'Payments') }}
)

select
    upper(trim(Payment_ID)) as Payment_ID,
    upper(trim(Invoice_ID)) as Invoice_ID,
    try_cast(nullif(trim(cast(Payment_Date as varchar)), '') as date) as Payment_Date,
    cast(
        replace(
            replace(cast(Payment_Amount_CAD as varchar), '$', ''), 
            ',', ''
        ) as decimal(12,2)
    ) as Payment_Amount_CAD,
    trim(Payment_Method) as Payment_Method,
    trim(Payment_Status) as Payment_Status
from source
