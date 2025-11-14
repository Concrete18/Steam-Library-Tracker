# standard library
import os, hashlib, yaml, requests, re

# local application imports
from library.obsidian.obsidian import Obsidian
from library.table import *

# third-party imports
import pandas as pd

APP_ID_COLUMN = "App ID"
NAME_COLUMN = "Name"
YEAR_COLUMN = "Release Year"
RATING_COLUMN = "Rating"


def file_hash(content: str) -> str:
    """Return a short hash of a string for comparison."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def find_local_library_image(app_id):
    starting_path = f"C:/Program Files (x86)/Steam/appcache/librarycache/{app_id}"
    for root, _, files in os.walk(starting_path):
        for file in files:
            if file == "library_600x900.jpg":
                return os.path.join(root, file)


def generate_markdown(name, row) -> str:
    """
    Generate the markdown content for a game note.
    """
    appid = row[APP_ID_COLUMN]
    rating = int(row[RATING_COLUMN])

    year = None
    year_value = row[YEAR_COLUMN]
    if pd.isna(year_value):
        pattern = r"\((\d{4})\)"
        matches = re.findall(pattern, name)
        if matches:
            year = int(matches[0])
    else:
        year = int(row[YEAR_COLUMN])

    image_path = (
        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"
    )
    response = requests.get(image_path)
    if not response.ok:
        # TODO move image into its own folder and delete it if it is noy longer needed
        image_path = find_local_library_image(appid)

    data = {
        "name": name,
        "appid": appid,
        "rating": rating,
        "game_platform": "Steam",
        "year": year,
        "store_page": f"https://store.steampowered.com/app/{appid}",
        "image": image_path,
    }
    return "---\n" + yaml.dump(data, sort_keys=False) + "---\n"


def sync_favorite_games_to_obsidian(ob: Obsidian, df: pd.DataFrame) -> None:
    """
    Syncs games to Obsidian Note as a table.
    """
    # filter high-rated games
    RATING_THRESHOLD = 9
    high_rated = df[df[RATING_COLUMN] >= RATING_THRESHOLD]

    DESTINATION_FOLDER = "Misc/Base Data/Favorite Games"
    valid_files = set()
    for _, row in high_rated.iterrows():
        name = str(row[NAME_COLUMN]).strip()
        filename = os.path.join(ob.full_path(DESTINATION_FOLDER), f"{name}.md")
        valid_files.add(filename)
        content = generate_markdown(name, row)
        new_hash = file_hash(content)

        # check if file exists and unchanged
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                old_content = f.read()
            old_hash = file_hash(old_content)
            if old_hash == new_hash:
                continue
            ob.update_note(filename, content)
            print(f"Updated: {name}")

        else:
            # write new or updated file
            ob.create_note(name, content, DESTINATION_FOLDER)
            print(f"Created: {name}")

    # delete files for games no longer rated 9+
    for file in os.listdir(ob.vault_path):
        if not file.endswith(".md"):
            continue
        full_path = os.path.join(ob.full_path(file))
        if full_path not in valid_files:
            # os.remove(full_path)
            print(f"Deleted: {file}")

    print("Sync complete.")


def sync_to_obsidian(dataframe: pd.DataFrame) -> None:
    """
    Syncs favorite games to multiple notes.
    """
    obsidian = Obsidian("D:/Obsidian Vault")

    sync_favorite_games_to_obsidian(obsidian, dataframe)
