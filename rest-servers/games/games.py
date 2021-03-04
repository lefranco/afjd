#!/usr/bin/env python3


"""
File : games.py

Handles the games
"""
import typing
import sqlite3
import random

import database
import allocations
import ownerships
import units
import forbiddens
import variants

# need to have a limit in sizes of fields
LEN_NAME_MAX = 20

# for safety
MIN_CYCLES_TO_PLAY = 10

# for safety
MIN_VICTORY_CENTERS = 10

# for the moment
IMPOSED_VARIANT = 'standard'


class Game:
    """ Class for handling a game """

    @staticmethod
    def free_identifier() -> int:
        """ finds an new identifier from database to use for this object """
        database.sql_execute("UPDATE games_counter SET value = value + 1", None, need_result=False)
        counter_found = database.sql_execute("SELECT value FROM games_counter", None, need_result=True)
        counter = counter_found[0][0]  # type: ignore
        return counter  # type: ignore

    @staticmethod
    def find_by_identifier(identifier: int) -> typing.Optional['Game']:
        """ class lookup : finds the object in database from identifier """
        games_found = database.sql_execute("SELECT game_data FROM games where identifier = ?", (identifier,), need_result=True)
        if not games_found:
            return None
        return games_found[0][0]  # type: ignore

    @staticmethod
    def find_by_name(name: str) -> typing.Optional['Game']:
        """ class lookup : finds the object in database from name """
        games_found = database.sql_execute("SELECT game_data FROM games where name = ?", (name,), need_result=True)
        if not games_found:
            return None
        return games_found[0][0]  # type: ignore

    @staticmethod
    def inventory() -> typing.List['Game']:
        """ class inventory : gives a list of all objects in database """
        games_found = database.sql_execute("SELECT game_data FROM games", need_result=True)
        if not games_found:
            return []
        games_list = [g[0] for g in games_found]
        return games_list

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        # create counter
        database.sql_execute("DROP TABLE IF EXISTS games_counter")
        database.sql_execute("CREATE TABLE games_counter (value INT)")
        database.sql_execute("INSERT INTO games_counter (value) VALUES (?)", (0,))

        # create actual table
        database.sql_execute("DROP TABLE IF EXISTS games")
        database.sql_execute("CREATE TABLE games (identifier INT UNIQUE PRIMARY KEY, name STR, game_data game)")
        database.sql_execute("CREATE UNIQUE INDEX name_game ON games (name)")

    def __init__(self, identifier: int, name: str, description: str, variant: str, archive: bool, anonymous: bool, silent: bool, cumulate: bool, fast: bool, deadline: int, speed_moves: int, cd_possible_moves: bool, speed_retreats: int, cd_possible_retreats: bool, speed_adjustments: int, cd_possible_builds: bool, cd_possible_removals: bool, play_weekend: bool, manual: bool, access_code: int, access_restriction_reliability: int, access_restriction_regularity: int, access_restriction_performance: int, current_advancement: int, nb_max_cycles_to_play: int, victory_centers: int, current_state: int) -> None:

        assert isinstance(identifier, int), "identifier must be an int"
        self._identifier = identifier

        assert isinstance(name, str), "name must be a str"
        self._name = name

        self._description = description
        self._variant = variant
        self._archive = archive
        self._anonymous = anonymous
        self._silent = silent
        self._cumulate = cumulate
        self._fast = fast
        self._deadline = deadline
        self._speed_moves = speed_moves
        self._cd_possible_moves = cd_possible_moves
        self._speed_retreats = speed_retreats
        self._cd_possible_retreats = cd_possible_retreats
        self._speed_adjustments = speed_adjustments
        self._cd_possible_builds = cd_possible_builds
        self._cd_possible_removals = cd_possible_removals
        self._play_weekend = play_weekend
        self._manual = manual
        self._access_code = access_code
        self._access_restriction_reliability = access_restriction_reliability
        self._access_restriction_regularity = access_restriction_regularity
        self._access_restriction_performance = access_restriction_performance
        self._current_advancement = current_advancement
        self._nb_max_cycles_to_play = nb_max_cycles_to_play
        self._victory_centers = victory_centers
        self._current_state = current_state

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO games (identifier, name, game_data) VALUES (?, ?, ?)", (self._identifier, self._name, self))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM games WHERE identifier = ?", (self._identifier,))

    def load_json(self, json_dict: typing.Dict[str, typing.Any]) -> bool:
        """ Load from dict - returns True if changed """

        changed = False

        if 'name' in json_dict and json_dict['name'] is not None and json_dict['name'] != self._name:
            self._name = json_dict['name']
            self._name = database.sanitize_field(self._name)
            self._name = self._name[:LEN_NAME_MAX]
            changed = True

        if 'description' in json_dict and json_dict['description'] is not None and json_dict['description'] != self._description:
            self._description = json_dict['description']
            self._description = database.sanitize_field(self._description)
            changed = True

        if 'variant' in json_dict and json_dict['variant'] is not None and json_dict['variant'] != self._variant:
            self._variant = json_dict['variant']
            self._variant = database.sanitize_field(self._variant)
            self._variant = self._variant[:LEN_NAME_MAX]

            # TODO : change later
            if self._variant != IMPOSED_VARIANT:
                self._variant = IMPOSED_VARIANT

            changed = True

        if 'archive' in json_dict and json_dict['archive'] is not None and json_dict['archive'] != self._archive:
            self._archive = json_dict['archive']
            changed = True

        if 'anonymous' in json_dict and json_dict['anonymous'] is not None and json_dict['anonymous'] != self._anonymous:
            self._anonymous = json_dict['variant']
            changed = True

        if 'silent' in json_dict and json_dict['silent'] is not None and json_dict['silent'] != self._silent:
            self._silent = json_dict['silent']
            changed = True

        if 'cumulate' in json_dict and json_dict['cumulate'] is not None and json_dict['cumulate'] != self._cumulate:
            self._cumulate = json_dict['cumulate']
            changed = True

        if 'fast' in json_dict and json_dict['fast'] is not None and json_dict['fast'] != self._fast:
            self._fast = json_dict['fast']
            changed = True

        if 'deadline' in json_dict and json_dict['deadline'] is not None and json_dict['deadline'] != self._deadline:
            self._deadline = json_dict['deadline']

            # safety
            # already done at server level

            changed = True

        if 'speed_moves' in json_dict and json_dict['speed_moves'] is not None and json_dict['speed_moves'] != self._speed_moves:
            self._speed_moves = json_dict['speed_moves']
            # safety
            if self._speed_moves < 0:
                self._speed_moves = 0
            changed = True

        if 'cd_possible_moves' in json_dict and json_dict['cd_possible_moves'] is not None and json_dict['cd_possible_moves'] != self._cd_possible_moves:
            self._cd_possible_moves = json_dict['cd_possible_moves']
            changed = True

        if 'speed_retreats' in json_dict and json_dict['speed_retreats'] is not None and json_dict['speed_retreats'] != self._speed_retreats:
            self._speed_retreats = json_dict['speed_retreats']
            # safety
            if self._speed_retreats < 0:
                self._speed_retreats = 0
            changed = True

        if 'cd_possible_retreats' in json_dict and json_dict['cd_possible_retreats'] is not None and json_dict['cd_possible_retreats'] != self._cd_possible_retreats:
            self._cd_possible_retreats = json_dict['cd_possible_retreats']
            changed = True

        if 'speed_adjustments' in json_dict and json_dict['speed_adjustments'] is not None and json_dict['speed_adjustments'] != self._speed_adjustments:
            self._speed_adjustments = json_dict['speed_adjustments']
            # safety
            if self._speed_adjustments < 0:
                self._speed_adjustments = 0
            changed = True

        if 'cd_possible_builds' in json_dict and json_dict['cd_possible_builds'] is not None and json_dict['cd_possible_builds'] != self._cd_possible_builds:
            self._cd_possible_builds = json_dict['cd_possible_builds']
            changed = True

        if 'cd_possible_removals' in json_dict and json_dict['cd_possible_removals'] is not None and json_dict['cd_possible_removals'] != self._cd_possible_removals:
            self._cd_possible_removals = json_dict['cd_possible_removals']
            changed = True

        if 'play_weekend' in json_dict and json_dict['play_weekend'] is not None and json_dict['play_weekend'] != self._play_weekend:
            self._play_weekend = json_dict['play_weekend']
            changed = True

        if 'manual' in json_dict and json_dict['manual'] is not None and json_dict['manual'] != self._manual:
            self._manual = json_dict['manual']
            changed = True

        if 'access_code' in json_dict and json_dict['access_code'] is not None and json_dict['access_code'] != self._access_code:
            self._access_code = json_dict['access_code']
            # safety
            if self._access_code < 0:
                self._access_code = abs(self._access_code)
            changed = True

        if 'access_restriction_reliability' in json_dict and json_dict['access_restriction_reliability'] is not None and json_dict['access_restriction_reliability'] != self._access_restriction_reliability:
            self._access_restriction_reliability = json_dict['access_restriction_reliability']
            # safety
            if self._access_restriction_reliability < 0:
                self._access_restriction_reliability = 0
            changed = True

        if 'access_restriction_regularity' in json_dict and json_dict['access_restriction_regularity'] is not None and json_dict['access_restriction_regularity'] != self._access_restriction_regularity:
            self._access_restriction_regularity = json_dict['access_restriction_regularity']
            # safety
            if self._access_restriction_regularity < 0:
                self._access_restriction_regularity = 0
            changed = True

        if 'access_restriction_performance' in json_dict and json_dict['access_restriction_performance'] is not None and json_dict['access_restriction_performance'] != self._access_restriction_performance:
            self._access_restriction_performance = json_dict['access_restriction_performance']
            # safety
            if self._access_restriction_performance < 0:
                self._access_restriction_performance = 0
            changed = True

        # current_advancement cannot be set directly

        if 'nb_max_cycles_to_play' in json_dict and json_dict['nb_max_cycles_to_play'] is not None and json_dict['nb_max_cycles_to_play'] != self._nb_max_cycles_to_play:
            self._nb_max_cycles_to_play = json_dict['nb_max_cycles_to_play']
            # safety
            if self._nb_max_cycles_to_play < MIN_CYCLES_TO_PLAY:
                self._nb_max_cycles_to_play = MIN_CYCLES_TO_PLAY
            changed = True

        if 'victory_centers' in json_dict and json_dict['victory_centers'] is not None and json_dict['victory_centers'] != self._victory_centers:
            self._victory_centers = json_dict['victory_centers']
            # safety
            if self._victory_centers < MIN_VICTORY_CENTERS:
                self._victory_centers = MIN_VICTORY_CENTERS
            changed = True

        if 'current_state' in json_dict and json_dict['current_state'] is not None and json_dict['current_state'] != self._current_state:
            self._current_state = json_dict['current_state']
            # safety
            if self._current_state not in [0, 1, 2]:
                self._current_state = 0
            changed = True

        return changed

    def save_json(self) -> typing.Dict[str, typing.Any]:
        """ Save to  dict """

        json_dict = {
            'name': self._name,
            'description': self._description,
            'variant': self._variant,
            'archive': self._archive,
            'anonymous': self._anonymous,
            'silent': self._silent,
            'fast': self._fast,
            'deadline': self._deadline,
            'cumulate': self._cumulate,
            'speed_moves': self._speed_moves,
            'cd_possible_moves': self._cd_possible_moves,
            'speed_retreats': self._speed_retreats,
            'cd_possible_retreats': self._cd_possible_retreats,
            'speed_adjustments': self._speed_adjustments,
            'cd_possible_builds': self._cd_possible_builds,
            'cd_possible_removals': self._cd_possible_removals,
            'play_weekend': self._play_weekend,
            'manual': self._manual,
            'access_code': self._access_code,
            'access_restriction_reliability': self._access_restriction_reliability,
            'access_restriction_regularity': self._access_restriction_regularity,
            'access_restriction_performance': self._access_restriction_performance,
            'current_advancement': self._current_advancement,
            'nb_max_cycles_to_play': self._nb_max_cycles_to_play,
            'victory_centers': self._victory_centers,
            'current_state': self._current_state,
        }
        return json_dict

    def number_allocated(self) -> int:
        """ number_allocated """

        game_id = self.identifier
        allocations_list = allocations.Allocation.list_by_game_id(game_id)
        num = 0
        for _, _, role_id in allocations_list:
            if role_id == 0:
                continue
            num += 1
        return num

    def delete_allocations(self) -> None:
        """  delete allocations """

        game_id = self.identifier
        allocations_list = allocations.Allocation.list_by_game_id(game_id)
        for game_id, player_id, role_id in allocations_list:
            allocation = allocations.Allocation(game_id, player_id, role_id)
            allocation.delete_database()

    def put_role(self, user_id: int, role: int) -> None:
        """ put player/game master in game """

        game_id = self.identifier
        allocation = allocations.Allocation(game_id, user_id, role)
        allocation.update_database()

    def get_role(self, role: int) -> typing.Optional[int]:
        """ retrieves player/game master id of role in game """

        game_id = self.identifier
        allocations_list = allocations.Allocation.list_by_game_id(game_id)
        for _, player_id, role_id in allocations_list:
            if role_id == role:
                return player_id
        return None

    def find_role(self, user: int) -> typing.Optional[int]:
        """ retrieves role of player id in game """

        game_id = self.identifier
        allocations_list = allocations.Allocation.list_by_game_id(game_id)
        for _, player_id, role_id in allocations_list:
            if player_id == user:
                return role_id
        return None

    def create_position(self) -> None:
        """ create position for game in database """

        variant_name = self.variant
        variant_data = variants.Variant.get_by_name(variant_name)
        assert variant_data is not None

        game_id = self.identifier

        # get start centers and put them in database
        start_centers_all_role = variant_data['start_centers']
        role_num = 1
        for start_centers_role in start_centers_all_role:
            for center_num in start_centers_role:
                ownership = ownerships.Ownership(game_id, center_num, role_num)
                ownership.update_database()
            role_num += 1

        # get start units and put them in database
        start_units_all_role = variant_data['start_units']
        role_num = 1
        for start_units_role in start_units_all_role:
            for type_num, start_units in start_units_role.items():
                for zone_num in start_units:
                    unit = units.Unit(game_id, int(type_num), zone_num, role_num, 0, 0)
                    unit.update_database()
            role_num += 1

    def delete_position(self) -> None:
        """ delete position for game in database """

        game_id = self.identifier

        # delete ownerships
        game_ownerships = ownerships.Ownership.list_by_game_id(game_id)
        for _, center_num, role_num in game_ownerships:
            ownership = ownerships.Ownership(game_id, center_num, role_num)
            ownership.delete_database()

        # delete units
        game_units = units.Unit.list_by_game_id(game_id)
        for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
            unit = units.Unit(game_id, type_num, zone_num, role_num, region_dislodged_from_num, fake)
            unit.delete_database()

        # delete forbiddens
        game_forbiddens = forbiddens.Forbidden.list_by_game_id(game_id)
        for _, region_num in game_forbiddens:
            forbidden = forbiddens.Forbidden(game_id, region_num)
            forbidden.delete_database()

    def start(self) -> None:
        """ start the game """

        # at this point we should have enough players

        # we make a random order
        # get variant
        variant_name = self.variant
        variant_data = variants.Variant.get_by_name(variant_name)
        assert variant_data is not None
        # get number of players
        number_players = variant_data['roles']['number']
        role_list = list(range(1, number_players + 1))
        random.shuffle(role_list)

        # we allocate players in the game according to this order
        game_id = self.identifier
        allocations_list = allocations.Allocation.list_by_game_id(game_id)
        num = 0
        for _, player_id, role_id in allocations_list:
            if role_id == 0:
                continue
            role_id = role_list[num]
            num += 1
            allocation = allocations.Allocation(game_id, player_id, role_id)
            allocation.update_database()

    def advance(self) -> None:
        """ advance the game """

        self._current_advancement += 1

    def terminate(self) -> None:
        """ start the game """

        # There does not seem anything to do for the moment here

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def name(self) -> str:
        """ property """
        return self._name

    @property
    def current_state(self) -> int:
        """ property """
        return self._current_state

    @property
    def current_advancement(self) -> int:
        """ property """
        return self._current_advancement

    @property
    def variant(self) -> str:
        """ property """
        return self._variant

    @property
    def deadline(self) -> int:
        """ property """
        return self._deadline

    def __str__(self) -> str:
        return f"name={self._name} variant={self._variant} description={self._description} archive={self._archive} anonymous={self._anonymous} silent={self._silent} cumulate={self._cumulate} fast={self._fast} deadline={self._deadline} speed_moves={self._speed_moves} cd_possible_moves={self._cd_possible_moves} speed_retreats={self._speed_retreats} cd_possible_retreats={self._cd_possible_retreats} speed_adjustments={self._speed_adjustments} cd_possible_builds={self._cd_possible_builds} cd_possible_removals={self._cd_possible_removals} play_weekend={self._play_weekend} manual={self._manual} access_code={self._access_code} access_restriction_reliability={self._access_restriction_reliability} access_restriction_regularity={self._access_restriction_regularity} access_restriction_performance={self._access_restriction_performance} current_advancement={self._current_advancement} nb_max_cycles_to_play={self._nb_max_cycles_to_play} victory_centers={self._victory_centers} current_state={self._current_state}"

    def adapt_game(self) -> bytes:
        """ To put an object in database """
        compressed_description = database.compress_text(self._description)
        return (f"{self._identifier}{database.STR_SEPARATOR}{self._name}{database.STR_SEPARATOR}{compressed_description}{database.STR_SEPARATOR}{self._variant}{database.STR_SEPARATOR}{int(bool(self._archive))}{database.STR_SEPARATOR}{int(bool(self._anonymous))}{database.STR_SEPARATOR}{int(bool(self._silent))}{database.STR_SEPARATOR}{int(bool(self._cumulate))}{database.STR_SEPARATOR}{int(bool(self._fast))}{database.STR_SEPARATOR}{self._deadline}{database.STR_SEPARATOR}{self._speed_moves}{database.STR_SEPARATOR}{int(bool(self._cd_possible_moves))}{database.STR_SEPARATOR}{self._speed_retreats}{database.STR_SEPARATOR}{int(bool(self._cd_possible_retreats))}{database.STR_SEPARATOR}{self._speed_adjustments}{database.STR_SEPARATOR}{int(bool(self._cd_possible_builds))}{database.STR_SEPARATOR}{int(bool(self._cd_possible_removals))}{database.STR_SEPARATOR}{int(bool(self._play_weekend))}{database.STR_SEPARATOR}{int(bool(self._manual))}{database.STR_SEPARATOR}{self._access_code}{database.STR_SEPARATOR}{self._access_restriction_reliability}{database.STR_SEPARATOR}{self._access_restriction_regularity}{database.STR_SEPARATOR}{self._access_restriction_performance}{database.STR_SEPARATOR}{self._current_advancement}{database.STR_SEPARATOR}{self._nb_max_cycles_to_play}{database.STR_SEPARATOR}{self._victory_centers}{database.STR_SEPARATOR}{self._current_state}").encode('ascii')


