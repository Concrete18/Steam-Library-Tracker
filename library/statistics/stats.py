# standard library
import datetime as dt
import json

# third-party imports
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout


class Statistics:

    def __init__(self):
        # TODO replace with data given at class instantiation
        self.PLAY_STATUS_CHOICES = (
            "Played",
            "Unplayed",
            "Finished",
            "Endless",
            "Replay",
            "Waiting",
            "Quit",
            "Ignore",
        )

        config_path = "library/statistics/settings.json"
        with open(config_path) as file:
            config_data = json.load(file)
            self.ignored_user_tags = config_data["ignored_user_tags"]

        # Load your Excel file
        file = (
            "D:\Dropbox\Coding\Projects\Python\Game Library Tracker\Game Library.xlsx"
        )
        self.dataframe = pd.read_excel(file, na_values="-")

        # Setup Rich console
        self.console = Console()

    def summary(self, df: pd.DataFrame) -> None:
        total_hours = df["Hours Played"].sum()
        avg_personal_rating = df["My Rating"].mean()
        avg_steam_rating = df["Steam Review Percent"].mean()

        summary = Panel.fit(
            f"""
        [bold cyan]Total Time Played:[/] {total_hours:.1f} hours
        [bold cyan]Average Personal Rating:[/] {avg_personal_rating:.2f}
        [bold cyan]Average Steam Rating:[/] {avg_steam_rating:.0%}
            """,
            title="Summary",
            border_style="green",
        )
        return summary

    def get_genre_stats(self, df: pd.DataFrame, n_entries: int = 15) -> None:
        """
        Average playtime per genre.
        """
        df = self.dataframe.dropna(subset=["Hours Played", "Genre"])
        genres_to_omit = [
            "-",
            "Free to Play",
            "Multiplayer",
            "Utilities",
            "Violent",
            "Early Access",
        ]

        df = df[df["Hours Played"].notna()].copy()
        df["Genre"] = df["Genre"].str.replace(" and ", ", ", regex=False)
        df["Genre"] = df["Genre"].str.split(", ")
        df_exploded = df.explode("Genre")
        df_exploded = df_exploded[~df_exploded["Genre"].isin(genres_to_omit)]

        avg_playtime_per_genre = (
            df_exploded.groupby("Genre")["Hours Played"]
            .mean()
            .sort_values(ascending=False)
        )
        # Playtime per genre
        table = Table(title="Average Playtime per Genre", show_lines=True)
        table.add_column("Genre", style="bold magenta")
        table.add_column("Avg Hours Played", justify="right")
        for genre, avg in avg_playtime_per_genre.items():
            table.add_row(genre, f"{avg:.2f}")
            n_entries -= 1
            if not n_entries:
                break
        return table

    def get_tag_stats(self, df: pd.DataFrame, n_entries: int = 15) -> None:
        """
        Average playtime per tag.
        """
        df = self.dataframe.copy()

        df = df.dropna(subset=["Hours Played", "User Tags"])
        df["User Tags"] = df["User Tags"].str.replace(" and ", ", ", regex=False)
        df["User Tags"] = df["User Tags"].str.split(", ")
        df_exploded = df.explode("User Tags")
        df_exploded = df_exploded[
            ~df_exploded["User Tags"].isin(self.ignored_user_tags)
        ]

        avg_playtime_per_tags = (
            df_exploded.groupby("User Tags")["Hours Played"]
            .mean()
            .sort_values(ascending=False)
        )
        # Playtime per tag
        table = Table(title="Average Playtime per Tags", show_lines=True)
        table.add_column("User Tags", style="bold magenta")
        table.add_column("Avg Hours Played", justify="right")
        for tag, avg in avg_playtime_per_tags.items():
            table.add_row(tag, f"{avg:.2f}")
            n_entries -= 1
            if not n_entries:
                break
        return table

    def output_play_status_info(self, df: pd.DataFrame) -> None:
        """
        Creates a table with counts and percentage of each play status.
        """
        df = self.dataframe

        table = Table(
            title="Play Status Stats",
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
            caption="Excludes Ignored",
        )
        PLAY_STATUS_COLUMN = "Play Status"

        # filters out games with "Ignore" play status
        df_filtered = df[df[PLAY_STATUS_COLUMN] != "Ignore"]
        play_statuses = df_filtered[PLAY_STATUS_COLUMN].value_counts()
        total_games_excluding_ignore = len(df_filtered)

        # Row creation
        row1, row2 = [], []
        for play_status in self.PLAY_STATUS_CHOICES:
            if play_status == "Ignore":
                continue
            count = play_statuses[play_status]
            table.add_column(play_status, justify="center")
            row1.append(str(count))
            row2.append(f"{count / total_games_excluding_ignore:.1%}")
        table.add_row(*row1)
        table.add_row(*row2)
        return table

    def build_layout(self, df: pd.DataFrame) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="summary"),
            Layout(name="play_status"),
            Layout(name="average_playtimes"),
            # Layout(name="footer", size=3),
        )
        layout["header"].update(
            Panel(
                "📊 Steam Game Library Stats",
                style="bold white on deep_sky_blue3",
                expand=False,
            )
        )
        layout["summary"].update(self.summary(df))

        layout["play_status"].update(Panel(self.output_play_status_info(df)))

        layout["average_playtimes"].split_row(
            Layout(name="left", size=45), Layout(name="right", size=45)
        )
        layout["left"].update(Panel(self.get_genre_stats(df)))

        layout["right"].update(Panel(self.get_tag_stats(df)))

        return layout

    def display_stats(self):
        df = self.dataframe.copy()

        # Parse dates
        df["Last Played"] = pd.to_datetime(df["Last Played"], errors="coerce")
        df["Date Added"] = pd.to_datetime(df["Date Added"], errors="coerce")

        # Games installed but not played recently (30+ days)
        recent_cutoff = dt.datetime.today() - dt.timedelta(days=30)
        stale_installed = df[
            (df["Installed"] == "Yes") & (df["Last Played"] < recent_cutoff)
        ]

        # new columns
        df["Linux Percent"] = (df["Linux Hours"] / df["Hours Played"] * 100).round(2)
        df["Days Since Last Played"] = (
            pd.Timestamp.today() - df["Last Played"]
        ).dt.days

        self.summary(df)
        self.output_play_status_info(df)
        # self.get_genre_stats(df)
        # self.get_tag_stats(df)

        layout = self.build_layout(df)
        self.console.print(layout)
