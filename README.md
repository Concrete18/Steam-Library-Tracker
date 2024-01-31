# Game Library Tracker

Steam and PlayStation Library Tracker allows keeping up with what you have played and want to play etc..
Many different types of information is auto retrieved using API's and Scraping.

Adding PlayStation games is a side feature and is not as feature rich as Steam games due to lack of a Playstation API.

## Images

![Console Preview](https://raw.githubusercontent.com/Concrete18/Game-Library-Tracker/main/images/Console.png)

![Excel Preview](https://raw.githubusercontent.com/Concrete18/Game-Library-Tracker/main/images/excel.png)

## Technology Used

- Python Pandas
- Rich Console
- Matplotlib
- API Requests
- Web Scraping with Requests and BeautifulSoup
- [EasierExcel](https://github.com/Concrete18/easierexcel) (my custom library based on OpenPyXL)

## Features

- [Auto Updating Steam Data](#Auto-Updating-Steam-Data)
- [Game Status Highlighting](#Game-Status-Highlighting)
- [PlayStation Library Ownership Tracking](#Adding-PlayStation-Games)
- [Favorite Game Sale Checker](#Favorite-Game-Sale-Checker)
- [Random game picker](#Random-game-picker)
- [Player Count Sync](#Player-Count-Sync)
- [Friends List Tracking](#Friends-List-Tracking)
- [Library Statistics](#Library-Statistics)

## Setup

1. Install Python (It is currently tested with Python 11.1 and Python 10)
2. Install dependencies with the following command.

   ```bash
   pip install -r requirements.txt
   ```

3. Run main.py so it can create your config file where you need to enter your steam ID and Steam API Key.
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

### Adding PlayStation Games

In order to add PlayStation Games, you need to copy a JSON response from your browser into a text file.
Your PlayStation account must be logged in for this to get your data.
This is the easiest method I have found so far.
It is faster than adding the games manually but I am unable to automate it yet.

Note: Hours are not tracked like Steam due to a lack of an API.

### Favorite Game Sale Checker

Allows choosing your own rating threshold so that a CSV can be made containing
all the games that are currently on sale with the selected rating or higher.

### Random game picker

Picks a random game based on the Play Status you select.

### Player Count Sync

Allows syncing of player counts for all games, recent games or only 1 game.

### Friends List Tracking

Get notified when you gain and lose friends from your steam friends list. You normally only know you
got a friend request but not whensomeone removes you or accepts your request. The check is set to look every week.

### Library Statistics

Shows many statistics and graphs for your library.

#### Examples:

- Total Hours Played
