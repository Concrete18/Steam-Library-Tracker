import datetime as dt
from pathlib import Path
import pytest, time, json, os


# local imports
from utils.utils import *


class TestCreateHyperlink:

    def test_success(self):
        url = "www.test.com"
        label = "Test Site"
        hyperlink = create_hyperlink(url, label)
        assert hyperlink == '=HYPERLINK("www.test.com","Test Site")'


class TestHoursPlayed:

    def test_get_hours_played(self):
        HOURS_PLAYED_TESTS = {
            800: 13.3,
            30: 0.5,
            2940: 49,
            0: None,
            None: None,
        }
        for minutes_played, answer in HOURS_PLAYED_TESTS.items():
            result = get_hours_played(minutes_played)
            assert result == answer


class TestTimePassed:

    def test_minutes(self):
        """
        tests function when given minutes
        """
        MINUTE_TESTS = {
            12: "12.0 Minutes",
            59: "59.0 Minutes",
            60: "1.0 Hour",
            59.99: "1.0 Hour",
            800: "13.3 Hours",
            1439: "1.0 Day",
            1440: "1.0 Day",
            1441: "1.0 Day",
            2940: "2.0 Days",
            1440 * 7: "1.0 Week",
            525600: "1.0 Year",
        }
        for minutes, answer in MINUTE_TESTS.items():
            output = convert_time_passed(minutes=minutes)
            assert output == answer

    def test_hours(self):
        """
        tests function when given hours
        """
        HOUR_TESTS = {
            0.2: "12.0 Minutes",
            1: "1.0 Hour",
            13.3: "13.3 Hours",
            24: "1.0 Day",
            23.99: "1.0 Day",
            48: "2.0 Days",
        }
        for hours, answer in HOUR_TESTS.items():
            output = convert_time_passed(hours=hours)
            assert output == answer

    def test_days(self):
        """
        tests function when given days
        """
        DAY_TESTS = {
            1: "1.0 Day",
            0.99: "1.0 Day",
            5.8: "5.8 Days",
            21: "3.0 Weeks",
            6.99: "1.0 Week",
            365: "1.0 Year",
        }
        for days, answer in DAY_TESTS.items():
            output = convert_time_passed(days=days)
            assert output == answer

    def test_weeks(self):
        """
        tests function when given weeks
        """
        WEEK_TESTS = {
            4.4: "1.0 Month",
            3.99: "1.0 Month",
            8.5: "2.0 Months",
            52: "1.0 Year",
        }
        for weeks, answer in WEEK_TESTS.items():
            output = convert_time_passed(weeks=weeks)
            assert output == answer

    def test_months(self):
        """
        tests function when given months
        """
        MONTH_TESTS = {
            1: "1.0 Month",
            0.5: "2.2 Weeks",
            12: "1.0 Year",
            11.99: "1.0 Year",
        }
        for months, answer in MONTH_TESTS.items():
            output = convert_time_passed(months=months)
            assert output == answer

    def test_years(self):
        """
        tests function when given years
        """
        YEAR_TESTS = {
            1: "1.0 Year",
            0.999: "1.0 Year",
            5: "5.0 Years",
        }
        for years, answer in YEAR_TESTS.items():
            output = convert_time_passed(years=years)
            assert output == answer

    def test_all_at_once(self):
        """
        Tests function when given Minutes, Hours, Days, Months and Years at the same time.
        """
        # tests all args at once
        output = convert_time_passed(
            minutes=60,
            hours=23,
            days=30,
            months=11,
            years=1,
        )
        assert output == "2.0 Years"


class TestConvertSize:

    def test_bytes(self):
        size = convert_size(256)
        assert size == (256, "B")

    def test_kilobytes(self):
        size = convert_size(16_584)
        assert size == (16.2, "KB")

    def test_megabytes(self):
        size = convert_size(11_457_496)
        assert size == (10.9, "MB")

    def test_gigbytes(self):
        size = convert_size(3_845_845_531)
        assert size == (3.6, "GB")

    def test_terabytes(self):
        size = convert_size(5_323_845_845_531)
        assert size == (4.8, "TB")


class TestGetDirSize:

    def test_success(self):
        dir = "tests/data/test_workshop/12345"
        bytes = get_dir_size(dir)
        assert bytes == 91

    def test_error(self):
        dir = "not real"
        with pytest.raises(ValueError):
            get_dir_size(dir)


