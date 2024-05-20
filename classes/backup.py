import shutil, os, zipfile
import datetime as dt
from pathlib import Path


class Backup:

    def __init__(self, file: str, backup_path="backup/", redundancy: int = 3) -> None:
        """
        File Backup.
        """
        if not isinstance(file, str):
            raise TypeError("file is not a string.")
        self.file = Path(file)
        self.redundancy = redundancy
        self.backup_dir = Path(backup_path)

    def __repr__(self):
        cls = self.__class__
        cls_name = cls.__name__
        attributes = ",\n  ".join(
            f"{name}={value!r}" for name, value in vars(self).items()
        )
        return f"{cls_name}(\n  {attributes}\n)"

    def __bool__(self):
        return self.file.exists()

    def __eq__(self, other):
        return self.file == other.file

    def _maintain_redundancy(self):
        """
        ph
        """
        pattern = f"{self.file.stem}_*{self.file.suffix}"
        backups = sorted(self.backup_dir.glob(pattern), key=os.path.getmtime)
        while len(backups) > self.redundancy:
            oldest_backup = backups.pop(0)
            oldest_backup.unlink()

    def run(self, compress=False) -> bool | None:
        """
        Runs a backup procedure for `self.file`.
        The function will return True if it is a success.
        """
        if not self.file.exists():
            raise FileNotFoundError()

        # ensure the backup directory exists
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True, exist_ok=True)

        # create a new backup file with a timestamp
        timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_filename = f"{self.file.stem}_{timestamp}{self.file.suffix}"
        backup_path = self.backup_dir / backup_filename

        # compresses or copies file
        if compress:
            with zipfile.ZipFile(self.file, "w") as jungle_zip:
                jungle_zip.write(backup_path, compress_type=zipfile.ZIP_DEFLATED)
        else:
            shutil.copy(self.file, backup_path)

        self._maintain_redundancy()
        return True
