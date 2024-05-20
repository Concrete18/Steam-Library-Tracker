import pytest

# classes
from classes.backup import Backup


class TestBackup:
    backup = Backup(file="tests/readme.md")

    def test_bool(self):
        """
        ph
        """
        assert self.backup

    def test_eq(self):
        """
        ph
        """
        backup2 = Backup(file="test")
        # same file is identical to itself
        assert self.backup == self.backup
        # different files are unique
        assert self.backup != backup2

    def test_file_not_found(self):
        backup = Backup(file="3211")
        with pytest.raises(FileNotFoundError):
            backup.run()

    def test_path_not_string(self):
        with pytest.raises(TypeError):
            Backup(file=3211)


if __name__ == "__main__":
    pytest.main([__file__])
