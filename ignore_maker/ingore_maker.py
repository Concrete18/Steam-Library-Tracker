with open('ignore_maker\data.txt') as f:
    games = f.read().splitlines()

def prep_for_ignore_list():
    for game in games:
        print(f'"{game}",')

def order_and_dupe_remover():
    found = []
    for game in games:
        if game not in found:
            found.append(game)
    found.sort()
    for game in found:
        print(game)

prep_for_ignore_list()
# order_and_dupe_remover()
