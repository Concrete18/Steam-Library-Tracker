import unittest
import datetime as dt

# classes
from main import Tracker


class TestStringMethods(unittest.TestCase):
    def test_get_year(self):
        tester = Tracker()
        date_tests = {
            "this is not a date": "Invalid Date",
            "Sep 14, 2016": "2016",
            "25 Apr, 1991": "1991",
            "16 Nov, 2009": "2009",
            "Mai 25, 1991": "1991",
            "Apr , 2015": "2015",
        }
        for date, bool in date_tests.items():
            self.assertEqual(tester.get_year(date), bool)

    def test_get_appid(self):
        tester = Tracker()
        appid_tests = {
            "Inscryption": 1092790,
            "Dishonored 2": 403640,
            "Deep Rock Galactic": 548430,
        }
        for name, answer in appid_tests.items():
            self.assertEqual(tester.get_appid(name), answer)

    def test_get_game_info(self):
        tester = Tracker()
        # checks using the app id for Deep Rock Galactic
        dict = tester.get_game_info(1145360)
        keys = ["name", "developers", "publishers"]
        for key in keys:
            self.assertIn(key, dict.keys())

    def test_get_metacritic(self):
        tester = Tracker()
        metacritic_tests = {
            "Dishonored 2": 86,
            "Deep Rock Galactic": 85,
            "Inscryption": 85,
            "Not a Real Game": "Page Error",
        }
        for name, answer in metacritic_tests.items():
            self.assertEqual(tester.get_metacritic(name, "pc"), answer)

    def test_get_time_to_beat(self):
        tester = Tracker()
        time_to_beat_tests = ["Dishonored 2", "Deep Rock Galactic", "Inscryption"]
        for name in time_to_beat_tests:
            result = tester.get_time_to_beat(name)
            self.assertIsInstance(result, float)
        result = tester.get_time_to_beat("Not a Real Game")
        self.assertEqual(result, "Not Found")

    def test_steam_deck_compat(self):
        tester = Tracker()
        passes = ["VERIFIED", "PLAYABLE", "UNSUPPORTED", "UNKNOWN"]
        appids = [1145360, 1167630, 667970, 1579380]
        for appid in appids:
            self.assertIn(tester.steam_deck_compat(appid), passes)
        invalid_appid = 9**30
        self.assertFalse(tester.steam_deck_compat(invalid_appid))

    def test_hours_played(self):
        tester = Tracker()
        time_hours_played = {
            800: 13.3,
            30: 0.5,
            2940: 49,
            0: None,
        }
        for minutes_played, answer in time_hours_played.items():
            self.assertEqual(tester.hours_played(minutes_played), answer)

    def test_time_passed(self):
        tester = Tracker()

        # tests function when given minutes
        minutes_tests = {
            12: "12.0 Minute(s)",
            59: "59.0 Minute(s)",
            60: "1.0 Hour(s)",
            800: "13.3 Hour(s)",
            1439: "1.0 Day(s)",
            1440: "1.0 Day(s)",
            1441: "1.0 Day(s)",
            2940: "2.0 Day(s)",
            1440 * 7: "1.0 Week(s)",
            525600: "1.0 Year(s)",
        }
        for minutes, answer in minutes_tests.items():
            output = tester.convert_time_passed(min=minutes)
            self.assertEqual(output, answer)

        # tests function when given hours
        hours_tests = {
            0.2: "12.0 Minute(s)",
            1: "1.0 Hour(s)",
            13.3: "13.3 Hour(s)",
            24: "1.0 Day(s)",
            48: "2.0 Day(s)",
        }
        for hours, answer in hours_tests.items():
            output = tester.convert_time_passed(hr=hours)
            self.assertEqual(output, answer)

        # tests function when given days
        days_tests = {
            1: "1.0 Day(s)",
            5.8: "5.8 Day(s)",
            21: "3.0 Week(s)",
            365: "1.0 Year(s)",
        }
        for days, answer in days_tests.items():
            output = tester.convert_time_passed(day=days)
            self.assertEqual(output, answer)

        # tests function when given weeks
        weeks_tests = {
            4.4: "1.0 Month(s)",
            # 3.5: "24.5 Day(s)",
            # 52.971: "1.0 Year(s)",
        }
        for weeks, answer in weeks_tests.items():
            output = tester.convert_time_passed(wk=weeks)
            self.assertEqual(output, answer)

        # # tests function when given months TODO
        # days_tests = {
        #     1: "1.0 Month(s)",
        #     18: "1.5 Year(s)",
        #     21: "3.0 Week(s)",
        #     365: "1.0 Year(s)",
        # }
        # for days, answer in days_tests.items():
        #     output = tester.convert_time_passed(day=days)
        #     self.assertEqual(output, answer)

        # # tests function when given years TODO
        # days_tests = {
        #     1: "1.0 Day(s)",
        #     5.8: "5.8 Day(s)",
        #     21: "3.0 Week(s)",
        #     365: "1.0 Year(s)",
        # }

        for days, answer in days_tests.items():
            output = tester.convert_time_passed(day=days)
            self.assertEqual(output, answer)
        # tests all args at once
        output = tester.convert_time_passed(min=60, hr=23, day=30, mnth=11, yr=1)
        self.assertEqual(output, "2.0 Year(s)")

    def test_days_since(self):
        tester = Tracker()
        date_tests = {
            2: dt.datetime(2022, 4, 22),
            10: dt.datetime(2022, 4, 14),
            365: dt.datetime(2021, 4, 24),
        }
        past_date = dt.datetime(2022, 4, 24)
        for answer, current_date in date_tests.items():
            self.assertEqual(tester.days_since(current_date, past_date), answer)

    def test_get_store_link(self):
        tester = Tracker()
        store_link_tests = {
            "752590": "https://store.steampowered.com/app/752590/",
            "629730": "https://store.steampowered.com/app/629730/",
        }
        for appid, answer in store_link_tests.items():
            self.assertEqual(tester.get_store_link(appid), answer)
            # tests that the url exists
            response = tester.request_url(answer)
            self.assertIn(appid, response.url)
            self.assertTrue(response)
        # test for broken link that redirects due to app id not being found
        invalid_url = "https://store.steampowered.com/app/6546546545465484213211545730/"
        response = tester.request_url(invalid_url)
        self.assertNotIn("6546546545465484213211545730", response.url)

    def test_get_steam_review(self):
        tester = Tracker()
        steam_review_tests = [
            752590,
            1161580,
            230410,
            752590,
        ]
        for appid in steam_review_tests:
            percent, total = tester.get_steam_review(appid=appid)
            self.assertIsInstance(percent, float)
            self.assertIsInstance(total, int)
        percent, total = tester.get_steam_review(appid=752590)
        self.assertIsInstance(percent, float)
        self.assertIsInstance(total, int)

    def test_get_game_info(self):
        tester = Tracker()
        default_dict = {
            "developers": "No Data",
            "publishers": "No Data",
            "genre": "No Data",
            "early_access": "No",
            "metacritic": "No Data",
            "steam_review_percent": "No Reviews",
            "steam_review_total": "No Reviews",
            "release_date": "No Year",
            "price": "No Data",
            "discount": "No Data",
            "on_sale": "No Data",
            "linux_compat": "Unsupported",
            "drm_notice": "No Data",
            "categories": "No Data",
            "ext_user_account_notice": "No Data",
        }
        appid_tests = [752590, 1161580, 230410]
        for appid in appid_tests:
            game_info = tester.get_game_info(appid=appid)
            self.assertIsInstance(game_info["Developers"], str)
            self.assertIsInstance(game_info["Publishers"], str)
            self.assertIsInstance(game_info["Genre"], str)
            self.assertIn(game_info["Early Access"], ["Yes", "No"])
            self.assertIsInstance(game_info["Metacritic"], int)
            self.assertIsInstance(game_info["Steam Review Percent"], float)
            self.assertIsInstance(game_info["Steam Review Total"], int)
            self.assertIsInstance(game_info["Release Year"], str)
            self.assertIsInstance(game_info["price"], str)
            self.assertIsInstance(game_info["discount"], float)
            self.assertIn(game_info["on_sale"], ["Yes", "No"])
            self.assertIsInstance(game_info["linux_compat"], str)
            self.assertIsInstance(game_info["drm_notice"], str)
            self.assertIsInstance(game_info["categories"], str)
            self.assertIsInstance(game_info["ext_user_account_notice"], str)
        # TODO ph comment
        # self.assertEqual(tester.get_game_info(None), default_dict)

    def test_url_sanitize(self):
        tester = Tracker()
        url_tests = {
            "Hood: Outlaws & Legends": "hood-outlaws-legends",
            "This is a (test), or is it?": "this-is-a-test-or-is-it",
            "Blade & Sorcery": "blade-sorcery",
        }
        for string, result in url_tests.items():
            self.assertEqual(tester.url_sanitize(string), result)

    def test_word_and_list(self):
        tester = Tracker()
        list_tests = [
            (["Test1"], "Test1"),
            (["Test1", "Test2"], "Test1 and Test2"),
            (["Test1", "Test2", "Test3"], "Test1, Test2 and Test3"),
        ]
        for list, result in list_tests:
            self.assertEqual(tester.word_and_list(list), result)

    def test_should_ignore(self):
        tester = Tracker()
        ignore_names = ["Half-Life 2: Lost Coast"]
        tester.name_ignore_list = [string.lower() for string in ignore_names]
        tester.appid_ignore_list = [61600, 12345864489]
        # empty args return false
        self.assertFalse(tester.should_ignore())
        # appid return true
        self.assertTrue(tester.should_ignore(appid=61600))
        self.assertTrue(tester.should_ignore(appid=12345864489))
        # appid return false
        self.assertFalse(tester.should_ignore(appid=345643))
        # name return true
        self.assertTrue(tester.should_ignore(name="Game Beta"))
        self.assertTrue(tester.should_ignore(name="Squad - Public Testing"))
        self.assertTrue(tester.should_ignore(name="Half-Life 2: Lost Coast"))
        # name return false
        self.assertFalse(tester.should_ignore(name="This is a great game"))

    def test_play_status(self):
        tester = Tracker()
        tests = [
            {"play_status": "Unplayed", "hours": 0.1, "ans": "Unplayed"},
            {"play_status": "Unplayed", "hours": 0.5, "ans": "Played"},
            {"play_status": "Unplayed", "hours": 1, "ans": "Playing"},
            {"play_status": "Unplayed", "hours": 0.5, "ans": "Played"},
            {"play_status": "Finished", "hours": 0.1, "ans": "Finished"},
            # do nothing
            {"play_status": "Waiting", "hours": 100, "ans": "Waiting"},
            {"play_status": "Quit", "hours": 100, "ans": "Quit"},
            {"play_status": "Finished", "hours": 100, "ans": "Finished"},
            {"play_status": "Ignore", "hours": 100, "ans": "Ignore"},
            # must play
            {"play_status": "Must Play", "hours": 0, "ans": "Must Play"},
            {"play_status": "Must Play", "hours": 0.5, "ans": "Played"},
            {"play_status": "Must Play", "hours": 1, "ans": "Playing"},
            # new game
            {"play_status": None, "hours": 0, "ans": "Unplayed"},
            {"play_status": None, "hours": 0.5, "ans": "Played"},
            {"play_status": None, "hours": 1, "ans": "Playing"},
            # error
            {"play_status": None, "hours": "Test", "ans": ""},
            {"play_status": "Unplayed", "hours": "Test", "ans": "Unplayed"},
        ]
        for a in tests:
            self.assertEqual(tester.play_status(a["play_status"], a["hours"]), a["ans"])

    def test_lev_distance(self):
        tester = Tracker()
        string_tests = [
            # insert
            {"word1": "test", "word2": "tests", "ans": 1},
            # delete
            {"word1": "bolt", "word2": "bot", "ans": 1},
            # replace
            {"word1": "spell", "word2": "spelt", "ans": 1},
            # insert, delete and replace
            {"word1": "Thinking", "word2": "Thoughts", "ans": 6},
        ]
        for a in string_tests:
            self.assertEqual(tester.lev_distance(a["word1"], a["word2"]), a["ans"])

    def test_sim_matcher(self):
        tester = Tracker()
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
            self.assertEqual(
                tester.lev_dist_matcher(string, test_list, debug=True)[0],
                answer,
            )
            # self.assertEqual(tester.sim_matcher(string, test_list, debug=True), answer)


if __name__ == "__main__":
    unittest.main()
