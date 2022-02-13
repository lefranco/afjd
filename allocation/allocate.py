#!/usr/bin/env python3


"""
File : allocate.py

Solves the problem of allocating players in a Diplomacy tournament
"""

import typing
import argparse
import sys
import collections
import random


# this is a standard diplomacy constant
POWERS = ['England', 'France', 'Germany', 'Italy', 'Austria', 'Russia', 'Turkey']

# as extracted from input file
PLAYERS_DATA: typing.List[str] = []
MASTERS_DATA: typing.List[str] = []


def panic() -> None:
    """ panic """
    print('You pressed Ctrl+C!')
    sys.exit(1)


class Game:
    """ a game """

    def __init__(self, name: str) -> None:
        self._name = name
        self._allocation: typing.Dict[int, Player] = {}

    def put_player_in(self, role: int, player: 'Player') -> None:
        """ puts the player in this game """

        assert isinstance(role, int), "role should be an int"
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(player, Player), "player should be a Player"

        assert role not in self._allocation, "role in game should be free"
        assert player not in self._allocation.values(), "player should not be in game already"

        # increase interaction
        for other_player in self._allocation.values():
            INTERACTION[frozenset([player, other_player])] += 1

        self._allocation[role] = player

    def take_player_out(self, role: int, player: 'Player') -> None:
        """ takes the player ou of this game """

        assert isinstance(role, int), "role should be an int"
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(player, Player), "player should be a Player"
        assert player in self._allocation.values(), "player should be in game already"

        assert role in self._allocation, "role in game should be in"
        del self._allocation[role]

        # decrease interaction
        for other_player in self._allocation.values():
            INTERACTION[frozenset([player, other_player])] -= 1

    def is_player_in_game(self, player: 'Player') -> bool:
        """ tells if player plays in this game """
        assert isinstance(player, Player), "player should be a Player"
        return player in self._allocation.values()

    def players_in_game(self) -> typing.List['Player']:
        """ players_in_game """
        return list(self._allocation.values())

    def has_role_in_game(self, role: int) -> bool:
        """ has_role """
        assert 0 <= role < len(POWERS), "role should be in range"
        return role in self._allocation

    def is_complete(self) -> bool:
        """ is the game complete ? """
        return len(self._allocation) == len(POWERS)

    def role_in_game(self, player: 'Player') -> int:
        """ tells which role this players has i nthis game """
        assert isinstance(player, Player), "player should be a Player"
        for role, player2 in self._allocation.items():
            if player2 == player:
                return role
        assert False, "Internal error in role_in_game()"
        return -1

    def player_with_role(self, role: int) -> 'Player':
        """ tells which player has this role in this game """
        assert 0 <= role < len(POWERS), "role should be in range"
        assert role in self._allocation, "Internal error in player_with_role()"
        return self._allocation[role]

    def list_players(self) -> str:
        """ display list of players of the game """
        return ";".join([str(self._allocation[r]) for r in range(len(POWERS))])

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

        assert isinstance(name, str)
        self._name = name
        self._allocation: typing.Dict[int, Game] = {}
        self._fully_allocated = False

    def put_in_game(self, role: int, game: Game) -> None:
        """ put the player in a game """

        assert isinstance(role, int)
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(game, Game)

        assert role not in self._allocation, "role for player should be free"
        self._allocation[role] = game

    def remove_from_game(self, role: int, game: Game) -> None:
        """ remove the player from a game """

        assert isinstance(role, int)
        assert 0 <= role < len(POWERS), "role should be in range"

        assert isinstance(game, Game)

        assert role in self._allocation, "role for player should be in"
        del self._allocation[role]

    def games_in(self) -> typing.Set[Game]:
        """ set of games the player plays in  """
        return set(self._allocation.values())

    def is_fully_allocated(self) -> bool:
        """ is the player fully allocated ? """
        return len(self._allocation) == len(POWERS)

    def has_role(self, role: int) -> bool:
        """ does the players has this role ? """
        assert 0 <= role < len(POWERS), "role should be in range"
        return role in self._allocation

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


def try_and_error() -> bool:
    """ try_and_error """

    #  print("try_and_error()")

    # find a game where to fill up
    game = None
    for game_poss in GAMES:
        if not game_poss.is_complete():
            game = game_poss
            break

    if game is None:
        # we are done
        return True

    assert game is not None

    # find a role
    role = None
    for role_poss in range(len(POWERS)):
        # game already has someone for this role
        if not game.has_role_in_game(role_poss):
            role = role_poss
            break

    if role is None:
        assert False, "Internal error : game has role or not !?"

    # players will be selected according to:
    # 1) fewest interactions with the ones in the game
    # 2) players which are in fewest games
    players_sorted = sorted(PLAYERS, key=lambda p: (sum([INTERACTION[frozenset([pp, p])] for pp in game.players_in_game()]), len(p.games_in())))  # type: ignore

    # find a player to put in
    for player_poss in players_sorted:

        # player already has a game for this role
        if player_poss.has_role(role):
            continue

        # player is already in this game
        if game.is_player_in_game(player_poss):
            continue

        player = player_poss

        # player_poss
        #  print(f"put {player} in {game}")

        game.put_player_in(role, player)
        player.put_in_game(role, game)

        # if we fail, we try otherwise !
        if try_and_error():
            return True

        #  print(f"remove {player} from {game}")
        player.remove_from_game(role, game)
        game.take_player_out(role, player)

    return False


