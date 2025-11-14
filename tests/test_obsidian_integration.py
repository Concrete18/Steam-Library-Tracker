# local application imports
from library.obsidian.integration import *

# third-party imports
import pandas as pd


class TestGetYear:

    def test_success(self):
        name = "Mass Effect 2 (2010)"
        nan_year = pd.NA
        year = get_year(name, nan_year)
        assert year == 2010
