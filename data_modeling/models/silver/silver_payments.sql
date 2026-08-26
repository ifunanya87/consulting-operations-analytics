/*
  Model: silver_payments
  Layer: Silver
  Description: Standardizes payment transaction logs for invoice matching.
  Why: Provides a clean transaction log table to track historical cash collections 
                and cash flow timing.
*/


with payments as (
    select * from {{ ref('stg_payments') }}
)
select
    Payment_Id,
    Invoice_Id,
    Payment_Date,
    Payment_Amount_CAD,
    Payment_Method,
    Payment_Status
from payments
