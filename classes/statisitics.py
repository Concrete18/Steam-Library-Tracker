import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


class Stat:
    def create_dataframe(
        excel_path,
    ):
        excel_path = r"Excel Game Sheet.xlsx"
        na_values = [
            "Page Error",
            "Not Enough Data",
            "Not Found",
            "No Data",
            "No Score",
            "No Release Year",
            "Invalid Release Year",
            "Invalid Date",
        ]
        date_columns = ["Release Year", "Date Updated", "Date Added"]
        return pd.read_excel(
            excel_path, engine="openpyxl", parse_dates=date_columns, na_values=na_values
        )

    def rating_comparison(self):
        df = self.create_dataframe()
        df = df[["Metacritic Score", "My Rating"]]
        df.dropna(axis=0, inplace=True)
        # sets up graph
        x = df["My Rating"]
        y = df["Metacritic Score"]
        plt.scatter(x, y)
        plt.xticks(rotation=90)
        plt.show()

    def rating_release_comparison(self):
        df = self.create_dataframe()
        x_value = "Release Year"
        # y_value = 'Metacritic Score'
        y_value = "Metacritic Score"
        df = df[[x_value, y_value]]
        df.dropna(axis=0, inplace=True)
        print(df)
        # sorts Release Year
        df = df.sort_values(by=x_value)

        # sets up graph
        x = df[x_value]
        plt.xlabel(x_value)

        y = df[y_value]
        plt.ylabel(y_value)

        plt.scatter(x, y)
        # plt.xticks(rotation = 90)
        plt.show()


Stat = Stat()
Stat.rating_release_comparison()
