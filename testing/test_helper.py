import datetime as dt
import unittest

# classes
from classes.helper import Helper


class HoursPlayed(unittest.TestCase):
    def setUp(self):
        self.t = Helper()

    def test_hours_played(self):
        time_hours_played = {
            800: 13.3,
            30: 0.5,
            2940: 49,
            0: None,
        }
        for minutes_played, answer in time_hours_played.items():
            with self.subTest(minutes_played=minutes_played, answer=answer):
                result = self.t.hours_played(minutes_played)
                self.assertEqual(result, answer)


class TimePassed(unittest.TestCase):
    """
    Tests convert_time_passed function
    """

    def setUp(self):
        self.t = Helper()

    def test_minutes(self):
        """
        tests function when given minutes
        """
        minutes_tests = {
            12: "12.0 Minutes",
            59: "59.0 Minutes",
            60: "1.0 Hour",
            800: "13.3 Hours",
            1439: "1.0 Day",
            1440: "1.0 Day",
            1441: "1.0 Day",
            2940: "2.0 Days",
            1440 * 7: "1.0 Week",
            525600: "1.0 Year",
        }
        for minutes, answer in minutes_tests.items():
            with self.subTest(minutes=minutes, answer=answer):
                output = self.t.convert_time_passed(min=minutes)
                self.assertEqual(output, answer)

    def test_hours(self):
        """
        tests function when given hours
        """
        hours_tests = {
            0.2: "12.0 Minutes",
            1: "1.0 Hour",
            13.3: "13.3 Hours",
            24: "1.0 Day",
            48: "2.0 Days",
        }
        for hours, answer in hours_tests.items():
            with self.subTest(hours=hours, answer=answer):
                output = self.t.convert_time_passed(hr=hours)
                self.assertEqual(output, answer)

    def test_days(self):
        """
        tests function when given days
        """
        days_tests = {
            1: "1.0 Day",
            5.8: "5.8 Days",
            21: "3.0 Weeks",
            365: "1.0 Year",
        }
        for days, answer in days_tests.items():
            with self.subTest(days=days, answer=answer):
                output = self.t.convert_time_passed(day=days)
                self.assertEqual(output, answer)

    def test_weeks(self):
        """
        tests function when given weeks
        """
        weeks_tests = {
            4.4: "1.0 Month",
            8.5: "2.0 Months",
            52: "1.0 Year",
        }
        for weeks, answer in weeks_tests.items():
            with self.subTest(weeks=weeks, answer=answer):
                output = self.t.convert_time_passed(wk=weeks)
                self.assertEqual(output, answer)

    def test_months(self):
        """
        tests function when given months
        """
        months_tests = {
            1: "1.0 Month",
            0.5: "2.2 Weeks",
            12: "1.0 Year",
        }
        for months, answer in months_tests.items():
            with self.subTest(months=months, answer=answer):
                output = self.t.convert_time_passed(mnth=months)
                self.assertEqual(output, answer)

    def test_years(self):
        """
        tests function when given years
        """
        days_tests = {
            1: "1.0 Year",
            5: "5.0 Years",
        }
        for years, answer in days_tests.items():
            with self.subTest(years=years, answer=answer):
                output = self.t.convert_time_passed(yr=years)
                self.assertEqual(output, answer)

    def test_all_at_once(self):
        """
        Tests function when given Minutes, Hours, Days, Months and
        Years at the same time.
        """
        # tests all args at once
        output = self.t.convert_time_passed(min=60, hr=23, day=30, mnth=11, yr=1)
        self.assertEqual(output, "2.0 Years")


class DaysSince(unittest.TestCase):
    """
    Tests days_since function
    """

    def setUp(self):
        self.t = Helper()

    def test_days_since(self):
        date_tests = {
            2: dt.datetime(2022, 4, 22),
            10: dt.datetime(2022, 4, 14),
            365: dt.datetime(2021, 4, 24),
        }
        past_date = dt.datetime(2022, 4, 24)
        for answer, current_date in date_tests.items():
            self.assertEqual(self.t.days_since(current_date, past_date), answer)


