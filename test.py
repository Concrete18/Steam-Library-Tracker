import datetime as dt
import time
import unittest
# classes
from Game_Tracker import Tracker
from classes.helper import Helper


class TestStringMethods(unittest.TestCase):


    def test_standardize_date(self):
        print('\n', 'standardize_date')
        test = Tracker()
        date_tests = {
            'this is not a date': 'Invalid Release Date',
            'Sep 14, 2016': 'Sep 14, 2016',
            '25 Apr, 1991': 'Apr 25, 1991',
            '16 Nov, 2009': 'Nov 16, 2009',
            'Mai 25, 1991': '1991',
        }
        for date, bool in date_tests.items():
            self.assertEqual(test.standardize_date(date), bool)

    def test_get_app_id(self):
        print('\n', 'get_app_id')  
        test = Tracker()
        app_id_tests = {
            'Dishonored 2': 403640,
            'Deep Rock Galactic': 548430,
            'Inscryption': 1092790,
        }
        for name, answer in app_id_tests.items():
            self.assertEqual(test.get_app_id(name), answer)

    def test_string_url_convert(self):
        print('\n', 'string_url_convert')  
        test = Tracker()
        string_tests = {
            'Where is the beef?': 'where_is_the_beef',
            'Deep Rock Galactic': 'deep_rock_galactic',
            'Inscryption': 'inscryption',
        }
        for string, answer in string_tests.items():
            self.assertEqual(test.string_url_convert(string), answer)

    # def test_get_proton_rating(self):
    #     print('\n', 'get_proton_rating')  
    #     test = Tracker()
    #     string_tests = {
    #         'Deep Rock Galactic': 'deep_rock_galactic',
    #         'Inscryption': 'inscryption',
    #     }
    #     for name, answer in string_tests.items():
    #         self.assertEqual(test.get_proton_rating(name), answer)

    # def test_standardize_date(self):
    #     print('\n', 'api_sleeper')
    #     test = Helper()
    #     cur_time = dt.datetime.now()
    #     test.api_sleeper('test', 5)
    #     test.api_sleeper('test', 5)
    #     print(dt.datetime.now() - cur_time)
        # self.assertEqual(dt.datetime.now() - cur_time > dt.timedelta(seconds=5), True)


if __name__ == '__main__':
    unittest.main()
