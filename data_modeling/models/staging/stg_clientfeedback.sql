/*
  Model: stg_clientfeedback
  Layer: Staging
  Description: Cleans raw client feedback entries, standardizes key identifiers and dates, 
                recalculates missing overall satisfaction scores from component averages, 
                and derives client recommendation indicators.
*/

{{ config(materialized='view') }}


with source as (
    select * from {{ source('raw_data', 'ClientFeedback') }}
),
calculated as (
    select 
        Feedback_ID,
        upper(trim(Project_ID)) as Project_ID,
        try_cast(nullif(trim(cast(Feedback_Date as varchar)), '') as date) as Feedback_Date,
        Delivery_Quality_Score,
        Communication_Score,
        Value_For_Money_Score,
        coalesce(
            Overall_Satisfaction_Score,
            round((Delivery_Quality_Score + Communication_Score + Value_For_Money_Score) / 3.0, 1)
        ) as Overall_Satisfaction_Score
    from source
)

select
    Feedback_ID,
    Project_ID,
    Feedback_Date,
    Delivery_Quality_Score,
    Communication_Score,
    Value_For_Money_Score,
    Overall_Satisfaction_Score,
    case 
        when Overall_Satisfaction_Score >= 4.0 then 'Yes'
        when Overall_Satisfaction_Score >= 3.5 then 'Maybe'
        else 'No'
    end as Would_Recommend
from calculated
