from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


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
