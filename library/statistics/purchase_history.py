# standard library
from pathlib import Path
import json, csv

# third-party imports
import pandas as pd
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def load_purchase_data() -> list[dict]:
    """
    Loads purchase history from config folder.
    """
    path = Path("data/steam_purchase_history.json")
    if path.exists():
        with open(path) as file:
            return json.load(file)
    return []


def create_csv():
    data = load_purchase_data()

    with open("data/steam_purchase_history.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(["name", "date", "type", "desc", "total"])
        "name, date, type, total"

        for entry in data:
            games = entry.get("games", [])
            date = entry.get("date")
            total = entry.get("total", 0)
            entry_type = entry.get("type")

            if len(games) == 1:
                writer.writerow([games[0], date, entry_type, "", total])
            elif entry_type == "In-Game Purchase":
                writer.writerow([games[0], date, entry_type, games[1], total])
            else:
                first = True
                for game in games:
                    grouped_total = total if first else 0
                    first = False
                    writer.writerow(
                        [
                            game,
                            date,
                            entry_type,
                            "grouped purchase",
                            grouped_total,
                        ]
                    )


def game_summary(df: pd.DataFrame) -> Panel:

    # market profit

    # TODO remove market data
    total_paid = df["total"].sum()
    avg_paid = df["total"].mean()

    now = pd.Timestamp.now().normalize()
    cur_week = df[df["date"] >= now - pd.Timedelta(days=7)]
    cur_month = df[df["date"] >= now - pd.Timedelta(days=30)]
    cur_year = df[df["date"] >= now - pd.Timedelta(days=365)]

    prev_week = df[
        (df["date"] >= now - pd.Timedelta(days=14))
        & (df["date"] <= now - pd.Timedelta(days=7))
    ]

    prev_month = df[
        (df["date"] >= now - pd.Timedelta(days=60))
        & (df["date"] <= now - pd.Timedelta(days=30))
    ]

    prev_year = df[
        (df["date"] >= now - pd.Timedelta(days=730))
        & (df["date"] <= now - pd.Timedelta(days=365))
    ]

    summary = Panel(
        f"""
    [bold cyan]Current Week:[/]   ${cur_week["total"].sum():,.2f}
    [bold cyan]Current Month:[/]  ${cur_month["total"].sum():,.2f}
    [bold cyan]Current Year:[/]   ${cur_year["total"].sum():,.2f}

    [bold cyan]Previous Week:[/]  ${prev_week["total"].sum():,.2f}
    [bold cyan]Previous Month:[/] ${prev_month["total"].sum():,.2f}
    [bold cyan]Previous Year:[/]  ${prev_year["total"].sum():,.2f}

    [bold cyan]Avg Price:[/] ${avg_paid:,.2f}
    [bold cyan]Total Payed:[/] ${total_paid:,.2f}
        """,
        title="Game Summary",
        border_style="green",
        expand=False,
    )
    return summary


def market_summary(df: pd.DataFrame) -> Panel:
    df = df[df["market"]]

    total_profit = df["total"].sum()
    total_revenue = df["total"].sum()
    total_bought = df["total"].sum()

    summary = Panel(
        f"""
    [bold cyan]Total Profit:[/] ${total_profit:.2f}
    [bold cyan]Total Revenue:[/] ${total_revenue:.2f}
    [bold cyan]Total Bought:[/] ${total_bought:.2f}
        """,
        title="Market Summary",
        border_style="green",
        expand=False,
    )
    return summary


def show_tables(df: pd.DataFrame):
    df = df[~df["not_games"]]

    plt.figure(figsize=(20, 10))
    plt.plot(df["date"], df["total"], marker="o")
    plt.xlabel("Date")
    plt.ylabel("Amount Spent ($)")
    plt.title("Steam Purchases Over Time")
    plt.grid(True)

    plt.show()

    # df["cumulative_total"] = df["total"].cumsum()
    # plt.figure(figsize=(20, 10))
    # plt.plot(df["date"], df["cumulative_total"], marker="o")
    # plt.xlabel("Date")
    # plt.ylabel("Total Spent ($)")
    # plt.title("Cumulative Steam Spending")
    # plt.grid(True)
    # plt.show()

    # monthly = df.set_index("date").resample("M")["total"].sum()
    # plt.figure(figsize=(20, 10))
    # monthly.plot(kind="bar")
    # plt.xlabel("Month")
    # plt.ylabel("Total Spent ($)")
    # plt.title("Monthly Steam Spending")
    # plt.tight_layout()
    # plt.show()


def in_game_purchases(df: pd.DataFrame):
    # ensure numeric
    df["total"] = pd.to_numeric(df["total"], errors="coerce")
    in_game = df[df["type"] == "In-Game Purchase"]
    sums = in_game.groupby("name", as_index=False)["total"].sum().values.tolist()
    sorted_sums = sorted(sums, key=lambda entry: entry[1], reverse=True)

    TABLE_TITLE = "In-Game Purchase Totals"
    table = Table(
        title=TABLE_TITLE,
        show_lines=True,
        title_style="bold",
        style="green3",
    )
    table.add_column("Name", justify="left")
    table.add_column("Total", justify="right")

    for name, total in sorted_sums:
        if name == "Uninitialized":
            continue
        row = [name, f"${total:.2f}"]
        table.add_row(*row)
    console.print(table, new_line_start=True)


def purchase_history_stats():
    file = "D:/Dropbox/Coding/Projects/Python/Game Library Tracker/data/steam_purchase_history.csv"
    df = pd.read_csv(file, na_values="?")

    # parses dates
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # non game mask
    ignore_keywords = ["Market", "Valve Index", "Steam Deck"]
    df["not_games"] = df["name"].str.contains(
        "|".join(ignore_keywords), case=False, na=False
    )
    # market mask
    df["market"] = df["type"].str.contains("Market", case=False, na=False)

    stats = [
        game_summary(df),
        market_summary(df),
        # show_tables(df),
    ]

    for entry in stats:
        console.print(entry)

    in_game_purchases(df)


if __name__ == "__main__":
    create_csv()
    purchase_history_stats()
