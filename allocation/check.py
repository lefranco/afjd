#!/usr/bin/env python3


"""
File : check.py

Checks a solution for the problem of allocating players in a Diplomacy tournament
For 1000 players takes 35 seconds on an average laptop
"""

import typing
import argparse
import sys
import collections
import csv

# this is a standard diplomacy constant
POWERS = ['England', 'France', 'Germany', 'Italy', 'Austria', 'Russia', 'Turkey']


class Game:
    """ a game """

    def __init__(self, name: str) -> None:
        self._name = name
        self._allocation: typing.Dict[int, Player] = {}

    def put_player_in(self, role: int, player: 'Player') -> None:
        """ puts the player in this game """

        assert isinstance(role, int), "Internal error: role should be an int"
        assert 0 <= role < len(POWERS), "Internal error: role should be in range"

        assert isinstance(player, Player), "Internal error: player should be a Player"

        assert role not in self._allocation, "Internal error: role in game should be free"
        assert player not in self._allocation.values(), "Internal error: player should not be in game already"

        # increase interaction
        for other_player in self._allocation.values():
            INTERACTION[frozenset([player, other_player])] += 1

        self._allocation[role] = player

    def is_player_in_game(self, player: 'Player') -> bool:
        """ tells if player plays in this game """
        assert isinstance(player, Player), "Internal error: player should be a Player"
        return player in self._allocation.values()

    def players_in_game(self) -> typing.List['Player']:
        """ extracts players allocated in this game """
        return list(self._allocation.values())

    def has_role_in_game(self, role: int) -> bool:
        """ hios the someone with this role in the game ? """
        assert 0 <= role < len(POWERS), "Internal error: role should be in range"
        return role in self._allocation

    def is_complete(self) -> bool:
        """ is the game complete ? """
        return len(self._allocation) == len(POWERS)

    def list_players(self) -> str:
        """ display list of players of the game """
        return ";".join([str(self._allocation[r] if r in self._allocation else "_") for r in range(len(POWERS))])

    @property
    def name(self) -> str:
        """ name """
        return self._name

    def __str__(self) -> str:
        return self._name


# list of games
GAMES: typing.List[Game] = []


class Player:
    """ a player """

    def __init__(self, name: str) -> None:

        assert isinstance(name, str), "Internal error: name should be str"
        self._name = name
        self._allocation: typing.Dict[int, Game] = {}
        self._fully_allocated = False
        self._is_master = False

    def put_in_game(self, role: int, game: Game) -> None:
        """ put the player in a game """

        assert isinstance(role, int), "Internal error: number should be int"
        assert 0 <= role < len(POWERS), "Internal error: role should be in range"

        assert isinstance(game, Game)

        assert role not in self._allocation, "Internal error: role for player should be free"
        self._allocation[role] = game

    def games_in(self) -> typing.List[Game]:
        """ games the player plays in  """
        return list(self._allocation.values())

    def has_role(self, role: int) -> bool:
        """ does the players has this role ? """
        assert 0 <= role < len(POWERS), "Internal error: role should be in range"
        return role in self._allocation

    def game_where_has_role(self, role: int) -> Game:
        """ game where the players has this role ? """
        assert 0 <= role < len(POWERS), "Internal error: role should be in range"
        assert role in self._allocation, "Internal error: player should have the role"
        return self._allocation[role]

    @property
    def name(self) -> str:
        """ name """
        return self._name

    def __str__(self) -> str:
        return self._name


# list of players
PLAYERS: typing.List[Player] = []

# says how many times two players are in same game
INTERACTION: typing.Counter[typing.FrozenSet[Player]] = collections.Counter()


def evaluate() -> typing.Tuple[int, int]:
    """ evaluate how good we have reached """

    worst = max(INTERACTION.values())
    worst_number = len([cp for cp in INTERACTION if INTERACTION[cp] == worst])
    return worst, worst_number


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--tournament_file', required=True, help='file tournament description')
    parser.add_argument('-p', '--print', action='store_true', required=False, help='output description for checking')
    args = parser.parse_args()

    # load players file
    with open(args.tournament_file, "r", encoding='utf-8') as csv_read_file:
        csv_reader = csv.reader(csv_read_file, delimiter=';')

        player_table: typing.Dict[str, Player] = dict()

        for row in csv_reader:
            name = row[0]
            name = name.replace(' ', '_')
            game = Game(name)
            GAMES.append(game)

            for role, player_name in enumerate(row[1:]):
                if player_name in player_table:
                    player = player_table[player_name]
                else:
                    player = Player(player_name)
                    PLAYERS.append(player)
                    player_table[player_name] = player
                game.put_player_in(role, player)
                player.put_in_game(role, game)

    worst, worst_number = evaluate()
    print(f"We have {worst_number} occurences of two players interacting {worst} times")

    print("Interactions more than once: ")
    for player1, player2 in [cp for cp in INTERACTION if INTERACTION[cp] > 1]:
        games = set(player1.games_in()) & set(player2.games_in())
        print(f"{player1} and {player2} in games {' '.join([g.name for g in games])}")

    # output stuff
    if args.print:
        for game in GAMES:
            print(f"{game.name};NA;{game.list_players()}")


if __name__ == '__main__':

    main()

    sys.exit(0)
