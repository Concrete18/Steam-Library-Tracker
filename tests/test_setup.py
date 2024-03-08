import pytest

from classes.setup import Setup


class TestValidateSteamApiKey:
    """
    Tests `validate_steam_key` function.
    Steam ID's must be allnumbers and 17 characters long.
    """

    setupObj = Setup()

    def test_True(self):
        TEST_API_KEY = "15D4C014D419C0642B1E707BED41G7D4"
        assert self.setupObj.validate_steam_key(TEST_API_KEY)

    def test_False(self):
        TEST_API_KEY = "15D4C014D419C0642B7D4"
        assert not self.setupObj.validate_steam_key(TEST_API_KEY)


class TestValidateSteamID:
    """
    Tests `validate_steam_id` function.
    Steam ID's must be allnumbers and 17 characters long.
    """

    setupObj = Setup()

    def test_True(self):
        assert self.setupObj.validate_steam_id(76561197960287930)
        assert self.setupObj.validate_steam_id("76561197960287930")

    def test_False(self):
        assert not self.setupObj.validate_steam_id(765611028793)
        assert not self.setupObj.validate_steam_id("not a steam id")


if __name__ == "__main__":
    pytest.main([__file__])
