#!/usr/bin/env python3


"""
File : allocate.py.

Solves the problem of allocating players in a Diplomacy tournament
For 1000 players takes 54 seconds on a good laptop (linux)
Limited to 275 players on windows
"""

import argparse
import collections
import cProfile
import faulthandler
import itertools
import math
import pathlib
import pstats
import random
import signal
import sys
import time
import types
import typing

PROFILE = False

# as extracted from input file
PLAYERS_DATA: typing.List[str] = []
MASTERS_DATA: typing.List[str] = []

INTERRUPT = False


def user_interrupt(_: int, __: typing.Optional[types.FrameType]) -> None:
    """user_interrupt."""
    global INTERRUPT

    print("CTRL+C was pressed.")

    if INTERRUPT:
        print("Ok, stop everything!")
        sys.exit(-1)

    INTERRUPT = True


PLAYERS_VARIANT = 0


class Game:
    """a game."""

    def __init__(self, name: str) -> None:
        """Construct."""
        self._name = name
        self._allocation: typing.Dict[int, Player] = {}

    def put_player_in(self, role: int, player: 'Player') -> None:
        """Put the player in this game."""
        assert isinstance(role, int), "Internal error: role should be an int"
        assert 0 <= role < PLAYERS_VARIANT, "Internal error: role should be in range"

        assert isinstance(player, Player), "Internal error: player should be a Player"

        assert role not in self._allocation, "Internal error: role in game should be free"
        assert player not in self._allocation.values(), "Internal error: player should not be in game already"

        # increase interaction
        for other_player in self._allocation.values():
            INTERACTION[frozenset([player, other_player])] += 1

        self._allocation[role] = player

    def take_player_out(self, role: int, player: 'Player') -> None:
        """Take the player out of this game."""
        assert isinstance(role, int), "Internal error: role should be an int"
        assert 0 <= role < PLAYERS_VARIANT, "Internal error: role should be in range"

        assert isinstance(player, Player), "Internal error: player should be a Player"
        assert player in self._allocation.values(), "Internal error: player should be in game already"

        assert role in self._allocation, "Internal error: role in game should be in"
        del self._allocation[role]

        # decrease interaction
        for other_player in self._allocation.values():
            INTERACTION[frozenset([player, other_player])] -= 1

    def is_player_in_game(self, player: 'Player') -> bool:
        """Tell if player plays in this game."""
        assert isinstance(player, Player), "Internal error: player should be a Player"
        return player in self._allocation.values()

    def players_in_game(self) -> typing.List['Player']:
        """Extract players allocated in this game."""
        return list(self._allocation.values())

    def has_role_in_game(self, role: int) -> bool:
        """Say if there is someone with this role in the game."""
        assert 0 <= role < PLAYERS_VARIANT, "Internal error: role should be in range"
        return role in self._allocation

    def is_complete(self) -> bool:
        """Say if the game is complete."""
        return len(self._allocation) == PLAYERS_VARIANT

    def list_players(self) -> str:
        """Display list of players of the game."""
        return ";".join([str(self._allocation.get(r, "_")) for r in range(PLAYERS_VARIANT)])

    @property
    def name(self) -> str:
        """Name."""
        return self._name

    def __str__(self) -> str:
        """Str."""
        return self._name


# list of games
GAMES: typing.List[Game] = []


class Player:
    """a player."""

    def __init__(self, name: str, number: int, *, playing: bool) -> None:
        """Construct."""
        assert isinstance(name, str), "Internal error: name should be str"
        self._name = name
        assert isinstance(number, int), "Internal error: number should be int"
        self._number = number
        self._allocation: typing.Dict[int, Game] = {}
        self._fully_allocated = False
        self._is_master = False
        self._playing = playing

    def put_in_game(self, role: int, game: Game) -> None:
        """Put the player in a game."""
        assert isinstance(role, int), "Internal error: number should be int"
        assert 0 <= role < PLAYERS_VARIANT, "Internal error: role should be in range"

        assert isinstance(game, Game)

        assert role not in self._allocation, "Internal error: role for player should be free"
        self._allocation[role] = game

    def remove_from_game(self, role: int, game: Game) -> None:
        """Remove the player from a game."""
        assert isinstance(role, int), "Internal error: role for player should be int"
        assert 0 <= role < PLAYERS_VARIANT, "Internal error: role should be in range"

        assert isinstance(game, Game), "Internal error: game for player should be a Game"

        assert role in self._allocation, "Internal error: role for player should be in"
        del self._allocation[role]

    def games_in(self) -> typing.List[Game]:
        """Games the player plays in."""
        return list(self._allocation.values())

    def has_role(self, role: int) -> bool:
        """Say if the players has this role."""
        assert 0 <= role < PLAYERS_VARIANT, "Internal error: role should be in range"
        return role in self._allocation

    def game_where_has_role(self, role: int) -> Game:
        """Get qame where the players has this role."""
        assert 0 <= role < PLAYERS_VARIANT, "Internal error: role should be in range"
        assert role in self._allocation, "Internal error: player should have the role"
        return self._allocation[role]

    @property
    def name(self) -> str:
        """Name."""
        return self._name

    @property
    def number(self) -> int:
        """Number."""
        return self._number

    @property
    def is_master(self) -> bool:
        """is_master."""
        return self._is_master

    @is_master.setter
    def is_master(self, is_master: bool) -> None:
        """Setter."""
        self._is_master = is_master

    def __str__(self) -> str:
        """Str."""
        return self._name


