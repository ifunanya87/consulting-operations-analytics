/*
  Model: dim_clients
  Layer: Gold
  Description: Standardizes client profile data and payment terms into one central view.
  Why: It creates a single source of truth to track revenue, projects, 
        and payments by industry, region, client size, and priority.
*/

{{ config(materialized='table') }}

SELECT
    c.Client_ID,
    c.Client_Name,
    c.Industry,
    c.City,
    c.Province,
    c.Region,
    c.Client_Size,
    c.Account_Manager_ID,
    c.Client_Start_Date,
    c.Active_Status,
    c.Payment_Terms_Days,
    c.Preferred_Invoice_Frequency,
    c.Client_Priority,
    c.Default_Currency
FROM {{ ref('silver_clients') }} c
