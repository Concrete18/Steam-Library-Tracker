import datetime as dt
import unittest

# classes
from Game_Tracker import Tracker


class TestStringMethods(unittest.TestCase):
    def test_get_year(self):
        print("\n", "get_year")
        test = Tracker()
        date_tests = {
            "this is not a date": "Invalid Date",
            "Sep 14, 2016": "2016",
            "25 Apr, 1991": "1991",
            "16 Nov, 2009": "2009",
            "Mai 25, 1991": "1991",
            "Apr , 2015": "2015",
        }
        for date, bool in date_tests.items():
            self.assertEqual(test.get_year(date), bool)

    def test_get_app_id(self):
        print("\n", "get_app_id")
        test = Tracker()
        app_id_tests = {
            "Dishonored 2": 403640,
            "Deep Rock Galactic": 548430,
            "Inscryption": 1092790,
        }
        for name, answer in app_id_tests.items():
            self.assertEqual(test.get_app_id(name), answer)

    def test_string_url_convert(self):
        print("\n", "string_url_convert")
        test = Tracker()
        string_tests = {
            "Where is the beef?": "where_is_the_beef",
            "Deep Rock Galactic": "deep_rock_galactic",
            "Inscryption": "inscryption",
        }
        for string, answer in string_tests.items():
            self.assertEqual(test.string_url_convert(string), answer)

    def test_get_game_info(self):
        print("\n", "get_game_info")
        test = Tracker()
        # checks using the app id for Deep Rock Galactic
        dict = test.get_game_info(1145360)
        keys = ["key", "developers", "publishers"]
        for key in keys:
            self.assertIn(key, dict.keys())

    def test_get_metacritic(self):
        print("\n", "get_metacritic")
        test = Tracker()
        metacritic_tests = {
            "Dishonored 2": 86,
            "Deep Rock Galactic": 85,
            "Inscryption": 85,
            "Not a Real Game": "Page Error",
        }
        for name, answer in metacritic_tests.items():
            self.assertEqual(test.get_metacritic(name, "pc"), answer)


if __name__ == "__main__":
    unittest.main()
