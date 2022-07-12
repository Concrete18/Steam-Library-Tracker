# Game Library Tracker

Steam and Playstation Library Tracker allows keeping up with what you have played and want to play ect... Many different types of information are auto retrieved using API's and Scraping.

```text
Note:
Adding playstation games is a side feature and is not as feature rich as
Steam games due to lack of an API compared to Steam.
```

## Images

WIP

## Features

* Auto Updating Steam Data
* Playstation Library Ownership Tracking (No hours tracked like Steam)
* Steam Deck Game Status Checker
* Favorite Game Sale Checker
* Random game picker
* Library Statistics using Pandas and Matplotlib

### Game Status Choices

* Playing
* Played
* Finished
* Unplayed
* Must Play
* Waiting
* Quit
* Ignore

## Setup

Install dependencies with the following command.

```bash
pip install -r requirements.txt
```

Once the program runs it should create your config file where you need to enter your steam ID and Steam API Key. Once this is done feel free to set up any of the other optional settings and then run again. This should run through your Steam Games and fill your newly created excel file.

## Todo

WIP
