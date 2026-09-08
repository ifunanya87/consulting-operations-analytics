/*
  Model: fact_project_performance
  Layer: Gold
  Description: Combines project budgets, labor costs, billed amounts, and delays into a single summary.
  Why: Provides a fast way to track project profits, budget overruns, and delays in one place.
*/


{{ config(materialized='table') }}

WITH timesheet_summary AS (
    select
        Project_ID,
        sum(Hours_Worked) as Total_Hours_Worked,
        sum(case when Billable_Flag = 'Billable' then Hours_Worked else 0 end) as Total_Billable_Hours,
        sum(Hours_Worked * coalesce(c.Hourly_Cost_Rate, c.Rule_Default_Cost_Rate, 0)) as Total_Actual_Labour_Cost
    from {{ ref('silver_timesheets') }} t
    left join {{ ref('silver_consultants') }} c on t.Consultant_ID = c.Consultant_ID
    group by Project_ID
),

invoice_summary as (
    select
        Project_ID,
        sum(Invoice_Subtotal_CAD) as Total_Invoiced_Subtotal_CAD,
        sum(Total_Invoice_Amount_CAD) as Total_Invoiced_Amount_CAD,
        sum(Total_Amount_Paid) as Total_Invoiced_Amount_Paid
    from {{ ref('silver_invoices') }}
    group by Project_ID
)

select
    -- Project Attributes & Dimensions
    p.Project_ID,
    p.Client_ID,
    p.Service_Line_ID,
    p.Project_Manager_ID,
    p.Project_Type,
    p.Project_Status,
    p.Start_Date,
    p.Planned_End_Date,
    p.Actual_End_Date,
    p.Schedule_Delay_Days,
    
    -- Contract & Budget Baselines
    p.Contract_Value_CAD,
    p.Budgeted_Cost_CAD,
    
    -- Timesheet Labor Aggregates
    coalesce(ts.Total_Hours_Worked, 0) as Total_Hours_Worked,
    coalesce(ts.Total_Billable_Hours, 0) as Total_Billable_Hours,
    coalesce(ts.Total_Actual_Labour_Cost, 0) as Total_Actual_Labour_Cost,
    
    -- Budget Variance (Budgeted Cost - Actual Labour Cost)
    (p.Budgeted_Cost_CAD - coalesce(ts.Total_Actual_Labour_Cost, 0)) as Budget_Variance_CAD,
    
    -- Invoicing Financial Aggregates
    coalesce(inv.Total_Invoiced_Subtotal_CAD, 0) as Total_Invoiced_Subtotal_CAD,
    coalesce(inv.Total_Invoiced_Amount_CAD, 0) as Total_Invoiced_Amount_CAD,
    coalesce(inv.Total_Invoiced_Amount_Paid, 0) as Total_Invoiced_Amount_Paid,
    
    -- Delivered Profit Margin (Contract Value - Actual Labour Cost)
    (p.Contract_Value_CAD - coalesce(ts.Total_Actual_Labour_Cost, 0)) as Delivered_Gross_Profit_Margin_CAD

from {{ ref('silver_projects') }} p
left join timesheet_summary ts on p.Project_ID = ts.Project_ID
left join invoice_summary inv on p.Project_ID = inv.Project_ID
