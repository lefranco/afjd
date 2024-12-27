#!/usr/bin/env python3

"""
Checks a solution for the problem of allocating players in a Diplomacy tournament.

For 1000 players takes 35 seconds on an average laptop.
"""


import argparse
import collections
import csv
import pathlib
import sys
import typing

PLAYERS_VARIANT = 0


class Game:
    """a game."""

    def __init__(self, name: str) -> None:
        """Construct."""
        self._name = name
        self._master: typing.Optional[Player] = None
        self._allocation: typing.Dict[int, Player] = {}

    def put_player_in(self, role: int, player: 'Player') -> None:
        """Put the player in this game."""
        assert isinstance(role, int), "Internal error: role should be an int"
        assert 1 <= role <= PLAYERS_VARIANT, "Internal error: role should be in range"

        assert isinstance(player, Player), "Internal error: player should be a Player"

        assert role not in self._allocation, "Internal error: role in game should be free"
        assert player not in self._allocation.values(), "Internal error: player should not be in game already"

        # increase interaction
        for other_player in self._allocation.values():
            INTERACTION[frozenset([player, other_player])] += 1

        self._allocation[role] = player

    def plays_in(self, player: 'Player') -> bool:
        """Check player is in game."""
        return player in self._allocation.values()

    def is_complete(self) -> bool:
        """Check game is complete."""
        return len(self._allocation) == PLAYERS_VARIANT

    def put_master(self, master: 'Player') -> None:
        """Put master."""
        # Check no GM plays in its game
        assert not self.plays_in(master), f"{master} plays in game {self._name} s/he masters !"

        self._master = master

    def list_players(self) -> str:
        """Display list of players of the game."""
        return ";".join([str(self._allocation[r]) for r in range(1, PLAYERS_VARIANT + 1)])

    @property
    def name(self) -> str:
        """Name."""
        return self._name

    @property
    def master(self) -> typing.Optional['Player']:
        """Name."""
        return self._master

    def __str__(self) -> str:
        """Str."""
        return self._name


# list of games
GAMES: typing.List[Game] = []


class Player:
    """a player."""

    def __init__(self, name: str) -> None:
        """Construct."""
        assert isinstance(name, str), "Internal error: name should be str"
        self._name = name
        self._allocation: typing.Dict[int, Game] = {}

    def put_in_game(self, role: int, game: Game) -> None:
        """Put the player in a game."""
        assert isinstance(role, int), "Internal error: number should be int"
        assert 1 <= role <= PLAYERS_VARIANT, "Internal error: role should be in range"

        assert isinstance(game, Game)

        assert role not in self._allocation, "Internal error: role for player should be free"
        self._allocation[role] = game

    def games_in(self) -> typing.List[Game]:
        """Extract games the player plays in."""
        return list(self._allocation.values())

    @property
    def name(self) -> str:
        """Name."""
        return self._name

    def __str__(self) -> str:
        """Str."""
        return self._name


# list of players
PLAYERS: typing.List[Player] = []

# says how many times two players are in same game
INTERACTION: typing.Counter[typing.FrozenSet[Player]] = collections.Counter()


def evaluate() -> typing.Tuple[int, int]:
    """Evaluate how good we have reached."""
    worst = max(INTERACTION.values())
    worst_number = len([cp for cp in INTERACTION if INTERACTION[cp] == worst])
    return worst, worst_number


def main() -> None:
    """Do main."""
    global PLAYERS_VARIANT

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--players_variant', required=True, type=int, help='number of players per game in the variant')
    parser.add_argument('-i', '--tournament_file', required=True, help='file tournament description')
    parser.add_argument('-p', '--print', action='store_true', required=False, help='output description for checking')
    args = parser.parse_args()

    PLAYERS_VARIANT = args.players_variant

    player_table: typing.Dict[str, Player] = {}

    # load players file
    with pathlib.Path(args.tournament_file).open(encoding='utf-8') as csv_read_file:
        csv_reader = csv.reader(csv_read_file, delimiter=';')

        for row in csv_reader:
            name = row[0]
            name = name.replace(' ', '_')

            # Check all games are unique
            assert name not in {g.name for g in GAMES}, f"Duplicate name for game {name}"

            game = Game(name)
            GAMES.append(game)

            for role, player_name in enumerate(row[1:]):

                # find or create player
                if player_name in player_table:
                    player = player_table[player_name]
                else:
                    player = Player(player_name)
                    PLAYERS.append(player)
                    player_table[player_name] = player

                # assign player (not master)
                if role == 0:
                    master = player
                else:
                    game.put_player_in(role, player)
                    player.put_in_game(role, game)

            game.put_master(master)

    # check all game are full
    for game in GAMES:
        assert game.is_complete(), f"game {game.name} misses at least one player"

    worst, worst_number = evaluate()
    print(f"We have {worst_number} occurences of two players interacting {worst} times")

    print("Interactions more than once: ")
    for player1, player2 in [cp for cp in INTERACTION if INTERACTION[cp] > 1]:
        games = set(player1.games_in()) & set(player2.games_in())
        print(f"{player1} and {player2} in games {' '.join([g.name for g in games])}")

    # output stuff
    if args.print:
        for game in GAMES:
            print(f"{game.name};{game.master};{game.list_players()}")


if __name__ == '__main__':

    main()

    sys.exit(0)
