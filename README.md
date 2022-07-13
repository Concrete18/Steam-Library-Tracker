# Game Library Tracker

Steam and Playstation Library Tracker allows keeping up with what you have played and want to play ect... Many different types of information are auto retrieved using API's and Scraping.

    Adding playstation games is a side feature and is not as feature rich as
    Steam games due to lack of an API compared to Steam.

## Images

WIP

## Technology Used

- Python Pandas
- Matplotlib
- API Requests with Requests
- Web Scraping with Requests and BeautifulSoup
- Custom Created module based on OpenPyXL

## Features

- Auto Updating Steam Data
- Playstation Library Ownership Tracking (No hours tracked like Steam)
- Steam Deck Game Status Checker
- Favorite Game Sale Checker
- Random game picker
- Library Statistics using Pandas and Matplotlib

### Game Status Choices

- Playing
- Played
- Finished
- Unplayed
- Must Play
- Waiting
- Quit
- Ignore

## Setup

1. Install dependencies with the following command.

   ```bash
   pip install -r requirements.txt
   ```

2. Run program so it can create your config file where you need to enter your steam ID and Steam API Key.

3. (Optional) Set up any of the other optional settings within the config.

4. Run Program again. This should run through your Steam Games and fill your newly created excel file.

5. Enjoy!

## Todo

- [ ] Allow Some Features to be toggled.

## Documentation

### Adding Playstation Games

WIP