def improve_interactions() -> None:
    """ improve_interactions """

    assert False, "Sorry, improve interactions is just not working... (yet ?)"

    # try to improve interactivity between players
    n = 0
    while True:

        # get the interactions between players of more than 1 (bad ones)
        bad_interactions = [i[0] for i in INTERACTION.items() if i[1] > 1]

        # nothing to do
        if not bad_interactions:
            break

        print(f"we have now {len(bad_interactions)} bad interactions")

        # let's kill one of them
        changed = False
        for interaction in bad_interactions:

            # common games between these players
            player1 = list(interaction)[0]
            player2 = list(interaction)[1]

            common_games = player1.games_in() & player2.games_in()
            assert len(common_games) > 1, "Interaction is bad or not !?"

            # try to make a swap by moving player1
            for game in common_games:

                role = game.role_in_game(player1)

                for other_game in GAMES:

                    if other_game == game:
                        continue
                    player3 = other_game.player_with_role(role)

                    if player3 == player1:
                        continue

                    if game.is_player_in_game(player3) or other_game.is_player_in_game(player1):
                        continue

                    # swap
                    # in games
                    game.take_player_out(role, player1)
                    other_game.take_player_out(role, player3)
                    other_game.put_player_in(role, player1)
                    game.put_player_in(role, player3)

                    # for players
                    player1.remove_from_game(role, game)
                    player3.remove_from_game(role, other_game)
                    player3.put_in_game(role, game)
                    player1.put_in_game(role, other_game)

                    n += 1
                    print(f"{n} swapping {player1}/{game} and {player3}/{other_game} (role={role})\n")
                    with open(f"state_{n}", "w", encoding='utf-8') as write_file:
                        write_file.write(f"swapping {player1}/{game} and {player3}/{other_game} (role={role})\n")
                        for game2 in GAMES:
                            write_file.write(f"{game2.name};xxx;{game2.list_players()}\n")

                    changed = True
                    break

                if changed:
                    break

            if changed:
                break


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
    parser.add_argument('-O', '--optimize', required=False, action='store_true', help='try to optimize interactions')
    parser.add_argument('-S', '--show_interactions', required=False, action='store_true', help='show interactions at the end of the process')

    parser.add_argument('-o', '--output_file', required=True, help='resulting file')
    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)
        print(f"Forced random seed to {args.seed}")

    # load players file
    with open(args.players_file, "r", encoding='utf-8') as read_file:
        PLAYERS_DATA = [p.rstrip() for p in read_file.readlines() if p.rstrip()]

    # all players must be different
    assert len(set(PLAYERS_DATA)) == len(PLAYERS_DATA), "Duplicate in players"
    print(f"We have {len(PLAYERS_DATA)} players")
    print("")

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
    print(f"We have {len(MASTERS_DATA)} masters")
    print("")

    # must be safe = less than  7
    assert len(MASTERS_DATA) < len(POWERS), "Number of masters is unsafe"

    player_table = {p.name: p for p in PLAYERS}
    masters_list = []
    for master_name in MASTERS_DATA:
        # a game master may not be playing
        if master_name not in player_table:
            print(f"Game master {master_name} is not playing !")
            player = Player(master_name)
        else:
            print(f"Game master {master_name} is playing !")
            player = player_table[master_name]
        masters_list.append(player)
    print("")

    if args.randomize:
        print("Randomizing players !")
        print("")
        random.shuffle(PLAYERS)

    # if badly designed, we may calculate for too long
    # so this allows us to interrupt gracefully
    try:
        status = try_and_error()
    except KeyboardInterrupt:
        panic()

    assert status, "Failed to make tournament !"

    # improve interactions (make less)
    if args.optimize:
        improve_interactions()

    # assign game masters to games
    master_game_table: typing.Dict[Game, Player] = {}
    for game in GAMES:
        master_select = sorted(masters_list, key=lambda m: len([g for g in GAMES if g in master_game_table and master_game_table[g] == m]))
        for master_poss in master_select:
            if not game.is_player_in_game(master_poss):
                master = master_poss
                break
        master_game_table[game] = master

    for master in masters_list:
        print(f"Game master {master.name} has {len([g for g in GAMES if master_game_table[g] == master])} games!")
    print("")

    # output stuff
    with open(args.output_file, "w", encoding='utf-8') as write_file:
        for game in GAMES:
            write_file.write(f"{game.name};{master_game_table[game].name};{game.list_players()}\n")

    if args.show_interactions:
        print("Worst interactions  > 1: ")
        for interaction, number in INTERACTION.most_common():
            if number == 1:
                break
            print(f"{list(interaction)[0]} <> {list(interaction)[1]} : {number}")

    sys.exit(0)


if __name__ == '__main__':
    main()
