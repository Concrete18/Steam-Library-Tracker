from classes.utils import Utils


class Steam(Utils):
    def get_owned_steam_games(self, steam_key, steam_id=0):
        """
        Gets the games owned by the given `steam_id`.
        """
        base_url = "http://api.steampowered.com/"
        api_action = "IPlayerService/GetOwnedGames/v0001/"
        url = base_url + api_action
        self.api_sleeper("steam_owned_games")
        query = {
            "key": steam_key,
            "steamid": steam_id,
            "l": "english",
            "include_played_free_games": 0,
            "format": "json",
            "include_appinfo": 1,
        }
        response = self.request_url(url, params=query)
        return response.json()["response"]["games"]

    def get_recently_played_steam_games(self, steam_key, steam_id=0, game_count=10):
        """
        Gets the games owned by the given `steam_id`.
        """
        base_url = "http://api.steampowered.com/"
        api_action = "IPlayerService/GetRecentlyPlayedGames/v1/"
        url = base_url + api_action
        self.api_sleeper("steam_owned_games")
        query = {
            "key": steam_key,
            "steamid": steam_id,
            "count": game_count,
        }
        response = self.request_url(url, params=query)
        return response.json()["response"]["games"]

    def get_game_info(self, app_id):
        """
        Gets game info with steam api using a `app_id`.
        """
        info_dict = {
            "game_name": "Unset",
            self.dev_col: "ND - Error",
            self.pub_col: "ND - Error",
            self.genre_col: "ND - Error",
            self.ea_col: "No",
            self.steam_rev_per_col: "No Reviews",
            self.steam_rev_total_col: "No Reviews",
            self.user_tags_col: "No Tags",
            self.release_col: "No Year",
            "price": "ND - Error",
            "discount": 0.0,
            "on_sale": False,
            "linux_compat": "Unsupported",
            "drm_notice": "ND - Error",
            "categories": "ND - Error",
            "ext_user_account_notice": "ND - Error",
        }

        def get_json_desc(data):
            return [item["description"] for item in data]

        url = "https://store.steampowered.com/api/appdetails"
        self.api_sleeper("steam_app_details")
        query = {"appids": app_id, "l": "english"}
        response = self.request_url(url, params=query)
        if not response:
            return info_dict
        dict = response.json()
        # gets games store data
        store_link = self.get_store_link(app_id)
        self.api_sleeper("store_data")
        response = self.request_url(store_link)
        # steam review data
        percent, total = self.get_steam_review(app_id=app_id, response=response)
        info_dict[self.steam_rev_per_col] = percent
        info_dict[self.steam_rev_total_col] = total
        # get user tags
        tags = self.get_steam_user_tags(app_id=app_id, response=response)
        info_dict[self.user_tags_col] = ", ".join(tags)
        # info_dict setup
        if "data" in dict[str(app_id)].keys():
            game_info = dict[str(app_id)]["data"]
            keys = game_info.keys()
            # get game name
            if "name" in keys:
                info_dict["game_name"] = game_info["name"]
            # get developer
            if "developers" in keys:
                output = self.word_and_list(game_info["developers"])
                info_dict[self.dev_col] = output
            # get publishers
            if "publishers" in keys:
                output = self.word_and_list(game_info["publishers"])
                info_dict[self.pub_col] = output
            # get genre
            if "genres" in keys:
                genres = get_json_desc(game_info["genres"])
                info_dict[self.genre_col] = ", ".join(genres)
                # early access
                if self.ea_col in info_dict[self.genre_col]:
                    info_dict[self.ea_col] = "Yes"
            # get release year
            if "release_date" in keys:
                release_date = game_info["release_date"]["date"]
                release_date = self.get_year(release_date)
                info_dict[self.release_col] = release_date
            # get price_info
            if "price_overview" in keys:
                price_data = game_info["price_overview"]
                price = price_data["final_formatted"]
                discount = price_data["discount_percent"]
                on_sale = price_data["discount_percent"] > 0
                if price:
                    info_dict["price"] = price
                if discount:
                    info_dict["discount"] = float(discount)
                if on_sale:
                    info_dict["on_sale"] = on_sale
            # get linux compat
            if "linux_compat" in keys:
                info_dict["linux_compat"] = game_info["platforms"]["linux"]
            # categories
            if "categories" in keys:
                categories = get_json_desc(game_info["categories"])
                info_dict["categories"] = self.word_and_list(categories)
            # drm info
            if "drm_notice" in keys:
                info_dict["drm_notice"] = game_info["drm_notice"]
            # external account
            if "ext_user_account_notice" in keys:
                info_dict["ext_user_account_notice"] = game_info[
                    "ext_user_account_notice"
                ]
            # runs unicode remover on all values
            return {k: self.unicode_remover(v) for k, v in info_dict.items()}
        return info_dict

    def get_app_list(self):
        """
        ph
        """
        main_url = "https://api.steampowered.com/"
        api_action = "ISteamApps/GetAppList/v0002/"
        url = main_url + api_action
        query = {"l": "english"}
        response = self.request_url(url, params=query)
        if not response:
            return None
        app_list = response.json()["applist"]["apps"]
        return app_list

    def get_app_id(self, game, app_list={}):
        """
        ph
        """
        for item in app_list:
            if item["name"] == game:
                return item["appid"]
        return None
