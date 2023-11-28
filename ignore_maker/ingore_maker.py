from pathlib import Path


class IgnoreMaker:
    games = Path("ignore_maker\data.txt").read_text().splitlines()

    def prep_for_ignore_list(self):
        """
        ph
        """
        unicode_issues = []
        for game in self.steam:
            if r"\u" in game:
                unicode_issues.append(game)
            else:
                print(f'"{game}",')
        if unicode_issues:
            print("The following have unicode issues")
            for game in unicode_issues:
                print(game)

    def order_and_dupe_remover(self):
        """
        ph
        """
        found = []
        for game in self.steam:
            if game not in found:
                found.append(game)
        found.sort()
        for game in found:
            print(game)

    def run(self):
        """
        ph
        """
        first_entry = self.steam[0]
        if first_entry.startswith('"') and first_entry.endswith('",'):
            self.order_and_dupe_remover()
        else:
            self.prep_for_ignore_list()


if __name__ == "__main__":
    app = IgnoreMaker()
    app.run()
