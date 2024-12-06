import pandas as pd
from datetime import datetime, timedelta
from typing import Literal


def filter_df_by_date(
    input_df: pd.DataFrame,
    relative_time: Literal["current", "next", "last", "none"] = "none",
    time_period: Literal["year", "month", "week", "day", "none"] = "none",
):
    """
    Plug in a dataframe (in practice, moods or journals) to filters rows for
    a specific time
    """

    if time_period != "none" and not input_df.empty:
        # Allows us to call the function without a date-time set

        # Establishing beginning and end of today as a benchmark
        today = datetime.today().date()
        start_of_today = datetime.combine(today, datetime.min.time())
        end_of_today = datetime.combine(today, datetime.max.time())

        # Creating variables according to user_chosen time_period
        if time_period == "year":
            start_of_range = start_of_today.replace(month=1, day=1)
            end_of_range = end_of_today.replace(month=12, day=31)
            increment = pd.DateOffset(years=1)
        elif time_period == "month":
            start_of_range = start_of_today.replace(day=1)
            end_of_range = end_of_today + pd.offsets.MonthEnd(0)
            increment = pd.DateOffset(months=1)
        elif time_period == "week":
            start_of_range = start_of_today - timedelta(days=start_of_today.weekday())
            end_of_range = start_of_range + timedelta(days=7)
            increment = timedelta(days=7)
        elif time_period == "day":
            start_of_range = datetime.combine(start_of_today, datetime.min.time())
            end_of_range = datetime.combine(start_of_today, datetime.max.time())
            increment = timedelta(days=1)

        # Increments time_periods
        if relative_time == "current":
            # Might be worth getting rid of this, I don't need to increment this "x"
            pass
        elif relative_time == "next":
            start_of_range += increment
            end_of_range += increment
        elif relative_time == "last":
            start_of_range -= increment
            end_of_range -= increment

        # Filters and outputs the data_frame
        time_sorted_df = input_df[
            (input_df["date"] >= start_of_range) & (input_df["date"] <= end_of_range)
        ]
        return time_sorted_df

    # If the user wants no date-time filters, returns the original dataframe
    return input_df

    # For a later date, want to add the display options:
    # 1. For months and years, I'd like to add a column to group by week / month.
    # For days, I'd also like to add a column for the weekday which corresponds to the meetings
