from difflib import SequenceMatcher
import time, json, requests, re
import datetime as dt

# logging
from logging.handlers import RotatingFileHandler
import logging as lg


class Logger:

    # logger setup
    log_formatter = lg.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%m-%d-%Y %I:%M:%S %p"
    )
    logger = lg.getLogger(__name__)
    logger.setLevel(lg.DEBUG)  # Log Level
    my_handler = RotatingFileHandler(
        "configs/tracker.log", maxBytes=5 * 1024 * 1024, backupCount=2
    )
    my_handler.setFormatter(log_formatter)
    logger.addHandler(my_handler)

    def log_return(self, func):
        """
        Logs return of function when this decoratior is applied.
        """

        def wrapped(*args, **kwargs):
            value = func(*args, **kwargs)
            self.logger.info(value)
            return value

        return wrapped


class Helper(Logger):
    def request_url(self, url, headers=None):
        """
        Quick data request with check for success.
        """
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            msg = "Connection Error: Internet can't be accessed"
            self.logger.warning(msg)
            return False
        if response.status_code == requests.codes.ok:
            return response
        elif response.status_code == 500:
            msg = "Server Error: make sure your api key and steam id is valid."
            self.logger.warning(msg)
        elif response.status_code == 404:
            msg = f"Server Error: 404 Content moved or was. URL: {url}"
            self.logger.warning(msg)
        elif response.status_code == 429:
            msg = "Server Error: Too Many reqeuests made. Waiting to try again."
            self.logger.warning(msg)
            self.logger.warning(response)
            time.sleep(5)
            self.request_url(url, headers=None)
        else:
            msg = f"Unknown Error: {response.status_code}"
            self.logger.warning(msg)
        return False

    def api_sleeper(self, api, sleep_length=0.5, api_calls={}) -> None:
        """
        Delays delays for a set period of time if the `api` was run too recently.
        Delay length is set by `sleep_length`.
        """
        cur_datetime = dt.datetime.now()
        if api in api_calls.keys():
            if api_calls[api] + dt.timedelta(seconds=sleep_length) > cur_datetime:
                time.sleep(sleep_length)
        api_calls[api] = cur_datetime

    def request_retryer():
        pass

    @staticmethod
    def string_url_convert(string) -> str:
        """
        Converts given `string` into a url ready string and returns it.
        """
        return re.sub(r"\W+", "", string.replace(" ", "_")).lower()

    @staticmethod
    def hours_played(minutes_played):
        """
        Converts minutes played to a hours played in decimal form.
        """
        return round(minutes_played / 60, 1)

    @staticmethod
    def time_passed(minutes_played):
        """
        Using `minutes_played`, outputs a nicely formatted time played and an int for hours played.

        Returns time_played and hours_played
        """
        time_played = f"{round(minutes_played, 1)} Minute(s)"
        hours_played = minutes_played / 60
        if hours_played > 24:
            days = round(hours_played / 24, 1)
            time_played = f"{days} Day(s)"
        elif minutes_played > 60:
            hours = round(hours_played, 1)
            time_played = f"{hours} Hour(s)"
        return time_played

    @staticmethod
    def unicode_remover(string) -> str:
        """
        Removes unicode from `string`.
        """
        if type(string) != str:
            return string
        replace_dict = {
            "\u2122": "",  # Trademarked sign
            "\u00ae": "",  # REGISTERED SIGN
            "\u00ae": "",  # REGISTERED SIGN
            "\u00e5": "a",  # a
            "\u00f6": "o",  # LATIN SMALL LETTER O WITH DIAERESIS
            "\u00e9": "e",  # LATIN SMALL LETTER E WITH ACUTE
            "\u2013": "-",  # EN DASH
            "&amp": "&",  # &
        }
        for unicode in replace_dict.keys():
            if unicode in string:
                for unicode, sub in replace_dict.items():
                    string = string.replace(unicode, sub)
                break
        conv_string = string.encode("ascii", "ignore").decode()
        return conv_string.strip()

    def ask_for_integer(self, msg="Type a Number: ") -> int:
        """
        Asks for a integer until an integer is given.
        """
        num = input(msg)
        while not num.isdigit():
            num = input(msg)
        return int(num)

    def lev_distance(self, word1: str, word2: str, lower=True) -> int:
        """
        Returns the Levenshtein distance of `word1` and `word2`.
        """
        if lower:
            word1, word2 = word1.lower(), word2.lower()
        cache = [[float("inf")] * (len(word2) + 1) for _ in range(len(word1) + 1)]
        for j in range(len(word2) + 1):
            cache[len(word1)][j] = len(word2) - j
        for i in range(len(word1) + 1):
            cache[i][len(word2)] = len(word1) - i
        for i in range(len(word1) - 1, -1, -1):
            for j in range(len(word2) - 1, -1, -1):
                if word1[i] == word2[j]:
                    cache[i][j] = cache[i + 1][j + 1]
                else:
                    min_change = min(
                        cache[i + 1][j], cache[i][j + 1], cache[i + 1][j + 1]
                    )
                    cache[i][j] = 1 + min_change
        return cache[0][0]

    def string_matcher(self, target_str, string_list, max_similarity=0.8, debug=False):
        """
        Finds a match for target_str in string_list using sequence matching.
        """
        match = None
        for string in string_list:
            if string.lower() == target_str.lower():
                return string
            match_perc = SequenceMatcher(
                None, target_str.lower(), string.lower()
            ).ratio()
            if match_perc > max_similarity:
                max_similarity = match_perc
                match = string
        if debug:
            match_perc = round(max_similarity, 2)
            print(f"\nTarget: {target_str}\nMatch: {match}\nMatch Perc: {match_perc}")
        return match

    def string_matcher2(
        self,
        target_str: str,
        string_list: list,
        max_distance=None,
        limit: int = 5,
        debug=False,
    ):
        """
        Finds a match for target_str in string_list using sequence matching.
        """
        if max_distance == None:
            max_distance = round(len(target_str) * 0.5)
            # max_distance = float("inf")
        starting_max = max_distance
        matches = {}
        match = None
        for string in string_list:
            distance = self.lev_distance(target_str, string)
            if distance < max_distance:
                max_distance = distance
                match = string
                matches[string] = distance
        if debug:
            print(f"\nTarget: {target_str}\nMatch: {match}")
            print(f"Distance: {max_distance}\nStarting Max:{starting_max}")
        sorted_keys = sorted(matches, key=matches.get)
        if len(sorted_keys) > limit:
            sorted_keys = sorted_keys[0:limit]
        return sorted_keys

    def save_json_output(self, new_data, filename):
        """
        Saves data into json format with the given filename.
        """
        json_object = json.dumps(new_data, indent=4)
        with open(filename, "w") as outfile:
            outfile.write(json_object)
        with open(filename) as file:
            last_check_data = json.load(file)
            if new_data != last_check_data:
                raise "Data did not save error"


