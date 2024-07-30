import datetime as dt

# local application imports
from classes.date_updater import create_game_data, get_dates_to_update

from easierexcel import Excel, Sheet


class TestCreateGameDict:

    def test_success(self):
        purchase_data = [
            {
                "date": "Jul 10, 2024",
                "games": ["Bad Game"],
                "type": "Purchase",
                "total": 15.25,
            },
            {
                "date": "Jul 11, 2024",
                "games": ["Hades"],
                "type": "Purchase",
                "total": 15.25,
            },
            {
                "date": "Jul 15, 2024",
                "games": ["Bad Game"],
                "type": "Refund",
                "total": 15.25,
            },
        ]
        app_list = [{"appid": 12345, "name": "Hades"}]
        games_data = create_game_data(purchase_data, app_list)
        assert games_data == {
            12345: {"game_name": "Hades", "purchase_date": "Jul 11, 2024"}
        }


class TestGetDatesToUpdate:

    def test_success(self, mocker):
        date = dt.datetime(2024, 5, 11)
        results = [date, "not date"]
        mocker.patch("easierexcel.Sheet.get_cell", side_effect=results)

        games_data = {
            12345: {"game_name": "Hades", "purchase_date": "Jul 11, 2024"},
            54321: {"game_name": "Other Game", "purchase_date": "Nov 7, 2420"},
        }
        test_sheet = Sheet(Excel("tests/data/test_library.xlsx"), "Name")
        dates_to_update = get_dates_to_update(games_data, test_sheet, "Test")
        assert dates_to_update == {12345: dt.datetime(2024, 7, 11)}
