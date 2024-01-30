from pathlib import Path
import shutil, json


class Setup:
    def setup():
        """
        Creates the config and excel file if they do not exist.
        """
        all_clear = True
        # config check
        config = Path("configs/config.json")
        excel_filename = "Game Library.xlsx"
        if not config.exists():
            config_template = Path("templates/config_template.json")
            shutil.copyfile(config_template, config)
            all_clear = False
        with open(config) as file:
            data = json.load(file)
            excel_filename = data["settings"]["excel_filename"]
        # excel check
        excel = Path(excel_filename)
        if not excel.exists():
            excel_template = Path("templates/Game_Library_Template.xlsx")
            shutil.copyfile(excel_template, excel)
            all_clear = False
        # exits out of function early if all clear
        if all_clear:
            return config, data
        # instructions
        print("Open the config and update the following entries:")
        print("steam_id\nsteam_api_key")
        input("\nPress Enter to Close")
        exit()
