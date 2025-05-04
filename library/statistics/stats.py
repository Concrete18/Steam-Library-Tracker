import pandas as pd
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout


from library.statistics.summary import get_summary

# Load your Excel file
file = "D:\Dropbox\Coding\Projects\Python\Game Library Tracker\Game Library.xlsx"
df = pd.read_excel(file, na_values="-")

# Setup Rich console
console = Console()
layout = Layout()

# Parse dates
df["Last Played"] = pd.to_datetime(df["Last Played"], errors="coerce")
df["Date Added"] = pd.to_datetime(df["Date Added"], errors="coerce")

# High-rated low-playtime games
high_rated_low_play = df[(df["My Rating"] >= 9) & (df["Hours Played"] < 5)]

# Games installed but not played recently (30+ days)
recent_cutoff = datetime.today() - timedelta(days=30)
stale_installed = df[(df["Installed"] == "Yes") & (df["Last Played"] < recent_cutoff)]

# Linux play percentage
df["Linux Play %"] = (df["Linux Hours"] / df["Hours Played"] * 100).round(2)

# Average playtime per genre
df = df.dropna(subset=["Hours Played", "Genre"])
genres_to_omit = ["-", "Free to Play", "Multiplayer", "Utilities", "Violent"]

df["Genre"] = df["Genre"].str.replace(" and ", ", ", regex=False)
df["Genre"] = df["Genre"].str.split(", ")
df_exploded = df.explode("Genre")
df_exploded = df_exploded[~df_exploded["Genre"].isin(genres_to_omit)]
avg_playtime_per_genre = (
    df_exploded.groupby("Genre")["Hours Played"].mean().sort_values(ascending=False)
)


def display_stats():
    """
    ph
    """
    summary = get_summary(df)

    # High-rated short-play table
    short_play_table = Table(title="High-Rated but Low Playtime Games", show_lines=True)
    short_play_table.add_column("Name", style="bold cyan")
    short_play_table.add_column("My Rating", justify="right")
    short_play_table.add_column("Hours Played", justify="right")
    for _, row in high_rated_low_play.iterrows():
        short_play_table.add_row(
            row["Name"], str(row["My Rating"]), f"{row['Hours Played']:.1f}"
        )

    # Stale installed table
    stale_table = Table(title="Installed but Not Played Recently", show_lines=True)
    stale_table.add_column("Name", style="bold cyan")
    stale_table.add_column("Last Played", justify="right")
    for _, row in stale_installed.iterrows():
        stale_table.add_row(row["Name"], row["Last Played"].date().isoformat())

    # Playtime per genre
    genre_table = Table(title="Average Playtime per Genre", show_lines=True)
    genre_table.add_column("Genre", style="bold magenta")
    genre_table.add_column("Avg Hours Played", justify="right")
    for genre, avg in avg_playtime_per_genre.items():
        genre_table.add_row(genre, f"{avg:.2f}")

    # Output to terminal
    console.print(summary)
    console.print(genre_table)
    console.print(short_play_table)
    # console.print(stale_table)