# list of players
PLAYERS: typing.List[Player] = []

# list of masters
MASTERS: typing.List[Player] = []

# says how many times two players are in same game
INTERACTION: typing.Counter[typing.FrozenSet[Player]] = collections.Counter()

# to be able to undo
SWAPS: typing.List[typing.Tuple[int, Player, Player, Game, Game]] = []
BEST_SWAPS: typing.List[typing.Tuple[int, Player, Player, Game, Game]] = []


def try_and_error(depth: int) -> bool:
    """try_and_error."""
    print(f"{depth // PLAYERS_VARIANT:5} ", end='\r', flush=True)

    # find a game where to fill up
    game = None
    for game_poss in GAMES:
        if not game_poss.is_complete():
            game = game_poss
            break
    else:
        # we are done
        return True

    # for linter
    assert game is not None

    # find a role
    role = None
    for role_poss in range(PLAYERS_VARIANT):
        # game already has someone for this role
        if not game.has_role_in_game(role_poss):
            role = role_poss
            break

    assert role is not None, "Internal error : game has role or not!?"

    # objective acceptable players : those not already in the game and do not already have the role
    acceptable_players = [p for p in PLAYERS if not p.has_role(role) and not game.is_player_in_game(p)]

    # there cannot be all game masters in same game (because it will not be possible to master the game)
    if not any(p for p in MASTERS if not game.is_player_in_game(p)):
        return False

    # players will be selected according to:
    # 1) fewest interactions with the ones in the game
    # 2) players which are in more games (more efficient than less games for some reason)
    # 3) identifier of player (for readability)

    players_sorted = sorted(acceptable_players,
                            key=lambda p: (sum([INTERACTION[frozenset([pp, p])] for pp in game.players_in_game()]),  # type: ignore[union-attr]
                                           len(p.games_in()),
                                           p.number))

    # find a player to put in
    for player in players_sorted:

        game.put_player_in(role, player)
        player.put_in_game(role, game)

        # if we fail, we try otherwise!
        if try_and_error(depth + 1):
            return True

        player.remove_from_game(role, game)
        game.take_player_out(role, player)

    return False


def evaluate() -> typing.Tuple[int, int, typing.List[int]]:
    """Evaluate how good we have reached."""
    worst = max(INTERACTION.values())
    worst_number = len([cp for cp in INTERACTION if INTERACTION[cp] == worst])
    worst_dump = [p.number for g in GAMES for p in g.players_in_game()]
    return worst, worst_number, worst_dump


def perform_swap(role: int, player1: Player, player2: Player, game1: Game, game2: Game, *, reverse: bool) -> None:
    """perform_swap."""
    if reverse:
        player1, player2 = player2, player1

    # for games
    game1.take_player_out(role, player1)
    game2.take_player_out(role, player2)
    game1.put_player_in(role, player2)
    game2.put_player_in(role, player1)

    # for players
    player1.remove_from_game(role, game1)
    player2.remove_from_game(role, game2)
    player1.put_in_game(role, game2)
    player2.put_in_game(role, game1)


REF_WORST = 0
REF_WORST_NUMBER = 0
REF_WORST_DUMP: typing.List[int] = []


