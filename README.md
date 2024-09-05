# Steam Library Tracker

Steam Library Tracker allows keeping up with what you have played and want to play etc..
Many different types of information is auto retrieved using API's and Scraping.

## Images

![Console Preview](https://raw.githubusercontent.com/Concrete18/Game-Library-Tracker/main/images/Console.png)

![Excel Preview](https://raw.githubusercontent.com/Concrete18/Game-Library-Tracker/main/images/excel.png)

## Technology Used

- Python Pandas
- Rich Console
- API Requests
- Web Scraping with Requests and BeautifulSoup
- [EasierExcel](https://github.com/Concrete18/easierexcel) (my custom library based on OpenPyXL)

## Features

- [Auto Updating Steam Data](#Auto-Updating-Steam-Data)
- [Game Status Highlighting](#Game-Status-Highlighting)
- [Favorite Game Sale Checker](#Favorite-Game-Sale-Checker)
- [Random game picker](#Random-game-picker)
- [Player Count Sync](#Player-Count-Sync)
- [Update Library Add Dates](#Update-Library-Add-Dates)
- [Friends List Tracking](#Friends-List-Tracking)
- [Library Statistics](#Library-Statistics)
- [Omit games by name or App ID](#Omit-games-by-Name-or-App-ID)

## Setup

1. Install Python (It is currently tested with Python 11.1 and Python 10)
2. Install dependencies with the following command.

```bash
pip install -r requirements.txt
```

3. Run main.py so it can create your config file where you need to enter your steam ID and Steam API Key.

```json
{
  "steam_data": {
    "steam_id": "Insert Steam ID",
    "steam_id_3": "Insert Steam ID3",
    "api_key": "Insert API Key",
    "steam_folder": "Insert Path to Steam Folder Here",
    "steam_library": "Insert Path to libraryfolders.vdf file (Optional) - Example: C:/Program Files (x86)/Steam/steamapps/libraryfolders.vdf"
  },
  "settings": {
    "excel_filename": "Game Library.xlsx",
    "friends_list_check_freq": 7,
    "logging": false
  },
  "last_runs": {},
  "friend_ids": []
}
```

4. (Optional) Set up any of the other optional settings within the config.
5. Run main.py again. This should run through your Steam Games and fill your newly created excel file.
6. Enjoy!

## Documentation

### Auto Updating Steam Data

Anytime you run Game Library Tracker, it will auto update data for all Steam games if they have new hours
to add or if any of columns are blank.

If many games are missing columns above a certain threshold, it will ask if you want to update them.

### Game Status Highlighting

You can label any game with a status (Listed Below) and it will auto highlight.

This uses Excel's Conditional Formatting so it can mess up sometimes if you change things manually such as
reordering columns.

- Played
- Unplayed
- Waiting
- Finished
- Endless
- Must Play
- Quit
- Ignore

### Favorite Game Sale Checker

Allows choosing your own rating threshold so that a CSV can be made containing
all the games that are currently on sale with the selected rating or higher.

### Random game picker

Picks a random game based on the Play Status you select.

### Player Count Sync

Allows syncing of player counts for all games, recent games or only 1 game.

### Update Library Add Dates

Update Dated Added dates using a json file. This is only needed due to the Steam API not providing purchase dates for games in any way I can find.

#### Json Example

```json
[
  {
    "date": "Jul 11, 2024",
    "games": ["Game 3"],
    "type": "Purchase",
    "total": 15.25
  },
  {
    "date": "Jul 10, 2024",
    "games": ["Game 1", "Game 2"],
    "type": "Purchase",
    "total": 13.06
  }
]
```

I wrote a script to pull this data from my steam purchase history page but the script is not currently released.

### Friends List Tracking

Get notified when you gain and lose friends from your steam friends list. You normally only know you
got a friend request but not whensomeone removes you or accepts your request. The check is set to look every week.

### Library Statistics

Shows many statistics and graphs for your library.

#### Examples:

- Total Hours Played

### Omit games by Name or App ID

Some games have a name that may be very common so you can use its App ID instead.

```json
{
  "app_id_ignore_list": [123456, "123456"],
  "name_ignore_list": ["Steam Deck Deposit"]
}
```