if __name__ == "__main__":
    pass
    App = Helper()

    # string1 = "grave Of The deaddancer: Switch Edition"
    # string2 = "Crypt Of The Necrodancer: Nintendo Switch Edition"
    # distance = App.lev_distance(string1, string2)
    # print(distance)

    test_list = [
        "This is a test, yay",
        "this is not it, arg",
        "Find the batman!",
        "Shadow Tactics: Blades of the Shogun - Aiko's Choice",
        "The Last of Us",
        "Elden Ring",
        "The Last of Us Part I",
        "The Last of Us Part II",
        "Waltz of the Wizard: Natural Magic",
        "Life is Strange™",
        "The Witcher 3: Wild Hunt",
        "Marvel's Spider-Man: Miles Morales",
        "Crypt Of The Necrodancer: Nintendo Switch Edition",
    ]

    test_list = [
        "Outer Wilds",
        "Desperados III",
        "Deep Rock Galactic",
        "Horizon Forbidden West",
        "Half-Life: Alyx",
        "The Last of Us Part II",
        "The Last of Us Remastered",
        "Uncharted 4: A Thief's End",
        "BioShock: The Collection",
        "Life Is Strange",
        "The Witcher 3: Wild Hunt",
        "DEATH STRANDING DIRECTOR'S CUT",
        "Hades",
        "The Forgotten City",
        "Demon's Souls",
        "Ratchet & Clank: Rift Apart",
        "Factorio",
        "Life is Strange™",
        "Resident Evil 2",
        "Portal 2",
        "Dishonored",
        "Subnautica",
        "Hollow Knight",
        "Marvel's Spider-Man: Miles Morales",
        "Portal",
        "BioShock",
        "Bloodborne",
        "God of War",
        "Journey",
        "Outer Wilds - Console",
        "Monster Hunter Rise",
        "SOMA",
        "BioShock Remastered",
        "ELDEN RING",
        "Teardown",
        "PowerWash Simulator",
        "Inscryption",
        "Waltz of the Wizard: Natural Magic",
        "Superliminal",
        "Apex Legends",
        "DEATHLOOP",
        "Sifu",
        "Metroid Dread",
        "Before Your Eyes",
        "HITMAN 2",
        "METAL GEAR SOLID V: THE DEFINITIVE EXPERIENCE",
        "Bioshock Infinite: The Complete Edition",
        "Detroit: Become Human",
        "Sekiro: Shadows Die Twice",
        "Titanfall 2",
        "Uncharted: The Lost Legacy",
        "SteamWorld Dig 2",
        "Gaurdians of the Galaxy",
        "Chroma Lab",
        "Control Ultimate Edition",
        "Inside",
        "Google Earth VR",
        "SUPERHOT",
        "Stardew Valley",
        "Deus Ex: Human Revolution",
        "Mass Effect 2 (2010)",
        "Counter-Strike: Global Offensive",
        "Borderlands 2",
        "Garry's Mod",
        "METAL GEAR SOLID V: THE PHANTOM PAIN",
        "HITMAN™",
        "HITMAN™ 2",
        "Infinifactory",
        "Shadow Tactics: Blades of the Shogun",
        "BioShock Infinite",
        "TowerFall Ascension",
        "Subnautica: Below Zero",
        "Wolfenstein: The New Order",
        "Shadow Warrior",
        "METAL GEAR RISING: REVENGEANCE",
        "DOOM",
        "Mark of the Ninja",
        "METAL GEAR SOLID V: GROUND ZEROES",
        "The Stanley Parable",
        "Transistor",
        "Ori and the Blind Forest",
        "Hacknet",
        "Hellblade: Senua's Sacrifice",
        "ENSLAVED™: Odyssey to the West™ Premium Edition",
        "Returnal",
        "SUPERHOT VR",
        "LIMBO",
        "Half-Life 2",
        "Hitman: Blood Money",
        "Waltz of the Wizard",
        "Hellblade: Senua's Sacrifice VR Edition",
        "A Plague Tale: Innocence",
        "Burnout Paradise: The Ultimate Box",
        "DEATH STRANDING",
        "GRAVITY RUSH 2",
        "Control",
        "Ghost of Tsushima",
        "inFAMOUS 2",
        "Horizon Zero Dawn",
        "inFAMOUS Second Son",
        "Marvel's Spider-Man",
        "Super Smash Bros. Ultimate",
        "Tom Clancy's Splinter Cell",
        "Batman: Arkham Asylum GOTY Edition",
        "Untitled Goose Game",
        "Warframe",
        "Rivals of Aether",
        "Tabletop Simulator",
        "Halo Infinite",
        "Trailmakers",
        "Shadow Tactics: Blades of the Shogun - Aiko's Choice",
        "Trover Saves the Universe",
        "Ultimate Chicken Horse",
        "Metro: Last Light Redux",
        "Mini Motorways",
        "Blade & Sorcery",
        "Dishonored 2",
        "The Jackbox Party Pack 2",
        "Pistol Whip",
        "Cyberpunk 2077",
        "Townscaper",
        "Timberborn",
        "SHADOW OF THE COLOSSUS",
        "BATMAN: ARKHAM KNIGHT",
        "Assassin's Creed Odyssey",
        "Middle-earth: Shadow of War",
        "Metro Exodus Enhanced Edition",
        "Besiege",
        "Poly Bridge 2",
        "BONEWORKS",
        "Golf With Your Friends",
        "Splitgate",
        "psychonauts 2",
        "The Jackbox Party Pack 7",
        "The Walking Dead: Saints & Sinners",
        "Viscera Cleanup Detail",
        "Chicory: A Colorful Tale",
        "Museum of Other Realities",
        "PAYDAY 2",
        "Distance",
        "EXAPUNKS",
        "Alien: Isolation",
        "Broforce",
        "Left 4 Dead 2",
        "Metro 2033 Redux",
        "Super Time Force Ultra",
        "FEZ",
        "GORN",
        "The Vanishing of Ethan Carter",
        "Chariot",
        "Tilt Brush",
        "Scanner Sombre",
        "Gone Home",
        "Rocket League",
        "Tom Clancy's Rainbow Six Siege",
        "Elite Dangerous",
        "Awesomenauts",
        "Terraria",
        "Watch_Dogs",
        "Divinity: Original Sin 2",
        "Dying Light",
        "DmC Devil May Cry",
        "The Witcher 2: Assassins of Kings Enhanced Edition",
        "Dungeon Defenders",
        "Magicka",
        "The Elder Scrolls V: Skyrim",
        "Just Cause 3",
        "DARK SOULS™ III",
        "Crysis 2",
        "Far Cry 4",
        "Batman™: Arkham Knight",
        "Tom Clancy's Splinter Cell Blacklist",
        "Sleeping Dogs™",
        "The Forest",
        "Middle-earth™: Shadow of War™",
        "Middle-earth™: Shadow of Mordor™",
        "Prey",
        "Hot Dogs, Horseshoes & Hand Grenades",
        "Saints Row IV",
        "Warhammer: Vermintide 2",
        "Tomb Raider",
        "Slime Rancher",
        "Opus Magnum",
        "The Elder Scrolls V: Skyrim VR",
        "Far Cry® 3 Blood Dragon",
        "Halo: The Master Chief Collection",
        "FTL: Faster Than Light",
        "Black Mesa",
        "Mad Max",
        "Max Payne 3",
        "Dishonored®: Death of the Outsider™ ",
        "Hyper Light Drifter",
        "Super Meat Boy",
        "Wolfenstein II: The New Colossus",
        "Heat Signature",
        "Gunpoint",
        "The Lab",
        "Thumper",
        "Human: Fall Flat",
        "Space Pirate Trainer",
        "Guacamelee! Gold Edition",
        "Hotline Miami",
        "Windlands",
        "Bayonetta",
        "Bridge Constructor Portal",
        "Dustforce",
        "Job Simulator",
        "Outlast",
        "Into the Breach",
        "Audioshield",
        "Little Inferno",
        "Wreckfest",
        "Return of the Obra Dinn",
        "Mirror's Edge",
        "Wolfenstein: The Old Blood ",
        "Grow Home",
        "theBlu",
        "Manifold Garden",
        "Beat Saber",
        "SpaceChem",
        "Alan Wake",
        "Lightmatter",
        "Jet Island",
        "Clustertruck",
        "Brothers - A Tale of Two Sons",
        "Panoptic",
        "SteamWorld Dig",
        "FAR: Lone Sails",
        "We Were Here Too",
        "Pony Island",
        "What Remains of Edith Finch",
        "Psychonauts",
        "Accounting+",
        "Accounting",
        "Size Matters",
        "DAYS GONE",
        "Devil May Cry 4 Special Edition",
        "Devil May Cry 5",
        "Far Cry 5",
        "The Unfinished Swan",
        "Pikmin 3 Deluxe",
        "Tony Hawk's Pro Skater 1 + 2",
        "Watch Dogs: Legion",
        "Little Nightmares",
        "HITMAN 3",
        "Concrete Genie",
        "Ratchet & Clank",
        "Guacamelee! Super Turbo Championship Edition",
        "Batman: Arkham City GOTY",
        "Fall Guys: Ultimate Knockout",
        "Dead Cell",
        "Spiritfarer",
        "Exo One",
        "Poly Bridge",
        "SpeedRunners",
        "Barotrauma",
        "DOOM Eternal",
        "HEAVY RAIN",
        "Monster Hunter World: Iceborne",
        "Assassin's Creed Origins",
        "Assassin's Creed Valhalla",
        "inFAMOUS First Light",
        "Solar Ash",
        "Webbed",
        "PUBG: BATTLEGROUNDS",
        "THE CORRIDOR",
        "ASTRONEER",
        "Operation Tango",
        "Mortal Kombat X",
        "Agents of Mayhem",
        "Sairento VR",
        "Evil Genius 2",
        "Darksiders II",
        "Dust: An Elysian Tail",
        "MOLEK-SYNTEZ",
        "Oxygen Not Included",
        "Arizona Sunshine",
        "Octodad: Dadliest Catch",
        "ABZÛ",
        "FORM",
        "Intake",
        "The Floor is Jelly",
        "Chivalry: Medieval Warfare",
        "Starbound",
        "RimWorld",
        "The Witness",
        "XCOM: Enemy Unknown",
        "Assassin's Creed IV Black Flag",
        "Onward",
        "Don't Starve",
        "No Man's Sky",
        "Raw Data",
        "Deus Ex: Mankind Divided™",
        "Rise of the Tomb Raider",
        "Cities: Skylines",
        "Surgeon Simulator",
        "Sniper Elite 3",
        "MORDHAU",
        "Spelunky",
        "Life is Strange: Before the Storm",
        "Bastion",
        "Magicka 2",
        "We Were Here Together",
        "Autonauts",
        "Aragami",
        "Monster Hunter: World",
        "Slay the Spire",
        "Spec Ops: The Line",
        "Among Us",
        "My Friend Pedro",
        "Void Bastards",
        "Ghostrunner",
        "Thomas Was Alone",
        "SUPERHOT: MIND CONTROL DELETE",
        "Grow Up",
        "Tacoma",
        "Budget Cuts",
        "Megaton Rainfall",
        "Tick Tock: A Tale for Two",
        "A Story About My Uncle",
        "I Expect You To Die",
        "Donut County",
        "We Were Here",
        "Bomb Squad Academy",
        "Sniper Elite V2",
        "Moonlighter",
        "Far Cry 3",
        "Grand Theft Auto V - Console",
        "Gravity Rush Remastered",
        "Immortals Fenyx Rising",
        "ASSASSIN'S CREED IV: BLACK FLAG",
        "Persona 5",
        "Vampyr",
        "The Darkness II",
        "Animal Crossing™: New Horizons",
        "ASTRAL CHAIN",
        "Nidhogg 2",
        "Main Assembly",
        "Moss",
        "Battlefield 1",
        "Battlefield V",
        "Maquette",
        "Valley",
        "Fallout 4",
        "Styx: Master of Shadows",
        "Torchlight II",
        "Saints Row: Gat out of Hell",
        "Shadow Warrior 2",
        "DEADBOLT",
        "Antichamber",
        "Breathedge",
        "Just Cause 4",
        "Shadow of the Tomb Raider",
        "Absolver",
        "The Pathless",
        "Robonauts",
        "Crypt Of The Necrodancer: Nintendo Switch Edition",
        "Red Dead Redemption 2",
        "Bugsnax",
        "The Last Guardian",
        "Grand Theft Auto V",
        "Lichdom: Battlemage",
        "Space Pirates and Zombies",
        "Borderlands: The Pre-Sequel",
        "Sir, You Are Being Hunted",
        "Borderlands 3",
        "Battlerite",
        "Hitman: Absolution",
        "Remnant: From the Ashes",
        "Kingdoms of Amalur: Reckoning™",
        "Unrailed!",
        "Domina",
        "Team Sonic Racing",
        "FAR: Changing Tides",
        "Patrick's Parabox",
        "Knightfall: A Daring Journey",
        "Amnesia: Rebirth",
        "Satisfactory",
        "VTOL VR",
        "Cyber Hook",
        "Paper Beast",
        "The Jackbox Party Pack 5",
        "Crunch Element",
        "Instruments of Destruction",
        "WorldBox - God Simulator",
        "Stick Fight: The Game",
        "Microsoft Flight Simulator",
        "Door Kickers 2",
        "Wingspan",
        "SimpleRockets 2",
        "Kerbal Space Program",
        "BPM: BULLETS PER MINUTE",
        "Super Animal Royale",
        "The Sexy Brutale",
        "There Is No Game: Wrong Dimension",
        "Until You Fall",
        "Tiny Tina's Assault on Dragon Keep: A Wonderlands One-shot Adventure",
        "EA SPORTS UFC 4",
        "Duskers",
        "Not For Broadcast",
        "",
        "DIRT5",
        "DIRT 5",
        "Persona 5 Strikers",
        "Paper Beast - Folded Edition",
        "The Jackbox Party Pack 4",
        "Disc Jam",
        "FINAL FANTASY VII REMAKE",
        "FINAL FANTASY XV",
        "Hunter's Arena: Legends",
        "MAIDEN",
        "Mortal Shell: Enhanced Edition",
        "Paragon",
        "STEEP",
        "WIPEOUT OMEGA COLLECTION",
        "YAKUZA 0",
        "YAKUZA KIWAMI",
        "KILLZONE SHADOW FALL",
        "Assassin's Creed Freedom Cry",
        "Amplitude",
        "Art of Balance",
        "Plants vs. Zombies: Battle for Neighborville",
        "ASTRO BOT Rescue Mission",
        "ABZU",
        "Beyond: Two Souls",
        "Godfall: Challenger Edition",
        "Borderlands: The Handsome Collection",
        "Call of Duty: Black Ops 4",
        "Call of Duty: Modern Warfare Remastered",
        "ENDER LILIES : Quietus of the Knights",
        "Cuphead",
        "Darksiders III",
        "Dauntless",
        "DEAD OR ALIVE 5 Last Round",
        "Destruction AllStars",
        "Dreams",
        "Crash Bandicoot N. Sane Trilogy",
        "Enter the Gungeon",
        "Farpoint",
        "flOw",
        "Flower",
        "Game of Thrones",
        "Genshin Impact",
        "God of War III Remastered",
        "GreedFall",
        "GWENT: The Witcher Card Game",
        "Injustice 2",
        "KID A MNESIA EXHIBITION",
        "Killing Floor 2",
        "Laser Disco Defenders",
        "LEGO DC Super-Villains",
        "Life is Strange 2",
        "Lumo",
        "Mafia: Definitive Edition",
        "NOT A HERO",
        "Oddworld: Soulstorm",
        "Outlast 2",
        "Overcooked",
        "Overcooked! All You Can Eat",
        "Predator: Hunting Grounds",
        "RESIDENT EVIL 7 biohazard",
        "Rez Infinite",
        "Rogue Aces",
        "SnowRunner",
        "Sonic Mania",
        "STAR WARS: Squadrons",
        "Stranded Deep",
        "Strike Vector EX",
        "Tales from the Borderlands",
        "Tearaway Unfolded",
        "Tennis World Tour 2",
        "That's You!",
        "The Binding of Isaac: Rebirth",
        "The Matrix Awakens: An Unreal Engine 5 Experience",
        "The Sims 4",
        "TorqueL",
        "Type:Rider",
        "Uncharted: The Nathan Drake Collection",
        "Unravel",
        "Until Dawn",
        "Virtua Fighter 5 Ultimate Showdown",
        "Zombie Army 4: Dead War",
        "Timelie",
        "Call of Juarez Gunslinger",
        "Universe Sandbox",
        "Budget Cuts 2: Mission Insolvency",
        "The Curious Tale of the Stolen Pets",
        "VVVVVV",
        "Space Haven",
        "Lethal League Blaze",
        "Hell Let Loose",
        "First Class Trouble",
        "Knockout City",
        "Kena: Bridge of Spirits",
        "Life is Strange: True Colors",
        "Kingdoms of Amalur: Re-Reckoning",
        "The Persistence",
        "Project Wingman",
        "Möbius Front '83",
        "House Flipper",
        "WRATH: Aeon of Ruin",
        "Turnip Boy Commits Tax Evasion",
        "Pavlov VR",
        "Night in the Woods",
        "STAB STAB STAB!",
        "People Playground",
        "Firewatch",
        "Doki Doki Literature Club Plus",
        "Titan Souls",
        "Frozen Synapse",
        "Scrap Mechanic",
        "Monaco",
        "The Talos Principle",
        "Worms Revolution",
        "The Showdown Effect",
        "BattleBlock Theater",
        "Lethal League",
        "Resident Evil 7 Biohazard",
        "Amnesia: The Dark Descent",
        "RUINER",
        "Need for Speed: Hot Pursuit",
        "Papo & Yo",
        "N++",
        "Screencheat",
        "Deponia",
        "The Room VR: A Dark Matter",
        "Fugl",
        "The Invisible Hours",
        "Blasters of the Universe",
        "Northgard",
        "Totally Accurate Battlegrounds",
        "Epistory - Typing Chronicles",
        "No Time To Explain Remastered",
        "BIT.TRIP Presents... Runner2: Future Legend of Rhythm Alien",
        "Serious Sam VR: The First Encounter",
        "Just In Time Incorporated",
        "AirMech® Command",
        "Escape Bloody Mary",
        "Thirty Flights of Loving",
        "Moving Out",
        "Cave Story+",
        "The King's Bird",
        "GRIP: Combat Racing",
        "When Ski Lifts Go Wrong ",
        "Realities",
        "Dynamite Jack",
        "Guts and Glory",
        "Lone Survivor: The Director's Cut",
        "Found",
        "Surgeon Simulator VR: Meet The Medic",
        "Western Press",
        "Devil Daggers",
        "Viscera Cleanup Detail: Santa's Rampage",
        "Sommad",
        "Google Spotlight Stories: Back to the Moon",
        "Google Spotlight Stories: Sonaria",
        "Valheim",
        "Darksiders",
        "Mortal Kombat Komplete Edition",
        "Disco Elysium",
        "Call of Duty: Advanced Warfare - Multiplayer",
        "Orcs Must Die!",
        "Tropico 4",
        "Gang Beasts",
        "The Walking Dead",
        "Surviving Mars",
        "SportsBar VR ",
        "Orcs Must Die! 2",
        "Vessel",
        "Race The Sun",
        "Redout: Enhanced Edition",
        "Overlord",
        "Insanely Twisted Shadow Planet",
        "Dirty Bomb",
        "Due Process",
        "Hardspace: Shipbreaker",
        "PixelJunk™ Shooter",
        "They Bleed Pixels",
        "Mushroom 11",
        "Rochard",
        "Beat Hazard",
        "In Verbis Virtus",
        "Dungeons 3",
        "The Chronicles of Riddick: Assault on Dark Athena",
        "Super Splatters",
        "Lucid Trips",
        "Door Kickers",
        "Stealth Bastard Deluxe",
        "Blocks That Matter",
        "Invisible, Inc.",
        "Racket: Nx",
        "Prison Architect",
        "Observer",
        "Offspring Fling!",
        "Teslagrad",
        "The Binding of Isaac",
        "Dragon Age: Origins - Ultimate Edition",
        "The Swapper",
        "Trine 2",
        "Rec Room",
        "Plague Inc: Evolved",
        "Creeper World 3: Arc Eternal",
        "The Jackbox Party Pack 6",
        "Tales from Space: Mutant Blobs Attack",
        "Natural Selection 2",
        "Hammerwatch",
        "Gunheart",
        "The Wizards - Dark Times",
        "Overload",
        "Dungeons 2",
        "Q.U.B.E: Director's Cut",
        "Jazzpunk: Director's Cut",
        "The Gallery - Episode 2: Heart of the Emberstone",
        "Phasmophobia",
        "Space Engineers",
        "Ziggurat",
        "Totally Accurate Battle Simulator",
        "Viscera Cleanup Detail: Shadow Warrior",
        "Cosmic Trip",
        "Gratuitous Space Battles",
        "Turbo Dismount",
        "Fruit Ninja VR",
        "shapez.io",
        "Receiver",
        "Project CARS 2",
        "Braid",
        "SHENZHEN I/O",
        "Tiny and Big: Grandpa's Leftovers",
        "The Witcher: Enhanced Edition",
        "Nidhogg",
        "ECHO",
        "Furi",
        "BeamNG.drive",
        "Tower of Guns",
        "Overcooked! 2",
        "Everybody's Gone to the Rapture",
        "Quantum Break",
        "Unmechanical",
        "Unfortunate Spacemen",
        "Windlands 2",
        "Kingdom: New Lands",
        "Contraption Maker",
        "Home Improvisation: Furniture Sandbox",
        "Goat Simulator",
        "Noita",
        "Papers, Please",
        "Wildfire",
        "PixelJunk™ Shooter Ultimate",
        "Gadgeteer",
        "Giana Sisters: Twisted Dreams",
        "DiRT Rally",
        "Mutant Year Zero: Road to Eden",
        "We Need To Go Deeper",
        "Blade Symphony",
        "Paddle Up",
        "Climbey",
        "ISLANDERS",
        "Hand of Fate",
        "The Gallery - Episode 1: Call of the Starseed",
        "Blacklight: Tango Down",
        "Call of Duty: Advanced Warfare",
        "Risk of Rain",
        "Boid",
        "Gish",
        "TO THE TOP",
        "The Jackbox Party Pack 3",
        "Town of Salem",
        "Lightblade VR",
        "Company of Heroes: Opposing Fronts",
        "Legend of Grimrock",
        "Proteus",
        "Slap City",
        "Overgrowth",
        "Don't Starve Together",
        "Portal Stories: Mel",
        "Yakuza 0",
        "Shatter",
        "Metro 2033",
        "Dear Esther",
        "Anomaly 2",
        "Counter-Strike: Source",
        "Richie's Plank Experience",
        "RUSH",
        "Audiosurf",
        "Super Hexagon",
        "Flywrench",
        "Organ Trail: Director's Cut",
        "Virtual Virtual Reality",
        "Iron Harvest",
        "MO:Astray",
        "Kittypocalypse",
        "Robot Roller-Derby Disco Dodgeball",
        "Verlet Swing",
        "NITE Team 4",
        "Dr. Langeskov, The Tiger, and The Terribly Cursed Emerald: A Whirlwind Heist",
        "Red Faction: Guerrilla Steam Edition",
        "Yooka-Laylee",
        "Strike Suit Zero",
        "NVIDIA® VR Funhouse",
        "BLARP!",
        "Irrational Exuberance: Prologue",
        "STARWHAL",
        "Skullgirls 2nd Encore",
        "Kill The Bad Guy",
        "FLY'N",
        "PixelJunk Eden",
        "TIS-100",
        "Fantastic Contraption",
        "Headlander",
        "Toki Tori",
        "Q.U.B.E. 2",
        "Spell Fighter VR",
        "Darwin Project",
        "AirMech Strike",
        "Superflight",
        "AER Memories of Old",
        "The Vanishing of Ethan Carter Redux",
        "In Other Waters",
        "Serial Cleaner",
        "Hot Lava",
        "Dragon's Dogma: Dark Arisen",
        "Deceit",
        "ROCKETSROCKETSROCKETS",
        "Devolverland Expo",
        "Everything",
        "The Wizards",
        "Eliza",
        "Forager",
        "Planet Coaster",
        "GOAT OF DUTY",
        "Divide by Sheep",
        "BioShock 2",
        "Surge",
        "STANDBY",
        "Joe Danger 2: The Movie",
        "DOOM VFR",
        "XCOM 2",
        "CONSORTIUM",
        "Everest VR",
        "HoloBall",
        "Hidden Folks",
        "OlliOlli",
        "Rock of Ages 2",
        "Undertale",
        "DiRT Rally 2.0",
        "Blasphemous",
        "The Talos Principle VR",
        "Intrusion 2",
        "Dimensional Intersection",
        "MOTHERGUNSHIP",
        "Google Spotlight Stories: Age of Sail",
        "Portal Stories: VR",
        "Genital Jousting",
        "Super Cloudbuilt ",
        "Wizorb",
        "Lovers in a Dangerous Spacetime",
        "HOMEBOUND",
        "Serious Sam VR: The Second Encounter",
        "Welcome to Light Fields",
        "Not For Broadcast: Prologue",
        "NightSky",
        "Capsized",
        "Stories: The Path of Destinies",
        "Closure",
        "Portal 2 - The Final Hours",
        "TOXIKK",
        "Allumette",
        "Override",
        "Serious Sam VR: The Last Hope",
        "Emily Wants To Play",
        "Remnants of Naezith",
        "Dead Space",
        "Brawlhalla",
        "The Body VR: Journey Inside a Cell",
        "Swords and Soldiers HD",
        "The Cubicle.",
        "Company of Heroes - Legacy Edition",
        "Quanero",
        "Music Inside: A VR Rhythm Game",
        "Cockroach VR",
        "140",
        "Road to Ballhalla",
        "Swords and Soldiers 2 Shawarmageddon",
        "Quake Live",
        "Gorilla Tag",
        "FORCED",
        "Unbreakable Vr Runner",
        "My Lil' Donut",
        "ABE VR",
        "Wake Up",
        "GNOG",
        "Teleglitch: Die More Edition",
        "Mr Shifty",
        "Beat Hazard 2",
        "HALP!",
        "Half-Life 2: Deathmatch",
        "The IOTA Project",
        "The Flame in the Flood",
        "English Country Tune",
        "The Long Dark",
        "Jaunt VR - Experience Cinematic Virtual Reality",
        "Ripple Effect",
        "Blueshift",
        "Gloomy Eyes",
        "AaaaaAAaaaAAAaaAAAAaAAAAA!!! for the Awesome",
        "Google Spotlight Stories: Pearl",
        "INVASION!",
        "Vrideo",
        "Thread Studio",
        "Alpha Mike Foxtrot",
        "Starman's VR Experience",
        "Blocks",
        "RETNE",
        "Major League Gladiators",
        "Colosse",
        "Sketchfab VR",
        "Piñata",
        "DreamLand",
        "Limberjack",
        "The VR Museum of Fine Art",
        "Snowday",
        "ShotForge",
        "The Bellows",
        "Stardust Vanguards",
        "Google Spotlight Stories: Rain or Shine",
        "Google Spotlight Stories: Special Delivery",
        "Minit",
        "The Awesome Adventures of Captain Spirit",
        "Aim Lab",
        "Serious Sam 3 VR: BFE",
        "Party Hard",
        "Nuclear Throne",
        "Cultist Simulator",
        "Thief Gold",
        "The Night Cafe",
        "Orwell",
        "World of Goo",
        "Torchlight",
        "Tell Me Why",
        "Relicta",
        "Retimed",
        "Cook, Serve, Delicious! 3?!",
        "Darksiders Genesis",
        "Family Man",
        "SIMULACRA 2",
        "Sniper Ghost Warrior Contracts",
        "Rock of Ages 3: Make & Break",
        "SIMULACRA",
        "Popup Dungeon",
        "Colt Canyon",
        "Ageless",
        "Kingdom Two Crowns",
        "XCOM: Chimera Squad",
        "Mortal Kombat 11",
        "Tom Clancy's Splinter Cell Blacklist - Uplay",
        "Boomerang Fu",
        "Trine 4: The Nightmare Prince",
        "Valfaris",
        "Maneater",
        "Guacamelee! 2",
        "Vampyr - Console",
        "Bomber Crew",
        "Pyre",
        "Mortal Shell",
        "Downwell",
        "Hyrule Warriors: Age Of Calamity",
        "Helltaker",
        "Defunct",
        "Astro Bears",
        "Bloodroots",
        "Super Chariot",
        "Disc Room",
        "Jet Lancer",
        "WHAT THE GOLF?",
        "Wilmot's Warehouse",
        "Owlboy",
        "Drawful 2",
        "Metal Unit",
        "Transpose",
        "Horizon Chase Turbo",
        "NieR:Automata",
        "Nioh",
        "Spyro™ Reignited Trilogy",
        "Fun with Ragdolls: The Game",
        "Pathfinder: Kingmaker",
        "Two Point Hospital",
        "Phantom Doctrine",
        "Age of Wonders III",
        "Evoland Legendary Edition",
        "Company of Heroes 2",
        "Catherine Classic",
        "The Messenger",
        "Almost There: The Platformer",
        "Skullgirls Encore",
        "Rayman Origins",
        "Heave Ho",
        "The Shapeshifting Detective",
        "Okami HD",
        "Snake Pass - Console",
        "Spyro 3: Year of the Dragon",
        "Kingdom Come: Deliverance",
        "Supraland",
        "Glitchspace",
        "Spyro the Dragon",
        "Spyro 2: Ripto's Rage!",
        "Super Motherload",
        "Headsnatchers",
        "Generation Zero®",
        "Sundered: Eldritch Edition",
        "Bad North",
        "Jotun: Valhalla Edition",
        "Bridge Constructor",
        "Sigma Theory",
        "Bound",
        "The Surge",
        "Trackmania Turbo",
        "Assassins Creed 3",
        "Transference",
        "Watch_dogs 2",
        "Just Cause™ 3: Multiplayer Mod",
        "The Red Stare",
        "Graveyard Keeper",
        "Paradigm",
        "Do Not Feed the Monkeys",
        "Bendy and the Ink Machine",
        "Sniper Elite 4",
        "Trials Fusion",
        "Tom Clancy's The Division",
        "Steep",
        "The Crew",
        "Please State Your Name : A VR Animated Film",
        "Spacewing VR",
        "Warstone TD",
        "Snake Pass",
        "L.A. Noire",
        "Late Shift",
        "Manual Samuel - Anniversary Edition",
        "Far Beyond: A space odysseyVR",
        "Lethal League Blaze - Console",
        "Unexplored",
        "Mages of Mystralia",
        "The Hex",
        "Jonah's Path",
        "QuiVr Vanguard",
        "Seven: Enhanced Edition",
        "SEGA Mega Drive & Genesis Classics",
        "Hell Yeah!",
        "Jet Set Radio",
        "Song of the Deep",
        "The Final Station",
        "10 Second Ninja X",
        "Life Is Strange™ - Directors' Commentary - 1.Two directors",
        "Life Is Strange™ - Directors' Commentary - 2. Let's play Life is Strange",
        "Life Is Strange™ - Directors' Commentary - 3. Intentions",
        "Life Is Strange™ - Directors' Commentary - 4. A matter of choice",
        "Life Is Strange™ - Directors' Commentary - 5. A lively world",
        "Life Is Strange™ - Directors' Commentary - 6. Capturing the moment",
        "Life Is Strange™ - Directors' Commentary - 7. Social issues",
        "Life Is Strange™ - Directors' Commentary - 8. Getting things right",
        "Life Is Strange™ - Directors' Commentary - 9. Voices of Arcadia Bay",
        "That Dragon, Cancer",
        "Batman™: Arkham Origins Blackgate - Deluxe Edition",
        "Batman™: Arkham Origins",
        "X-Morph: Defense",
        "Full Metal Furies",
        "The Adventure Pals",
        "Oxenfree",
        "Layers of Fear",
        "Grand Theft Auto: San Andreas",
        "Aegis Defenders",
        "Volume",
        "Rituals",
        "DARK SOULS™ II: Scholar of the First Sin",
        "Double Action: Boogaloo",
        "Frostpunk",
        "Stealth Inc 2",
        "Outland",
        "Yoku's Island Express",
        "Basingstoke",
        "The Magic Circle",
        "Ninja Pizza Girl",
        "TIMEframe",
        "Magicite",
        "Road Redemption",
        "Mini Metro",
        "Explodemon",
        "Q.U.B.E.",
        "The Beginner's Guide",
        "Satellite Reign",
        "Breach & Clear",
        "Goodbye Deponia",
        "KAMI",
        "StarMade",
        "Legend of Grimrock 2",
        "Mercenary Kings",
        "Aquaria",
        "Edge of Space",
        "Draw a Stickman: EPIC",
        "Sanctum 2",
        "Shadowrun Returns",
        "Company of Heroes ",
        "Chaos on Deponia",
        "Cry of Fear",
        "Company of Heroes: Tales of Valor",
        "To the Moon",
        "Rocketbirds: Hardboiled Chicken",
        "EDGE",
        "Zen Bound® 2",
        "Avadon: The Black Fortress",
        "The Bard's Tale",
        "BioShock 2 Remastered",
        "Osmos",
        "Fractal: Make Blooms Not War",
        "Cogs",
        "Dear Esther: Landmark Edition",
        "Evil Genius",
        "Red Faction Guerrilla Re-Mars-tered",
        "Half-Life 2: Episode Two",
        "Half-Life 2: Episode One",
        "Half-Life: Source",
    ]
    match = App.string_matcher2("The Last of Us Part", test_list)
    print(match)
