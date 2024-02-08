from pathlib import Path
import shutil, json, re


class Setup:

    @staticmethod
    def create_file(file, temp_path):
        """
        Creates the `file` by copying the template from `temp_path` if it does not exist.
        """
        if not file.exists():
            config_template = Path(f"templates/{temp_path}")
            shutil.copyfile(config_template, file)
            return True
        return False

    def validate_steam_id(self, steam_id):
        """
        Validates a `steam_id`.
        """
        steam_id = str(steam_id)
        pattern = r"^\d{17}$"
        if re.match(pattern, steam_id):
            return True
        else:
            return False

    def validate_steam_key(self, steam_key: str):
        """
        Validates a `steam_key`.
        """
        pattern = r"^\w{32}$"
        if re.match(pattern, steam_key):
            return True
        else:
            return False

    def validate_config(self, config_data):
        """
        Checks to see if the config data is usable.
        """
        steam_id = config_data["steam_data"]["steam_id"]
        api_key = config_data["steam_data"]["api_key"]
        errors = []
        if not self.validate_steam_id(steam_id):
            errors.append("Steam ID is Invalid")
        if not self.validate_steam_key(api_key):
            errors.append("Steam API Key is Invalid")
        return errors

    def setup(self):
        """
        Creates all missing config files if they do not exist.
        """
        all_clear = True
        # config file
        config_path = Path("configs/config.json")
        if self.create_file(config_path, "config_template.json"):
            all_clear = False
        # gets excel file name
        excel_filename = "Game Library.xlsx"
        with open(config_path) as file:
            config_data = json.load(file)
            excel_filename = config_data["settings"]["excel_filename"]
        # excel check
        excel_path = Path(excel_filename)
        if self.create_file(excel_path, "Game_Library_Template.xlsx"):
            all_clear = False
        # ignore file
        ignore_path = Path("configs/ignore.json")
        if self.create_file(ignore_path, "ignore_template.json"):
            all_clear = False
        # exits out of function early if all clear
        if all_clear:
            errors = self.validate_config(config_data)
            with open(ignore_path) as file:
                ignore_data = json.load(file)
            if not errors:
                return config_path, config_data, ignore_data
            else:
                print(errors)
                exit()
        # instructions
        # TODO only show instructions depending on what was missing
        print("Open the config and update the following entries:")
        print("steam_id\nsteam_api_key")
        input("\nPress Enter to Close")
        exit()
