from typing import Tuple
from pathlib import Path
import shutil, json, re


class Setup:

    def validate_steam_id(self, steam_id: int) -> bool:
        """
        Validates a `steam_id`.
        """
        steam_id = str(steam_id)
        pattern = r"^\d{17}$"
        if re.match(pattern, steam_id):
            return True
        else:
            return False

    def validate_steam_key(self, steam_key: str) -> bool:
        """
        Validates a `steam_key`.
        """
        pattern = r"^\w{32}$"
        if re.match(pattern, steam_key):
            return True
        else:
            return False

    def validate_config(self, config_data) -> list:
        """
        Checks to see if the config data is usable.
        """
        errors = []

        steam_id = config_data["steam_data"]["steam_id"]
        if not self.validate_steam_id(steam_id):
            errors.append("Steam ID is Invalid")

        api_key = config_data["steam_data"]["api_key"]
        if not self.validate_steam_key(api_key):
            errors.append("Steam API Key is Invalid")

        return errors

    @staticmethod
    def create_file(file, temp_path) -> bool:
        """
        Creates the `file` by copying the template from `temp_path` if it does not exist.
        """
        if not file.exists():
            config_template = Path(f"configs/templates/{temp_path}")
            shutil.copyfile(config_template, file)
            return True
        return False

    def run(self) -> tuple[str, dict, dict] | None:
        """
        Creates all missing config files if they do not exist.

        Once they exist, the data is returned.
        """
        newly_created_files = []

        # config file
        config_filename = "config.json"
        config_path = Path(f"configs/{config_filename}")
        if self.create_file(config_path, "config_template.json"):
            info = {
                "name": config_filename,
                "instruction": "Open the config and update the following required entries:\nsteam_id\napi_key",
            }
            newly_created_files.append(info)
        else:
            # gets excel file name
            excel_filename = "Game Library.xlsx"
            with open(config_path) as file:
                config_data = json.load(file)
                excel_filename = config_data["settings"]["excel_filename"]

            # excel file creation
            excel_path = Path(excel_filename)
            if self.create_file(excel_path, "Game_Library_Template.xlsx"):
                info = {
                    "name": excel_filename,
                    "instruction": "This file was recreated using the template",
                }
                newly_created_files.append(info)

        # ignore file
        ignore_filename = "ignore.json"
        ignore_path = Path(f"configs/{ignore_filename}")
        if self.create_file(ignore_path, "ignore_template.json"):
            info = {
                "name": ignore_filename,
                "instruction": "Insert any game names or app id's that you do not want to me synced (Optional)",
            }
            newly_created_files.append(info)

        if newly_created_files:
            for file in newly_created_files:
                print(f"\n{file['name']} was missing\n{file['instruction']}")
        else:
            errors = self.validate_config(config_data)
            with open(ignore_path) as file:
                ignore_data = json.load(file)
            if not errors:
                return config_path, config_data, ignore_data
            else:
                print(errors)
        input("\nPress Enter to Close")
        exit()


if __name__ == "__main__":
    setup = Setup()
    setup.run()
