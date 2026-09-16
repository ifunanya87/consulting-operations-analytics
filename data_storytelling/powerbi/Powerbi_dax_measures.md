<!-- # Power BI DAX Measures & Analytics Reference

This document contains all pre-built DAX measures used across the **ExpertEdge Consulting Executive Dashboard**. 

If you prefer to visualize these models inside **Power BI Desktop**:
1. Connect Power BI Desktop to your Gold Layer tables (`dim_*` and `fact_*`).
2. Establish **1-to-Many single-direction relationships** from `dim_*` tables to `fact_*` tables.
3. Create a blank measure table in Power BI (e.g., `_Measures`) and copy-paste the DAX formulas below.

---

## 1. Executive Summary & Financial Performance

### Total Invoiced Revenue

```dax
Total Invoiced Revenue CAD = 
SUM('fact_invoices'[total_invoice_amount_cad]) 

```dax
Total Delivered Gross Margin CAD = 
SUM('fact_project_performance'[Delivered_Gross_Margin_CAD])

```dax
Gross Margin % = 
DIVIDE(
    [Total Delivered Gross Margin CAD],
    SUM('fact_project_performance'[Contract_Value_CAD]),
    0
)

```dax
Total Budget Variance CAD = 
SUM('fact_project_performance'[Budget_Variance_CAD])


### Cash Collection Rate (% Paid)
##### Tells users how efficiently issued invoices are turning into cash in the bank.

```dax
Collection Rate % = 
DIVIDE(
    SUM('fact_project_performance'[Total_Invoiced_Amount_Paid]),
    SUM('fact_project_performance'[Total_Invoiced_Amount_CAD]),
    0
)

### Contract Billed %
##### Compares total invoiced subtotal (before tax) against total signed contract value.

```dax
% Contract Billed = 
DIVIDE(
    SUM('fact_project_performance'[Total_Invoiced_Subtotal_CAD]),
    SUM('fact_project_performance'[Contract_Value_CAD]),
    0
)

### Average CSAT
##### Calculates average client satisfaction directly from raw survey response logs.

```dax
Average CSAT = 
AVERAGE('fact_client_feedback'[Overall_Satisfaction_Score])


## 2. Project Delivery & Schedule Performance

### Total Active Projects

```dax
Total Active Projects = 
CALCULATE(
    COUNTROWS('fact_project_performance'),
    'fact_project_performance'[Project_Status] = "Active"
)

```dax
Delayed Projects Count = 
CALCULATE(
    COUNTROWS('fact_project_performance'),
    'fact_project_performance'[Schedule_Delay_Days] > 0
)

```dax
Schedule Delay Rate % = 
DIVIDE(
    [Delayed Projects Count],
    COUNTROWS('fact_project_performance'),
    0
)


## 3. Resource Utilization & Labor Costs

### Utilization Rate %
##### Measures proportion of total logged hours spent on billable client work.

```dax
Utilization Rate % = 
DIVIDE(
    SUM('fact_project_performance'[Total_Billable_Hours]),
    SUM('fact_project_performance'[Total_Hours_Worked]),
    0
)


-->
