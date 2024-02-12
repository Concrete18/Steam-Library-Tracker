import datetime as dt
import unittest

# classes
from classes.utils import Utils


class HoursPlayed(unittest.TestCase):
    """
    Tests `hours_played` function
    """

    def setUp(self):
        self.t = Utils()

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
    Tests `convert_time_passed` function
    """

    def setUp(self):
        self.t = Utils()

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
                output = self.t.convert_time_passed(minutes=minutes)
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
                output = self.t.convert_time_passed(hours=hours)
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
                output = self.t.convert_time_passed(days=days)
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
                output = self.t.convert_time_passed(weeks=weeks)
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
                output = self.t.convert_time_passed(months=months)
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
                output = self.t.convert_time_passed(years=years)
                self.assertEqual(output, answer)

    def test_all_at_once(self):
        """
        Tests function when given Minutes, Hours, Days, Months and
        Years at the same time.
        """
        # tests all args at once
        output = self.t.convert_time_passed(
            minutes=60,
            hours=23,
            days=30,
            months=11,
            years=1,
        )
        self.assertEqual(output, "2.0 Years")


class DaysSince(unittest.TestCase):
    """
    Tests `days_since` function
    """

    def setUp(self):
        self.t = Utils()

    def test_set_date(self):
        past_date = dt.datetime(2022, 4, 22)
        current_date = dt.datetime(2022, 4, 24)
        days_since = self.t.days_since(past_date, current_date)
        self.assertEqual(days_since, 2)

    def test_todays_date(self):
        past_date = dt.datetime.now() - dt.timedelta(days=7)
        days_since = self.t.days_since(past_date)
        self.assertEqual(days_since, 7)


class StringToDate(unittest.TestCase):
    """
    Tests `string_to_date` function
    """

    def setUp(self):
        self.t = Utils()

    def test_valid(self):
        date = self.t.string_to_date("02/24/2022")
        self.assertEqual(date, dt.datetime(2022, 2, 24, 0, 0))

    def test_not_valid(self):
        with self.assertRaises(ValueError):
            self.t.string_to_date("")


class GetYear(unittest.TestCase):
    """
    Tests `get_year` function.
    """

    def setUp(self):
        self.t = Utils()

    def test_valid(self):
        date_tests = {
            "Sep 14, 2016": "2016",
            "25 Apr, 1991": "1991",
            "16 Nov, 2009": "2009",
            "Mai 25, 1991": "1991",
            "Apr , 2015": "2015",
        }
        for date, answer in date_tests.items():
            with self.subTest(date=date):
                year = self.t.get_year(date)
                self.assertEqual(year, answer, "The year was not correctly found")

    def test_invalid(self):
        year = self.t.get_year("this is not a date")
        self.assertIsNone(year)


class UrlSanitize(unittest.TestCase):
    """
    Tests `url_sanitize` function
    """

    def setUp(self):
        self.t = Utils()

    def test_url_sanitize(self):
        url_tests = {
            "Hood: Outlaws & Legends": "hood-outlaws-legends",
            "This is a (test), or is it?": "this-is-a-test-or-is-it",
            "Blade & Sorcery": "blade-sorcery",
        }
        for string, result in url_tests.items():
            self.assertEqual(self.t.url_sanitize(string), result)


class UnicodeRemover(unittest.TestCase):
    """
    Tests `unicode_remover` function
    """

    def setUp(self):
        self.t = Utils()

    def test_trademark(self):
        new_string = self.t.unicode_remover("Game Name™")
        self.assertEqual(new_string, "Game Name")

    def test_trim_removal(self):
        new_string = self.t.unicode_remover("® ® ® ö Test ® ® ®")
        self.assertEqual(new_string, "o Test")

    def test_trim_removal(self):
        new_string = self.t.unicode_remover("\u2122 \u2013Test\u2013 \u2122")
        self.assertEqual(new_string, "-Test-")

    def test_not_string(self):
        new_string = self.t.unicode_remover(123)
        self.assertEqual(new_string, 123)


class CreateAndSentence(unittest.TestCase):
    """
    Tests `list_to_sentence` function.
    """

    def setUp(self):
        self.t = Utils()

    def test_list_to_sentence(self):
        list_tests = [
            (["Test1"], "Test1"),
            (["Test1", "Test2"], "Test1 and Test2"),
            (["Test1", "Test2", "Test3"], "Test1, Test2 and Test3"),
            ([], ""),
        ]
        for list, answer in list_tests:
            with self.subTest(list=list, answer=answer):
                result = self.t.list_to_sentence(list)
                self.assertEqual(result, answer)


class LevenshteinDistance(unittest.TestCase):
    """
    Tests `lev_distance` Function.
    """

    def setUp(self):
        self.t = Utils()

    def test_lev_distance_insert(self):
        """
        Tests Levenshtein Distance insert difference.
        """
        self.assertEqual(self.t.lev_distance("test", "tests"), 1)
        self.assertEqual(self.t.lev_distance("test", "the tests"), 5)

    def test_lev_distance_delete(self):
        """
        Tests Levenshtein Distance delete difference.
        """
        self.assertEqual(self.t.lev_distance("bolt", "bot"), 1)
        self.assertEqual(self.t.lev_distance("bridges", "bride"), 2)

    def test_lev_distance_replace(self):
        """
        Tests Levenshtein Distance replace difference.
        """
        self.assertEqual(self.t.lev_distance("spell", "spelt"), 1)
        self.assertEqual(self.t.lev_distance("car", "bat"), 2)

    def test_lev_distance_all_change(self):
        """
        Tests Levenshtein Distance insert, delete and replace all at once.
        """
        self.assertEqual(self.t.lev_distance("Thinking", "Thoughts"), 6)


class SimilarityMatching(unittest.TestCase):
    def setUp(self):
        self.t = Utils()

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


# class SimMatcher(unittest.TestCase):
#     def setUp(self):
#         self.t = Utils()

#     def test_lev_dist_matcher(self):
#         test_list = [
#             "This is a test, yay",
#             "this is not it, arg",
#             "Find the batman!",
#             "Shadow Tactics: Blades of the Shogun - Aiko's Choice",
#             "The Last of Us",
#             "Elden Ring",
#             "The Last of Us Part I",
#             "The Last of Us Part II",
#             "Waltz of the Wizard: Natural Magic",
#             "Life is Strange™",
#             "The Witcher 3: Wild Hunt",
#             "Marvel's Spider-Man: Miles Morales",
#             "Crypt Of The Necrodancer: Nintendo Switch Edition",
#         ]
#         string_tests = {
#             "This is a test": "This is a test, yay",
#             "find th bamtan": "Find the batman!",
#             "Eldn Rings": "Elden Ring",
#             "Shadow Tactics Blades of the Shougn Aikos Choce": "Shadow Tactics: Blades of the Shogun - Aiko's Choice",
#             "the last of us": "The Last of Us",
#             "Walk of the Wizard: Natural Magik": "Waltz of the Wizard: Natural Magic",
#             "The last of us Part I": "The Last of Us Part I",
#             "Life is Strange 1": "Life is Strange™",
#             "Witcher 3: The Wild Hunt": "The Witcher 3: Wild Hunt",
#             "Spider-Man: Miles Morales": "Marvel's Spider-Man: Miles Morales",
#             "grave Of The deaddancer: Switch Edition": "Crypt Of The Necrodancer: Nintendo Switch Edition",
#         }
#         for string, answer in string_tests.items():
#             result = self.t.sim_matcher(string, test_list)[0]
#             self.assertEqual(result, answer)


class AnyIsNum(unittest.TestCase):
    """
    Tests `any_is_num` function.
    """

    def setUp(self):
        self.t = Utils()

    def test_true_num(self):
        self.assertTrue(self.t.any_is_num(155))
        self.assertTrue(self.t.any_is_num(45.15))

    def test_true_string(self):
        self.assertTrue(self.t.any_is_num("1232"))
        self.assertTrue(self.t.any_is_num("123.2"))

    def test_false(self):
        self.assertFalse(self.t.any_is_num("not a num"))


if __name__ == "__main__":
    unittest.main()
