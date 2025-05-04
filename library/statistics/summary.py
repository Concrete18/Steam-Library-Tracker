import pandas as pd
from rich.panel import Panel


def get_summary(df: pd.DataFrame):
    """
    Summary panel
    """
    total_hours = df["Hours Played"].sum()
    avg_my_rating = df["My Rating"].mean()
    avg_steam_rating = df["Steam Review Percent"].mean()

    summary = Panel.fit(
        f"""
    [bold cyan]Total Time Played:[/] {total_hours:.1f} hours
    [bold cyan]Average My Rating:[/] {avg_my_rating:.2f}
    [bold cyan]Average Steam Rating:[/] {avg_steam_rating:.0%}
    """,
        title="Summary",
        border_style="green",
    )
    return summary
