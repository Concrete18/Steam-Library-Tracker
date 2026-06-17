from rich.console import Console
from rich.theme import Theme
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

custom_theme = Theme(
    {
        "primary": "bold deep_sky_blue1",
        "secondary": "bold pale_turquoise1",
        # error
        "info": "dim cyan",
        "warning": "bold magenta",
        "danger": "bold red",
        # color scale
        "top_scale": "bold green1",
        "high_scale": "bold spring_green1",
        "mid_scale": "bold cyan1",
        "bottom_scale": "bold steel_blue1",
        "faded": "grey58",
        # play status
        "endless": "bold green4",
        "finished": "bold green1",
        "played": "bold light_goldenrod2",
        "unplayed": "bold sky_blue2",
        "waiting": "bold dark_goldenrod",
        "quit": "bold deep_pink2",
        "replay": "bold dodger_blue2",
    }
)
console = Console(theme=custom_theme)


def create_progress_bar(title: str, elapsed=False) -> Progress:
    counter = TimeRemainingColumn()
    if elapsed:
        counter = TimeElapsedColumn()
    progress_bar = Progress(
        TextColumn(title),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        MofNCompleteColumn(),
        TextColumn("|"),
        counter,
    )
    return progress_bar
