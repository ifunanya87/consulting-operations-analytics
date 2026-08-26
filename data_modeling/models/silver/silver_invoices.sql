/*
  Model: silver_invoices
  Layer: Silver
  Description: Pre-calculates outstanding balances, days past due, and categorical 
                aging buckets.
  Why: Materializes financial aging logic directly in SQL so DAX only performs simple 
                aggregations (SUM, AVERAGE).
*/


with invoices as (
    select * from {{ ref('stg_invoices') }}
)
select
    Invoice_Id,
    Project_Id,
    Client_Id,
    Invoice_Date,
    Due_Date,
    Invoice_Subtotal_CAD,
    Tax_Rate,
    Tax_Amount_CAD,
    Total_Invoice_Amount_CAD,
    Total_Amount_Paid,
    Invoice_Status,
    (Total_Invoice_Amount_CAD - Total_Amount_Paid) as Outstanding_Balance,
    
    -- Days past due relative to cutoff date (2025-12-31)
    case 
        when (Total_Invoice_Amount_CAD - Total_Amount_Paid) > 0 
        then greatest(0, datediff('day', Due_Date, cast('{{ var("snapshot_date", "2025-12-31") }}' as date)))
        else 0 
    end as Days_Past_Due,

    -- Categorical AR aging buckets using dbt project variable
    case 
        when (Total_Invoice_Amount_CAD - Total_Amount_Paid) <= 0 then 'Current / Paid'
        when datediff('day', Due_Date, cast('{{ var("snapshot_date", "2025-12-31") }}' as date)) <= 0 then 'Current'
        when datediff('day', Due_Date, cast('{{ var("snapshot_date", "2025-12-31") }}' as date)) <= 30 then '1-30 Days'
        when datediff('day', Due_Date, cast('{{ var("snapshot_date", "2025-12-31") }}' as date)) <= 90 then '31-90 Days'
        when datediff('day', Due_Date, cast('{{ var("snapshot_date", "2025-12-31") }}' as date)) <= 365 then '91-365 Days'
        else '>365 Days'
    end as Aging_Bucket
from invoices
