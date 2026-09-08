/*
  Model: dim_locations
  Layer: Gold
  Description: Maps office branch locations to reporting regions and provincial tax 
              configurations (tax designations and rates).
  Why: Facilitates regional performance comparisons, geographic revenue distribution 
              analysis, and provincial tax compliance reporting.
*/


{{ config(materialized='table') }}

SELECT
    loc.Branch_ID,
    loc.City,
    loc.Province,
    loc.Region,
    loc.Office_Open_Date,
    loc.Branch_Manager,
    loc.Tax_Name,
    loc.Tax_Rate
FROM {{ ref('silver_locations') }} loc
