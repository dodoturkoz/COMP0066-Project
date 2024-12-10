from datetime import date, datetime, timedelta

from database.setup import Database


class StreakService:
    mood_streaks: list[int]
    current_user_streak: int
    database: Database

    def __init__(self, db: Database, crr_user_id: int):
        self.database = db
        self.mood_streaks = self.get_all_user_mood_streaks(crr_user_id)
        self.mood_streaks.sort(reverse=True)

    def print_current_user_streak(self) -> None:
        position = self.get_current_user_position()
        ties = self.get_current_user_ties()
        print(
            f"You have logged your mood for {self.current_user_streak} days in a row."
        )

        position_string = ""
        if position == 1:
            position_string = "You have the longest streak in the leaderboard"
        else:
            position_string = f"Your position in the leaderboard is {position}"

        tie_string = f", tied with {ties} other users" if ties > 0 else ""

        print(f"{position_string}{tie_string}.")

        if position == 1:
            print("Continue logging your mood daily to maintain your lead!")
        else:
            print("Continue registering your mood daily to advance in the leaderboard!")

    def get_current_user_position(self) -> int:
        """
        Get the current user's position in the streak leaderboard.
        """
        return self.mood_streaks.index(self.current_user_streak) + 1

    def get_current_user_ties(self) -> int:
        """
        Get the number of users who have the same streak as the current user.
        """
        return self.mood_streaks.count(self.current_user_streak) - 1

    def get_all_user_mood_streaks(self, crr_user_id: int) -> list[int]:
        """
        Get the mood streaks of all users.
        """
        self.database.cursor.execute("SELECT user_id FROM Users WHERE role = 'patient'")
        users = self.database.cursor.fetchall()
        mood_streaks = []

        for user in users:
            mood_streaks.append(self.get_user_mood_streak(user))
            if user == crr_user_id:
                self.current_user_streak = mood_streaks[-1]

        return mood_streaks

    def get_user_mood_streak(self, user_id: int) -> int:
        """
        Calculate a streak of mood entries for a user.
        """

        # Get all dates where the user has mood entries
        # NOTE: this is not the most efficient as we call the db for each user
        self.database.cursor.execute(
            "SELECT date FROM MoodEntries WHERE user_id = ?", (user_id,)
        )
        dates = self.database.cursor.fetchall()
        streak = 0

        # Max streak is 10 years
        for i in range(1, 365 * 10):
            # Go back one day at a time and check if the user has a mood entry
            test_date = datetime.combine(
                date.today() - timedelta(days=i), datetime.min.time()
            )

            if test_date in dates:
                streak += 1
            else:
                # Stop when we find a day without a mood entry
                break

        return streak
