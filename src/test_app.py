import copy
import unittest
from datetime import date, timedelta

from fastapi import HTTPException

from src import app as app_module


class SignupValidationTests(unittest.TestCase):
    def setUp(self):
        self.activities = copy.deepcopy(app_module.activities)

    def tearDown(self):
        app_module.activities.clear()
        app_module.activities.update(self.activities)

    def signup(self, activity_name, email="new@mergington.edu"):
        return app_module.signup_for_activity(activity_name, email)

    def test_rejects_duplicate_enrollment(self):
        with self.assertRaises(HTTPException) as error:
            self.signup("Chess Club", "michael@mergington.edu")

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail, "Student is already signed up")

    def test_rejects_full_activity(self):
        activity = app_module.activities["Chess Club"]
        activity["participants"] = [
            f"student{index}@mergington.edu"
            for index in range(activity["max_participants"])
        ]

        with self.assertRaises(HTTPException) as error:
            self.signup("Chess Club")

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail, "Activity is full")

    def test_rejects_signup_before_registration_opens(self):
        app_module.activities["Chess Club"]["registration_start"] = (
            date.today() + timedelta(days=1)
        ).isoformat()

        with self.assertRaises(HTTPException) as error:
            self.signup("Chess Club")

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(
            error.exception.detail,
            "Registration for this activity has not opened"
        )

    def test_rejects_signup_after_registration_closes(self):
        app_module.activities["Chess Club"]["registration_end"] = (
            date.today() - timedelta(days=1)
        ).isoformat()

        with self.assertRaises(HTTPException) as error:
            self.signup("Chess Club")

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(
            error.exception.detail,
            "Registration for this activity has closed"
        )

    def test_accepts_signup_within_registration_window(self):
        activity = app_module.activities["Chess Club"]
        activity["registration_start"] = (
            date.today() - timedelta(days=1)
        ).isoformat()
        activity["registration_end"] = (
            date.today() + timedelta(days=1)
        ).isoformat()

        self.signup("Chess Club")

        self.assertIn("new@mergington.edu", activity["participants"])

    def test_rejects_more_than_two_activity_enrollments(self):
        email = "new@mergington.edu"
        self.signup("Art Club", email)
        self.signup("Gym Class", email)

        with self.assertRaises(HTTPException) as error:
            self.signup("Math Club", email)

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(
            error.exception.detail,
            "Students may sign up for at most 2 activities"
        )

    def test_rejects_overlapping_schedule(self):
        email = "new@mergington.edu"
        self.signup("Chess Club", email)

        with self.assertRaises(HTTPException) as error:
            self.signup("Basketball Team", email)

        self.assertEqual(error.exception.status_code, 400)
        self.assertIn("Chess Club enrollment", error.exception.detail)

    def test_allows_same_time_on_different_days(self):
        email = "new@mergington.edu"
        self.signup("Chess Club", email)

        self.signup("Programming Class", email)

        self.assertIn(
            email, app_module.activities["Programming Class"]["participants"]
        )

    def test_allows_non_overlapping_times_on_shared_day(self):
        email = "new@mergington.edu"
        self.signup("Gym Class", email)

        self.signup("Chess Club", email)

        self.assertIn(
            email, app_module.activities["Chess Club"]["participants"]
        )

    def test_detects_partial_overlap_across_multiple_shared_days(self):
        email = "new@mergington.edu"
        self.signup("Programming Class", email)

        with self.assertRaises(HTTPException) as error:
            self.signup("Soccer Team", email)

        self.assertEqual(error.exception.status_code, 400)
        self.assertIn("Programming Class enrollment", error.exception.detail)


if __name__ == "__main__":
    unittest.main()