class UrlSanitize(unittest.TestCase):
    def setUp(self):
        self.t = Helper()

    def test_url_sanitize(self):
        url_tests = {
            "Hood: Outlaws & Legends": "hood-outlaws-legends",
            "This is a (test), or is it?": "this-is-a-test-or-is-it",
            "Blade & Sorcery": "blade-sorcery",
        }
        for string, result in url_tests.items():
            self.assertEqual(self.t.url_sanitize(string), result)


class WordAndList(unittest.TestCase):
    """
    Tests word_and_list function.
    """

    def setUp(self):
        self.t = Helper()

    def test_word_and_list(self):
        list_tests = [
            (["Test1"], "Test1"),
            (["Test1", "Test2"], "Test1 and Test2"),
            (["Test1", "Test2", "Test3"], "Test1, Test2 and Test3"),
        ]
        for list, answer in list_tests:
            with self.subTest(list=list, answer=answer):
                result = self.t.word_and_list(list)
                self.assertEqual(result, answer)


class LevenshteinDistance(unittest.TestCase):
    """
    Tests Similarity Matching Functions.
    """

    def setUp(self):
        self.t = Helper()

    def test_lev_distance_insert(self):
        """
        Tests Levenshtein Distance insert difference.
        """
        self.assertEqual(self.t.lev_distance("test", "tests"), 1)

    def test_lev_distance_delete(self):
        """
        Tests Levenshtein Distance delete difference.
        """
        self.assertEqual(self.t.lev_distance("bolt", "bot"), 1)

    def test_lev_distance_replace(self):
        """
        Tests Levenshtein Distance replace difference.
        """
        self.assertEqual(self.t.lev_distance("spell", "spelt"), 1)

    def test_lev_distance_all_change(self):
        """
        Tests Levenshtein Distance insert, delete and replace all at once.
        """
        self.assertEqual(self.t.lev_distance("Thinking", "Thoughts"), 6)


class SimilarityMatching(unittest.TestCase):
    def setUp(self):
        self.t = Helper()

    def test_lev_dist_matcher(self):
        test_list = [
            "This is a test, yay",
            "this is not it, arg",
            "Find the batman!",
            "Shadow Tactics: Blades of the Shogun - Aiko's Choice",
            "The Last of Us",
            "Elden Ring",
            "The Last of Us Part I",
            "The Last of Us Part II",
            "Waltz of the Wizard: Natural Magic",
            "Life is Strange™",
            "The Witcher 3: Wild Hunt",
            "Marvel's Spider-Man: Miles Morales",
            "Crypt Of The Necrodancer: Nintendo Switch Edition",
        ]
        string_tests = {
            "This is a test": "This is a test, yay",
            "find th bamtan": "Find the batman!",
            "Eldn Rings": "Elden Ring",
            "Shadow Tactics Blades of the Shougn Aikos Choce": "Shadow Tactics: Blades of the Shogun - Aiko's Choice",
            "the last of us": "The Last of Us",
            "Walk of the Wizard: Natural Magik": "Waltz of the Wizard: Natural Magic",
            "The last of us Part I": "The Last of Us Part I",
            "Life is Strange 1": "Life is Strange™",
            "Witcher 3: The Wild Hunt": "The Witcher 3: Wild Hunt",
            "Spider-Man: Miles Morales": "Marvel's Spider-Man: Miles Morales",
            "grave Of The deaddancer: Switch Edition": "Crypt Of The Necrodancer: Nintendo Switch Edition",
        }
        for string, answer in string_tests.items():
            result = self.t.lev_dist_matcher(string, test_list)[0]
            self.assertEqual(result, answer)


if __name__ == "__main__":
    unittest.main()
