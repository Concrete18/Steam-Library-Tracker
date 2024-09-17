# standard library
from pathlib import Path
import datetime as dt
import json

# local imports
from utils.steam import *

# my package imports
from easierexcel import Sheet


def parse_date(entry):
    """
    Parses dates in the `Jan 10, 2024` format.
    """
    return dt.datetime.strptime(entry["date"], "%b %d, %Y")


def sort_purchase_history(data: list[dict]) -> list[dict]:
    """
    Sorts purchase history by date.
    """
    if "date" not in data[0].keys():
        return []
    return sorted(data, key=lambda entry: parse_date(entry))


def load_purchase_data() -> list[dict]:  # pragma: no cover
    """
    Loads purchase history from config folder.
    """
    path = Path("configs\steam_purchase_history.json")
    if path.exists():
        with open(path) as file:
            purchase_data = json.load(file)
        if purchase_data:
            return sort_purchase_history(purchase_data)
    return []


def create_game_data(purchase_data: list[dict], app_list: list[dict]) -> list[dict]:
    """
    Creates a list of game data while removing entries that were purchased and then refunded

    `purchase_data` must be in ascending purchase_date order to work properly.
    """
    to_update = {}
    for entry in purchase_data:
        entry_type = entry.get("type")
        games = entry.get("games", [])
        for game_name in games:
            app_id = get_app_id(game_name, app_list)
            if entry_type == "Refund":
                to_update.pop(app_id, None)
            else:
                purchase_date = entry.get("date")
                to_update[app_id] = {
                    "game_name": game_name,
                    "purchase_date": purchase_date,
                }
    return to_update


def get_dates_to_update(
    games_data: list[dict],
    steam_sheet: Sheet,
    date_added_col: str,
) -> list[dict]:
    """
    Updates the Date Added column with the correct dates using `games_data`,
    """
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
