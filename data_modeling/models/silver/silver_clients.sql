/*
  Model: silver_clients
  Layer: Silver
  Description: Combines primary client profile records with payment contract terms 
                to build a unified client entity.
  Why: Merging contract terms into the client model keeps client attributes together, 
        preventing redundant joins in Gold dimensions.
*/


with clients as (
    select * from {{ ref('stg_clients') }}
),
contract_terms as (
    select * from {{ ref('stg_clientcontractterms') }}
)
select
    c.Client_Id,
    c.Client_Name,
    c.Industry,
    c.City,
    c.Province,
    c.Region,
    c.Client_Size,
    c.Account_Manager_Id,
    c.Client_Start_Date,
    c.Active_Status,
    ct.Payment_Terms_Days,
    ct.Preferred_Invoice_Frequency,
    ct.Client_Priority,
    ct.Default_Currency
from clients c
left join contract_terms ct 
    on c.Client_Id = ct.Client_Id
