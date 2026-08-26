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
SUM('fact_invoices'[total_invoice_amount_cad]) -->
