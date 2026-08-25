/*
  Model: stg_invoices
  Layer: Staging
  Description: Cleans invoice financial figures, standardizes primary and foreign keys, 
                backfills missing provincial tax rates and amounts via client locations, 
                and dynamically derives invoice payment statuses using cleared payment totals.
*/

{{ config(materialized='view') }}


with source as (
    select * from {{ source('raw_data', 'Invoices') }}
),
prepared as (
    select 
        upper(trim(Invoice_ID)) as Invoice_ID,
        upper(trim(Project_ID)) as Project_ID,
        upper(trim(Client_ID)) as Client_ID,
        try_cast(nullif(trim(cast(Invoice_Date as varchar)), '') as date) as Invoice_Date,
        try_cast(nullif(trim(cast(Due_Date as varchar)), '') as date) as Due_Date,
        cast(replace(replace(cast(Invoice_Subtotal_CAD as varchar), '$', ''), ',', '') as decimal(10,2)) as Invoice_Subtotal_CAD,
        cast(replace(cast(Tax_Rate as varchar), '%', '') as decimal(7,5)) as Tax_Rate,
        cast(replace(replace(cast(Tax_Amount_CAD as varchar), '$', ''), ',', '') as decimal(10,2)) as Tax_Amount_CAD,
        cast(replace(replace(cast(Total_Invoice_Amount_CAD as varchar), '$', ''), ',', '') as decimal(10,2)) as Total_Invoice_Amount_CAD,
        lower(trim(Invoice_Status)) as raw_status
    from source
),
sums as (
    select 
        Invoice_ID,
        sum(Payment_Amount_CAD) as total_paid
    from {{ ref('stg_payments') }}
    where Payment_Status = 'Cleared'
    group by Invoice_ID
),
tax_lookups as (
    select 
        p.Invoice_ID,
        t.Tax_Rate as lookup_tax_rate
    from prepared p
    left join {{ ref('stg_projects') }} cp on p.Project_ID = cp.Project_ID
    left join {{ ref('stg_clients') }} c on p.Client_ID = c.Client_ID
    left join {{ ref('stg_taxrates') }} t on c.Province = t.Province
)

select 
    p.Invoice_ID,
    p.Project_ID,
    p.Client_ID,
    p.Invoice_Date,
    p.Due_Date,
    p.Invoice_Subtotal_CAD,
    coalesce(p.Tax_Rate, cast(tl.lookup_tax_rate as decimal(7,5))) as Tax_Rate,
    coalesce(p.Tax_Amount_CAD, cast(p.Invoice_Subtotal_CAD * tl.lookup_tax_rate as decimal(10,2))) as Tax_Amount_CAD,
    coalesce(p.Total_Invoice_Amount_CAD, cast(p.Invoice_Subtotal_CAD + coalesce(p.Tax_Amount_CAD, p.Invoice_Subtotal_CAD * tl.lookup_tax_rate) as decimal(10,2))) as Total_Invoice_Amount_CAD,
    coalesce(s.total_paid, 0.00) as Total_Amount_Paid,
    case 
        when coalesce(s.total_paid, 0.00) >= p.Total_Invoice_Amount_CAD then 'Paid'
        when coalesce(s.total_paid, 0.00) > 0.00 and p.Due_Date < '2025-12-31' then 'Partially Paid - Overdue'
        when coalesce(s.total_paid, 0.00) > 0.00 then 'Partially Paid'
        when coalesce(s.total_paid, 0.00) = 0.00 and p.Due_Date < '2025-12-31' then 'Overdue'
        else 'Open'
    end as Invoice_Status
from prepared p
left join sums s on p.Invoice_ID = s.Invoice_ID
left join tax_lookups tl on p.Invoice_ID = tl.Invoice_ID
