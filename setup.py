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
        # steam id check
        steam_id = config_data.get("steam_data", {}).get("steam_id", "")
        if not self.validate_steam_id(steam_id):
            errors.append("Steam ID is Invalid")
        # steam api key
        api_key = config_data.get("steam_data", {}).get("api_key", "")
        if not self.validate_steam_key(api_key):
            errors.append("Steam API Key is Invalid")
        return errors

    @staticmethod
    def create_file_if_missing(file, temp_path) -> bool:
        """
        Creates the `file` by copying the template from `temp_path` if it does not exist.
        """
        if not file.exists():  # pragma: no cover
            config_template = Path(f"configs/templates/{temp_path}")
            shutil.copyfile(config_template, file)
            return True
        return False

    def run(self) -> tuple[str, dict, dict] | None:
        """
        Creates all missing config files if they do not exist.

        Once they exist, the data is returned.
        """
        # TODO improve this so it is easier to add more files
        newly_created_files = []
        # config file
        config_filename = "config.json"
        config_path = Path(f"configs/{config_filename}")
        if self.create_file_if_missing(config_path, "config_template.json"):
            newly_created_files.append(
                {
                    "name": config_filename,
                    "instruction": "Open the config and update the following required entries:\nsteam_id\napi_key",
                }
            )
        else:
            # gets excel file name
            excel_filename = "Game Library.xlsx"
            with open(config_path) as file:
                config_data = json.load(file)
                excel_filename = config_data["settings"]["excel_filename"]

            # excel file creation
            excel_path = Path(excel_filename)
            if self.create_file_if_missing(excel_path, "Game_Library_Template.xlsx"):
                newly_created_files.append(
                    {
                        "name": excel_filename,
                        "instruction": "This file was recreated using the template",
                    }
                )

        # excel options
        excel_options_filename = "excel_options.json"
        excel_options_path = Path(f"configs/{excel_options_filename}")
        if self.create_file_if_missing(
            excel_options_path, "excel_options_template.json"
        ):
            newly_created_files.append(
                {
                    "name": excel_options_filename,
                    "instruction": "Insert any game names or app id's that you do not want to me synced (Optional)",
                }
            )
        else:
            with open(excel_options_path) as file:
                excel_options = json.load(file)

        # ignore file
        ignore_filename = "ignore.json"
        ignore_path = Path(f"configs/{ignore_filename}")
        if self.create_file_if_missing(ignore_path, "ignore_template.json"):
            newly_created_files.append(
                {
                    "name": ignore_filename,
                    "instruction": "Insert any game names or app id's that you do not want to me synced (Optional)",
                }
            )
        else:
            with open(ignore_path) as file:
                ignore_data = json.load(file)

        if newly_created_files:
            for file in newly_created_files:
                print(f"\n{file['name']} was missing\n{file['instruction']}")
        else:
            errors = self.validate_config(config_data)
            if not errors:
                return config_path, config_data, ignore_data, excel_options
            else:
                print(errors)
        input("\nPress Enter to Close")
        exit()


if __name__ == "__main__":  # pragma: no cover
    setup = Setup()
    setup.run()
