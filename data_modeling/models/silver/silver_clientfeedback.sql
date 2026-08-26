/*
  Model: silver_clientfeedback
  Layer: Silver
  Description: Standardizes post-project customer survey feedback responses.
  Why: Isolates survey satisfaction scores, delivery quality ratings, and communication 
                scores for feedback reporting.
*/


with feedback as (
    select * from {{ ref('stg_clientfeedback') }}
)
select
    Feedback_ID,
    Project_ID,
    Feedback_Date,
    Delivery_Quality_Score,
    Communication_Score,
    Value_For_Money_Score,
    Overall_Satisfaction_Score,
    Would_Recommend
from feedback
