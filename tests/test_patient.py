import unittest
from unittest.mock import MagicMock
from modules.patient import Patient


class TestPatient(unittest.TestCase):
    def setUp(self):
        # mock database connection
        self.mock_database = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_database.cursor = self.mock_cursor

        # mock user data for mock patient
        self.user_data = {
            "user_id": 1,
            "username": "testuser",
            "first_name": "Test",
            "surname": "User",
            "email": "testuser@example.com",
            "is_active": True,
        }

        self.patient = Patient(
            database=self.mock_database,
            **self.user_data,
        )

    def test_display_previous_moods_no_entries(self):
        # mock query returning no results
        self.mock_cursor.fetchall.return_value = []

        result = self.patient.display_previous_moods()

        self.assertEqual(result, [])

    def test_display_previous_moods_with_entries(self):
        mock_entries = [
            {"date": "2024-01-01", "text": "Feeling great!", "mood": "Great"},
            {
                "date": "2024-01-02",
                "text": "I had a bad exam.",
                "mood": "Terrible",
            },
        ]
        self.mock_cursor.fetchall.return_value = mock_entries

        result = self.patient.display_previous_moods()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["mood"], "Great")
        self.assertEqual(result[1]["text"], "I had a bad exam.")

    def test_cancel_appointment_not_found(self):
        self.mock_cursor.rowcount = 0

        result = self.patient.cancel_appointment(5)

        self.mock_database.connection.commit.assert_not_called()
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
