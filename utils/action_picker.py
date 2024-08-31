# standard library
import sys

# third-party imports
from rich.console import Console
from pick import pick


console = Console()


def advanced_picker(
    choices: list[tuple[str, callable]],
    prompt: str,
    indicator="->",
) -> tuple[str, callable]:
    """
    Choice picker using the advanced and less compatible Pick module.
    """
    options = [choice[0] for choice in choices]
    selected_index = pick(options, prompt, indicator=indicator)[1]
    return choices[selected_index]


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
        if "exit" in name.lower():
            return
        if repeat:
            action_picker(choices, repeat)
