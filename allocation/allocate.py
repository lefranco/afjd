#!/usr/bin/env python3


"""
File : allocate.py

players allocation in a tournament
"""

import typing
import argparse
import sys
import random


def panic() -> None:
    """ panic """
    print('You pressed Ctrl+C!')
    sys.exit(1)


POWERS = ['England', 'France', 'Germany', 'Italy', 'Austria', 'Russia', 'Turkey']

PLAYERS_DATA: typing.List[str] = []
MASTERS_DATA: typing.List[str] = []

GAMES: typing.List['Game'] = []
PLAYERS: typing.List['Player'] = []


class Game:
    """ a game """

    def __init__(self, name: str) -> None:
        self._name = name
        self._allocation: typing.Dict[int, Player] = {}

    def put_player_in(self, role: int, player: 'Player') -> None:
        """ put_player_in """

        assert isinstance(role, int), "role should be an int"
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(player, Player), "player should be a Player"

        assert role not in self._allocation, "role in game should be free"
        self._allocation[role] = player

    def take_player_out(self, role: int, player: 'Player') -> None:
        """ put_player """

        assert isinstance(role, int), "role should be an int"
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(player, Player), "player should be a Player"

        assert role in self._allocation, "role in game should be in"
        del self._allocation[role]

    def player_in_game(self, player: 'Player') -> bool:
        """ player_in_game """
        return player in self._allocation.values()

    def has_role(self, role: int) -> bool:
        """ has_role """
        return role in self._allocation

    def list_players(self) -> str:
        """ describe_players """
        return ";".join([str(p) for p in self._allocation.values()])

    def complete(self) -> bool:
        """ complete """
        return len(self._allocation) == len(POWERS)

    @property
    def name(self) -> str:
        """ name """
        return self._name


class Player:
    """ a player """

    def __init__(self, name: str) -> None:

        assert isinstance(name, str)
        self._name = name
        self._allocation: typing.Dict[int, Game] = {}
        self._fully_allocated = False

    def put_in_game(self, role: int, game: Game) -> None:
        """ put_in_game """

        assert isinstance(role, int)
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(game, Game)

        assert role not in self._allocation, "role for player should be free"
        self._allocation[role] = game

    def remove_from_game(self, role: int, game: Game) -> None:
        """ remove_from_game """

        assert isinstance(role, int)
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(game, Game)

        assert role in self._allocation, "role for player should be in"
        del self._allocation[role]

    def number_games_already_in(self) -> int:
        """ number_games_already_in """
        return len(self._allocation)

    def fully_allocated(self) -> bool:
        """ fully_allocated """
        return len(self._allocation) == len(POWERS)

    def has_role(self, role: int) -> bool:
        """ has_role """
        return role in self._allocation

    @property
    def name(self) -> str:
        """ name """
        return self._name

    def __str__(self) -> str:
        return self._name


def try_and_error() -> bool:
    """ try_and_error """

    #  print("try_and_error()")

    # find a game where to fill up
    game = None
    for game_poss in GAMES:
        if not game_poss.complete():
            game = game_poss
            break

    if not game:
        # we are done
        return True

    # find a role
    role = None
    for role_poss in range(len(POWERS)):
        # game already has someone for this role
        if not game.has_role(role_poss):
            role = role_poss
            break

    if role is None:
        assert False, "Internal error : game has role or not !?"

    # find a player to put in

    players_sorted = sorted(PLAYERS, key=lambda p: p.number_games_already_in())

    for player_poss in players_sorted:

        # player already has a game for this role
        if player_poss.has_role(role):
            continue

        # player is already in this game
        if game.player_in_game(player_poss):
            continue

        player = player_poss

        # player_poss
        #  print(f"put {player} in {game}")
        player.put_in_game(role, game)
        game.put_player_in(role, player)

        # if we fail, we try otherwise !
        if try_and_error():
            return True

        #  print(f"remove {player} from {game}")
        player.remove_from_game(role, game)
        game.take_player_out(role, player)

    return False


