import pytest

from classes.setup import Setup


class TestValidateSteamApiKey:
    """
    Tests `validate_steam_key` function.
    Steam ID's must be allnumbers and 17 characters long.
    """

    setupObj = Setup()

    def test_True(self):
        test_api_key = "15D4C014D419C0642B1E707BED41G7D4"
        is_steam_key = self.setupObj.validate_steam_key(test_api_key)
        assert is_steam_key is True

    def test_False(self):
        test_api_key = "15D4C014D419C0642B7D4"
        is_steam_key = self.setupObj.validate_steam_key(test_api_key)
        assert is_steam_key is False


class TestValidateSteamID:
    """
    Tests `validate_steam_id` function.
    Steam ID's must be allnumbers and 17 characters long.
    """

    setupObj = Setup()

    def test_True(self):
        assert self.setupObj.validate_steam_id(76561197960287930) is True
        assert self.setupObj.validate_steam_id("76561197960287930") is True

    def test_False(self):
        assert self.setupObj.validate_steam_id(765611028793) is False
        assert self.setupObj.validate_steam_id("asjkdhadsjdhjssaj") is False


if __name__ == "__main__":
    pytest.main([__file__])
