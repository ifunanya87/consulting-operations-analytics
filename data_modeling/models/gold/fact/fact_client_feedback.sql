/*
  Model: fact_client_feedback
  Layer: Gold
  Description: Stores client feedback, rating scores, and review results from completed projects.
  Why: Tracks service quality and see how happy clients are to boost client retention.
*/


{{ config(materialized='table') }}

select
    fb.Feedback_ID,
    fb.Project_ID,
    p.Client_ID,
    p.Service_Line_ID,
    fb.Feedback_Date,
    fb.Delivery_Quality_Score,
    fb.Communication_Score,
    fb.Value_For_Money_Score,
    fb.Overall_Satisfaction_Score,
    fb.Would_Recommend
from {{ ref('silver_clientfeedback') }} fb
left join {{ ref('silver_projects') }} p 
    on fb.Project_ID = p.Project_ID
