# Game Library Tracker

Steam and PlayStation Library Tracker allows keeping up with what you have played and want to play etc.. Many different types of information is auto retrieved using API's and Scraping.

Adding PlayStation games is a side feature and is not as feature rich as
Steam games due to lack of an API compared to Steam.

## Images

![Console Preview](https://raw.githubusercontent.com/Concrete18/Game-Library-Tracker/main/images/Console.png)

![Excel Preview](https://raw.githubusercontent.com/Concrete18/Game-Library-Tracker/main/images/excel.png)

## Technology Used

- Python Pandas
- Matplotlib
- API Requests with Requests
- Web Scraping with Requests and BeautifulSoup
- Custom Created Class based on OpenPyXL called [EasierExcel](https://github.com/Concrete18/easierexcel)

## Features

- [Auto Updating Steam Data](#Auto-Updating-Steam-Data)
- [Game Status Highlighting](#Game-Status-Highlighting)
- [PlayStation Library Ownership Tracking](#Adding-PlayStation-Games)
- [Steam Deck Game Status Checker](#Steam-Deck-Game-Status-Checker)
- [Favorite Game Sale Checker](#Favorite-Game-Sale-Checker)
- [Random game picker](#Random-game-picker)
- [Library Statistics](#Library-Statistics)

## Setup

1. Install dependencies with the following command.

   ```bash
   pip install -r requirements.txt
   ```

2. Run main.py so it can create your config file where you need to enter your steam ID and Steam API Key.
3. (Optional) Set up any of the other optional settings within the config.
4. Run main.py again. This should run through your Steam Games and fill your newly created excel file.
5. Enjoy!

## To Do

- [] Allow Some Features to be toggled.

## Documentation

### Auto Updating Steam Data

Anytime you run Game Library Tracker, it will auto update data for all Steam games if they have new hours to add or if any of columns are blank.

If many games are missing columns above a certain threshold, it will ask if you want to update them.

### Game Status Highlighting

You can label any game with a status (Listed Below) and it will auto highlight.

This uses Excel's Conditional Formatting so it can mess up sometimes if you change things manually such as reordering columns.

- Playing
- Played
- Finished
- Unplayed
- Must Play
- Waiting
- Quit
- Ignore

### Adding PlayStation Games

In order to add PlayStation Games, you need to copy a JSON response from your browser into a text file.
Your PlayStation account must be logged in for this to get your data.
This is the easiest method I have found so far.
It is faster than adding the games manually but I am unable to automate it yet.

    Note:
    Hours are not tracked like Steam due to a lack of an API.

### Steam Deck Game Status Checker

Checks for Steam Deck Status updates. If any are found it will update the column.

### Favorite Game Sale Checker

Allows choosing your own rating threshold so that a CSV can be made containing
all the games that are currently on sale with the selected rating or higher.

### Random game picker

Picks a random game based on the Play Status you select.

### Library Statistics

Shows many statistics and graphs for your library.

#### Examples:

- Total Hours Played
