# standard library
from typing import Callable
import sys

# third-party imports
from rich.console import Console
from pick import pick

console = Console()

# pragma: no cover


def advanced_picker(
    choices: list[tuple[str, Callable | None]],
    prompt: str,
    indicator="->",
) -> tuple[str, Callable]:
    """
    Choice picker using the advanced and less compatible Pick module.
    """
    options = [choice[0] for choice in choices if choice[1]]
    selected_index = pick(options, prompt, indicator=indicator)[1]
    return choices[selected_index]  # type: ignore


def action_picker(choices: list[tuple], repeat: bool = True) -> None:
    """
    Allows picking a task using Arrow Keys and Enter.
    """
    # skip if terminal is incompatible.
    if not sys.stdout.isatty():
        print("\nSkipping Task Picker.\nInput can't be used")
        return
    input("\nPress Enter to Pick Next Action:")
    PROMPT = "What do you want to do? (Use Arrow Keys and Enter):"
    selected = advanced_picker(choices, PROMPT)
    if selected:
        name, func = selected
        msg = f"\n[b underline]{name}[/] Selected"
        console.print(msg, highlight=False)
        func()
        if repeat:
            action_picker(choices, repeat)
