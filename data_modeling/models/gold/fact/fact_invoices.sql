/*
  Model: fact_invoices
  Layer: Gold
  Description: Tracks billing details, payments received, unpaid balances, and 
                overdue invoices.
  Why: Helps monitor unpaid bills, track incoming cash, and measure billing accuracy.
*/


{{ config(materialized='table') }}

select
    inv.Invoice_ID,
    inv.Project_ID,
    inv.Client_ID,
    inv.Invoice_Date,
    inv.Due_Date,
    inv.Invoice_Subtotal_CAD,
    inv.Tax_Rate,
    inv.Tax_Amount_CAD,
    inv.Total_Invoice_Amount_CAD,
    inv.Total_Amount_Paid,
    inv.Invoice_Status,
    inv.Outstanding_Balance,
    inv.Days_Past_Due,
    inv.Aging_Bucket
from {{ ref('silver_invoices') }} inv