class TestDaysSince:

    def test_set_date(self):
        past_date = dt.datetime(2022, 4, 22)
        current_date = dt.datetime(2022, 4, 24)
        days_since = get_days_since(past_date, current_date)
        assert days_since == 2

    def test_todays_date(self):
        past_date = dt.datetime.now() - dt.timedelta(days=7)
        days_since = get_days_since(past_date)
        assert days_since == 7


class TestFormatFloats:

    def test_valid(self):
        string = format_floats(1234.12345, 1)
        assert string == "1,234.1"
        string = format_floats(1234.12345, 3)
        assert string == "1,234.123"

    def test_n_digits_not_valid(self):
        with pytest.raises(TypeError):
            format_floats(1234.12345, "1")


class TestStringToDate:

    def test_valid(self):
        date = string_to_date("02/24/2022")
        assert date == dt.datetime(2022, 2, 24, 0, 0)

    def test_not_valid(self):
        with pytest.raises(ValueError):
            string_to_date("")


class TestGetYear:

    def test_valid(self):
        DATE_TESTS = {
            "Sep 14, 2016": 2016,
            "25 Apr, 1991": 1991,
            "16 Nov, 2009": 2009,
            "Mai 25, 1991": 1991,
            "Apr , 2015": 2015,
        }
        for date, answer in DATE_TESTS.items():
            year = get_year(date)
            assert year == answer

    def test_invalid(self):
        year = get_year("this is not a date")
        assert year is None


class TestUrlSanitize:

    def test_url_sanitize(self):
        URL_TESTS = {
            "Hood: Outlaws & Legends": "hood-outlaws-legends",
            "This is a (test), or is it?": "this-is-a-test-or-is-it",
            "Blade & Sorcery": "blade-sorcery",
        }
        for string, result in URL_TESTS.items():
            assert url_sanitize(string) == result


class TestUnicodeRemover:

    def test_trademark(self):
        new_string = unicode_remover("Game Name™")
        assert new_string == "Game Name"

    def test_trim_removal(self):
        new_string = unicode_remover("® ® ® ö Test ® ® ®")
        assert new_string == "o Test"

    def test_trim_removal(self):
        new_string = unicode_remover("\u2122 \u2013Test\u2013 \u2122")
        assert new_string == "-Test-"

    def test_not_string(self):
        new_string = unicode_remover(123)
        assert new_string == 123


class TestCreateAndSentence:

    def test_list_to_sentence(self):
        LIST_TESTS = [
            (["Test1"], "Test1"),
            (["Test1", "Test2"], "Test1 and Test2"),
            (["Test1", "Test2", "Test3"], "Test1, Test2 and Test3"),
            ([], ""),
        ]
        for list, answer in LIST_TESTS:
            result = list_to_sentence(list)
            assert result == answer


class TestSaveJson:

    @classmethod
    def setup_class(cls):
        print("\nSetup Class")
        cls.path = Path("tests/test.json")

    @classmethod
    def teardown_class(cls):
        print("\nTeardown Class")

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        print("\nSetup Method")
        if self.path.exists():
            os.remove(self.path)
        with open(self.path, "w") as file:
            file.write("{}")
        yield
        print("\nTeardown Method")
        if self.path.exists():
            os.remove(self.path)

    @staticmethod
    def read_json(path):
        with open(path) as file:
            return json.load(file)

    def test_creates_file(self):
        # verify empty
        with open(self.path) as file:
            empty_data = json.load(file)
        assert empty_data == {}
        # create data
        test_data = {}
        save_json(test_data, self.path)
        # verify data
        with open(self.path) as file:
            empty_data = json.load(file)
        created_data = self.read_json(self.path)
        assert created_data == test_data


class TestRecentlyExecuted:

    SECS_IN_DAYS = 86400

    def test_true(self):
        past_time = time.time() - (self.SECS_IN_DAYS * 3)
        data = {
            "last_runs": {
                "test_run": past_time,
            },
        }
        name = "test_run"
        n_days = 5
        test = recently_executed(data, name, n_days)
        assert test is True

    def test_false(self):
        past_time = time.time() - (self.SECS_IN_DAYS * 7)
        data = {
            "last_runs": {
                "test_run": past_time,
            },
        }
        name = "test_run"
        n_days = 5
        test = recently_executed(data, name, n_days)
        assert test is False


class TestCreateRichDateAndTime:

    def test_success(self):
        date = dt.datetime(2000, 1, 1, 1, 1)
        rich_date = create_rich_date_and_time(date)
        answer = (
            "[secondary]Saturday, January 01, 2000[/] [dim]|[/] [secondary]01:01 AM[/]"
        )
        assert rich_date == answer


if __name__ == "__main__":
    pytest.main([__file__])