def main() -> None:
    """ main """

    # we make big use of recursion here
    sys.setrecursionlimit(10000)

    global PLAYERS_DATA
    global MASTERS_DATA

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--seed', required=False, help='force seed for random')
    parser.add_argument('-r', '--randomize', required=False, action='store_true', help='randomize players before making tournament (to avoid predictibility)')
    parser.add_argument('-g', '--game_names_prefix', required=True, help='prefix for name of games')
    parser.add_argument('-p', '--players_file', required=True, help='file with names of players')
    parser.add_argument('-m', '--masters_file', required=True, help='file with names of game master')
    parser.add_argument('-o', '--output_file', required=True, help='resulting file')
    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)
        print(f"Forced random seed to {args.seed}", file=sys.stderr)

    # load players file
    with open(args.players_file, "r", encoding='utf-8') as read_file:
        PLAYERS_DATA = [p.rstrip() for p in read_file.readlines() if p.rstrip()]

    # all players must be different
    assert len(set(PLAYERS_DATA)) == len(PLAYERS_DATA), "Duplicate in players"
    print(f"We have {len(PLAYERS_DATA)} players", file=sys.stderr)
    print("", file=sys.stderr)

    # must be enough = more than 7
    assert len(PLAYERS_DATA) >= len(POWERS), "You need more players to hope success!"

    # make players
    for player_id, _ in enumerate(PLAYERS_DATA):
        name = PLAYERS_DATA[player_id]
        player = Player(name)
        PLAYERS.append(player)

    # make games (as many as players)
    for game_id, _ in enumerate(PLAYERS):
        name = f"{args.game_names_prefix}_{game_id+1}"
        game = Game(name)
        GAMES.append(game)

    # load masters file
    with open(args.masters_file, "r", encoding='utf-8') as read_file:
        MASTERS_DATA = [m.rstrip() for m in read_file.readlines() if m.rstrip()]

    assert len(set(MASTERS_DATA)) == len(MASTERS_DATA), "Duplicate in masters"
    print(f"We have {len(MASTERS_DATA)} masters", file=sys.stderr)
    print("", file=sys.stderr)

    # must be safe = less than  7
    assert len(MASTERS_DATA) < len(POWERS), "Number of masters is unsafe"

    player_table = {p.name: p for p in PLAYERS}
    masters_list = []
    for master_name in MASTERS_DATA:
        # a game master may not be playing
        if master_name not in player_table:
            print(f"Game master {master_name} is not playing !", file=sys.stderr)
            player = Player(master_name)
        else:
            print(f"Game master {master_name} is playing !", file=sys.stderr)
            player = player_table[master_name]
        masters_list.append(player)
    print("", file=sys.stderr)

    if args.randomize:
        print("Randomizing players !", file=sys.stderr)
        print("", file=sys.stderr)
        random.shuffle(PLAYERS)

    # if badly designed, we may calculate for too long
    # so this allows us to interrupt gracefully
    try:
        status = try_and_error()
    except KeyboardInterrupt:
        panic()

    assert status, "Failed to make tournament !"

    # assign game masters to games
    master_game_table: typing.Dict[Game, Player] = {}
    for game in GAMES:
        master_select = sorted(masters_list, key=lambda m: len([g for g in GAMES if g in master_game_table and master_game_table[g] == m]))
        for master_poss in master_select:
            if not game.player_in_game(master_poss):
                master = master_poss
                break
        master_game_table[game] = master

    for master in masters_list:
        print(f"Game master {master.name} has {len([g for g in GAMES if master_game_table[g] == master])} games!", file=sys.stderr)
    print("", file=sys.stderr)

    # output stuff
    with open(args.output_file, "w", encoding='utf-8') as read_file:
        for game in GAMES:
            read_file.write(f"{game.name};{master_game_table[game].name};{game.list_players()}\n")

    sys.exit(0)


if __name__ == '__main__':
    main()