def convert_game(buffer: bytes) -> Game:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    identifier = int(tab[0].decode())
    name = tab[1].decode()

    compressed_description = tab[2].decode()
    description = database.uncompress_text(compressed_description)

    variant = tab[3].decode()
    archive = bool(int(tab[4].decode()))
    anonymous = bool(int(tab[5].decode()))
    silent = bool(int(tab[6].decode()))
    cumulate = bool(int(tab[7].decode()))
    fast = bool(int(tab[8].decode()))
    deadline = int(tab[9].decode())
    speed_moves = int(tab[10].decode())
    cd_possible_moves = bool(int(tab[11].decode()))
    speed_retreats = int(tab[12].decode())
    cd_possible_retreats = bool(int(tab[13].decode()))
    speed_adjustments = int(tab[14].decode())
    cd_possible_builds = bool(int(tab[15].decode()))
    cd_possible_removals = bool(int(tab[16].decode()))
    play_weekend = bool(int(tab[17].decode()))
    manual = bool(int(tab[18].decode()))
    access_code = int(tab[19].decode())
    access_restriction_reliability = int(tab[20].decode())
    access_restriction_regularity = int(tab[21].decode())
    access_restriction_performance = int(tab[22].decode())
    current_advancement = int(tab[23].decode())
    nb_max_cycles_to_play = int(tab[24].decode())
    victory_centers = int(tab[25].decode())
    current_state = int(tab[26].decode())
    game = Game(identifier, name, description, variant, archive, anonymous, silent, cumulate, fast, deadline, speed_moves, cd_possible_moves, speed_retreats, cd_possible_retreats, speed_adjustments, cd_possible_builds, cd_possible_removals, play_weekend, manual, access_code, access_restriction_reliability, access_restriction_regularity, access_restriction_performance, current_advancement, nb_max_cycles_to_play, victory_centers, current_state)
    return game


# Interfaces between python and database
sqlite3.register_adapter(Game, Game.adapt_game)
sqlite3.register_converter('game', convert_game)


if __name__ == '__main__':
    assert False, "Do not run this script"
