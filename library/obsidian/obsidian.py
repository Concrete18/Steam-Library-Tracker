# standard library
from pathlib import Path
import os


class Obsidian:
    def __init__(self, vault_path: str) -> None:
        self.vault_path = Path(vault_path)
        if not self.vault_path.exists():
            raise Exception("Vault Path does not exist.")

    def __str__(self):
        return f'Obsidian(vault_path="{self.vault_path}")'

    def __bool__(self):
        return bool(self.vault_path)

    def full_path(self, sub_directory) -> str:
        return self.vault_path / sub_directory

    @staticmethod
    def create_url_link(title: str, url: str) -> str:
        """
        Create a markdown URL using the given `title` and `url`.
        """
        return f"[{title}]({url})"

    @staticmethod
    def cleaned_title(title):
        return title.replace(":", "").strip() or "untitled"

    @staticmethod
    def insert_image(url_or_path):
        """
        ph
        """
        return f"![[{url_or_path}]]"

    @staticmethod
    def create_markdown_table(
        headers: list[str],
        rows: list[list[str]],
    ) -> str:
        """
        Generate a Markdown table string from headers and rows.
        Supports alignment via header suffixes or an optional alignment list.

        Header suffixes:
            - "<" = left
            - ":" = center
            - ">" = right
        Example: "Price>" → right-aligned column

        Args:
            headers (list[str]): Column headers (may include suffixes for alignment).
            rows (list[list[str]]): Table rows (list of lists).

        Returns:
            str: The generated Markdown table as a string.
        """
        if not headers:
            raise ValueError("Headers cannot be empty.")

        # Extract alignments from headers
        alignments = []
        clean_headers = []
        for header in headers:
            if header.endswith(">"):
                alignments.append("r")
                clean_headers.append(header[:-1])
            elif header.endswith(":"):
                alignments.append("c")
                clean_headers.append(header[:-1])
            elif header.endswith("<"):
                alignments.append("l")
                clean_headers.append(header[:-1])
            else:
                alignments.append("l")
                clean_headers.append(header)

        align_map = {
            "l": ":---",
            "c": ":---:",
            "r": "---:",
        }
        separator = "| " + " | ".join(align_map[a] for a in alignments) + " |"
        header_row = "| " + " | ".join(clean_headers) + " |"
        data_rows = [
            "| " + " | ".join(str(cell) for cell in row) + " |" for row in rows
        ]

        return "\n".join([header_row, separator, *data_rows])

    def find_note_by_title(self, target_title: str) -> Path | None:
        """
        Allows searching for an existing note by title.
        """
        cleaned_title = self.cleaned_title(target_title)
        for root, _, files in os.walk(self.vault_path):
            for f in files:
                file = Path(f)
                print(file.stem, file.suffix)
                if cleaned_title == file.stem and file.suffix == ".md":
                    path = Path(f"{root}/{file.name}")
                    if path.exists():
                        return path

    def update_note(self, note_path: str, body: str) -> bool:
        """
        Replaces note's text with `body` by `note_path`.
        Returns True if note was updated and False if it does not exist.
        """
        full_path = self.full_path(note_path)
        if not os.path.exists(full_path):
            return False
        with open(full_path, "w", encoding="utf-8") as outfile:
            outfile.write(body)
        return True

    def create_note(self, title: str, body: str, note_folder: str) -> bool:
        """
        Create a new note in Obsidian.
        Returns True if note was created and False if it already exists.
        """
        cleaned_title = self.cleaned_title(title)
        file = self.vault_path / note_folder / f"{cleaned_title}.md"
        if file.exists():
            return False
        with open(file, "w", encoding="utf-8") as outfile:
            outfile.write(body)
        return True


if __name__ == "__main__":
    obsidian = Obsidian("tests/obsidian")
    print(obsidian)
    note = obsidian.find_note_by_title("Game 1")
    print(note)
