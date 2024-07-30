# standard library
import json
import datetime as dt

# local application imports
from classes.steam import Steam

steam_class = Steam()


def load_purchase_data() -> list[dict]:  # pragma: no cover
    """
    Loads purchase history from config folder.
    """
    path = "configs\steam_purchase_history.json"
    with open(path) as file:
        purchase_data = json.load(file)
    if purchase_data:
        # check if data is out of order first
        purchase_data.reverse()
        return purchase_data
    else:
        return []


def create_game_data(purchase_data, app_list):
    to_update = {}
    for entry in purchase_data:
        entry_type = entry.get("type")
        games = entry.get("games", [])
        for game_name in games:
            app_id = steam_class.get_app_id(game_name, app_list)
            if entry_type == "Refund":
                to_update.pop(app_id, None)
            else:
                purchase_date = entry.get("date")
                to_update[app_id] = {
                    "game_name": game_name,
                    "purchase_date": purchase_date,
                }
    return to_update


def get_dates_to_update(games_data, steam_sheet, date_added_col):
    dates_to_update = {}
    for app_id, data in games_data.items():
        current_datetime = steam_sheet.get_cell(app_id, date_added_col)
        if type(current_datetime) != dt.datetime:
            continue
        purchase_date = data.get("purchase_date")
        purchase_datetime = dt.datetime.strptime(purchase_date, "%b %d, %Y")
        if current_datetime.date() != purchase_datetime.date():
            dates_to_update[app_id] = purchase_datetime
    return dates_to_update


def update_dates(dates_to_update, steam_sheet, date_added_col):  # pragma: no cover
    for app_id, purchase_datetime in dates_to_update.items():
        steam_sheet.update_cell(app_id, date_added_col, purchase_datetime)


def update_purchase_date(app_list, steam_sheet, date_added_col):  # pragma: no cover
    """
    Updates Games `Added Date` based on a json.
    """
    purchase_data = load_purchase_data()
    games_data = create_game_data(purchase_data, app_list)
    dates_to_update = get_dates_to_update(games_data, steam_sheet, date_added_col)
    update_dates(dates_to_update, steam_sheet, date_added_col)
