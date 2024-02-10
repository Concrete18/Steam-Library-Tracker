import unittest

from classes.setup import Setup


class ValidateSteamApiKey(unittest.TestCase):
    """
    Tests `validate_steam_key` function.
    Steam ID's must be allnumbers and 17 characters long.
    """

    def setUp(self):
        self.s = Setup()

    def test_True(self):
        test_api_key = "15D4C014D419C0642B1E707BED41G7D4"
        is_steam_key = self.s.validate_steam_key(test_api_key)
        self.assertTrue(is_steam_key, "Should be a steam key")

    def test_False(self):
        test_api_key = "15D4C014D419C0642B7D4"
        is_steam_key = self.s.validate_steam_key(test_api_key)
        self.assertFalse(is_steam_key, "Should not be a steam key")


class ValidateSteamID(unittest.TestCase):
    """
    Tests `validate_steam_id` function.
    Steam ID's must be allnumbers and 17 characters long.
    """

    def setUp(self):
        self.s = Setup()

    def test_True(self):
        steam_ids = [
            76561197960287930,
            "76561197960287930",
        ]
        for id in steam_ids:
            with self.subTest(msg=type(id), id=id):
                result = self.s.validate_steam_id(id)
                self.assertTrue(result)

    def test_False(self):
        steam_ids = [
            765611028793,
            "asjkdhadsjdhjssaj",
        ]
        for id in steam_ids:
            with self.subTest(msg=type(id), id=id):
                result = self.s.validate_steam_id(id)
                self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
