import pandas as pd
from datetime import datetime, timedelta

def filter_df_by_date(input_df: pd.DataFrame, relative_time: str, time_period: str):
    """
    Plug in a dataframe (in practice, moods or journals) to create a row
    around a specific time
    """
    #Most of this works, a few details to figure out

    today = datetime.today().date()
    start_of_today = datetime.combine(today, datetime.min.time())
    
    if time_period == "year":
        start_of_range = start_of_today.replace(month=1, day=1)
        end_of_range = start_of_today.replace(month=12, day=31)
        # increment = timedelta(year=1)
        # next and last year don't work because you can't increment by year
    elif time_period == "month":
        start_of_range = start_of_today.replace(day=1)
        end_of_range = start_of_today + pd.offsets.MonthEnd(0)
        # increment = timedelta(month=1)
        # next and last month don't work because you can't increment by month
        # Also differnet format for end_of_range and start_of_range migth cause issues
    elif time_period == "week":
        start_of_range = start_of_today - timedelta(days=start_of_today.weekday())
        end_of_range = start_of_range + timedelta(days=6)
        increment = timedelta(days=7)
    elif time_period == "day":
        start_of_range = datetime.combine(start_of_today, datetime.min.time())
        end_of_range = datetime.combine(start_of_today, datetime.max.time())
        increment = timedelta(days=1)

    # Increment them according to what you're trying to do
    if relative_time == "current":
        # Might be worth getting rid of this, I don't need to increment this "x"
        pass
    elif relative_time == "next":
        start_of_range += increment
        end_of_range += increment
    elif relative_time == "last":
        start_of_range -= increment
        end_of_range -= increment

    time_sorted_df = input_df[
        (input_df["date"] >= start_of_range) & (input_df["date"] <= end_of_range)
    ]
    return time_sorted_df

    # For a later date, want to add the display options:
    # 1. For months and years, I'd like to add a column to group by week / month.
    # For days, I'd also like to add a column for the weekday which corresponds to the meetings