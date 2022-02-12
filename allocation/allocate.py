#!/usr/bin/env python3


"""
File : allocate.py

players allocation in a tournament
"""

import typing
import argparse
import sys

# profiling
import cProfile
import pstats

# Set this to true to profile functions (but program will be slow)
PROFILE = False

def panic() -> None:
    """ panic """

    print('You pressed Ctrl+C!')

    if PROFILE:
        PR.disable()
        # stats
        PS = pstats.Stats(PR)
        PS.strip_dirs()
        PS.sort_stats('time')
        PS.print_stats()  # uncomment to have profile stats

    sys.exit(0)


POWERS = ['England', 'France', 'Germany', 'Italy', 'Austria', 'Russia', 'Turkey']

PLAYERS_DATA: typing.List[str] = []
MASTERS_DATA: typing.List[str] = []

GAMES: typing.List['Game'] = []
PLAYERS: typing.List['Player'] = []


class Game:
    """ a game """

    def __init__(self, game_id: int) -> None:
        self._number = game_id
        self._allocation: typing.Dict[int, Player] = {}
        self._complete = False

    def put_player_in(self, role: int, player: 'Player') -> None:
        """ put_player_in """

        assert isinstance(role, int), "role should be an int"
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(player, Player), "player should be a Player"

        assert role not in self._allocation, "role in game should be free"
        self._allocation[role] = player

        self._complete = len(self._allocation) == len(POWERS)

    def take_player_out(self, role: int, player: 'Player') -> None:
        """ put_player """

        assert isinstance(role, int), "role should be an int"
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(player, Player), "player should be a Player"

        assert role in self._allocation, "role in game should be in"
        del self._allocation[role]
        self._complete = False

    def player_in_game(self, player: 'Player') -> bool:
        """ player_in_game """
        return player in self._allocation.values()

    def has_role(self, role: int) -> bool:
        """ has_role """
        return role in self._allocation

    def describe_players(self) -> str:
        """ describe_players """
        return " ".join([f"{POWERS[k]} : {v}" for k, v in self._allocation.items()])

    def complete(self) -> bool:
        """ complete """
        return self._complete

    @property
    def number(self) -> int:
        """ number """
        return self._number

    def __str__(self) -> str:
        return f"Game n°{self._number}"


class Player:
    """ a player """

    def __init__(self, player_id: int) -> None:

        assert isinstance(player_id, int)
        assert 0 <= player_id < len(PLAYERS_DATA), "player_id should be in range"
        self._name = PLAYERS_DATA[player_id]
        self._allocation: typing.Dict[int, Game] = {}
        self._fully_allocated = False

    def put_in_game(self, role: int, game: Game) -> None:
        """ put_in_game """

        assert isinstance(role, int)
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(game, Game)

        assert role not in self._allocation, "role for player should be free"
        self._allocation[role] = game
        self._fully_allocated = len(self._allocation) == len(POWERS)

    def remove_from_game(self, role: int, game: Game) -> None:
        """ remove_from_game """

        assert isinstance(role, int)
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(game, Game)

        assert role in self._allocation, "role for player should be in"
        del self._allocation[role]
        self._fully_allocated = False

    def fully_allocated(self) -> bool:
        """ fully_allocated """
        return self._fully_allocated

    def has_role(self, role: int) -> bool:
        """ has_role """
        return role in self._allocation

    def __str__(self) -> str:
        return self._name


BEST_GAMES_COMPLETED = 0

def attempt() -> bool:
    """ attempt """

    #  print("attempt()")

    # find a game where to fill up
    game = None
    for game_poss in GAMES:
        if not game_poss.complete():
            game = game_poss
            break

    if not game:
        # we are done
        return True

    global BEST_GAMES_COMPLETED
    completed_now = game.number
    if completed_now > BEST_GAMES_COMPLETED:
        print(f"{completed_now=}", file=sys.stderr)
        BEST_GAMES_COMPLETED = completed_now

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
    for player_poss in PLAYERS:

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
        if attempt():
            return True

        #  print(f"remove {player} from {game}")
        player.remove_from_game(role, game)
        game.take_player_out(role, player)

    return False


def main() -> None:
    """ main """

    sys.setrecursionlimit(10000)

    global PLAYERS_DATA
    global MASTERS_DATA

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--players_file', required=True, help='names of players')
    parser.add_argument('-m', '--masters_file', required=True, help='names of game master')
    args = parser.parse_args()

    # load players file
    with open(args.players_file, "r", encoding='utf-8') as read_file:
        PLAYERS_DATA = [p.rstrip() for p in read_file.readlines()]

    # all players must be different
    assert len(set(PLAYERS_DATA)) == len(PLAYERS_DATA), "Duplicate in players"

    # must divide 7
    assert len(PLAYERS_DATA) % len(POWERS) == 0, "Number of players does not allow success"

    # make players
    for player_id, _ in enumerate(PLAYERS_DATA):
        player = Player(player_id)
        PLAYERS.append(player)

    # make games (as many as players)
    for game_id, _ in enumerate(PLAYERS):
        game = Game(game_id)
        GAMES.append(game)

    # load masters file
    with open(args.masters_file, "r", encoding='utf-8') as read_file:
        MASTERS_DATA = [m.rstrip() for m in read_file.readlines()]

    print(f"{MASTERS_DATA=}")
    assert len(set(MASTERS_DATA)) == len(MASTERS_DATA), "Duplicate in masters"

    try:
        status = attempt()
    except KeyboardInterrupt:
        panic()

    assert status, "Failed to make tournament !"

    # show stuff
    print("========================")
    for game in GAMES:
        print(f"{game} : {game.describe_players()}")


if __name__ == '__main__':

    # this if script too slow and profile it
    if PROFILE:
        PR = cProfile.Profile()
        PR.enable()  # uncomment to have profile stats

    main()

    if PROFILE:
        PR.disable()
        # stats
        PS = pstats.Stats(PR)
        PS.strip_dirs()
        PS.sort_stats('time')
        PS.print_stats()  # uncomment to have profile stats

    sys.exit(0)
