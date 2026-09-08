/*
  Model: fact_payments
  Layer: Gold
  Description: Records payments received for invoices, projects, and clients.
  Why: Tracks payment methods, speed up cash flow checks, and create an audit trail for incoming money.
*/


{{ config(materialized='table') }}

select
    pay.Payment_ID,
    pay.Invoice_ID,
    inv.Project_ID,
    inv.Client_ID,
    pay.Payment_Date,
    pay.Payment_Amount_CAD,
    pay.Payment_Method,
    pay.Payment_Status
from {{ ref('silver_payments') }} pay
left join {{ ref('silver_invoices') }} inv 
    on pay.Invoice_ID = inv.Invoice_ID