def hill_climb() -> bool:
    """hill_climb."""
    global REF_WORST
    global REF_WORST_NUMBER
    global REF_WORST_DUMP

    while True:

        worst, worst_number, worst_dump = evaluate()
        if (worst, worst_number, worst_dump) < (REF_WORST, REF_WORST_NUMBER, REF_WORST_DUMP):
            print(f"{worst:2} ({worst_number:5})", end='\r', flush=True)
            REF_WORST, REF_WORST_NUMBER, REF_WORST_DUMP = worst, worst_number, worst_dump

        # are we done
        if worst == 1:
            return True

        # find the candidates
        candidates = set().union(*[cp for cp in INTERACTION if INTERACTION[cp] > 1])
        assert candidates, "Internal error : no candidates "

        if len(candidates) != len(PLAYERS):
            complements = set(PLAYERS) - set(candidates)
            # take one from conflicting and one from not conflicting
            couples = list(itertools.product(candidates, complements))
        else:
            # take any two from those conflicting
            couples = list(itertools.combinations(candidates, 2))

        # works better with random
        random.shuffle(couples)

        changed = False
        for player1, player2 in couples:

            roles = list(range(PLAYERS_VARIANT))
            random.shuffle(roles)

            # find a swap
            for role in roles:

                game1 = player1.game_where_has_role(role)
                game2 = player2.game_where_has_role(role)

                assert game1 != game2, "Internal error hill climb 1"

                if game1.is_player_in_game(player2) or game2.is_player_in_game(player1):
                    continue

                assert game1 not in player2.games_in(), "Internal error hill climb 21"
                assert game2 not in player1.games_in(), "Internal error hill climb 22"

                # try the swap
                perform_swap(role, player1, player2, game1, game2, reverse=False)

                # do we accept ?
                rejected = False

                # there cannot be all game masters in same game (because it will not be possible to master the game)
                if not any(p for p in MASTERS if not game1.is_player_in_game(p)):
                    rejected = True
                if not any(p for p in MASTERS if not game2.is_player_in_game(p)):
                    rejected = True

                if not rejected:

                    # evaluate
                    new_worst, new_worst_number, new_worst_dump = evaluate()

                    # do we accept ? must improve...
                    if (new_worst, new_worst_number, new_worst_dump) < (worst, worst_number, worst_dump):
                        # memorize the swap
                        SWAPS.append((role, player1, player2, game1, game2))
                        changed = True
                        break

                # not accepted : put it back
                perform_swap(role, player1, player2, game1, game2, reverse=True)

            if changed:
                break

        if not changed:
            return False


