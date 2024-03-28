import pytest

from setup import Setup


class TestValidateSteamApiKey:
    """
    Steam ID's must all be numbers and 17 characters long.
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
    Steam ID's must all be numbers and 17 characters long.
    """

    setupObj = Setup()

    def test_True(self):
        assert self.setupObj.validate_steam_id(76561197960287930)
        assert self.setupObj.validate_steam_id("76561197960287930")

    def test_False(self):
        assert not self.setupObj.validate_steam_id(765611028793)
        assert not self.setupObj.validate_steam_id("not a steam id")


class TestValidateConfig:
    """
    Steam ID's must all be numbers and 17 characters long.
    """

    setupObj = Setup()

    def test_success(self):
        config_data = {
            "steam_data": {
                "steam_id": 76561197960287930,
                "api_key": "15D4C014D419C0642B1E707BED41G7D4",
            }
        }
        errors = self.setupObj.validate_config(config_data)
        assert not errors

    def test_fail(self):
        config_data = {}
        errors = self.setupObj.validate_config(config_data)
        answer = ["Steam ID is Invalid", "Steam API Key is Invalid"]
        assert errors == answer


if __name__ == "__main__":
    pytest.main([__file__])
