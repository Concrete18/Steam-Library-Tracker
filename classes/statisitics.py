import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import numpy as np
import json

from easierexcel import Excel, Sheet


class Stat:
    def __init__(self, dataframe):
        self.df = dataframe
        # turns Genre section from string to series
        self.df["Genre"] = self.df["Genre"].str.replace(" and ", ",")
        self.df["Genre"] = self.df["Genre"].str.replace(" ", "")
        self.df["Genre"] = self.df["Genre"].str.split(",")

    def my_rating_comparison(self):
        y_value = "Steam Review Percent"
        x_value = "My Rating"
        df = self.df[[y_value, x_value]]

        # sets up graph
        plt.title("Steam Reviews vs. My Ratings")
        # x axis
        x = df[x_value]
        plt.xlabel(x_value)
        plt.xlim([1, 10])
        plt.xticks(range(1, 11))

        # y axis
        y = df[y_value]
        plt.ylim([1, 100])
        plt.ylabel(y_value)

        # base settings
        plt.scatter(x, y, s=70, alpha=0.15)
        plt.plot([1, 10], [1, 100], "g")
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.show()

    # def steam_rating_comparison(self):
    #     y_value = "Metacritic"
    #     x_value = "Steam Review Percent"
    #     df = self.df[[y_value, x_value]].copy()
    #     df[x_value] = df[x_value] * 100

    #     # sets up graph
    #     plt.title("Metacritic vs. Steam Review")

    #     # x axis
    #     x = df[x_value]
    #     plt.xlabel(x_value)
    #     plt.xlim([1, 100])
    #     plt.xticks(range(0, 101, 10), rotation=90)

    #     # y axis
    #     y = df[y_value]
    #     plt.ylim([1, 100])
    #     plt.ylabel(y_value)

    #     # base settings
    #     plt.scatter(x, y, 50, "0.0", lw=2)  # optional
    #     plt.scatter(x, y, 50, "1.0", lw=0)  # optional
    #     plt.scatter(x, y, 40, "C0", lw=0, alpha=0.3)
    #     plt.plot([1, 100], [1, 100], "g")
    #     plt.tight_layout()
    #     plt.show()

    def rating_release_comparison(self, rating_column):
        y_value = rating_column
        x_value = "Release Year"
        df = self.df[[x_value, y_value]]
        # df.dropna(axis=0, inplace=True)

        # sets up graph
        plt.title(f"{rating_column} by Year")

        # sorts Release Year
        df = df.sort_values(by=x_value)

        # x setup
        x = df[x_value]
        plt.xlabel(x_value)
        plt.xticks(np.arange(min(x), max(x) + 1, 1.0), rotation=90)

        # y setup
        y = df[y_value]
        plt.ylabel(y_value)

        plt.scatter(x, y, s=70, alpha=0.70)
        plt.tight_layout()
        plt.show()

    def avg_rating_by_year(self):
        """
        Shows average rating by year on a long graph.
        BUG currently a blank plot
        """
        new_df = self.df[["Steam Review Percent", "Release Year"]].copy()
        new_df["Steam Review"] = new_df["Steam Review Percent"] * 100.0
        new_df.groupby("Release Year")["Steam Review"].mean()
        new_df.dropna(axis=0, inplace=True)

        # sets up graph
        plt.title("AVG Rating by Year")

        # x axis
        x = new_df["Release Year"]
        plt.xlabel("Year")
        plt.xticks(np.arange(min(x), max(x) + 1, 1.0), rotation=90)

        # y axis
        y = new_df["Steam Review"]
        plt.ylim([1, 11])
        plt.ylabel("AVG Rating")

        # base settings
        plt.plot(x, y)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    # excel setup
    config = Path("configs\config.json")
    with open(config) as file:
        data = json.load(file)
    excel_filename = data["settings"]["excel_filename"]
    excel = Excel(excel_filename, log_file="logs/excel.log")

    # stat setup
    na_values = [
        "NaN",
        "NF - Error",
        "Invalid Date",
        "ND - Error",
        "No Tags",
        "No Year",
        "No Score",
        "Not Found",
        "No Reviews",
        "Not Enough Reviews",
        "No Publisher",
        "No Developer",
    ]
    steam = Sheet(excel, sheet_name="Steam", column_name="App ID")
    df = steam.create_dataframe(na_vals=na_values)

    # run
    stats = Stat(df)
    stats.get_game_statistics()
    stats.my_rating_comparison()
    # stats.rating_release_comparison("Steam Review Percent")