def main() -> None:
    """Do main."""
    start_time = time.time()

    global PLAYERS_DATA
    global MASTERS_DATA
    global SWAPS
    global BEST_SWAPS

    global REF_WORST
    global REF_WORST_NUMBER
    global REF_WORST_DUMP

    global PLAYERS_VARIANT

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--players_variant', required=True, type=int, help='number of players per game in the variant')
    parser.add_argument('-p', '--players_file', required=True, help='file with names of players')
    parser.add_argument('-m', '--masters_file', required=True, help='file with names of game master')
    parser.add_argument('-g', '--game_names_prefix', required=True, help='prefix for name of games')
    parser.add_argument('-o', '--output_file', required=True, help='resulting file')
    parser.add_argument('-s', '--show', required=False, action='store_true', help='show worst interactions')
    parser.add_argument('-d', '--deterministic', required=False, action='store_true', help='make it deterministic')
    parser.add_argument('-l', '--limit', required=False, type=int, help='limit to first players of the file (for testing)')
    args = parser.parse_args()

    # make it deterministic if requested
    if args.deterministic:
        random.seed(0)

    # load players file
    with pathlib.Path(args.players_file).open(encoding='utf-8') as read_file:
        PLAYERS_DATA = [p.rstrip() for p in read_file if p.rstrip()]

    # for testing purpose we may limit to fewer players
    if args.limit:
        assert args.limit <= len(PLAYERS_DATA), "Please set the limit to less than the number of players in file"
        PLAYERS_DATA = PLAYERS_DATA[:args.limit]

    # all players must be different
    assert len(set(PLAYERS_DATA)) == len(PLAYERS_DATA), "Duplicate in players"

    PLAYERS_VARIANT = args.players_variant

    # must be enough players for at least one game
    assert len(PLAYERS_DATA) >= PLAYERS_VARIANT, "With so few players you wont make a single game!"

    # make it harder to guess
    random.shuffle(PLAYERS_DATA)

    # make players
    for player_id, _ in enumerate(PLAYERS_DATA):
        name = PLAYERS_DATA[player_id]
        player = Player(name, player_id, playing=True)
        PLAYERS.append(player)

    # check game identifiers prefix
    assert args.game_names_prefix.isidentifier(), "Game prefix is incorrect, should look like an identifier"

    # make games (as many as players)
    size = math.floor(math.log10(len(PLAYERS))) + 1
    for game_id, _ in enumerate(PLAYERS):
        name = f"{args.game_names_prefix}_{game_id+1:0{size}}"
        game = Game(name)
        GAMES.append(game)

    # load masters file
    with pathlib.Path(args.masters_file).open(encoding='utf-8') as read_file:
        MASTERS_DATA = [m.rstrip() for m in read_file if m.rstrip()]

    assert len(set(MASTERS_DATA)) == len(MASTERS_DATA), "Duplicate in masters"

    # must be more than 1
    assert len(MASTERS_DATA) >= 1, "There must be at least one master for all these games"

    player_table = {p.name: p for p in PLAYERS}
    for master_name in MASTERS_DATA:
        # a game master be playing or not
        if master_name not in player_table:
            print(f"Game master {master_name} is not playing!")
            player = Player(master_name, -1, playing=False)
        else:
            print(f"Game master {master_name} is playing!")
            player = player_table[master_name]
            assert player.name == master_name, "Internal error: game master lost his/her name!"
        player.is_master = True
        MASTERS.append(player)

    # Print a recap
    nb_players = len(PLAYERS)
    nb_non_playing_masters = len([p for p in MASTERS if p.number == -1])
    nb_playing_masters = len([p for p in PLAYERS if p.is_master])

    print(f"We have {nb_players} players, {nb_non_playing_masters} non playing masters and {nb_playing_masters} playing masters")
    assert not (nb_non_playing_masters == 0 and nb_playing_masters == 1), "This configuration will no succeed : need more than a single playing master"

    print("Showing <number of games completed>")

    # if badly designed, we may calculate for too long
    # so this allows us to interrupt gracefully
    try:
        status = try_and_error(0)
    except KeyboardInterrupt:
        print("Ok I give up!")
        return

    # end line after displaying depth
    print()

    assert status, "Sorry : failed to make initial tournament! Contact support!"

    print("Press CTRL-C to interrupt")
    print("Showing <number of interactions> (<Number of occurrences>)")

    signal.signal(signal.SIGINT, user_interrupt)

    best_worst, best_worst_number = nb_players, 0

    REF_WORST, REF_WORST_NUMBER, REF_WORST_DUMP = evaluate()
    print(f"{REF_WORST:2} ({REF_WORST_NUMBER:5})", end='\r', flush=True)

    while True:

        # make a climb
        SWAPS = []
        status = hill_climb()
        if status:
            break

        # evaluate
        worst, worst_number, _ = evaluate()

        # is this our best so far ?
        if (worst, worst_number) < (best_worst, best_worst_number):
            best_worst, best_worst_number = worst, worst_number
            BEST_SWAPS = SWAPS.copy()

        # undo everything for a new start
        for (role, player1, player2, game1, game2) in reversed(SWAPS):
            perform_swap(role, player1, player2, game1, game2, reverse=True)

        # we were interrupted
        if INTERRUPT:
            break

    # do not handle CTRL-C any more
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if not status:
        print("Sorry : failed to make a perfect tournament! Contact support!")
        # still apply BEST SWAPS
        for (role, player1, player2, game1, game2) in BEST_SWAPS:
            perform_swap(role, player1, player2, game1, game2, reverse=False)

    # now we assign game masters to games
    master_game_table: typing.Dict[Game, Player] = {}
    for game in GAMES:
        master_select = sorted(MASTERS, key=lambda m: len([g for g in GAMES if g in master_game_table and master_game_table[g] == m]))
        master = None
        for master_poss in master_select:
            if not game.is_player_in_game(master_poss):
                master = master_poss
                break
        assert master, f"Sorry : Could not put a master in game {game}! Contact support!"
        master_game_table[game] = master

    for master in MASTERS:
        print(f"Game master {master.name} has {len([g for g in GAMES if master_game_table[g] == master])} games!")

    worst, worst_number, _ = evaluate()
    if worst > 1:
        print(f"We have {worst_number} occurrences of two players interacting {worst} times")
    else:
        print("Allocation is perfect!")

    if args.show:
        print("Interactions more than once: ")
        for player1, player2 in [cp for cp in INTERACTION if INTERACTION[cp] > 1]:
            games = set(player1.games_in()) & set(player2.games_in())
            print(f"{player1} and {player2} in games {' '.join([g.name for g in games])}")

    # output stuff
    if args.output_file:
        with pathlib.Path(args.output_file).open("w", encoding='utf-8') as write_file:
            for game in GAMES:
                write_file.write(f"{game.name};{master_game_table[game].name};{game.list_players()}\n")
        print(f"File {args.output_file} was written.")

    finished_time = time.time()
    elapsed = finished_time - start_time
    print(f"Elapsed time : {elapsed} sec.")
    sys.exit(0)


if __name__ == '__main__':

    # we make big use of recursion here
    sys.setrecursionlimit(10000)

    # windows can crash if too deep
    faulthandler.enable()

    # this if script too slow and profile it
    PR = cProfile.Profile()
    if PROFILE:
        PR.enable()

    main()

    if PROFILE:
        PR.disable()
        PS = pstats.Stats(PR)
        PS.strip_dirs()
        PS.sort_stats('time')
        PS.print_stats()  # uncomment to have profile stats

    sys.exit(0)
