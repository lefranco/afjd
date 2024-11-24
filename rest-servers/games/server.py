#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import collections
import json
import datetime
import time
import argparse
import sys
import threading
import pathlib

import waitress
import flask
import flask_cors
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore
import requests

import mylogger
import populate
import allocations
import ownerships
import units
import imagined_units
import actives
import submissions
import communication_orders
import orders
import forbiddens
import transitions
import reports
import capacities
import games
import contents
import declarations
import messages
import variants
import trainings
import database
import visits
import votes
import notes
import definitives
import incidents
import incidents2
import lowdata
import agree
import tournaments
import groupings
import assignments
import dropouts
import replacements
import exporter
import orders_logger

SESSION = requests.Session()

APP = flask.Flask(__name__)
flask_cors.CORS(APP)
API = flask_restful.Api(APP)

GAME_PARSER = flask_restful.reqparse.RequestParser()
GAME_PARSER.add_argument('name', type=str, required=True)
GAME_PARSER.add_argument('description', type=str, required=False)
GAME_PARSER.add_argument('variant', type=str, required=False)
GAME_PARSER.add_argument('fog', type=int, required=False)
GAME_PARSER.add_argument('archive', type=int, required=False)
GAME_PARSER.add_argument('anonymous', type=int, required=False)
GAME_PARSER.add_argument('nomessage_current', type=int, required=False)
GAME_PARSER.add_argument('nopress_current', type=int, required=False)
GAME_PARSER.add_argument('fast', type=int, required=False)
GAME_PARSER.add_argument('scoring', type=str, required=False)
GAME_PARSER.add_argument('deadline', type=int, required=False)
GAME_PARSER.add_argument('deadline_hour', type=int, required=False)
GAME_PARSER.add_argument('deadline_sync', type=int, required=False)
GAME_PARSER.add_argument('grace_duration', type=int, required=False)
GAME_PARSER.add_argument('speed_moves', type=int, required=False)
GAME_PARSER.add_argument('cd_possible_moves', type=int, required=False)
GAME_PARSER.add_argument('speed_retreats', type=int, required=False)
GAME_PARSER.add_argument('cd_possible_retreats', type=int, required=False)
GAME_PARSER.add_argument('speed_adjustments', type=int, required=False)
GAME_PARSER.add_argument('cd_possible_builds', type=int, required=False)
GAME_PARSER.add_argument('used_for_elo', type=int, required=False)
GAME_PARSER.add_argument('play_weekend', type=int, required=False)
GAME_PARSER.add_argument('manual', type=int, required=False)
GAME_PARSER.add_argument('access_code', type=int, required=False)
GAME_PARSER.add_argument('access_restriction_reliability', type=int, required=False)
GAME_PARSER.add_argument('access_restriction_regularity', type=int, required=False)
GAME_PARSER.add_argument('access_restriction_performance', type=int, required=False)
GAME_PARSER.add_argument('current_advancement', type=int, required=False)
GAME_PARSER.add_argument('nb_max_cycles_to_play', type=int, required=False)
GAME_PARSER.add_argument('current_state', type=int, required=False)
GAME_PARSER.add_argument('just_play', type=int, required=False)
GAME_PARSER.add_argument('game_type', type=int, required=False)
GAME_PARSER.add_argument('force_wait', type=int, required=False)
GAME_PARSER.add_argument('end_voted', type=int, required=False)

# for game parameter alteration
GAME_PARSER2 = flask_restful.reqparse.RequestParser()
GAME_PARSER2.add_argument('name', type=str, required=False)
GAME_PARSER2.add_argument('used_for_elo', type=int, required=False)
GAME_PARSER2.add_argument('fast', type=int, required=False)
GAME_PARSER2.add_argument('archive', type=int, required=False)
GAME_PARSER2.add_argument('game_type', type=int, required=False)
GAME_PARSER2.add_argument('current_state', type=int, required=False)
GAME_PARSER2.add_argument('finished', type=int, required=False)
GAME_PARSER2.add_argument('end_voted', type=int, required=False)
GAME_PARSER2.add_argument('nb_max_cycles_to_play', type=int, required=False)

GAMES_SELECT_PARSER = flask_restful.reqparse.RequestParser()
GAMES_SELECT_PARSER.add_argument('selection', type=str, required=True)

ALLOCATION_PARSER = flask_restful.reqparse.RequestParser()
ALLOCATION_PARSER.add_argument('game_id', type=int, required=True)
ALLOCATION_PARSER.add_argument('player_pseudo', type=str, required=True)
ALLOCATION_PARSER.add_argument('delete', type=int, required=True)

ROLE_ALLOCATION_PARSER = flask_restful.reqparse.RequestParser()
ROLE_ALLOCATION_PARSER.add_argument('game_id', type=int, required=True)
ROLE_ALLOCATION_PARSER.add_argument('player_pseudo', type=str, required=True)
ROLE_ALLOCATION_PARSER.add_argument('role_id', type=int, required=True)
ROLE_ALLOCATION_PARSER.add_argument('delete', type=int, required=True)

RECTIFICATION_PARSER = flask_restful.reqparse.RequestParser()
RECTIFICATION_PARSER.add_argument('ownerships', type=str, required=True)
RECTIFICATION_PARSER.add_argument('units', type=str, required=True)

SUBMISSION_PARSER = flask_restful.reqparse.RequestParser()
SUBMISSION_PARSER.add_argument('role_id', type=int, required=True)
SUBMISSION_PARSER.add_argument('orders', type=str, required=True)
SUBMISSION_PARSER.add_argument('definitive', type=int, required=False)
SUBMISSION_PARSER.add_argument('names', type=str, required=True)
SUBMISSION_PARSER.add_argument('adjudication_names', type=str, required=True)

AGREE_PARSER = flask_restful.reqparse.RequestParser()
AGREE_PARSER.add_argument('role_id', type=int, required=True)
AGREE_PARSER.add_argument('definitive', type=int, required=False)
AGREE_PARSER.add_argument('adjudication_names', type=str, required=True)

FORCE_AGREE_PARSER = flask_restful.reqparse.RequestParser()
FORCE_AGREE_PARSER.add_argument('role_id', type=int, required=True)
FORCE_AGREE_PARSER.add_argument('adjudication_names', type=str, required=True)

COMMUTE_AGREE_PARSER = flask_restful.reqparse.RequestParser()
COMMUTE_AGREE_PARSER.add_argument('now', type=float, required=True)
COMMUTE_AGREE_PARSER.add_argument('adjudication_names', type=str, required=True)

SUBMISSION_PARSER2 = flask_restful.reqparse.RequestParser()
SUBMISSION_PARSER2.add_argument('role_id', type=int, required=True)
SUBMISSION_PARSER2.add_argument('names', type=str, required=True)

SUBMISSION_PARSER3 = flask_restful.reqparse.RequestParser()
SUBMISSION_PARSER3.add_argument('role_id', type=int, required=True)
SUBMISSION_PARSER3.add_argument('orders', type=str, required=True)

ADJUDICATION_PARSER = flask_restful.reqparse.RequestParser()
ADJUDICATION_PARSER.add_argument('names', type=str, required=True)

SIMULATION_PARSER = flask_restful.reqparse.RequestParser()
SIMULATION_PARSER.add_argument('variant_name', type=str, required=True)
SIMULATION_PARSER.add_argument('orders', type=str, required=True)
SIMULATION_PARSER.add_argument('units', type=str, required=True)
SIMULATION_PARSER.add_argument('names', type=str, required=True)

DECLARATION_PARSER = flask_restful.reqparse.RequestParser()
DECLARATION_PARSER.add_argument('role_id', type=int, required=True)
DECLARATION_PARSER.add_argument('role_name', type=str, required=True)
DECLARATION_PARSER.add_argument('anonymous', type=int, required=True)
DECLARATION_PARSER.add_argument('announce', type=int, required=True)
DECLARATION_PARSER.add_argument('content', type=str, required=True)

DECLARATION_PARSER2 = flask_restful.reqparse.RequestParser()
DECLARATION_PARSER2.add_argument('content', type=str, required=True)

MESSAGE_PARSER = flask_restful.reqparse.RequestParser()
MESSAGE_PARSER.add_argument('role_id', type=int, required=True)
MESSAGE_PARSER.add_argument('role_name', type=str, required=True)
MESSAGE_PARSER.add_argument('dest_role_ids', type=str, required=True)
MESSAGE_PARSER.add_argument('content', type=str, required=True)

VISIT_PARSER = flask_restful.reqparse.RequestParser()
VISIT_PARSER.add_argument('role_id', type=int, required=True)

VOTE_PARSER = flask_restful.reqparse.RequestParser()
VOTE_PARSER.add_argument('role_id', type=int, required=True)
VOTE_PARSER.add_argument('value', type=int, required=True)

NOTE_PARSER = flask_restful.reqparse.RequestParser()
NOTE_PARSER.add_argument('role_id', type=int, required=True)
NOTE_PARSER.add_argument('content', type=str, required=True)

TOURNAMENT_PARSER = flask_restful.reqparse.RequestParser()
TOURNAMENT_PARSER.add_argument('name', type=str, required=True)
TOURNAMENT_PARSER.add_argument('game_id', type=int, required=True)

TOURNAMENT_PARSER2 = flask_restful.reqparse.RequestParser()
TOURNAMENT_PARSER2.add_argument('director_id', type=int, required=True)

GROUPING_PARSER = flask_restful.reqparse.RequestParser()
GROUPING_PARSER.add_argument('game_id', type=int, required=True)
GROUPING_PARSER.add_argument('delete', type=int, required=True)

IMAGINE_PARSER = flask_restful.reqparse.RequestParser()
IMAGINE_PARSER.add_argument('type_num', type=int, required=True)
IMAGINE_PARSER.add_argument('zone_num', type=int, required=True)
IMAGINE_PARSER.add_argument('role_num', type=int, required=True)
IMAGINE_PARSER.add_argument('delete', type=int, required=True)

TRAINING_PARSER = flask_restful.reqparse.RequestParser()
TRAINING_PARSER.add_argument('variant_name', type=str, required=True)
TRAINING_PARSER.add_argument('role_id', type=str, required=True)
TRAINING_PARSER.add_argument('orders', type=str, required=True)
TRAINING_PARSER.add_argument('situation', type=str, required=True)
TRAINING_PARSER.add_argument('advancement', type=int, required=True)
TRAINING_PARSER.add_argument('names', type=str, required=True)


# admin id
ADDRESS_ADMIN = 1

# a little welcome message to new games
WELCOME_TO_GAME = "Bienvenue sur cette partie gérée par le serveur de l'AFJD"

# creates some locks for some critical sections (where there can only be one at same time)
# there is one lock per ongoing game
# waitress uses threads, not processes
MOVE_GAME_LOCK_TABLE: typing.Dict[str, threading.Lock] = {}

# to avoid repeat messages/declarations
NO_REPEAT_DELAY_SEC = 15

# account allowed to clear old ratings
COMMUTER_ACCOUNT = "TheCommuter"

# if deadline is more away that this game is dying
CRITICAL_DELAY_DAY = 7

# initial deadline (in days) - how long before considering game has problems getting complete
DELAY_FOR_COMPLETING_GAME_DAYS = 21


def apply_supported(complete_unit_dict: typing.Dict[str, typing.List[typing.List[int]]], unit_dict: typing.Dict[str, typing.List[typing.List[int]]], orders_list: typing.List[typing.List[int]]) -> None:
    """ apply_supported
    this will change the parameters
    """

    # adding units of 'complete_unit_dict' to 'unit_dict' that appear as passive in 'orders_list'

    # the units we know
    known_units_zones = {u[0] for us in unit_dict.values() for u in us}

    # the dangling passives that need to be referenced
    dangling_passives_zones = {o[4] for o in orders_list if o[4] != 0 and o[4] not in known_units_zones}

    # complete table of all units
    complete_unit_reference_table = {u[1]: (r, u[0]) for r, us in complete_unit_dict.items() for u in us}

    # now we can complete the units
    for zone_num in dangling_passives_zones:
        role_num, type_num = complete_unit_reference_table[zone_num]
        if role_num not in unit_dict:
            unit_dict[role_num] = []
        unit_dict[role_num].append([type_num, zone_num])


def apply_visibility(variant_name: str, role_id: int, ownership_dict: typing.Dict[str, int], dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]], unit_dict: typing.Dict[str, typing.List[typing.List[int]]], forbidden_list: typing.List[int], orders_list: typing.List[typing.List[int]], fake_units_list: typing.List[typing.List[int]], seen_regions_list: typing.List[int]) -> None:
    """ apply_visibility
    this will change the parameters
    """

    # load the visibility data
    location = './variants'
    name = f'{variant_name}_visibility'
    extension = '.json'
    full_name_file = pathlib.Path(location, name).with_suffix(extension)
    assert full_name_file.exists(), f"Missing file stating visibilities for {variant_name}"
    with open(full_name_file, 'r', encoding="utf-8") as file_ptr:
        data_json = json.load(file_ptr)
    assert isinstance(data_json, dict), f"File file stating visibilities for {variant_name} is not a dict"
    center2region = data_json['center2region']
    zone2region = data_json['zone2region']
    visibility_table = data_json['visibility_table']

    # what regions do I occupy ?
    occupied_regions = set()
    # where I have a center
    occupied_regions |= {center2region[k] for k, v in ownership_dict.items() if v == int(role_id)}
    # where I have a unit
    occupied_regions |= {zone2region[str(u[1])] for k, v in unit_dict.items() if int(k) == int(role_id) for u in v}
    # where I have a dislodged unit
    occupied_regions |= {zone2region[str(u[1])] for k, v in dislodged_unit_dict.items() if int(k) == int(role_id) for u in v}

    # what regions are adjacent to what I occupy ?
    adjacent_regions = set().union(*(visibility_table[str(r)] for r in occupied_regions))

    # seen region
    seen_regions = occupied_regions | adjacent_regions

    # ownership uses a center
    ownership_dict2 = {k: v for k, v in ownership_dict.items() if center2region[k] in seen_regions}

    # units use a zone
    unit_dict2 = {}
    for role, role_units in unit_dict.items():
        selected = [v for v in role_units if zone2region[str(v[1])] in seen_regions]
        if selected:
            unit_dict2[role] = selected

    dislodged_unit_dict2 = {}
    for role, role_dis_units in dislodged_unit_dict.items():
        selected = [v for v in role_dis_units if zone2region[str(v[1])] in seen_regions]
        if selected:
            dislodged_unit_dict2[role] = selected

    # forbiddens use region
    forbidden_list2 = [f for f in forbidden_list if f in seen_regions]

    # table of unit ownership to detect my orders
    unit_owner = {}
    for role, role_units in unit_dict.items():
        for unit in role_units:
            unit_owner[unit[1]] = int(role)
    for role, role_units in dislodged_unit_dict.items():
        for unit in role_units:
            unit_owner[unit[1]] = int(role)
    for fake in fake_units_list:
        unit_owner[fake[2]] = fake[3]

    # see orders if my order or I see unit, passive (simple)
    orders_list2 = [o for o in orders_list if unit_owner[o[3]] == int(role_id) or (zone2region[str(o[3])] in seen_regions and (o[4] == 0 or zone2region[str(o[4])] in seen_regions) and (o[5] == 0 or zone2region[str(o[5])] in seen_regions))]

    # see fake unit if sees region where it will appear
    fake_units_list2 = [f for f in fake_units_list if zone2region[str(f[2])] in seen_regions]

    # update parameters

    # ownership_dict
    ownership_dict.clear()
    ownership_dict.update(ownership_dict2)

    # unit_dict
    unit_dict.clear()
    unit_dict.update(unit_dict2)

    # dislodged_unit_dict
    dislodged_unit_dict.clear()
    dislodged_unit_dict.update(dislodged_unit_dict2)

    # forbidden_list
    forbidden_list.clear()
    forbidden_list.extend(forbidden_list2)

    # orders_list
    orders_list.clear()
    orders_list.extend(orders_list2)

    # fake_units_list
    fake_units_list.clear()
    fake_units_list.extend(fake_units_list2)

    # seen_list
    seen_regions_list.clear()
    seen_regions_list.extend(seen_regions)


class RepeatPreventer(typing.Dict[typing.Tuple[int, int], float]):
    """ Table """

    def can(self, game_id: int, role_id: int) -> bool:
        """ can """

        if (game_id, role_id) not in self:
            return True

        now = time.time()
        return now > self[(game_id, role_id)] + NO_REPEAT_DELAY_SEC

    def did(self, game_id: int, role_id: int) -> None:
        """ did """

        # do it
        now = time.time()
        self[(game_id, role_id)] = now

        # house clean
        obsoletes = [k for (k, v) in self.items() if v < now - NO_REPEAT_DELAY_SEC]
        for key in obsoletes:
            del self[key]


def notify_last_line(sql_executor: database.SqlExecutor, game_id: int, payload: str) -> None:
    """ notify_last_line """

    # create declaration here
    with POST_DECLARATION_LOCK:

        # create a content
        identifier = contents.Content.free_identifier(sql_executor)
        time_stamp = int(time.time())  # now
        content = contents.Content(identifier, int(game_id), time_stamp, payload)
        content.update_database(sql_executor)

        role_id = -1
        anonymous = False
        announce = True

        # create a declaration linked to the content
        declaration = declarations.Declaration(int(game_id), role_id, anonymous, announce, identifier)
        declaration.update_database(sql_executor)


@API.resource('/trainings-list')
class TrainingsListRessource(flask_restful.Resource):  # type: ignore
    """  TrainingsListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets all possible trainings
        EXPOSED
        """

        mylogger.LOGGER.info("/training-list - GET - getting all trainings")

        trainings_dict = trainings.Training.get_dict()

        data = trainings_dict
        return data, 200


@API.resource('/trainings/<name>')
class TrainingIdentifierRessource(flask_restful.Resource):  # type: ignore
    """ TrainingIdentifierRessource """

    def get(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets json file in database about a training
        EXPOSED
        """

        mylogger.LOGGER.info("/trainings/<name> - GET - retrieving trainings json file %s", name)

        if not name.isidentifier():
            flask_restful.abort(400, msg=f"Training {name} is incorrect as a name")

        # find data
        training = trainings.Training.get_by_name(name)
        if training is None:
            flask_restful.abort(404, msg=f"Training {name} doesn't exist")

        assert training is not None
        return training, 200


@API.resource('/variants/<name>')
class VariantIdentifierRessource(flask_restful.Resource):  # type: ignore
    """ VariantIdentifierRessource """

    def get(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets json file in database about a variant
        EXPOSED
        """

        mylogger.LOGGER.info("/variants/<name> - GET - retrieving variant json file %s", name)

        if not name.isidentifier():
            flask_restful.abort(400, msg=f"Variant {name} is incorrect as a name")

        # find data
        variant = variants.Variant.get_by_name(name)
        if variant is None:
            flask_restful.abort(404, msg=f"Variant {name} doesn't exist")

        assert variant is not None
        return variant, 200


@API.resource('/game-identifiers/<name>')
class GameIdentifierRessource(flask_restful.Resource):  # type: ignore
    """ GameIdentifierRessource """

    def get(self, name: str) -> typing.Tuple[int, int]:  # pylint: disable=R0201
        """
        From name get identifier
        EXPOSED
        Note : currently not used
        """

        mylogger.LOGGER.info("/game-identifiers/<name> - GET - retrieving identifier of game name=%s", name)

        # find the game
        sql_executor = database.SqlExecutor()
        game = games.Game.find_by_name(sql_executor, name)
        del sql_executor

        if game is None:
            flask_restful.abort(404, msg=f"Game {name} doesn't exist")

        assert game is not None
        return game.identifier, 200


@API.resource('/debrief-game/<name>')
class DebriefGameRessource(flask_restful.Resource):  # type: ignore
    """ DebriefGameRessource """

    def post(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Debrief game
        EXPOSED
        """

        mylogger.LOGGER.info("/games/<name> - POST - debrief game name=%s", name)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_name(sql_executor, name)

        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game {name} does not exist")

        # check this is game_master
        assert game is not None
        if game.get_role(sql_executor, 0) != user_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # game must be ongoing
        if game.current_state != 1:
            del sql_executor
            flask_restful.abort(404, msg="Game is not ongoing")

        # game must be soled or end-voted or finished
        if not (game.soloed or game.end_voted or game.finished):
            del sql_executor
            flask_restful.abort(404, msg="Game is not soloed or end-voted or finished")

        # debrief
        game.debrief()

        game.update_database(sql_executor)
        sql_executor.commit()

        del sql_executor

        data = {'name': name, 'msg': 'Ok for debrief'}
        return data, 200


@API.resource('/games/<name>')
class GameRessource(flask_restful.Resource):  # type: ignore
    """ GameRessource """

    def get(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Get all information about game
        EXPOSED
        """

        mylogger.LOGGER.info("/games/<name> - GET- retrieving data of game name=%s", name)

        # find the game
        sql_executor = database.SqlExecutor()
        game = games.Game.find_by_name(sql_executor, name)
        del sql_executor

        if game is None:
            flask_restful.abort(404, msg=f"Game {name} doesn't exist")

        assert game is not None
        data = game.save_json()
        return data, 200

    def put(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Updates information about a game
        EXPOSED
        """

        mylogger.LOGGER.info("/games/<name> - PUT - updating game name=%s", name)

        args = GAME_PARSER.parse_args(strict=True)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_name(sql_executor, name)

        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game {name} does not exist")

        # check this is game_master
        assert game is not None
        if game.get_role(sql_executor, 0) != user_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # prevent master from renaming the game
        if 'name' in args:
            if args['name'] != game.name:
                del sql_executor
                flask_restful.abort(404, msg="You are not allowed to change the name of the game - see with administrator")

        # pay more attention to deadline
        entered_deadline = args['deadline']

        if entered_deadline is not None:

            if entered_deadline == 0:  # this means "now, please !"

                # now at server time
                args['deadline'] = int(time.time() + 1)

            else:

                # check it
                deadline_date = datetime.datetime.fromtimestamp(entered_deadline, datetime.timezone.utc)

                # cannot be in past
                if deadline_date < datetime.datetime.now(tz=datetime.timezone.utc):
                    date_desc = deadline_date.strftime('%Y-%m-%d %H:%M:%S')
                    del sql_executor
                    flask_restful.abort(400, msg=f"You cannot set a deadline in the past from now!:'{date_desc}' (GMT)")

                # cannot be weekend for some games
                if not game.play_weekend:
                    deadline_day = deadline_date.date()
                    if deadline_day.weekday() in [5, 6]:
                        date_desc = deadline_date.strftime('%Y-%m-%d %H:%M:%S')
                        del sql_executor
                        flask_restful.abort(400, msg=f"You cannot set a deadline in the weekend for this game!:'{date_desc}' (GMT)")

        # keep a note of game state before
        current_state_before = game.current_state

        assert game is not None
        changed = game.load_json(args)
        if not changed:

            del sql_executor

            data = {'name': name, 'msg': 'Ok but no change !'}
            return data, 200

        # special : game changed state
        if game.current_state != current_state_before:

            if current_state_before == 0 and game.current_state == 1:

                # create and insert lock for that game
                lock = threading.Lock()
                MOVE_GAME_LOCK_TABLE[game.name] = lock

                # ----
                # we are starting the game
                # ----

                # check enough players if game is not archive

                if not game.archive:

                    nb_players_allocated = game.number_allocated(sql_executor)
                    variant_name = game.variant
                    variant_data = variants.Variant.get_by_name(variant_name)
                    assert variant_data is not None
                    number_players_expected = variant_data['roles']['number']

                    if nb_players_allocated < number_players_expected:
                        data = {'name': name, 'msg': 'Not enough players !'}
                        del sql_executor
                        return data, 400

                    if nb_players_allocated > number_players_expected:
                        data = {'name': name, 'msg': 'Too many players !'}
                        del sql_executor
                        return data, 400

                # start the game
                game.start(sql_executor)
                # commited later

                # give a deadlines
                now = time.time()
                game.push_deadline(now)
                # commited later

                if not (game.fast or game.archive):

                    # notify players
                    subject = f"La partie {game.name} a démarré !"
                    game_id = game.identifier
                    allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
                    addressees = []
                    for _, player_id, __ in allocations_list:
                        addressees.append(player_id)
                    body = "Bonjour !\n"
                    body += "\n"
                    body += "Vous pouvez commencer à jouer dans cette partie !\n"
                    body += "\n"
                    body += "Pour se rendre directement sur la partie :\n"
                    body += f"https://diplomania-gen.fr?game={game.name}"

                    json_dict = {
                        'addressees': " ".join([str(a) for a in addressees]),
                        'subject': subject,
                        'body': body,
                        'type': 'start_stop',
                    }

                    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
                    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
                    url = f"{host}:{port}/mail-players"
                    # for a rest API headers are presented differently
                    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
                    if req_result.status_code != 200:
                        print(f"ERROR from server  : {req_result.text}")
                        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                        del sql_executor
                        flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

            elif current_state_before == 1 and game.current_state == 2:

                # delete lock for that game
                del MOVE_GAME_LOCK_TABLE[game.name]

                # ----
                # we are finishing the game
                # ----

                # no check ?
                game.terminate()
                # commited later

                if not (game.fast or game.archive):

                    # notify players
                    subject = f"La partie {game.name} s'est terminée !"
                    game_id = game.identifier
                    allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
                    addressees = []
                    for _, player_id, __ in allocations_list:
                        addressees.append(player_id)
                    body = "Bonjour !\n"
                    body += "\n"
                    body += "Vous ne pouvez plus jouer dans cette partie !\n"
                    body += "\n"
                    body += "Pour se rendre directement sur la partie :\n"
                    body += f"https://diplomania-gen.fr?game={game.name}"

                    json_dict = {
                        'addressees': " ".join([str(a) for a in addressees]),
                        'subject': subject,
                        'body': body,
                        'type': 'start_stop',
                    }

                    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
                    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
                    url = f"{host}:{port}/mail-players"
                    # for a rest API headers are presented differently
                    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
                    if req_result.status_code != 200:
                        print(f"ERROR from server  : {req_result.text}")
                        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                        del sql_executor
                        flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

            elif current_state_before == 0 and game.current_state == 3:
                # ----
                # we are distinguishing a waiting game
                # ----

                # nothing to do actually
                pass

            elif current_state_before == 2 and game.current_state == 3:

                # ----
                # we are distinguishing a finished  game
                # ----

                # nothing to do actually
                pass

            elif current_state_before == 3 and game.current_state == 2:

                # ----
                # we are undistinguishing the game
                # ----

                # nothing to do actually
                pass

            else:
                data = {'name': name, 'msg': 'Transition not allowed'}
                del sql_executor
                return data, 400

        game.update_database(sql_executor)
        sql_executor.commit()

        del sql_executor

        data = {'name': name, 'msg': 'Ok updated'}
        return data, 200

    def delete(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Deletes a game
        EXPOSED
        """

        mylogger.LOGGER.info("/games/<name> - DELETE - deleting game name=%s", name)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_name(sql_executor, name)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game {name} doesn't exist")

        # check this is game_master
        assert game is not None
        if game.get_role(sql_executor, 0) != user_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # check game state
        if game.current_state == 1:
            del sql_executor
            flask_restful.abort(400, msg=f"Game {name} is ongoing. Terminate it first.")

        # check game state
        if game.current_state == 3:
            del sql_executor
            flask_restful.abort(400, msg=f"Game {name} is distinguished. Undistinguish it first.")

        game_id = game.identifier

        # check game not in tournament
        tournaments_game = groupings.Grouping.list_by_game_id(sql_executor, game_id)
        if tournaments_game:
            del sql_executor
            flask_restful.abort(400, msg="Seems the game is in some tournament. Remove it from tournament first.")

        # delete allocations
        game.delete_allocations(sql_executor)

        # and position
        game.delete_position(sql_executor)

        # and report
        report = reports.Report.find_by_identifier(sql_executor, game_id)
        assert report is not None
        report.delete_database(sql_executor)

        # and capacity
        capacity = capacities.Capacity(int(game_id), 0)
        capacity.delete_database(sql_executor)

        # and actives
        for (_, role_num) in actives.Active.list_by_game_id(sql_executor, int(game_id)):
            active = actives.Active(int(game_id), role_num)
            active.delete_database(sql_executor)

        # and submissions
        for (_, role_num) in submissions.Submission.list_by_game_id(sql_executor, int(game_id)):
            submission = submissions.Submission(int(game_id), role_num)
            submission.delete_database(sql_executor)

        # and agreements
        for (_, role_num, _) in definitives.Definitive.list_by_game_id(sql_executor, int(game_id)):
            definitive = definitives.Definitive(int(game_id), role_num, 0)
            definitive.delete_database(sql_executor)

        # delete votes
        for (_, role_num, _) in votes.Vote.list_by_game_id(sql_executor, int(game_id)):
            vote = votes.Vote(int(game_id), role_num, False)
            vote.delete_database(sql_executor)

        # delete contents
        for (identifier, _, _, _) in contents.Content.list_by_game_id(sql_executor, int(game_id)):
            content = contents.Content(identifier, 0, 0, '')
            content.delete_database(sql_executor)

        # delete declarations
        for (_, _, _, _, content_id) in declarations.Declaration.list_by_game_id(sql_executor, int(game_id)):
            declaration = declarations.Declaration(0, 0, False, False, content_id)
            declaration.delete_database(sql_executor)

        # delete messages
        for (_, _, _, content_id) in messages.Message.list_by_game_id(sql_executor, int(game_id)):
            message = messages.Message(0, 0, 0, content_id)
            message.delete_database(sql_executor)

        # delete incidents
        for (_, role_num, advancement, _, _, _) in incidents.Incident.list_by_game_id(sql_executor, int(game_id)):
            incident = incidents.Incident(int(game_id), role_num, advancement, 0, 0)
            incident.delete_database(sql_executor)

        # delete incidents2
        for (_, role_num, advancement, _) in incidents2.Incident2.list_by_game_id(sql_executor, int(game_id)):
            incident2 = incidents2.Incident2(int(game_id), role_num, advancement)
            incident2.delete_database(sql_executor)

        # delete dropouts
        for (_, role_num, player_id, _) in dropouts.Dropout.list_by_game_id(sql_executor, int(game_id)):
            dropout = dropouts.Dropout(int(game_id), role_num, player_id)
            dropout.delete_database(sql_executor)

        # delete replacements
        for (_, role_num, player_id, _, entering) in replacements.Replacement.list_by_game_id(sql_executor, int(game_id)):
            replacement = replacements.Replacement(int(game_id), role_num, player_id, bool(entering))
            replacement.delete_database(sql_executor)

        # delete transitions
        for transition in transitions.Transition.list_by_game_id(sql_executor, int(game_id)):
            transition.delete_database(sql_executor)

        # finally delete game
        assert game is not None
        game.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'name': name, 'msg': 'Ok removed'}
        return data, 200


@API.resource('/alter_games/<name>')
class AlterGameRessource(flask_restful.Resource):  # type: ignore
    """ AlterGameRessource """

    def put(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Updates information about a game (as site administrattor)
        EXPOSED
        """

        mylogger.LOGGER.info("/alter_games/<name> - PUT - alterating game name=%s", name)

        args = GAME_PARSER2.parse_args(strict=True)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_name(sql_executor, name)

        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game {name} does not exist")

        # get admin pseudo
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/pseudo-admin"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            del sql_executor
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get pseudo admin {message}")
        admin_pseudo = req_result.json()

        # check user is admin
        if pseudo != admin_pseudo:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to alter a game!")

        assert game is not None

        # keep a note of game state before
        name_before = game.name
        current_state_before = game.current_state

        changed = game.load_json(args)
        if not changed:

            del sql_executor

            data = {'name': name, 'msg': 'Ok but no change !'}
            return data, 200

        # check we have a 'legal' transition and take action

        # only if we rename game
        if 'name' in args:
            new_name = args['name']
            if new_name != name_before:
                if games.Game.find_by_name(sql_executor, new_name):
                    del sql_executor
                    flask_restful.abort(404, msg=f"There is already a game named {new_name}!")

                # change the lock !
                if name_before in MOVE_GAME_LOCK_TABLE:
                    lock = MOVE_GAME_LOCK_TABLE[name_before]
                    del MOVE_GAME_LOCK_TABLE[name_before]
                    MOVE_GAME_LOCK_TABLE[new_name] = lock

        if current_state_before == 1 and game.current_state == 0:
            # ongoing to waiting
            # suppress lock file
            del MOVE_GAME_LOCK_TABLE[game.name]

        elif current_state_before == 2 and game.current_state == 1:
            # finished to ongoing
            # create lock file
            lock = threading.Lock()
            MOVE_GAME_LOCK_TABLE[game.name] = lock

        elif current_state_before == 2 and game.current_state == 0:
            # finished to waiting
            # nothing to do
            pass

        elif current_state_before != game.current_state:
            # rejected
            del sql_executor
            data = {'name': name, 'msg': 'State game transition rejected (either because legal or impossible) !'}
            return data, 400

        game.update_database(sql_executor)
        sql_executor.commit()

        del sql_executor

        data = {'name': name, 'msg': 'Ok altered'}
        return data, 200


CREATE_GAME_LOCK = threading.Lock()


@API.resource('/games-in-state/<current_state>')
class GameStateListRessource(flask_restful.Resource):  # type: ignore
    """ GameStateListRessource """

    def get(self, current_state: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Get list of all games (dictionary identifier -> name)
        EXPOSED
        """

        mylogger.LOGGER.info("/games/<state> - GET - get getting all games names current_state=%s", current_state)

        sql_executor = database.SqlExecutor()

        games_list = games.Game.inventory(sql_executor)

        del sql_executor

        data = {str(g.identifier): {'name': g.name, 'variant': g.variant, 'fog': g.fog, 'description': g.description, 'deadline': g.deadline, 'current_advancement': g.current_advancement, 'current_state': g.current_state, 'archive': g.archive, 'fast': g.fast, 'anonymous': g.anonymous, 'grace_duration': g.grace_duration, 'scoring': g.scoring, 'nopress_current': g.nopress_current, 'nomessage_current': g.nomessage_current, 'nb_max_cycles_to_play': g.nb_max_cycles_to_play, 'used_for_elo': g.used_for_elo, 'game_type': g.game_type, 'force_wait': g.force_wait, 'finished': g.finished, 'soloed': g.soloed, 'end_voted': g.end_voted} for g in games_list if g.current_state == int(current_state)}

        return data, 200


@API.resource('/games')
class GameListRessource(flask_restful.Resource):  # type: ignore
    """ GameListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Get list of all games (dictionary identifier -> name)
        EXPOSED
        """

        mylogger.LOGGER.info("/games - GET - get getting all games names")

        sql_executor = database.SqlExecutor()

        games_list = games.Game.inventory(sql_executor)

        del sql_executor

        data = {str(g.identifier): {'name': g.name, 'variant': g.variant, 'fog': g.fog, 'description': g.description, 'deadline': g.deadline, 'current_advancement': g.current_advancement, 'current_state': g.current_state, 'archive': g.archive, 'fast': g.fast, 'anonymous': g.anonymous, 'grace_duration': g.grace_duration, 'scoring': g.scoring, 'nopress_current': g.nopress_current, 'nomessage_current': g.nomessage_current, 'nb_max_cycles_to_play': g.nb_max_cycles_to_play, 'used_for_elo': g.used_for_elo, 'game_type': g.game_type, 'force_wait': g.force_wait, 'finished': g.finished, 'soloed': g.soloed, 'end_voted': g.end_voted} for g in games_list}

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Creates a new game
        EXPOSED
        """

        mylogger.LOGGER.info("/games - POST - creating new game name")

        args = GAME_PARSER.parse_args(strict=True)

        name = args['name']
        just_play = args['just_play']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        if not name.isidentifier():
            flask_restful.abort(400, msg=f"Name '{name}' is not a valid name")

        # cannot have a void scoring
        if args['scoring']:
            scoring_provided = args['scoring']
            if not games.check_scoring(scoring_provided):
                flask_restful.abort(404, msg=f"Scoring '{scoring_provided}' is not a valid scoring code")
        else:
            args['scoring'] = games.default_scoring()

        # cannot have a void game_type
        if args['game_type']:
            game_type_provided = args['game_type']
            if not games.check_game_type(game_type_provided):
                flask_restful.abort(404, msg=f"Game type '{game_type_provided}' is not a valid game type code")
        else:
            args['game_type'] = games.default_game_type()

        # set several parameters from game_type
        if args['game_type'] == 0:  # Nego
            args['nopress_current'] = 0
            args['nomessage_current'] = 0
        elif args['game_type'] == 1:  # Blitz
            args['nopress_current'] = 1
            args['nomessage_current'] = 1
        elif args['game_type'] == 2:  # Nego publique
            args['nopress_current'] = 0
            args['nomessage_current'] = 1
        elif args['game_type'] == 3:  # Blitz ouverte
            args['nopress_current'] = 0
            args['nomessage_current'] = 1

        # we do not want a deadline here, we make our own
        time_stamp = time.time()
        forced_deadline = int(time_stamp) + DELAY_FOR_COMPLETING_GAME_DAYS * 24 * 60 * 60
        args['deadline'] = forced_deadline

        sql_executor = database.SqlExecutor()

        with CREATE_GAME_LOCK:

            # find the game
            game = games.Game.find_by_name(sql_executor, name)

            if game is not None:
                del sql_executor
                flask_restful.abort(400, msg=f"Game {name} already exists")

            # create game here
            identifier = games.Game.free_identifier(sql_executor)
            game = games.Game(identifier, '', '', '', False, False, False, False, False, False, False, False, '', 0, 0, False, 0, 0, False, 0, False, 0, False, False, False, False, 0, 0, 0, 0, 0, 0, 0, 0, False)
            _ = game.load_json(args)
            game.update_database(sql_executor)

            # make position for game
            game.create_position(sql_executor)

            game_id = game.identifier

            # add a little report
            time_stamp = int(time.time())
            report = reports.Report(game_id, time_stamp, WELCOME_TO_GAME)
            report.update_database(sql_executor)

            # get variant
            variant_name = game.variant
            variant_dict = variants.Variant.get_by_name(variant_name)
            if variant_dict is None:
                del sql_executor
                flask_restful.abort(404, msg=f"Variant {variant_name} doesn't exist")

            # get number of roles from variant
            assert variant_dict is not None
            nb_roles = int(variant_dict['roles']['number']) + 1

            # add a capacity
            capacity = capacities.Capacity(game_id, nb_roles)
            capacity.update_database(sql_executor)

            # add that all players are active (those who own a center - that will do)
            game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
            active_roles = {o[2] for o in game_ownerships}
            for role_num in active_roles:
                active = actives.Active(int(game_id), role_num)
                active.update_database(sql_executor)

            # allocate game master to game (or admin)
            if just_play:

                # game creator goes in the game
                dangling_role_id = -1
                # cannot fail
                _ = game.put_role(sql_executor, user_id, dangling_role_id)

                # admin game master of the game
                # cannot fail
                _ = game.put_role(sql_executor, ADDRESS_ADMIN, 0)

            else:

                # game creator is game master of the game
                # cannot fail
                _ = game.put_role(sql_executor, user_id, 0)

            # if game has a passive role, fill it

            variant_name = game.variant
            variant_data = variants.Variant.get_by_name(variant_name)
            assert variant_data is not None

            for role_id_str, passive_pseudo in variant_data['disorder'].items():

                role_id = int(role_id_str)

                # get player identifier
                host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
                port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
                url = f"{host}:{port}/player-identifiers/{passive_pseudo}"
                req_result = SESSION.get(url)
                if req_result.status_code != 200:
                    print(f"ERROR from server  : {req_result.text}")
                    del sql_executor
                    message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                    flask_restful.abort(404, msg=f"Failed to get id from pseudo for {passive_pseudo} : {message}")
                passive_user_id = req_result.json()

                # allocate passive to game
                # cannot fail
                _ = game.put_role(sql_executor, passive_user_id, role_id)

            sql_executor.commit()
            del sql_executor
            # end of pretected section

        data = {'name': name, 'msg': 'Ok game created'}
        return data, 201


@API.resource('/games-select')
class GameSelectListRessource(flask_restful.Resource):  # type: ignore
    """ GameSelectListRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Provides list of some games ( selected by identifier)
        Should be a get but has parameters
        parameter is a space separated string of ints
        EXPOSED
        """

        mylogger.LOGGER.info("/games-select - POST - get getting some games only name")

        args = GAMES_SELECT_PARSER.parse_args(strict=True)

        selection_submitted = args['selection']

        try:
            selection_list = list(map(int, selection_submitted.split()))
        except:  # noqa: E722 pylint: disable=bare-except
            flask_restful.abort(400, msg="Bad selection. Use a space separated list of numbers")

        sql_executor = database.SqlExecutor()
        games_list = games.Game.inventory(sql_executor)
        del sql_executor

        data = {str(g.identifier): {'name': g.name, 'variant': g.variant, 'deadline': g.deadline, 'current_advancement': g.current_advancement, 'current_state': g.current_state} for g in games_list if g.identifier in selection_list}
        return data, 200


@API.resource('/active_players')
class ActivePlayersRessource(flask_restful.Resource):  # type: ignore
    """ ActivePlayersRessource """

    # an allocation is a game-role-pseudo relation where role is -1

    def get(self) -> typing.Tuple[typing.List[int], int]:  # pylint: disable=R0201
        """
        Get list active players)
        EXPOSED
        """

        mylogger.LOGGER.info("/active_players - GET - get all active players")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get admin pseudo
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/pseudo-admin"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get pseudo admin {message}")
        admin_pseudo = req_result.json()

        # check user is admin
        if pseudo != admin_pseudo:
            flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to get all active players")

        sql_executor = database.SqlExecutor()
        allocations_list = allocations.Allocation.inventory(sql_executor)
        del sql_executor

        data = list({p for (_, p, _) in allocations_list})

        return data, 200


@API.resource('/allocations-games-in-state/<current_state>')
class AllocationStateListRessource(flask_restful.Resource):  # type: ignore
    """ AllocationStateListRessource """

    # an allocation is a game-role-pseudo relation where role is -1

    def get(self, current_state: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Get list of all allocations only games that are not anonymous (dictionary identifier -> (gm name, list of players names) only if game in some state)
        EXPOSED
        """

        mylogger.LOGGER.info("/allocations - GET - get getting all allocations in non anonymous games current_state=%s", current_state)

        sql_executor = database.SqlExecutor()
        allocations_list = allocations.Allocation.inventory(sql_executor)
        games_list = games.Game.inventory(sql_executor)
        del sql_executor

        # games that are in proper state
        relevant_games = {g.identifier for g in games_list if g.current_state == int(current_state)}

        # games we can speak about the players
        allowed_games = {g.identifier for g in games_list if not g.anonymous}

        # game_masters_dict
        game_masters_dict: typing.Dict[int, typing.List[int]] = collections.defaultdict(list)
        for (game_id, player_id, role_id) in allocations_list:
            if game_id not in relevant_games:
                continue
            if role_id != 0:
                continue
            game_masters_dict[player_id].append(game_id)

        # players_dict and active dict
        players_dict: typing.Dict[int, typing.List[int]] = collections.defaultdict(list)
        active_dict: typing.Dict[int, int] = {}
        for (game_id, player_id, role_id) in allocations_list:
            if game_id not in relevant_games:
                continue
            if role_id == 0:
                continue
            if player_id not in active_dict:
                active_dict[player_id] = 0
            active_dict[player_id] += 1
            if game_id not in allowed_games:
                continue
            players_dict[player_id].append(game_id)

        data = {'game_masters_dict': game_masters_dict, 'players_dict': players_dict, 'active_dict': active_dict}
        return data, 200


# These people may not join games
OUTCASTS: typing.List[str] = []


@API.resource('/allocations')
class AllocationListRessource(flask_restful.Resource):  # type: ignore
    """ AllocationListRessource """

    # an allocation is a game-role-pseudo relation where role is -1

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Get list of all allocations only games that are not anonymous (dictionary identifier -> (gm name, list of players names))
        EXPOSED
        """

        mylogger.LOGGER.info("/allocations - GET - get getting all allocations in non anonymous games")

        sql_executor = database.SqlExecutor()
        allocations_list = allocations.Allocation.inventory(sql_executor)
        games_list = games.Game.inventory(sql_executor)
        del sql_executor

        # games we can speak about the players
        allowed_games = {g.identifier for g in games_list if not g.anonymous}

        # game_masters_dict
        game_masters_dict: typing.Dict[int, typing.List[int]] = collections.defaultdict(list)
        for (game_id, player_id, role_id) in allocations_list:
            if role_id != 0:
                continue
            game_masters_dict[player_id].append(game_id)

        # players_dict
        players_dict: typing.Dict[int, typing.List[int]] = collections.defaultdict(list)
        for (game_id, player_id, role_id) in allocations_list:
            if game_id not in allowed_games:
                continue
            if role_id == 0:
                continue
            players_dict[player_id].append(game_id)

        data = {'game_masters_dict': game_masters_dict, 'players_dict': players_dict}
        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Creates or deletes an allocation (a relation player-role-game)
        EXPOSED
        """

        mylogger.LOGGER.info("/allocations - POST - creating/deleting new allocation")

        args = ALLOCATION_PARSER.parse_args(strict=True)

        game_id = args['game_id']
        player_pseudo = args['player_pseudo']
        delete = args['delete']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check user has right to add allocation - must be concerned user or game master

        # find the player
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{player_pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from player_pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # find the game master
        assert game is not None
        game_master_id = game.get_role(sql_executor, 0)
        if game_master_id is not None:
            if user_id not in [game_master_id, player_id]:
                del sql_executor
                flask_restful.abort(403, msg="You do not seem to be either the game master of the game or the concerned player")
        else:
            if user_id not in [player_id]:
                del sql_executor
                flask_restful.abort(403, msg="You do not seem to be the concerned player")

        # abort if has a role
        raw_allocations = allocations.Allocation.list_by_game_id(sql_executor, game_id)
        if player_id in [r[1] for r in raw_allocations if r[2] != -1]:
            del sql_executor
            flask_restful.abort(400, msg="You cannot remove or put in the game someone already assigned a role")

        dangling_role_id = -1

        if not delete:

            if pseudo in OUTCASTS:
                del sql_executor
                flask_restful.abort(400, msg="Error not allowed to join games")

            # put in game
            # cannot fail
            _ = game.put_role(sql_executor, player_id, dangling_role_id)

            # is if full now ?
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)

            game_capacity = capacities.Capacity.find_by_identifier(sql_executor, game_id)
            if game_capacity is None:
                del sql_executor
                flask_restful.abort(400, msg="Error cound not find capacity of the game")

            assert game_capacity is not None
            if game.current_state in [0, 1] and len(allocations_list) >= game_capacity:
                # it is : send notification to game master

                if game_master_id is not None:
                    # if there actually is a game master of course !

                    subject = f"La partie {game.name} est maintenant complète !"
                    addressees = [game_master_id]
                    body = "Bonjour !\n"
                    body += "\n"
                    if game.current_state == 0:
                        body += "Vous pouvez donc démarrer cette partie !\n"
                    elif game.current_state == 1:
                        body += "Vous pouvez donc donner un rôle au remplaçant !\n"
                    body += "\n"
                    body += "Pour se rendre directement sur la partie :\n"
                    body += f"https://diplomania-gen.fr?game={game.name}"

                    json_dict = {
                        'addressees': " ".join([str(a) for a in addressees]),
                        'subject': subject,
                        'body': body,
                        'type': 'start_stop',
                    }

                    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
                    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
                    url = f"{host}:{port}/mail-players"
                    # for a rest API headers are presented differently
                    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
                    if req_result.status_code != 200:
                        print(f"ERROR from server  : {req_result.text}")
                        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                        del sql_executor
                        flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

            sql_executor.commit()
            del sql_executor

            data = {'msg': 'Ok allocation updated or created'}
            return data, 201

        game.remove_role(sql_executor, player_id, dangling_role_id)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok allocation deleted if present'}
        return data, 200


@API.resource('/role-allocations')
class RoleAllocationListRessource(flask_restful.Resource):  # type: ignore
    """ AllocationListRessource """

    # a role-allocation is a game-role-pseudo relation where role is <> -1

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Creates or deletes an role allocation (a relation player-role-game)
        creates : There should be a single -1 role allacation
        deletes : That will create a -1 role allocation
        EXPOSED
        """

        mylogger.LOGGER.info("/role-allocations - POST - creating/deleting new role-allocation")

        args = ROLE_ALLOCATION_PARSER.parse_args(strict=True)

        game_id = args['game_id']
        player_pseudo = args['player_pseudo']
        role_id = args['role_id']
        delete = args['delete']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check user has right to add allocation - must game master

        # find the player
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{player_pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from player_pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # find the game master
        assert game is not None
        game_master_id = game.get_role(sql_executor, 0)

        # first branch : dealing with game master
        if role_id == 0:

            if player_id != user_id:
                del sql_executor
                flask_restful.abort(403, msg="You cannot assign or desassign game mastership for someone else")

            if not delete:
                # taking game master role

                if game_master_id == player_id:
                    del sql_executor
                    flask_restful.abort(400, msg="You are already game master of this game !")

                if game_master_id is not None:
                    del sql_executor
                    flask_restful.abort(403, msg="There is already a game master in this game !")

                role_id_found = game.find_role(sql_executor, player_id)
                if role_id_found is not None and role_id_found != -1:
                    del sql_executor
                    flask_restful.abort(400, msg="You cannot take game mastership since you are a player in this game")

                # put role
                # cannot fail
                _ = game.put_role(sql_executor, player_id, role_id)

                # we have a replacement here (game master entering)
                replacement = replacements.Replacement(game_id, role_id, player_id, True)
                replacement.update_database(sql_executor)  # noqa: F821

                sql_executor.commit()
                del sql_executor

                data = {'msg': 'Ok game master role-allocation updated or created'}
                return data, 201

            # quitting game master role

            if player_id != game_master_id:
                del sql_executor
                flask_restful.abort(403, msg="You cannot quit game mastership since you are not game master")

            # put dangling
            dangling_role_id = -1
            # cannot fail
            _ = game.put_role(sql_executor, player_id, dangling_role_id)

            # we have a replacement here (game master quitting)
            replacement = replacements.Replacement(game_id, role_id, player_id, False)
            replacement.update_database(sql_executor)  # noqa: F821

            sql_executor.commit()
            del sql_executor

            data = {'msg': 'Ok game master role-allocation deleted'}
            return data, 200

        # second branch : dealing with player - not game master

        if user_id != game_master_id:
            del sql_executor
            flask_restful.abort(403, msg="You need be the game master of the game to allocate ro unallocate roles")

        # giving player role
        if not delete:

            if player_id == game_master_id:
                del sql_executor
                flask_restful.abort(403, msg="You cannot put the game master of the game as a player in the game")

            if game.current_state == 0 and not game.manual:
                del sql_executor
                flask_restful.abort(400, msg="This is a manual game, allocation will be done at game start")

            role_id_found = game.find_role(sql_executor, player_id)
            if role_id_found == role_id:
                del sql_executor
                flask_restful.abort(400, msg="This player already has this exact role in this game")

            player_id_found = game.get_role(sql_executor, role_id)
            if player_id_found is not None:
                del sql_executor
                flask_restful.abort(403, msg="There is already a player who has this role in this game")

            # put role
            status = game.put_role(sql_executor, player_id, role_id)
            if not status:
                del sql_executor
                flask_restful.abort(400, msg="This role is incorrect for the variant of this game")

            # we have a replacement here (player entering)
            replacement = replacements.Replacement(game_id, role_id, player_id, True)
            replacement.update_database(sql_executor)  # noqa: F821

            sql_executor.commit()
            del sql_executor

            data = {'msg': 'Ok player role-allocation updated or created'}
            return data, 201

        # revoking player role

        player_id_found = game.get_role(sql_executor, role_id)
        if player_id_found is None:
            del sql_executor
            flask_restful.abort(404, msg="There is no player with the role you want to revoke in this game")

        if player_id_found != player_id:
            del sql_executor
            flask_restful.abort(404, msg="This player does not have the role you want to revoke in this game")

        # put dangling
        dangling_role_id = -1
        # cannot fail
        _ = game.put_role(sql_executor, player_id, dangling_role_id)

        # we have a quitter here (until further notice)
        dropout = dropouts.Dropout(game_id, role_id, player_id)
        dropout.update_database(sql_executor)  # noqa: F821

        # we have a replacement here (player quitting)
        replacement = replacements.Replacement(game_id, role_id, player_id, False)
        replacement.update_database(sql_executor)  # noqa: F821

        sql_executor.commit()
        del sql_executor

        # report
        data = {'msg': 'Ok player role-allocation deleted if present'}
        return data, 200


@API.resource('/game-master/<game_id>')
class GameMasterRessource(flask_restful.Resource):  # type: ignore
    """ GameRoleRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Optional[int], int]:  # pylint: disable=R0201
        """
        Get game master of a game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-master/<game_id> GETTING - getting game master game id=%s", game_id)

        sql_executor = database.SqlExecutor()

        allocations_list = allocations.Allocation.list_by_role_id_game_id(sql_executor, 0, game_id)

        del sql_executor

        players_id_list = [a[1] for a in allocations_list]
        players_id = players_id_list[0] if players_id_list else None

        return players_id, 200


@API.resource('/game-role/<game_id>')
class GameRoleRessource(flask_restful.Resource):  # type: ignore
    """ GameRoleRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Optional[int], int]:  # pylint: disable=R0201
        """
        Get my role in a game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-role/<game_id> GETTING - getting role game id=%s", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)

        del sql_executor

        role_table = {str(a[1]): a[2] for a in allocations_list}

        role_id = None
        if str(player_id) in role_table:
            role_found = role_table[str(player_id)]
            if role_found != -1:
                role_id = role_found

        return role_id, 200


@API.resource('/all-games-roles')
class AllGamesRolesRessource(flask_restful.Resource):  # type: ignore
    """ AllGamesRolesRessource """

    def get(self) -> typing.Tuple[typing.Optional[typing.Dict[int, int]], int]:  # pylint: disable=R0201
        """
        Get all my roles in all my games
        EXPOSED
        """

        mylogger.LOGGER.info("/all-games-roles GETTING - getting all roles all games")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        # get list of games in which player is involved
        sql_executor = database.SqlExecutor()
        allocations_list = allocations.Allocation.list_by_player_id(sql_executor, player_id)
        del sql_executor

        dict_role_id: typing.Dict[int, int] = {}
        for game_id, _, role_id in allocations_list:
            dict_role_id[game_id] = role_id

        return dict_role_id, 200


@API.resource('/game-allocations/<game_id>')
class AllocationGameRessource(flask_restful.Resource):  # type: ignore
    """ AllocationGameRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets all allocations for the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-allocations/<game_id> - GET - get getting allocations for game id=%s", game_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get answer
        allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)

        data = {str(a[1]): a[2] for a in allocations_list}

        # find game master
        assert game is not None
        game_master_id = game.get_role(sql_executor, 0)

        del sql_executor

        if game.anonymous:

            # check authentication from user server
            host = lowdata.SERVER_CONFIG['USER']['HOST']
            port = lowdata.SERVER_CONFIG['USER']['PORT']
            url = f"{host}:{port}/verify"
            jwt_token = flask.request.headers.get('AccessToken')
            if not jwt_token:
                flask_restful.abort(400, msg="Missing authentication!")
            req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
            if req_result.status_code != 200:
                mylogger.LOGGER.error("ERROR = %s", req_result.text)
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                flask_restful.abort(401, msg=f"Bad authentication!:{message}")

            pseudo = req_result.json()['logged_in_as']

            # get player identifier
            host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
            port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/player-identifiers/{pseudo}"
            req_result = SESSION.get(url)
            if req_result.status_code != 200:
                print(f"ERROR from server  : {req_result.text}")
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
            user_id = req_result.json()

            if user_id != game_master_id:

                # check moderator rights

                # get moderator list
                host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
                port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
                url = f"{host}:{port}/moderators"
                req_result = SESSION.get(url)
                if req_result.status_code != 200:
                    message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                    flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
                the_moderators = req_result.json()

                # check pseudo in moderator list
                if pseudo not in the_moderators:
                    flask_restful.abort(403, msg="You need to be the game master of the game (or site moderator) so you are not allowed to see the roles of this anonymous game")

        return data, 200


@API.resource('/player-allocations/<player_id>')
class AllocationPlayerRessource(flask_restful.Resource):  # type: ignore
    """ AllocationPlayerRessource """

    def get(self, player_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets all allocations for the player
        Note : here because data is in this database
        EXPOSED
        """

        mylogger.LOGGER.info("/player-allocations/<player_id> - GET - get getting allocations for player player_id=%s", player_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        if user_id != int(player_id):
            flask_restful.abort(403, msg="Only player can get his/her player allocations")

        sql_executor = database.SqlExecutor()
        allocations_list = allocations.Allocation.list_by_player_id(sql_executor, player_id)
        del sql_executor

        data = {str(a[0]): a[2] for a in allocations_list}
        return data, 200


@API.resource('/player-allocations2/<player_id>')
class AllocationPlayer2Ressource(flask_restful.Resource):  # type: ignore
    """ AllocationPlayer2Ressource """

    def get(self, player_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets all allocations for the player (from moderator)
        Note : here because data is in this database
        EXPOSED
        """

        mylogger.LOGGER.info("/player-allocations2/<player_id> - GET - get getting allocations for player player_id=%s from moderator", player_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get moderator list
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/moderators"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
        the_moderators = req_result.json()

        # check pseudo in moderator list
        if pseudo not in the_moderators:
            flask_restful.abort(403, msg="Need to be moderator to get list of all games by a player!")

        sql_executor = database.SqlExecutor()
        allocations_list = allocations.Allocation.list_by_player_id(sql_executor, player_id)
        del sql_executor

        data = {str(a[0]): a[2] for a in allocations_list}
        return data, 200


@API.resource('/games-incomplete')
class GamesIncompleteRessource(flask_restful.Resource):  # type: ignore
    """ GamesIncompleteRessource """

    def get(self) -> typing.Tuple[typing.List[typing.Tuple[int, int, int]], int]:  # pylint: disable=R0201
        """
        Gets all  games that do not have all players
        EXPOSED
        """

        mylogger.LOGGER.info("/games-incomplete - GET - get getting all games not ready")

        sql_executor = database.SqlExecutor()
        full_games_data = sql_executor.execute("select games.identifier, count(*) as filled_count, capacities.value from games join allocations on allocations.game_id=games.identifier join capacities on capacities.game_id=games.identifier group by identifier", need_result=True)
        del sql_executor

        # keep only the ones where no role is missing
        assert full_games_data is not None
        data = [tr[0] for tr in full_games_data if tr[1] < tr[2]]

        return data, 200


@API.resource('/games-recruiting')
class GamesRecruitingRessource(flask_restful.Resource):  # type: ignore
    """ GamesRecruitingRessource """

    def get(self) -> typing.Tuple[typing.List[typing.Tuple[int, int, int]], int]:  # pylint: disable=R0201
        """
        Gets all  games that do not have all players
        EXPOSED
        """

        mylogger.LOGGER.info("/games-recruiting - GET - get getting all games recruiting")

        sql_executor = database.SqlExecutor()
        full_games_data = sql_executor.execute("select games.identifier, count(*) as filled_count, capacities.value from games join allocations on allocations.game_id=games.identifier join capacities on capacities.game_id=games.identifier group by identifier", need_result=True)
        del sql_executor

        # keep only the ones where a role is missing
        assert full_games_data is not None
        data = [tr for tr in full_games_data if tr[1] < tr[2]]

        return data, 200


@API.resource('/game-imagine-unit/<game_id>/<role_id>')
class GameImagineUnitRessource(flask_restful.Resource):  # type: ignore
    """ GameImagineUnitRessource """

    def post(self, game_id: int, role_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Imagine a unit of a game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-imagine-unit/<game_id>/<role_id> - POST - imagine a unit game id=%s role_id=%s", game_id, role_id)

        args = IMAGINE_PARSER.parse_args(strict=True)
        type_submitted = args['type_num']
        zone_submitted = args['zone_num']
        role_submitted = args['role_num']
        delete = args['delete']

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check the game position is protected
        assert game is not None
        if not game.fog:
            del sql_executor
            flask_restful.abort(404, msg="This game is not fog of war !")

        # check a role is provided
        if role_id is None:
            del sql_executor
            flask_restful.abort(404, msg="Role is missing !")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            del sql_executor
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # who is player for role ?
        assert game is not None
        player_id = game.get_role(sql_executor, int(role_id))

        # must be player
        if user_id != player_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the player who corresponds to this role")

        # safety checks for buggy front end
        variant_name = game.variant
        variant_data = variants.Variant.get_by_name(variant_name)
        assert variant_data is not None

        if int(type_submitted) not in [1, 2]:
            del sql_executor
            flask_restful.abort(403, msg="'type_submitted' is wrong !")

        if int(zone_submitted) not in range(1, len(variant_data['regions']) + len(variant_data['coastal_zones']) + 1):
            del sql_executor
            flask_restful.abort(403, msg="'zone_submitted' is wrong !")

        if int(role_submitted) not in range(1, variant_data['roles']['number'] + 1):
            del sql_executor
            flask_restful.abort(403, msg="'role_submitted' is wrong !")

        if delete:

            # IMPORTANT : check deleted unit not as passive in order

            # gvet the orders
            orders_list = orders.Order.list_by_game_id_role_num(sql_executor, int(game_id), int(role_id))

            # get the passives that need to be referenced
            passives_zones = {o[4] for o in orders_list if o[4] != 0}

            # cannot remove reference to one of these
            if zone_submitted in passives_zones:
                del sql_executor
                flask_restful.abort(403, msg="Remove order referencing this unit first !")

            # create the imagined unit
            imagined_unit = imagined_units.ImaginedUnit(int(game_id), int(role_id), int(type_submitted), int(zone_submitted), int(role_submitted))
            imagined_unit.delete_database(sql_executor)
            sql_executor.commit()

            del sql_executor

            data = {'msg': 'Imagined unit deleted!'}
            return data, 201

        # create the imagined unit
        imagined_unit = imagined_units.ImaginedUnit(int(game_id), int(role_id), int(type_submitted), int(zone_submitted), int(role_submitted))
        imagined_unit.update_database(sql_executor)
        sql_executor.commit()

        del sql_executor

        data = {'msg': 'Imagined unit inserted!'}
        return data, 201


@API.resource('/game-fog-of-war-positions/<game_id>/<role_id>')
class GameFogOfWarPositionRessource(flask_restful.Resource):  # type: ignore
    """ GameFogOfWarPositionRessource """

    def get(self, game_id: int, role_id: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets position of the game (fog of war : foggy variant mainly)
        EXPOSED
        """

        mylogger.LOGGER.info("/game-fog-of-war-positions/<game_id>/<role_id> - GET - getting fog of war position for game id=%s role id=%s", game_id, role_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check the game position is protected
        assert game is not None
        if not game.fog:
            del sql_executor
            flask_restful.abort(404, msg="This game is not fog of war !")

        # make some checks if a role is provided
        if role_id != 'None':  # strange

            # check authentication from user server
            host = lowdata.SERVER_CONFIG['USER']['HOST']
            port = lowdata.SERVER_CONFIG['USER']['PORT']
            url = f"{host}:{port}/verify"
            jwt_token = flask.request.headers.get('AccessToken')
            if not jwt_token:
                del sql_executor
                flask_restful.abort(400, msg="Missing authentication!")
            req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
            if req_result.status_code != 200:
                mylogger.LOGGER.error("ERROR = %s", req_result.text)
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                del sql_executor
                flask_restful.abort(401, msg=f"Bad authentication!:{message}")

            pseudo = req_result.json()['logged_in_as']

            # get player identifier
            host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
            port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/player-identifiers/{pseudo}"
            req_result = SESSION.get(url)
            if req_result.status_code != 200:
                print(f"ERROR from server  : {req_result.text}")
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                del sql_executor
                flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
            user_id = req_result.json()

            # who is player for role ?
            assert game is not None
            player_id = game.get_role(sql_executor, int(role_id))

            # must be player or master
            if user_id != player_id:
                del sql_executor
                flask_restful.abort(403, msg="You do not seem to be the player or game master who corresponds to this role")

        # get ownerships
        ownership_dict: typing.Dict[str, int] = {}
        game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
        for _, center_num, role_num in game_ownerships:
            ownership_dict[str(center_num)] = role_num

        # get units
        game_units = units.Unit.list_by_game_id(sql_executor, game_id)
        unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        # fake_unit_dict : no
        dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
            if fake:
                pass  # this is confidential
            elif region_dislodged_from_num:
                dislodged_unit_dict[str(role_num)].append([type_num, zone_num, region_dislodged_from_num])
            else:
                unit_dict[str(role_num)].append([type_num, zone_num])

        # get forbiddens
        forbidden_list: typing.List[int] = []
        game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)
        for _, region_num in game_forbiddens:
            forbidden_list.append(region_num)

        # game not ongoing or game master or game actually soloed or end-voted or finished : you get get a clear picture
        if game.current_state != 1 or (role_id != 'None' and int(role_id) == 0) or game.soloed or game.end_voted or game.finished:
            del sql_executor
            data = {
                'ownerships': ownership_dict,
                'dislodged_ones': dislodged_unit_dict,
                'units': unit_dict,
                'forbiddens': forbidden_list,
                'imagined_units': {},
            }
            return data, 200

        # now we can start hiding stuff

        # get an empty picture if things if no role provided since protected
        if role_id == 'None':
            data = {
                'ownerships': {},
                'dislodged_ones': {},
                'units': {},
                'forbiddens': [],
                'imagined_units': {},
            }
            return data, 200

        orders_list2: typing.List[typing.List[int]] = []
        fake_units_list2: typing.List[typing.List[int]] = []
        seen_regions_list: typing.List[int] = []

        # this will update last parameters
        variant_name = game.variant
        apply_visibility(variant_name, int(role_id), ownership_dict, dislodged_unit_dict, unit_dict, forbidden_list, orders_list2, fake_units_list2, seen_regions_list)

        # get imagined units
        imagined_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        imagined_game_units = imagined_units.ImaginedUnit.list_by_game_id_role_num(sql_executor, game_id, int(role_id))
        for _, _, type_num, zone_num, role_num in imagined_game_units:
            imagined_unit_dict[str(role_num)].append([type_num, zone_num])

        del sql_executor

        data = {
            'ownerships': ownership_dict,
            'dislodged_ones': dislodged_unit_dict,
            'units': unit_dict,
            'forbiddens': forbidden_list,
            'imagined_units': imagined_unit_dict,
            'seen_regions': seen_regions_list
        }

        return data, 200


@API.resource('/game-positions/<game_id>')
class GamePositionRessource(flask_restful.Resource):  # type: ignore
    """ GamePositionRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Changes position of a game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-positions/<game_id> - POST - rectifying position game id=%s", game_id)

        args = RECTIFICATION_PARSER.parse_args(strict=True)

        ownerships_submitted = args['ownerships']
        units_submitted = args['units']

        try:
            the_ownerships = json.loads(ownerships_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert ownerships from json to text ?")

        try:
            the_units = json.loads(units_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert units from json to text ?")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        # check user has right to change position - must be admin

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get admin pseudo
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/pseudo-admin"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            del sql_executor
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get pseudo admin {message}")
        admin_pseudo = req_result.json()

        # check user is admin
        if pseudo != admin_pseudo:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to rectify a position!")

        # store position

        # purge previous ownerships
        for (_, center_num, role_num) in ownerships.Ownership.list_by_game_id(sql_executor, int(game_id)):
            ownership = ownerships.Ownership(int(game_id), center_num, role_num)
            ownership.delete_database(sql_executor)

        # purge previous units
        for (_, type_num, role_num, zone_num, region_dislodged_from_num, fake) in units.Unit.list_by_game_id(sql_executor, int(game_id)):
            unit = units.Unit(int(game_id), type_num, role_num, zone_num, region_dislodged_from_num, fake)
            unit.delete_database(sql_executor)

        # insert new ownerships
        for the_ownership in the_ownerships:
            center_num = the_ownership['center_num']
            role = the_ownership['role']
            ownership = ownerships.Ownership(int(game_id), center_num, role)
            ownership.update_database(sql_executor)

        # insert new units
        for the_unit in the_units:
            type_num = the_unit['type_unit']
            zone_num = the_unit['zone']
            role_num = the_unit['role']
            unit = units.Unit(int(game_id), type_num, zone_num, role_num, 0, 0)
            unit.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok position rectified'}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets position of the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-positions/<game_id> - GET - getting position for game id=%s", game_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check the game position is not protected
        assert game is not None
        if game.fog:
            del sql_executor
            flask_restful.abort(404, msg="This game is fog of war !")

        # get ownerships
        ownership_dict = {}
        game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
        for _, center_num, role_num in game_ownerships:
            ownership_dict[str(center_num)] = role_num

        # get units
        unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        game_units = units.Unit.list_by_game_id(sql_executor, game_id)
        for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
            if fake:
                pass  # this is confidential
            elif region_dislodged_from_num:
                dislodged_unit_dict[str(role_num)].append([type_num, zone_num, region_dislodged_from_num])
            else:
                unit_dict[str(role_num)].append([type_num, zone_num])

        # get forbiddens
        forbidden_list = []
        game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)
        for _, region_num in game_forbiddens:
            forbidden_list.append(region_num)

        # no imagined units
        imagined_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = {}

        del sql_executor

        data = {
            'ownerships': ownership_dict,
            'dislodged_ones': dislodged_unit_dict,
            'units': unit_dict,
            'forbiddens': forbidden_list,
            'imagined_units': imagined_unit_dict,
        }
        return data, 200


@API.resource('/game-fog-of-war-reports/<game_id>/<role_id>')
class GameFogOfWarReportRessource(flask_restful.Resource):  # type: ignore
    """ GameFogOfWarReportRessource """

    def get(self, game_id: int, role_id: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets the restrcited report of adjudication for the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-reports/<game_id>/<role_id> - GET - getting fog of war report game id=%s role_id=%s", game_id, role_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check the game position is protected
        assert game is not None
        if not game.fog:
            del sql_executor
            flask_restful.abort(404, msg="This game is not fog of war !")

        # make some checks if a role is provided
        if role_id != 'None':  # strange

            # check authentication from user server
            host = lowdata.SERVER_CONFIG['USER']['HOST']
            port = lowdata.SERVER_CONFIG['USER']['PORT']
            url = f"{host}:{port}/verify"
            jwt_token = flask.request.headers.get('AccessToken')
            if not jwt_token:
                flask_restful.abort(400, msg="Missing authentication!")
            req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
            if req_result.status_code != 200:
                mylogger.LOGGER.error("ERROR = %s", req_result.text)
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                del sql_executor
                flask_restful.abort(401, msg=f"Bad authentication!:{message}")

            pseudo = req_result.json()['logged_in_as']

            # get player identifier
            host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
            port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/player-identifiers/{pseudo}"
            req_result = SESSION.get(url)
            if req_result.status_code != 200:
                print(f"ERROR from server  : {req_result.text}")
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                del sql_executor
                flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
            user_id = req_result.json()

            # who is player for role ?
            assert game is not None
            player_id = game.get_role(sql_executor, int(role_id))

            # must be player, game master
            if user_id != player_id:
                del sql_executor
                flask_restful.abort(403, msg="You do not seem to be the player or game master who corresponds to this role")

        # find the report
        report = reports.Report.find_by_identifier(sql_executor, game_id)
        if report is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Report happens to be missing for {game_id}")

        assert report is not None

        # game not ongoing or game master or game actually soloed or game-voted or finished: you get get a clear picture
        if game.current_state != 1 or (role_id != 'None' and int(role_id) == 0) or game.soloed or game.end_voted or game.finished:
            # extract report data
            content = report.content
            del sql_executor
            data = {'time_stamp': report.time_stamp, 'content': content}
            return data, 200

        # otherwise nothing
        del sql_executor
        data = {'time_stamp': report.time_stamp, 'content': "---"}
        return data, 200


@API.resource('/game-reports/<game_id>')
class GameReportRessource(flask_restful.Resource):  # type: ignore
    """ GameReportRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets the report of adjudication for the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-reports/<game_id> - GET - getting report game id=%s", game_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check the game position is not protected
        assert game is not None
        if game.fog:
            del sql_executor
            flask_restful.abort(404, msg="This game is fog of war !")

        # find the report
        report = reports.Report.find_by_identifier(sql_executor, game_id)
        if report is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Report happens to be missing for {game_id}")

        # extract report data
        assert report is not None
        content = report.content

        del sql_executor

        data = {'time_stamp': report.time_stamp, 'content': content}
        return data, 200


@API.resource('/game-fog-of-war-transitions/<game_id>/<advancement>/<role_id>')
class GameFogOfWarTransitionRessource(flask_restful.Resource):  # type: ignore
    """ GameFogOfWarTransitionRessource """

    def get(self, game_id: int, advancement: int, role_id: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets the full fog of war report  (transition : postions + orders + report) of adjudication for the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-fog-of-war-transitions/<game_id>/<advancement>/<role_id> - GET - getting transition game id=%s advancement=%s role id=%s ", game_id, advancement, role_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check the game position is protected
        assert game is not None
        if not game.fog:
            del sql_executor
            flask_restful.abort(404, msg="This game is not fog of war !")

        # make some checks if a role is provided
        if role_id != 'None':  # strange

            # check authentication from user server
            host = lowdata.SERVER_CONFIG['USER']['HOST']
            port = lowdata.SERVER_CONFIG['USER']['PORT']
            url = f"{host}:{port}/verify"
            jwt_token = flask.request.headers.get('AccessToken')
            if not jwt_token:
                del sql_executor
                flask_restful.abort(400, msg="Missing authentication!")
            req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
            if req_result.status_code != 200:
                mylogger.LOGGER.error("ERROR = %s", req_result.text)
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                del sql_executor
                flask_restful.abort(401, msg=f"Bad authentication!:{message}")

            pseudo = req_result.json()['logged_in_as']

            # get player identifier
            host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
            port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/player-identifiers/{pseudo}"
            req_result = SESSION.get(url)
            if req_result.status_code != 200:
                print(f"ERROR from server  : {req_result.text}")
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                del sql_executor
                flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
            user_id = req_result.json()

            # who is player for role ?
            assert game is not None
            player_id = game.get_role(sql_executor, int(role_id))

            # must be player, game master
            if user_id != player_id:
                del sql_executor
                flask_restful.abort(403, msg="You do not seem to be the player or game master who corresponds to this role")

        # find the transition
        transition = transitions.Transition.find_by_game_advancement(sql_executor, game_id, advancement)
        if transition is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Transition happens to be missing for {game_id} / {advancement}")

        assert transition is not None

        # extract transition data
        the_situation = json.loads(transition.situation_json)
        the_orders = json.loads(transition.orders_json)
        report_txt = transition.report_txt

        # game not ongoing or game master or game actually soloed or end-voted or finished: you get get a clear picture
        if game.current_state != 1 or (role_id != 'None' and int(role_id) == 0) or game.soloed or game.end_voted or game.finished:
            del sql_executor
            data = {'time_stamp': transition.time_stamp, 'situation': the_situation, 'orders': the_orders, 'report_txt': report_txt}
            return data, 200

        # get a partial picture of things
        del sql_executor

        # get an empty picture if things if no role provided since protected
        if role_id == 'None':
            data = {'time_stamp': transition.time_stamp, 'situation': {'ownerships': {}, 'dislodged_ones': {}, 'units': {}, 'forbiddens': []}, 'orders': {'orders': [], 'fake_units': []}, 'report_txt': "---"}
            return data, 200

        ownership_dict = the_situation['ownerships']
        dislodged_unit_dict = the_situation['dislodged_ones']
        unit_dict = the_situation['units']
        forbidden_list = the_situation['forbiddens']

        orders_list = the_orders['orders']
        fake_units_list = the_orders['fake_units']

        seen_regions_list: typing.List[int] = []

        # backup orders
        complete_unit_dict = unit_dict.copy()

        # this will update last parameters
        variant_name = game.variant
        apply_visibility(variant_name, int(role_id), ownership_dict, dislodged_unit_dict, unit_dict, forbidden_list, orders_list, fake_units_list, seen_regions_list)

        # this will insert supported units that need to be seen (this will update unit_dict parameter)
        apply_supported(complete_unit_dict, unit_dict, orders_list)

        data = {
            'time_stamp': transition.time_stamp,
            'situation': {
                'ownerships': ownership_dict,
                'dislodged_ones': dislodged_unit_dict,
                'units': unit_dict,
                'forbiddens': forbidden_list,
                'seen_regions': seen_regions_list
            },
            'orders': {
                'orders': orders_list,
                'fake_units': fake_units_list
            },
            'report_txt': "---"
        }
        return data, 200


@API.resource('/game-transitions/<game_id>/<advancement>')
class GameTransitionRessource(flask_restful.Resource):  # type: ignore
    """ GameTransitionRessource """

    def get(self, game_id: int, advancement: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets the full report  (transition : postions + orders + report) of adjudication for the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-transitions/<game_id>/<advancement> - GET - getting transition game id=%s advancement=%s", game_id, advancement)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check the game position is not protected
        assert game is not None
        if game.fog:
            del sql_executor
            flask_restful.abort(404, msg="This game is fog of war !")

        # find the transition
        transition = transitions.Transition.find_by_game_advancement(sql_executor, game_id, advancement)
        if transition is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Transition happens to be missing for {game_id} / {advancement}")

        # extract transition data
        assert transition is not None
        the_situation = json.loads(transition.situation_json)
        the_orders = json.loads(transition.orders_json)
        report_txt = transition.report_txt

        del sql_executor

        data = {'time_stamp': transition.time_stamp, 'situation': the_situation, 'orders': the_orders, 'report_txt': report_txt}
        return data, 200


@API.resource('/game-transitions/<game_id>')
class GameTransitionsRessource(flask_restful.Resource):  # type: ignore
    """ GameTransitionsRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[int, int], int]:  # pylint: disable=R0201
        """
        Gets all existing transitions of that game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-transitions/<game_id> - GET - getting transitions game id=%s", game_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # find the transition
        list_transitions = transitions.Transition.list_by_game_id(sql_executor, game_id)

        del sql_executor

        trans_dict = {}
        for transition in list_transitions:
            trans_dict[transition.advancement] = transition.time_stamp

        data = trans_dict
        return data, 200


@API.resource('/game-force-agree-solve/<game_id>')
class GameForceAgreeSolveRessource(flask_restful.Resource):  # type: ignore
    """ GameForceAgreeSolveRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Force agree to solve with these orders by a game master
        EXPOSED
        """
        mylogger.LOGGER.info("/game-force-agree-solve/<game_id> - POST - force agreeing from game master to solve with orders game id=%s", game_id)

        args = FORCE_AGREE_PARSER.parse_args(strict=True)

        role_id = args['role_id']
        adjudication_names = args['adjudication_names']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is game master
        assert game is not None
        game_master_id = game.get_role(sql_executor, 0)

        # must be game master or commuter
        if user_id != game_master_id and pseudo != COMMUTER_ACCOUNT:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game or the commuter")

        if role_id == 0:
            del sql_executor
            flask_restful.abort(400, msg="Invalid role_id parameter")

        # begin of protected section
        with MOVE_GAME_LOCK_TABLE[game.name]:

            # check orders are required
            actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
            needed_list = [o[1] for o in actives_list]
            if role_id not in needed_list:
                del sql_executor
                flask_restful.abort(400, msg="This role does not seem to require any orders")

            # check orders are submitted
            submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
            submitted_list = [o[1] for o in submissions_list]
            if role_id not in submitted_list:
                del sql_executor
                flask_restful.abort(400, msg="This role does not seem to have submitted orders yet")

            if not game.past_deadline():
                del sql_executor
                flask_restful.abort(400, msg="We are not after deadline, please change deadline first.")

            # are civil disorders allowed for the game ?
            if not game.civil_disorder_allowed():
                del sql_executor
                flask_restful.abort(400, msg="Civil disorder in this game, for this season, does not seem to be allowed. Sent a notification to player.")

            # handle definitive boolean
            # game master forced player to agree to adjudicate
            now = time.time()
            status, late, unsafe, missing, adjudicated, debug_message = agree.fake_post(now, game_id, role_id, True, adjudication_names, sql_executor)

            if not status:
                del sql_executor  # noqa: F821
                flask_restful.abort(400, msg=f"Failed to agree (forced) to adjudicate : {debug_message}")

            # this may have caused player to be late
            if late:
                subject = f"L'arbitre de la partie {game.name} ou l'automate a forcé votre accord, ce qui vous inflige un retard !"
                game_id = game.identifier
                allocations_list = allocations.Allocation.list_by_role_id_game_id(sql_executor, role_id, game_id)
                addressees = []
                for _, player_id, __ in allocations_list:
                    addressees.append(player_id)

                body = "Bonjour !\n"
                body += "\n"
                body += "Votre accord a été forcé sur cette partie et vous étiez en retard !\n"
                body += "\n"
                body += "Conclusion : vous avez un retard sur cette partie...\n"
                body += "\n"
                body += "Pour se rendre directement sur la partie :\n"
                body += f"https://diplomania-gen.fr?game={game.name}"

                json_dict = {
                    'addressees': " ".join([str(a) for a in addressees]),
                    'subject': subject,
                    'body': body,
                    'type': 'late',
                }

                host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
                port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
                url = f"{host}:{port}/mail-players"
                # for a rest API headers are presented differently
                req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
                if req_result.status_code != 200:
                    print(f"ERROR from server  : {req_result.text}")
                    message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                    del sql_executor
                    flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

            if adjudicated:

                # reload game
                game = games.Game.find_by_identifier(sql_executor, game_id)
                assert game is not None

                # notify players

                if not (game.fast or game.archive):

                    subject = f"La partie {game.name} a avancé (avec l'aide de l'arbitre ou de l'automate)!"
                    game_id = game.identifier
                    allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
                    addressees = []
                    for _, player_id, __ in allocations_list:
                        addressees.append(player_id)
                    body = "Bonjour !\n"
                    body += "\n"
                    body += "Vous pouvez continuer à jouer dans cette partie !\n"
                    body += "\n"
                    body += "Note : Vous pouvez désactiver cette notification en modifiant un paramètre de votre compte sur le site.\n"
                    body += "\n"
                    body += "Pour se rendre directement sur la partie :\n"
                    body += f"https://diplomania-gen.fr?game={game.name}"

                    json_dict = {
                        'addressees': " ".join([str(a) for a in addressees]),
                        'subject': subject,
                        'body': body,
                        'type': 'adjudication',
                    }

                    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
                    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
                    url = f"{host}:{port}/mail-players"
                    # for a rest API headers are presented differently
                    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
                    if req_result.status_code != 200:
                        print(f"ERROR from server  : {req_result.text}")
                        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                        del sql_executor
                        flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

                    # declaration from system
                    if game.last_year():
                        payload = "Attention, dernière année !"
                        notify_last_line(sql_executor, game_id, payload)  # noqa: F821

            sql_executor.commit()  # noqa: F821
            del sql_executor  # noqa: F821
            # end of protected section

        data = {'late': late, 'unsafe': unsafe, 'missing': missing, 'adjudicated': adjudicated, 'debug_message': debug_message, 'msg': "Forced!"}
        return data, 201


@API.resource('/game-commute-agree-solve/<game_id>')
class GameCommuteAgreeSolveRessource(flask_restful.Resource):  # type: ignore
    """ GameCommuteAgreeSolveRessource """

    def post(self, game_id: int) -> typing.Tuple[None, int]:  # pylint: disable=R0201
        """
        Commute agree to solve from after deadline to now by a clockwork
        EXPOSED
        """
        mylogger.LOGGER.info("/game-commute-agree-solve/<game_id> - POST - commute agreeing from clockwork to solve with orders game id=%s", game_id)

        args = COMMUTE_AGREE_PARSER.parse_args(strict=True)

        adjudication_names = args['adjudication_names']
        now = args['now']

        # needed for sending mails
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        assert game is not None

        # game must not be archive or fast
        if game.fast or game.archive:
            del sql_executor
            flask_restful.abort(404, msg="This game is archive or fast")

        # game must be ongoing
        if game.current_state != 1:
            del sql_executor
            flask_restful.abort(403, msg="Game does not seem to be ongoing")

        # begin of protected section
        with MOVE_GAME_LOCK_TABLE[game.name]:

            # game must not be soloed
            if game.soloed:
                del sql_executor
                flask_restful.abort(403, msg="Game seems to be actually soloed")

            # game must not be end voted
            if game.end_voted:
                del sql_executor
                flask_restful.abort(403, msg="Game seems to be actually end-voted")

            # game must not be actually finished
            if game.finished:
                del sql_executor
                flask_restful.abort(403, msg="Game seems to be actually finished")

            # check orders are required
            actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
            needed_list = [o[1] for o in actives_list]
            if not needed_list:
                del sql_executor
                flask_restful.abort(400, msg="There is no role that require orders")

            # check orders are submitted
            submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
            submitted_list = [o[1] for o in submissions_list]
            if set(submitted_list) != set(needed_list):
                missing_list = list(set(needed_list) - set(submitted_list))
                del sql_executor
                flask_restful.abort(400, msg=f"There is at least a role that does not seem to have submitted orders yet : {missing_list}")

            # check some orders are submitted agreed but after
            definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
            agreed_after_list = [o[1] for o in definitives_list if o[2] == 2]
            if not agreed_after_list:
                del sql_executor
                flask_restful.abort(400, msg="There is no role that agrees to solve but only after the deadline")

            if not game.past_deadline():
                del sql_executor
                flask_restful.abort(400, msg="We are not after deadline, please change deadline first.")

            # handle definitive boolean
            # automaton makes transition 2 (agree after)-> 1 (agree now)
            for role_id in agreed_after_list:
                # late cannot be set here
                status, _, __, ___, adjudicated, debug_message = agree.fake_post(now, game_id, role_id, 1, adjudication_names, sql_executor)
                if not status:
                    break
                if adjudicated:
                    break

            if not status:
                del sql_executor  # noqa: F821
                flask_restful.abort(400, msg=f"Failed to agree (commute) to adjudicate : {debug_message}")

            if adjudicated:

                # reload game
                game = games.Game.find_by_identifier(sql_executor, game_id)
                assert game is not None

                # notify players

                subject = f"La partie {game.name} a avancé (avec l'aide de l'automate)!"
                game_id = game.identifier
                allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
                addressees = []
                for ____, player_id, _____ in allocations_list:
                    addressees.append(player_id)
                body = "Vous pouvez continuer à jouer dans cette partie !\n"
                body += "\n"
                body += "Note : Vous pouvez désactiver cette notification en modifiant un paramètre de votre compte sur le site.\n"
                body += "\n"
                body += "Pour se rendre directement sur la partie :\n"
                body += f"https://diplomania-gen.fr?game={game.name}"

                json_dict = {
                    'addressees': " ".join([str(a) for a in addressees]),
                    'subject': subject,
                    'body': body,
                    'type': 'adjudication',
                }

                host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
                port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
                url = f"{host}:{port}/mail-players"
                # for a rest API headers are presented differently
                req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
                if req_result.status_code != 200:
                    print(f"ERROR from server  : {req_result.text}")
                    message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                    del sql_executor
                    flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

                # declaration from system
                if game.last_year():
                    payload = "Attention, dernière année !"
                    notify_last_line(sql_executor, game_id, payload)  # noqa: F821

            sql_executor.commit()  # noqa: F821
            del sql_executor  # noqa: F821
            # end of protected section

        return None, 201


@API.resource('/game-orders/<game_id>')
class GameOrderRessource(flask_restful.Resource):  # type: ignore
    """ GameOrderRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Submit orders
        EXPOSED
        """

        mylogger.LOGGER.info("/game-orders/<game_id> - POST - submitting orders game id=%s", game_id)

        args = SUBMISSION_PARSER.parse_args(strict=True)

        role_id = args['role_id']
        orders_submitted = args['orders']
        definitive_value = args['definitive']
        names = args['names']
        adjudication_names = args['adjudication_names']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            orders_logger.LOGGER.critical("CRIT-1-NO-TOKEN")
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            orders_logger.LOGGER.critical("CRIT-2-BAD-AUTHENTICATION")
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            orders_logger.LOGGER.critical("CRIT-3-FAILED-ID")
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            orders_logger.LOGGER.critical("CRIT-4-NO-GAME")
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")
        assert game is not None

        # store the game deadline
        game_deadline = datetime.datetime.fromtimestamp(game.deadline, datetime.timezone.utc)

        # Now we have full information for game logger

        # who is player for role ?
        player_id = game.get_role(sql_executor, role_id)

        # must be player
        if user_id != player_id:
            orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-5-NOT-PLAYER")
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the player who corresponds to this role")

        # not allowed for game master
        if role_id == 0 and not game.archive:
            orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-6-NOT-POSSIBLE-MASTER")
            del sql_executor
            flask_restful.abort(403, msg="Submitting orders is not possible for game master for non archive games")

        # archive games and fast games stick to agree now
        if game.fast or game.archive:
            if definitive_value == 2:
                orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR_7-AFTER-FAST-ARCHIVE")
                del sql_executor
                flask_restful.abort(403, msg="Submitting agreement after deadine is not possible for fast or archive games")

        # begin of protected section
        with MOVE_GAME_LOCK_TABLE[game.name]:

            # must not be soloed
            if game.soloed:
                orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-8-SOLOED")
                del sql_executor
                flask_restful.abort(403, msg="Game is soloed!")

            # must not be end voted
            if game.end_voted:
                orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-8bis-END-VOTED")
                del sql_executor
                flask_restful.abort(403, msg="Game is end-voted!")

            # must not be finished
            if game.finished:
                orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-9-FINISHED")
                del sql_executor
                flask_restful.abort(403, msg="Game is finished!")

            # check orders are required
            # needed list : those who need to submit orders
            if role_id != 0:
                actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
                needed_list = [o[1] for o in actives_list]
                if role_id not in needed_list:
                    orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-10-NO-ORDER-REQUIRED")
                    del sql_executor
                    flask_restful.abort(403, msg="This role does not seem to require any orders")

            # extract orders from input
            try:
                the_orders = json.loads(orders_submitted)
            except json.JSONDecodeError:
                orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-11-JSON")
                del sql_executor
                flask_restful.abort(400, msg="Did you convert orders from json to text ?")

            # check the phase
            for the_order in the_orders:
                if game.current_advancement % 5 in [0, 2]:
                    if the_order['order_type'] not in [1, 2, 3, 4, 5]:
                        orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-12-WRONG-PHASE-1")
                        del sql_executor
                        flask_restful.abort(400, msg="Seems we have a move phase, you must provide move orders! (or more probably, you submitted twice or game changed just before you submitted)")
                if game.current_advancement % 5 in [1, 3]:
                    if the_order['order_type'] not in [6, 7]:
                        orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-13-WRONG-PHASE-2")
                        del sql_executor
                        flask_restful.abort(400, msg="Seems we have a retreat phase, you must provide retreat orders! (or more probably, you submitted twice or game changed just before you submitted")
                if game.current_advancement % 5 in [4]:
                    if the_order['order_type'] not in [8, 9]:
                        orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-14-WRONG-PHASE-3")
                        del sql_executor
                        flask_restful.abort(400, msg="Seems we have a adjustements phase, you must provide adjustments orders! (or more probably, you submitted twice or game changed just before you submitted")

            # put in database fake units - units for build orders

            # first we remove the fake units of the role already present
            game_units = units.Unit.list_by_game_id(sql_executor, game_id)  # noqa: F821
            for _, type_num, zone_num, role_num, _, fake in game_units:
                if not fake:
                    continue
                if not (role_id == 0 or role_num == int(role_id)):
                    continue
                fake_unit = units.Unit(int(game_id), type_num, zone_num, role_num, 0, True)
                fake_unit.delete_database(sql_executor)  # noqa: F821

            # we check not building where there is already a unit
            # get the occupied zones
            game_units = units.Unit.list_by_game_id(sql_executor, game_id)  # noqa: F821
            occupied_zones: typing.Set[int] = set()
            for _, _, zone_num, _, _, fake in game_units:
                if not fake:
                    occupied_zones.add(zone_num)
            # check not build on occupied zone
            for the_order in the_orders:
                if the_order['order_type'] == 8:
                    zone_num = the_order['active_unit']['zone']
                    if zone_num in occupied_zones:
                        orders_logger.LOGGER.warning("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "15-BUILD-ALREADY")
                        del sql_executor
                        flask_restful.abort(400, msg="Trying to build in a zone where there is already a unit")

            # then we put the incoming ones in the database
            inserted_fake_unit_list: typing.List[typing.List[int]] = []
            for the_order in the_orders:
                if the_order['order_type'] == 8:
                    type_num = the_order['active_unit']['type_unit']
                    role_num = the_order['active_unit']['role']
                    zone_num = the_order['active_unit']['zone']
                    inserted_fake_unit_list.append([type_num, zone_num, role_num])
                    fake_unit = units.Unit(int(game_id), type_num, zone_num, role_num, 0, True)
                    # insert
                    fake_unit.update_database(sql_executor)  # noqa: F821

            # now checking validity of orders

            # evaluate variant
            variant_name = game.variant
            variant_dict = variants.Variant.get_by_name(variant_name)
            if variant_dict is None:
                orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-16-NO-VARIANT")
                del sql_executor
                flask_restful.abort(404, msg=f"Variant {variant_name} doesn't exist")
            variant_dict_json = json.dumps(variant_dict)

            # evaluate situation

            # situation: get ownerships
            ownership_dict: typing.Dict[str, int] = {}
            game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)  # noqa: F821
            for _, center_num, role_num in game_ownerships:
                ownership_dict[str(center_num)] = role_num

            # situation: get units
            game_units = units.Unit.list_by_game_id(sql_executor, game_id)  # noqa: F821
            unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
            fake_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
            dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
            for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
                if fake:
                    # ignore units built by other roles (otherwise may guess other builds)
                    if role_id not in (0, role_num):
                        continue
                    fake_unit_dict[str(role_num)].append([type_num, zone_num])
                elif region_dislodged_from_num:
                    dislodged_unit_dict[str(role_num)].append([type_num, zone_num, region_dislodged_from_num])
                else:
                    unit_dict[str(role_num)].append([type_num, zone_num])

            # situation: get forbiddens
            forbidden_list = []
            game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)  # noqa: F821
            for _, region_num in game_forbiddens:
                forbidden_list.append(region_num)

            # apply visibility if the game position is protected
            if game.fog:

                orders_list2: typing.List[typing.List[int]] = []
                fake_units_list2: typing.List[typing.List[int]] = []
                seen_regions_list: typing.List[int] = []

                # now we can start hiding stuff
                # this will update last parameters
                apply_visibility(variant_name, role_id, ownership_dict, dislodged_unit_dict, unit_dict, forbidden_list, orders_list2, fake_units_list2, seen_regions_list)

                # get imagined units
                imagined_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
                imagined_game_units = imagined_units.ImaginedUnit.list_by_game_id_role_num(sql_executor, game_id, role_id)  # noqa: F821
                for _, _, type_num, zone_num, role_num in imagined_game_units:
                    imagined_unit_dict[str(role_num)].append([type_num, zone_num])

                # add them to submission
                for role_num1, role_units1 in unit_dict.items():
                    if role_num1 in imagined_unit_dict:
                        role_units1.extend(imagined_unit_dict[role_num1])

            situation_dict = {
                'ownerships': ownership_dict,
                'dislodged_ones': dislodged_unit_dict,
                'units': unit_dict,
                'fake_units': fake_unit_dict,
                'forbiddens': forbidden_list,
            }
            situation_dict_json = json.dumps(situation_dict)

            orders_list = []
            for the_order in the_orders:
                order = orders.Order(int(game_id), 0, 0, 0, 0, 0)
                order.load_json(the_order)
                order_export = order.export()
                orders_list.append(order_export)

            orders_list_json = json.dumps(orders_list)

            json_dict = {
                'variant': variant_dict_json,
                'advancement': game.current_advancement,
                'situation': situation_dict_json,
                'orders': orders_list_json,
                'names': names,
                'role': role_id,
            }

            # post to solver
            host = lowdata.SERVER_CONFIG['SOLVER']['HOST']
            port = lowdata.SERVER_CONFIG['SOLVER']['PORT']
            url = f"{host}:{port}/solve"
            req_result = SESSION.post(url, data=json_dict)

            if 'msg' in req_result.json():
                submission_report = req_result.json()['msg']
            else:
                submission_report = "\n".join([req_result.json()['stderr'], req_result.json()['stdout']])

            # adjudication failed
            if req_result.status_code != 201:

                # we remove the inserted fake units
                for type_num, zone_num, role_num in inserted_fake_unit_list:
                    fake_unit = units.Unit(int(game_id), type_num, zone_num, role_num, 0, True)
                    # remove
                    fake_unit.delete_database(sql_executor)  # noqa: F821

                print(f"ERROR from solve server  : {req_result.text}")
                orders_logger.LOGGER.warning("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "17-ORDERS-REJECTED")
                del sql_executor
                flask_restful.abort(400, msg=f":-( {submission_report}")

            # ok so orders are accepted

            # store orders

            # purge previous

            # get list
            if int(role_id) != 0:
                previous_orders = orders.Order.list_by_game_id_role_num(sql_executor, int(game_id), role_id)  # noqa: F821
            else:
                previous_orders = orders.Order.list_by_game_id(sql_executor, int(game_id))  # noqa: F821

            # purge
            for (_, role_num, _, zone_num, _, _) in previous_orders:
                order = orders.Order(int(game_id), role_num, 0, zone_num, 0, 0)
                order.delete_database(sql_executor)  # noqa: F821

            # insert new ones
            for the_order in the_orders:
                order = orders.Order(int(game_id), 0, 0, 0, 0, 0)
                order.load_json(the_order)
                order.update_database(sql_executor)  # noqa: F821

                # special case : build : create a fake unit
                # this was done before submitting
                # we tolerate that some extra fake unit may persist from previous submission

            # insert this submisssion (if not game master)
            if role_id != 0:
                submission = submissions.Submission(int(game_id), int(role_id))
                submission.update_database(sql_executor)  # noqa: F821

            # handle definitive boolean
            # player submitted orders and agreed (or not) to adjudicate
            now = time.time()
            status, late, unsafe, missing, adjudicated, debug_message = agree.fake_post(now, game_id, role_id, definitive_value, adjudication_names, sql_executor)  # noqa: F821

            if not status:
                orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-18-FAILED-AGREE")
                del sql_executor  # noqa: F821
                flask_restful.abort(400, msg=f"Failed to agree to adjudicate : {debug_message}")

            if adjudicated:

                # reload game
                game = games.Game.find_by_identifier(sql_executor, game_id)  # noqa: F821
                assert game is not None

                if not (game.fast or game.archive):

                    # notify players
                    subject = f"La partie {game.name} a avancé !"
                    game_id = game.identifier
                    allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)  # noqa: F821
                    addressees = []
                    for _, player_id, __ in allocations_list:
                        addressees.append(player_id)
                    body = "Bonjour !\n"
                    body += "\n"
                    body += "Vous pouvez continuer à jouer dans cette partie !\n"
                    body += "\n"
                    body += "Note : Vous pouvez désactiver cette notification en modifiant un paramètre de votre compte sur le site.\n"
                    body += "\n"
                    body += "Pour se rendre directement sur la partie :\n"
                    body += f"https://diplomania-gen.fr?game={game.name}"

                    json_dict = {
                        'addressees': " ".join([str(a) for a in addressees]),
                        'subject': subject,
                        'body': body,
                        'type': 'adjudication',
                    }

                    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
                    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
                    url = f"{host}:{port}/mail-players"
                    # for a rest API headers are presented differently
                    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
                    if req_result.status_code != 200:
                        print(f"ERROR from server  : {req_result.text}")
                        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                        orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-19-FAILED-SEND-NOTIFICATION")
                        del sql_executor
                        flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

                    # declaration from system
                    if game.last_year():
                        payload = "Attention, dernière année !"
                        notify_last_line(sql_executor, game_id, payload)  # noqa: F821

            else:

                # put passive players in disorder (must be done by first player to actually submit orders in first turn so not to be in game creation of game start)

                variant_name = game.variant
                variant_data = variants.Variant.get_by_name(variant_name)
                assert variant_data is not None

                for role_id_str in variant_data['disorder']:
                    role_id = int(role_id_str)
                    status, _, message = agree.disorder(game_id, role_id, game, variant_data, adjudication_names, sql_executor)  # noqa: F821
                    if not status:
                        orders_logger.LOGGER.error("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "ERR-20-FAILED-SET-DISORDER")
                        del sql_executor
                        flask_restful.abort(400, msg=f"Failed to set power {role_id} in disorder : {message}")

            sql_executor.commit()  # noqa: F821
            del sql_executor  # noqa: F821
            # end of protected section

        orders_logger.LOGGER.info("pseudo=%s game=%s role=%d definitive=%d deadline=%s info=%s", pseudo, game.name, role_id, definitive_value, game_deadline, "100-SUBMITTED!")

        data = {'late': late, 'unsafe': unsafe, 'missing': missing, 'adjudicated': adjudicated, 'debug_message': debug_message, 'msg': submission_report}

        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets orders
        EXPOSED
        """

        mylogger.LOGGER.info("/game-orders/<game_id> - GET - getting back orders game id=%s", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(sql_executor, player_id)
        if role_id is None:
            del sql_executor
            flask_restful.abort(403, msg=f"You do not seem to play or master game {game_id}")

        # not allowed for game master
        if role_id == 0 and not game.archive:
            del sql_executor
            flask_restful.abort(403, msg="Getting submitted orders is not possible for game master for non archive game")

        # get orders
        assert role_id is not None
        if role_id == 0:
            orders_list = orders.Order.list_by_game_id(sql_executor, game_id)
        else:
            orders_list = orders.Order.list_by_game_id_role_num(sql_executor, game_id, role_id)

        # get fake units
        if role_id == 0:
            units_list = units.Unit.list_by_game_id(sql_executor, game_id)
        else:
            units_list = units.Unit.list_by_game_id_role_num(sql_executor, game_id, role_id)
        fake_units_list = [u for u in units_list if u[5]]

        del sql_executor

        data = {
            'orders': orders_list,
            'fake_units': fake_units_list,
        }
        return data, 200


@API.resource('/game-force-no-orders/<game_id>')
class GameForceNoOrderRessource(flask_restful.Resource):  # type: ignore
    """ GameForceNoOrderRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Submit civil disorder
        EXPOSED
        """

        mylogger.LOGGER.info("/game-force-no-orders/<game_id> - POST - submitting civil disorder game id=%s", game_id)

        args = SUBMISSION_PARSER2.parse_args(strict=True)

        role_id = args['role_id']
        names = args['names']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check user has right to submit civil disorder - must be game master

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # find game master
        assert game is not None
        game_master_id = game.get_role(sql_executor, 0)

        # must be game master or commuter
        if user_id != game_master_id and pseudo != COMMUTER_ACCOUNT:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game of the commuter")

        if role_id == 0:
            del sql_executor
            flask_restful.abort(400, msg="Invalid role_id parameter")

        # check orders are required
        # needed list : those who need to submit orders
        actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
        needed_list = [o[1] for o in actives_list]
        if role_id not in needed_list:
            del sql_executor
            flask_restful.abort(400, msg="This role does not seem to require any orders")

        # are civil disorders allowed for the game ?
        if not game.civil_disorder_allowed():
            del sql_executor
            flask_restful.abort(400, msg="Civil disorder in this game, for this season, does not seem to be allowed. Replace player.")

        # evaluate variant
        variant_name = game.variant
        variant_dict = variants.Variant.get_by_name(variant_name)
        if variant_dict is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Variant {variant_name} doesn't exist")

        variant_dict_json = json.dumps(variant_dict)

        # evaluate situation

        # situation: get ownerships
        ownership_dict: typing.Dict[str, int] = {}
        game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
        for _, center_num, role_num in game_ownerships:
            ownership_dict[str(center_num)] = role_num

        # situation: get units
        game_units = units.Unit.list_by_game_id(sql_executor, game_id)
        unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        fake_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
            if fake:
                fake_unit_dict[str(role_num)].append([type_num, zone_num])
            elif region_dislodged_from_num:
                dislodged_unit_dict[str(role_num)].append([type_num, zone_num, region_dislodged_from_num])
            else:
                unit_dict[str(role_num)].append([type_num, zone_num])

        # situation: get forbiddens
        forbidden_list = []
        game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)
        for _, region_num in game_forbiddens:
            forbidden_list.append(region_num)

        situation_dict = {
            'ownerships': ownership_dict,
            'dislodged_ones': dislodged_unit_dict,
            'units': unit_dict,
            'fake_units': fake_unit_dict,
            'forbiddens': forbidden_list,
        }
        situation_dict_json = json.dumps(situation_dict)

        json_dict = {
            'variant': variant_dict_json,
            'advancement': game.current_advancement,
            'situation': situation_dict_json,
            'names': names,
            'role': role_id,
        }

        # post to disorderer
        host = lowdata.SERVER_CONFIG['SOLVER']['HOST']
        port = lowdata.SERVER_CONFIG['SOLVER']['PORT']
        url = f"{host}:{port}/disorder"
        req_result = SESSION.post(url, data=json_dict)

        if 'msg' in req_result.json():
            submission_report = req_result.json()['msg']
        else:
            submission_report = "\n".join([req_result.json()['stderr'], req_result.json()['stdout']])

        # adjudication failed
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(400, msg=f"Failed to submit civil disorder {message} : {submission_report}")

        # ok so orders are made up ok

        orders_default = req_result.json()['orders_default']

        # store orders

        # purge previous

        previous_orders = orders.Order.list_by_game_id_role_num(sql_executor, int(game_id), role_id)

        # purge
        for (_, role_num, _, zone_num, _, _) in previous_orders:
            order = orders.Order(int(game_id), role_num, 0, zone_num, 0, 0)
            order.delete_database(sql_executor)

        # insert new ones
        for the_order in orders_default:
            order = orders.Order(int(game_id), 0, 0, 0, 0, 0)
            order.load_json(the_order)
            order.update_database(sql_executor)

            # special case : build : create a fake unit
            # this was done before submitting
            # we tolerate that some extra fake unit may persist from previous submission

        # insert this submission
        submission = submissions.Submission(int(game_id), int(role_id))
        submission.update_database(sql_executor)

        # insert incident2 (civil disorder)
        advancement = game.current_advancement
        incident2 = incidents2.Incident2(int(game_id), int(role_id), advancement)
        incident2.update_database(sql_executor)  # noqa: F821

        sql_executor.commit()
        del sql_executor

        data = {'msg': f"Ok civil disorder submitted {submission_report}"}
        return data, 201


@API.resource('/game-communication-orders/<game_id>')
class GameCommunicationOrderRessource(flask_restful.Resource):  # type: ignore
    """ GameCommunicationOrderRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Submit communication orders
        EXPOSED
        """

        mylogger.LOGGER.info("/game-communication-orders/<game_id> - POST - submitting communication orders game id=%s", game_id)

        args = SUBMISSION_PARSER3.parse_args(strict=True)

        role_id = args['role_id']
        communication_orders_submitted = args['orders']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # not allowed for game master
        if role_id == 0:
            flask_restful.abort(403, msg="Submitting communication orders is not possible for game master")

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is player for role ?
        assert game is not None
        player_id = game.get_role(sql_executor, role_id)

        # must be player
        if user_id != player_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the player who corresponds to this role")

        # situation: get units
        game_units = units.Unit.list_by_game_id(sql_executor, game_id)
        unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
            if fake:
                pass
            elif region_dislodged_from_num:
                unit_dict[str(role_num)].append([type_num, zone_num])
            else:
                unit_dict[str(role_num)].append([type_num, zone_num])

        # apply visibility if the game is fog
        if game.fog:

            # situation: get ownerships
            ownership_dict: typing.Dict[str, int] = {}
            game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)  # noqa: F821
            for _, center_num, role_num in game_ownerships:
                ownership_dict[str(center_num)] = role_num

            # now we can start hiding stuff
            # need these two parameters
            dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = {}
            forbidden_list: typing.List[int] = []

            orders_list2: typing.List[typing.List[int]] = []
            fake_units_list2: typing.List[typing.List[int]] = []
            seen_regions_list: typing.List[int] = []

            # this will update last parameters
            variant_name = game.variant
            apply_visibility(variant_name, role_id, ownership_dict, dislodged_unit_dict, unit_dict, forbidden_list, orders_list2, fake_units_list2, seen_regions_list)

        # check orders (rough check)

        try:
            the_communication_orders = json.loads(communication_orders_submitted)
        except json.JSONDecodeError:
            del sql_executor
            flask_restful.abort(400, msg="Did you convert orders from json to text ?")

        for the_communication_order in the_communication_orders:
            communication_order = communication_orders.CommunicationOrder(int(game_id), 0, 0, 0, 0, 0)
            communication_order.load_json(the_communication_order)
            role_num, order_type_num, active_unit_zone_num, _, _ = communication_order.export()

            # check that order

            # cannot order if not active

            actives_list = actives.Active.list_by_game_id_role_num(sql_executor, game_id, role_num)  # noqa: F821
            if not actives_list:
                del sql_executor
                flask_restful.abort(400, msg="Passed a communication order for role not active")

            # cannot order for someone else
            if role_num != role_id:
                del sql_executor
                flask_restful.abort(400, msg="Passed a communication order for unit not owned")

            # cannot order for a non existing unit
            if active_unit_zone_num not in {u[1] for u in unit_dict[str(role_num)]}:
                del sql_executor
                flask_restful.abort(400, msg="Passed a communication order for a non existing unit")

            # cannot order a non movement order (with front end cannot happen)
            if order_type_num not in [1, 2, 3, 4, 5]:
                del sql_executor
                flask_restful.abort(400, msg="Passed a communication order but not in movement phase")

        # ok so orders are accepted

        # store orders

        # purge previous

        # get list
        previous_communication_orders = communication_orders.CommunicationOrder.list_by_game_id_role_num(sql_executor, int(game_id), role_num)  # noqa: F821

        # purge
        for (_, role_num, _, zone_num, _, _) in previous_communication_orders:
            communication_order = communication_orders.CommunicationOrder(int(game_id), role_num, 0, zone_num, 0, 0)
            communication_order.delete_database(sql_executor)  # noqa: F821

        # insert new ones
        for the_communication_order in the_communication_orders:
            communication_order = communication_orders.CommunicationOrder(int(game_id), 0, 0, 0, 0, 0)
            communication_order.load_json(the_communication_order)
            communication_order.update_database(sql_executor)  # noqa: F821

        sql_executor.commit()  # noqa: F821
        del sql_executor  # noqa: F821

        data = {'msg': "Ok communication orders stored"}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets communication orders
        EXPOSED
        """

        mylogger.LOGGER.info("/game-communication-orders/<game_id> - GET - getting back communication orders game id=%s", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # check user has right to get orders - must be player or game master

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(sql_executor, player_id)
        if role_id is None:
            del sql_executor
            flask_restful.abort(403, msg=f"You do not seem to play or master game {game_id}")

        # not allowed for game master
        if role_id == 0:
            del sql_executor
            flask_restful.abort(403, msg="Getting communication orders is not possible for game master")

        # get orders
        assert role_id is not None
        communication_orders_list = communication_orders.CommunicationOrder.list_by_game_id_role_num(sql_executor, game_id, role_id)

        fake_units_list: typing.List[int] = []

        del sql_executor

        data = {
            'orders': communication_orders_list,
            'fake_units': fake_units_list,
        }
        return data, 200


@API.resource('/game-orders-submitted/<game_id>')
class GameOrdersSubmittedRessource(flask_restful.Resource):  # type: ignore
    """ GameOrdersSubmittedRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[int]], int]:  # pylint: disable=R0201
        """
        Gets list of roles which have submitted orders, orders are missing, orders are not needed for given game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-orders-submitted/<game_id> - GET - getting which orders submitted, missing, not needed for game id=%s", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        # check user has right to get status of orders - must be game master or player in game - or admin

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(sql_executor, player_id)
        if role_id is None:

            # check moderator rights

            # get moderator list
            host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
            port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/moderators"
            req_result = SESSION.get(url)
            if req_result.status_code != 200:
                del sql_executor
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
            the_moderators = req_result.json()

            # check pseudo in moderator list
            if pseudo not in the_moderators and pseudo != COMMUTER_ACCOUNT:
                del sql_executor
                flask_restful.abort(403, msg="You do not seem to play or master the game (or to be site moderator or the commuter) so you are not alowed to see the submissions!")

        # submissions_list : those who submitted orders
        submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
        submitted_list = [o[1] for o in submissions_list]

        # definitives_list : those who agreed to adjudicate with their orders nows
        definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
        agreed_now_list = [o[1] for o in definitives_list if o[2] == 1]
        agreed_after_list = [o[1] for o in definitives_list if o[2] == 2]

        # you get only information for your own role
        if role_id is not None and role_id != 0:
            submitted_list = [r for r in submitted_list if r == role_id]
            agreed_now_list = [r for r in agreed_now_list if r == role_id]
            agreed_after_list = [r for r in agreed_after_list if r == role_id]

        # needed list : those who need to submit orders
        actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
        needed_list = [o[1] for o in actives_list]

        del sql_executor

        data = {'submitted': submitted_list, 'agreed_now': agreed_now_list, 'agreed_after': agreed_after_list, 'needed': needed_list}
        return data, 200


@API.resource('/all-player-games-ongoing-votes')
class AllPlayerGamesOngoingVotesRessource(flask_restful.Resource):  # type: ignore
    """ AllPlayerGamesOngoingVotesRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Dict[int, int]], int]:  # pylint: disable=R0201
        """
        Gets list of games where a vote is ongoing
        EXPOSED
        """

        mylogger.LOGGER.info("/all-player-games-ongoing-votes - GET - getting games where vote is ongoing for my games")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # get list of games in which player is involved
        allocations_list = allocations.Allocation.list_by_player_id(sql_executor, player_id)

        dict_voted_list: typing.Dict[int, int] = {}
        for game_id, _, _ in allocations_list:

            # definitives_list : those who agreed to adjudicate with their orders now
            votes_list = votes.Vote.list_by_game_id(sql_executor, game_id)

            # just say there is or not some votes
            dict_voted_list[game_id] = len(votes_list)

        del sql_executor

        data = {'dict_voted': dict_voted_list}
        return data, 200


@API.resource('/all-player-games-orders-submitted')
class AllPlayerGamesOrdersSubmittedRessource(flask_restful.Resource):  # type: ignore
    """ AllPlayerGamesOrdersSubmittedRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Dict[int, typing.List[int]]], int]:  # pylint: disable=R0201
        """
        Gets list of roles which have submitted orders, orders are missing, orders are not needed for all my games
        EXPOSED
        """

        mylogger.LOGGER.info("/all-player-games-orders-submitted - GET - getting orders status for my games")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # get list of games in which player is involved
        allocations_list = allocations.Allocation.list_by_player_id(sql_executor, player_id)

        dict_submitted_list: typing.Dict[int, typing.List[int]] = {}
        dict_agreed_now_list: typing.Dict[int, typing.List[int]] = {}
        dict_agreed_after_list: typing.Dict[int, typing.List[int]] = {}
        dict_needed_list: typing.Dict[int, typing.List[int]] = {}
        for game_id, _, role_id in allocations_list:

            # submissions_list : those who submitted orders
            submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
            submitted_list = [o[1] for o in submissions_list]

            # definitives_list : those who agreed to adjudicate with their orders now
            definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
            agreed_now_list = [o[1] for o in definitives_list if o[2] == 1]
            agreed_after_list = [o[1] for o in definitives_list if o[2] == 2]

            # game is anonymous : you get only information for your own role
            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None
            if game.anonymous:
                if role_id is not None and role_id != 0:
                    submitted_list = [r for r in submitted_list if r == role_id]
                    agreed_now_list = [r for r in agreed_now_list if r == role_id]
                    agreed_after_list = [r for r in agreed_after_list if r == role_id]

            dict_submitted_list[game_id] = submitted_list
            dict_agreed_now_list[game_id] = agreed_now_list
            dict_agreed_after_list[game_id] = agreed_after_list

            # needed list : those who need to submit orders
            actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
            needed_list = [o[1] for o in actives_list]
            dict_needed_list[game_id] = needed_list

        del sql_executor

        data = {'dict_submitted': dict_submitted_list, 'dict_agreed_now': dict_agreed_now_list, 'dict_agreed_after': dict_agreed_after_list, 'dict_needed': dict_needed_list}
        return data, 200


@API.resource('/all-games-missing-orders')
class AllGamesMissingOrdersRessource(flask_restful.Resource):  # type: ignore
    """ AllGamesMissingOrdersRessource """

    def get(self) -> typing.Tuple[typing.Dict[int, typing.Dict[int, int]], int]:  # pylint: disable=R0201
        """
        Gets list of roles which are late all ongoing games
        EXPOSED
        """

        mylogger.LOGGER.info("/all-games-late-orders - GET - getting which are late for all ongoing games")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # check moderator rights

        # get moderator list
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/moderators"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
        the_moderators = req_result.json()

        # check pseudo in moderator list
        if pseudo not in the_moderators:
            flask_restful.abort(403, msg="You do not seem to be site moderator) so you are not alowed to see all the missing orders!")

        # result to build
        dict_missing_list: typing.Dict[int, typing.Dict[int, int]] = {}

        sql_executor = database.SqlExecutor()
        games_list = sql_executor.execute("select identifier from games", need_result=True)
        if not games_list:
            games_list = []
        games_id_list = [g[0] for g in games_list]

        for game_id in games_id_list:

            # game is not ongoing : ignore
            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None
            if game.current_state != 1:
                continue

            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            role2player = {r: p for _, p, r in allocations_list}

            # needed list : those who need to submit orders
            actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
            needed_list = [o[1] for o in actives_list]

            # submissions_list : those who submitted orders
            submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
            submitted_list = [o[1] for o in submissions_list]

            # definitives_list : those who agreed to adjudicate with their orders now
            definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
            agreed_now_after_list = [o[1] for o in definitives_list if o[2] in [1, 2]]

            # missing_list
            missing_list = [r for r in needed_list if r not in submitted_list or r not in agreed_now_after_list]
            dict_missing_list[game_id] = {r: role2player[r] for r in missing_list if r in role2player}

        del sql_executor

        data = dict_missing_list
        return data, 200


@API.resource('/simulation')
class SimulationRessource(flask_restful.Resource):  # type: ignore
    """ SimulationRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Performs a simulation
        EXPOSED
        """

        mylogger.LOGGER.info("/simulation - POST - simulation")

        args = SIMULATION_PARSER.parse_args(strict=True)

        variant_name = args['variant_name']
        orders_submitted = args['orders']
        units_submitted = args['units']
        names = args['names']

        mylogger.LOGGER.info("variant_name=%s orders_submitted=%s units_submitted=%s", variant_name, orders_submitted, units_submitted)  # names not logged

        # evaluate variant
        variant_dict = variants.Variant.get_by_name(variant_name)
        if variant_dict is None:
            flask_restful.abort(404, msg=f"Variant {variant_name} doesn't exist")

        variant_dict_json = json.dumps(variant_dict)

        # evaluate situation

        try:
            the_units = json.loads(units_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert units from json to text ?")

        # situation: get ownerships
        ownership_dict: typing.Dict[str, int] = {}

        # situation: get units
        unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        for the_unit in the_units:
            type_num = the_unit['type_unit']
            zone_num = the_unit['zone']
            role_num = the_unit['role']
            unit_dict[str(role_num)].append([type_num, zone_num])

        # no fake unit at this point
        fake_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = {}

        # no dislodged unit at this point
        dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = {}

        # no forbiddens at this point
        forbidden_list: typing.List[int] = []

        # need to have one
        game_fake_advancement = 0

        situation_dict = {
            'ownerships': ownership_dict,
            'dislodged_ones': dislodged_unit_dict,
            'units': unit_dict,
            'fake_units': fake_unit_dict,
            'forbiddens': forbidden_list,
        }
        situation_dict_json = json.dumps(situation_dict)

        # evaluate orders
        orders_list = []

        try:
            the_orders = json.loads(orders_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert orders from json to text ?")

        for the_order in the_orders:
            order = orders.Order(0, 0, 0, 0, 0, 0)
            order.load_json(the_order)
            order_export = order.export()
            orders_list.append(order_export)

        orders_list_json = json.dumps(orders_list)

        json_dict = {
            'variant': variant_dict_json,
            'advancement': game_fake_advancement,
            'situation': situation_dict_json,
            'orders': orders_list_json,
            'names': names,
        }

        # post to solver
        host = lowdata.SERVER_CONFIG['SOLVER']['HOST']
        port = lowdata.SERVER_CONFIG['SOLVER']['PORT']
        url = f"{host}:{port}/solve"
        req_result = SESSION.post(url, data=json_dict)

        if 'msg' in req_result.json():
            adjudication_report = req_result.json()['msg']
        else:
            adjudication_report = "\n".join([req_result.json()['stderr'], req_result.json()['stdout']])

        # adjudication failed
        if req_result.status_code != 201:
            print(f"ERROR from solve server  : {req_result.text}")
            flask_restful.abort(404, msg=f":-( {adjudication_report}")

        # extract new report
        orders_result = req_result.json()['orders_result']
        orders_result_simplified = orders_result

        data = {
            'msg': f"Ok adjudication performed : {adjudication_report}",
            'result': f"{orders_result_simplified}"}
        return data, 201


POST_MESSAGE_LOCK = threading.Lock()
POST_MESSAGE_REPEAT_PREVENTER = RepeatPreventer()


@API.resource('/game-messages/<game_id>')
class GameMessageRessource(flask_restful.Resource):  # type: ignore
    """  GameMessageRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Insert message in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-messages/<game_id> - POST - creating new message game id=%s", game_id)

        args = MESSAGE_PARSER.parse_args(strict=True)

        role_id = args['role_id']
        role_name = args['role_name']
        dest_role_ids_submitted = args['dest_role_ids']
        payload = args['content']

        # protection from "surrogates not allowed"
        payload_safe = payload.encode('utf-8', errors='ignore').decode()

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # check user has right to post message - must be player of game master

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # find player for role
        assert game is not None
        expected_id = game.get_role(sql_executor, role_id)

        # can be player of game master but must correspond
        if user_id != expected_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game or the player in charge of the role")

        # get destinees
        try:
            dest_role_ids = list(map(int, dest_role_ids_submitted.split()))
        except:  # noqa: E722 pylint: disable=bare-except
            del sql_executor
            flask_restful.abort(400, msg="Bad list of addresses identifiers. Use a space separated list of numbers")

        if not dest_role_ids:
            del sql_executor
            flask_restful.abort(400, msg="There should be at least one destinee")

        nb_addressees = len(dest_role_ids)

        # checks relative to message

        if game.nomessage_current:

            # find game master
            assert game is not None
            game_master_id = game.get_role(sql_executor, 0)  # noqa: F821

            # is game master sending or are we sending to game master only ?
            if not (user_id == game_master_id or dest_role_ids == [0]):
                del sql_executor
                flask_restful.abort(403, msg="Only game master may send or receive message in 'no message' game")

        # create message here
        with POST_MESSAGE_LOCK:

            if not POST_MESSAGE_REPEAT_PREVENTER.can(int(game_id), role_id):
                del sql_executor
                flask_restful.abort(400, msg="You have already messaged a very short time ago")

            # create a content
            identifier = contents.Content.free_identifier(sql_executor)  # noqa: F821
            time_stamp = int(time.time())  # now
            content = contents.Content(identifier, int(game_id), time_stamp, payload_safe)
            content.update_database(sql_executor)  # noqa: F821

            # create a message linked to the content
            for dest_role_id in dest_role_ids:
                message = messages.Message(int(game_id), role_id, dest_role_id, identifier)
                message.update_database(sql_executor)  # noqa: F821

            POST_MESSAGE_REPEAT_PREVENTER.did(int(game_id), role_id)

        subject = f"Un joueur (ou l'arbitre) vous a envoyé un message dans la partie {game.name}"
        allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)  # noqa: F821
        addressees = []
        for _, player_id, role_id1 in allocations_list:
            if role_id1 in dest_role_ids:
                addressees.append(player_id)
        body = "Bonjour !\n"
        body += "\n"

        body += f"Auteur du message : {role_name}\n"
        body += "\n"
        body += "Contenu du message :\n"
        body += "================\n"
        body += payload_safe
        body += "\n"
        body += "================\n"

        body += "Vous pouvez aller consulter le message et y répondre sur le site....\n"
        body += "\n"
        body += "Note : Vous pouvez désactiver cette notification en modifiant un paramètre de votre compte sur le site.\n"
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={game.name}"

        json_dict = {
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'type': 'message',
        }

        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"
        # for a rest API headers are presented differently
        req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

        sql_executor.commit()  # noqa: F821
        del sql_executor  # noqa: F821

        data = {'msg': f"Ok {nb_addressees} message(s) inserted"}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets all or some messages of game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-messages/<game_id> - GET - getting back messages game id=%s", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # check user has right to read message - must be player of game master

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(sql_executor, player_id)
        if role_id is None:
            del sql_executor
            flask_restful.abort(403, msg=f"You do not seem to play or master game {game_id}")

        # gather messages
        assert role_id is not None
        messages_extracted_list = messages.Message.list_with_content_by_game_id(sql_executor, game_id)

        # get all message
        messages_dict_mess: typing.Dict[int, typing.Tuple[int, int, contents.Content]] = {}
        messages_dict_dest: typing.Dict[int, typing.List[int]] = collections.defaultdict(list)
        for _, identifier, author_num, addressee_num, time_stamp, content in messages_extracted_list:
            if identifier not in messages_dict_mess:
                messages_dict_mess[identifier] = author_num, time_stamp, content
            messages_dict_dest[identifier].append(addressee_num)

        # extract the ones not concerned
        messages_list: typing.List[typing.Tuple[int, int, int, typing.List[int], str]] = []
        for identifier, (author_num, time_stamp, content) in messages_dict_mess.items():
            addressees_num = messages_dict_dest[identifier]
            if role_id == author_num or role_id in addressees_num:
                messages_list.append((identifier, author_num, time_stamp, addressees_num, content.payload))

        del sql_executor

        data = {
            'messages_list': messages_list,
        }
        return data, 200


POST_DECLARATION_REPEAT_PREVENTER = RepeatPreventer()
POST_DECLARATION_LOCK = threading.Lock()


@API.resource('/game-declarations/<game_id>')
class GameDeclarationRessource(flask_restful.Resource):  # type: ignore
    """  GameDeclarationRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Insert declaration in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-declarations/<game_id> - POST - creating new declaration game id=%s", game_id)

        args = DECLARATION_PARSER.parse_args(strict=True)

        role_id = args['role_id']
        role_name = args['role_name']
        anonymous = args['anonymous']
        announce = args['announce']
        payload = args['content']

        # protection from "surrogates not allowed"
        payload_safe = payload.encode('utf-8', errors='ignore').decode()

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check user has right to post declatation - must be player of game master or moderator if announce

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        assert game is not None

        if announce:

            if role_id != 0:
                del sql_executor
                flask_restful.abort(404, msg="Must pretend to be game master for announce")

            # use the user_id as role
            role_id = user_id

            if anonymous:
                del sql_executor
                flask_restful.abort(404, msg="Must not be anonymous for announce")

            # check moderator rights

            # get moderator list
            host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
            port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/moderators"
            req_result = SESSION.get(url)
            if req_result.status_code != 200:
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                del sql_executor
                flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
            the_moderators = req_result.json()

            # check pseudo in moderator list
            if pseudo not in the_moderators:
                del sql_executor
                flask_restful.abort(403, msg="You need to be site moderator to post an announce in a game")

        else:

            # who is player for role ?
            expected_id = game.get_role(sql_executor, role_id)

            # can be player of game master but must correspond
            if user_id != expected_id:
                del sql_executor
                flask_restful.abort(403, msg="You do not seem to be the game master of the game or the player in charge of the role")

            # checks relative to no press
            if game.nopress_current:

                # find game master
                assert game is not None
                game_master_id = game.get_role(sql_executor, 0)

                # must be game master
                if user_id != game_master_id:
                    del sql_executor
                    flask_restful.abort(403, msg="Only game master may declare in a 'no press' game")

        # create declaration here
        with POST_DECLARATION_LOCK:

            if not POST_DECLARATION_REPEAT_PREVENTER.can(int(game_id), role_id):
                del sql_executor
                flask_restful.abort(400, msg="You have already declared a very short time ago")

            # create a content
            identifier = contents.Content.free_identifier(sql_executor)
            time_stamp = int(time.time())  # now
            content = contents.Content(identifier, int(game_id), time_stamp, payload_safe)
            content.update_database(sql_executor)

            # create a declaration linked to the content
            declaration = declarations.Declaration(int(game_id), role_id, anonymous, announce, identifier)
            declaration.update_database(sql_executor)

            POST_DECLARATION_REPEAT_PREVENTER.did(int(game_id), role_id)

        if announce:
            subject = f"Un modérateur a posté une déclaration (annonce) dans la partie {game.name}"
        elif anonymous:
            subject = f"Un joueur (ou l'arbitre) a posté une déclaration anonyme dans la partie {game.name}"
        elif role_id == 0:
            subject = f"L'arbitre a posté une déclaration dans la partie {game.name}"
        else:
            subject = f"Un joueur a posté une déclaration dans la partie {game.name}"
        allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
        addressees = []
        for _, player_id, role_id1 in allocations_list:
            if role_id1 != role_id:
                addressees.append(player_id)
        body = "Bonjour !\n"
        body += "\n"

        if announce:
            body += f"Auteur de la déclaration (annonce) : {pseudo}\n"
            body += "\n"
        elif not anonymous:
            body += f"Auteur de la déclaration : {role_name}\n"
            body += "\n"
        body += "Contenu de la déclaration :\n"
        body += "================\n"
        body += payload_safe
        body += "\n"
        body += "================\n"

        body += "Vous pouvez aller consulter la déclaration et y répondre sur le site !\n"
        body += "\n"
        body += "Note : Vous pouvez désactiver cette notification en modifiant un paramètre de votre compte sur le site.\n"
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={game.name}"

        json_dict = {
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'type': 'message',
        }

        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"
        # for a rest API headers are presented differently
        req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

        sql_executor.commit()
        del sql_executor

        data = {'msg': "Ok declaration inserted."}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets all or some declarations of game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-declarations/<game_id> - GET - getting back declarations game id=%s", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # check user has right to read declaration - must be player of game master or moderator

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check moderator rights

        # get moderator list
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/moderators"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            del sql_executor
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
        the_moderators = req_result.json()

        role_id: typing.Optional[int] = 0

        # check pseudo in moderator list
        if pseudo not in the_moderators:

            # get the role
            assert game is not None
            role_id = game.find_role(sql_executor, player_id)
            if role_id is None:
                del sql_executor
                flask_restful.abort(403, msg=f"You do not seem to play or master game {game_id} or be site moderator")

        # gather declarations
        declarations_list = declarations.Declaration.list_with_content_by_game_id(sql_executor, game_id)

        declarations_list_ret = []
        for _, identifier, author_num, anonymous, announce, time_stamp, content in declarations_list:
            if anonymous and role_id != 0:
                declarations_list_ret.append((identifier, announce, anonymous, -1, time_stamp, content.payload))
            else:
                declarations_list_ret.append((identifier, announce, anonymous, author_num, time_stamp, content.payload))

        del sql_executor

        data = {'declarations_list': declarations_list_ret}
        return data, 200


@API.resource('/date-last-declarations')
class DateLastDeclarationsRessource(flask_restful.Resource):  # type: ignore
    """  DateLastDeclarationsRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets date of last declarations of all games in which player plays
        EXPOSED
        """

        mylogger.LOGGER.info("/date-last-declarations - GET - getting date last declarations of all my games")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        declarations_list = declarations.Declaration.last_date_by_player_id(sql_executor, player_id)
        dict_time_stamp = dict(declarations_list)

        del sql_executor

        data = {'dict_time_stamp': dict_time_stamp}
        return data, 200


@API.resource('/date-last-game-messages')
class DateLastGameMessagesRessource(flask_restful.Resource):  # type: ignore
    """  DateLastGameMessagesRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Gets date of last messages sent to player's role in all games in which player plays
        EXPOSED
        """

        mylogger.LOGGER.info("/date-last-game-message - GET - getting date last received messages of all my games")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        messages_list = messages.Message.last_date_by_player_id(sql_executor, player_id)
        dict_time_stamp = dict(messages_list)

        del sql_executor

        data = {'dict_time_stamp': dict_time_stamp}
        return data, 200


@API.resource('/game-visits/<game_id>/<visit_type>')
class GameVisitsRessource(flask_restful.Resource):  # type: ignore
    """  GameVisitsRessource """

    def post(self, game_id: int, visit_type: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Insert visit in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-visits/<game_id>/<visit_type> - POST - creating new visit game id=%s visit_type=%s", game_id, visit_type)

        args = VISIT_PARSER.parse_args(strict=True)

        role_id = args['role_id']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # check user has right to post visit - must be player of game master

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is player for role ?
        assert game is not None
        expected_id = game.get_role(sql_executor, role_id)

        # can be player of game master but must correspond
        if user_id != expected_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game or the player in charge of the role")

        # create visit here
        time_stamp = int(time.time())
        visit = visits.Visit(int(game_id), role_id, int(visit_type), time_stamp)
        visit.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': "Ok visit inserted"}
        return data, 201

    def get(self, game_id: int, visit_type: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Retrieve visit in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-visits/<game_id> - GET - retrieving last visit game id=%s visit_type=%s", game_id, visit_type)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # check user has right to read visit - must be player of game master

        # check there is a game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(sql_executor, player_id)
        if role_id is None:
            del sql_executor
            flask_restful.abort(403, msg=f"You do not seem to play or master game {game_id}")

        # serves as default (very long time ago)
        time_stamp = 0

        # retrieve visit here
        assert role_id is not None
        visits_list = visits.Visit.list_by_game_id_role_num(sql_executor, game_id, role_id, visit_type)
        if visits_list:
            visit = visits_list[0]
            _, _, _, time_stamp = visit

        del sql_executor

        data = {'time_stamp': time_stamp}
        return data, 200


@API.resource('/all-game-visits/<visit_type>')
class AllGameVisitsRessource(flask_restful.Resource):  # type: ignore
    """  AllGameVisitsRessource """

    def get(self, visit_type: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Retrieve visit for all my games in database
        EXPOSED
        """

        mylogger.LOGGER.info("/all-game-visits - GET - retrieving last visit visit_type=%s", visit_type)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # get list of games in which player is involved
        allocations_list = allocations.Allocation.list_by_player_id(sql_executor, player_id)

        dict_time_stamp: typing.Dict[int, int] = {}
        for game_id, _, role_id in allocations_list:

            # serves as default (very long time ago)
            time_stamp = 0

            # retrieve visit here
            assert role_id is not None
            visits_list = visits.Visit.list_by_game_id_role_num(sql_executor, game_id, role_id, visit_type)
            if visits_list:
                visit = visits_list[0]
                _, _, _, time_stamp = visit

            dict_time_stamp[game_id] = time_stamp

        del sql_executor

        data = {'dict_time_stamp': dict_time_stamp}
        return data, 200


@API.resource('/game-votes/<game_id>')
class GameVoteRessource(flask_restful.Resource):  # type: ignore
    """  GameVoteRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Insert vote in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-votes/<game_id> - POST - creating new vote game id=%s", game_id)

        args = VOTE_PARSER.parse_args(strict=True)

        role_id = args['role_id']
        value = args['value']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # not allowed for game master
        if role_id == 0:
            flask_restful.abort(403, msg="Submitting vote for game end is not possible for game master")

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is player for role ?
        assert game is not None
        expected_player_id = game.get_role(sql_executor, role_id)
        expected_master_id = game.get_role(sql_executor, 0)

        # must be player or game master
        if user_id not in [expected_player_id, expected_master_id]:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the player who is in charge or the game master of the game")

        # game must be ongoing
        if game.current_state != 1:
            del sql_executor
            flask_restful.abort(403, msg="Game does not seem to be ongoing")

        # create or delete vote here

        # player
        if user_id == expected_player_id:
            if value is None:
                # Erase
                vote = votes.Vote(int(game_id), role_id, False)
                vote.delete_database(sql_executor)
            else:
                # Create
                vote = votes.Vote(int(game_id), role_id, bool(value))
                vote.update_database(sql_executor)

        # master
        if user_id == expected_master_id:
            # Erase
            vote = votes.Vote(int(game_id), role_id, bool(value))
            vote.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': "Ok vote inserted or deleted"}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Retrieve vote in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-votes/<game_id> - GET - retrieving vote game id=%s", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # check user has right to read visit - must be player of game master

        # check there is a game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(sql_executor, player_id)
        if role_id is None:
            del sql_executor
            flask_restful.abort(403, msg=f"You do not seem to play or master game {game_id}")

        # retrieve vote here
        assert role_id is not None
        if role_id == 0:
            votes_list = votes.Vote.list_by_game_id(sql_executor, game_id)
        else:
            votes_list = votes.Vote.list_by_game_id_role_num(sql_executor, game_id, role_id)

        del sql_executor

        data = {'votes': votes_list}
        return data, 200


@API.resource('/vaporize-player/<player_id>')
class VaporizePlayerRessource(flask_restful.Resource):  # type: ignore
    """ VaporizePlayerRessource """

    def post(self, player_id: int) -> typing.Tuple[typing.Dict[str, str], int]:  # pylint: disable=R0201
        """
        Remove incidents, dropouts, replacements for given player
        EXPOSED
        """

        mylogger.LOGGER.info("/vaporize-player/<player_id> - POST - vaporize player id=%s", player_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        if user_id != int(player_id):
            flask_restful.abort(404, msg="Not the expected player for vaporization")

        sql_executor = database.SqlExecutor()

        # delete incidents
        sql_executor.execute("DELETE FROM incidents WHERE player_id = ?", (player_id,))

        # delete dropouts
        sql_executor.execute("DELETE FROM dropouts WHERE player_id = ?", (player_id,))

        # delete replacements
        sql_executor.execute("DELETE FROM replacements WHERE player_id = ?", (player_id,))

        sql_executor.commit()

        del sql_executor

        data = {'msg': f"Ok, {pseudo} ({player_id}) vaporized !"}
        return data, 200


@API.resource('/player-game-incidents')
class PlayerGameIncidentsRessource(flask_restful.Resource):  # type: ignore
    """ PlayerGameIncidentsRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, int, int, float]]], int]:  # pylint: disable=R0201
        """
        Gets list of incidents incident for given player
        EXPOSED
        """

        mylogger.LOGGER.info("/player-game-incidents - GET - getting incidents for player")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # incidents_list : those who submitted orders after deadline
        incidents_list = incidents.Incident.list_by_player_id(sql_executor, user_id)

        # player_id only provided if not in game at this role (because left or was moved)
        late_list = [(o[0], o[1], o[2], o[4], o[5]) for o in incidents_list]

        del sql_executor

        data = {'incidents': late_list}
        return data, 200


@API.resource('/player-game-dropouts')
class PlayerGameDropoutsRessource(flask_restful.Resource):  # type: ignore
    """ PlayerGameDropoutsRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, float]]], int]:  # pylint: disable=R0201
        """
        Gets list of incidents dropout for given player
        EXPOSED
        """

        mylogger.LOGGER.info("/player-game-dropouts - GET - getting incidents for player")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # dropouts_list : those who quitted the game
        dropouts_list = dropouts.Dropout.list_by_player_id(sql_executor, user_id)
        dropout_list = [(o[0], o[1], o[3]) for o in dropouts_list]

        del sql_executor

        data = {'dropouts': dropout_list}
        return data, 200


@API.resource('/game-incidents/<game_id>')
class GameIncidentsRessource(flask_restful.Resource):  # type: ignore
    """ GameIncidentsRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, typing.Optional[int], int, float]]], int]:  # pylint: disable=R0201
        """
        Gets list of roles which have produced an incident for given game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-incidents/<game_id> - GET - getting which incidents occured for game id=%s", game_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # incidents_list : those who submitted orders after deadline
        incidents_list = incidents.Incident.list_by_game_id(sql_executor, game_id)

        assert game is not None

        # player_id only provided if not anonymous
        late_list = [(o[1], o[2], o[3] if not game.anonymous else None, o[4], o[5]) for o in incidents_list]

        del sql_executor

        data = {'incidents': late_list}
        return data, 200


@API.resource('/game-master-incidents/<game_id>')
class GameMasterIncidentsRessource(flask_restful.Resource):  # type: ignore
    """ GameMasterIncidentsRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, int, int, float]]], int]:  # pylint: disable=R0201
        """
        Gets list of roles which have produced an incident for given game with pseudo for a game master
        EXPOSED
        """

        mylogger.LOGGER.info("/game-master-incidents/<game_id> - GET - getting which incidents occured for game id=%s for master", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # find game master
        assert game is not None
        game_master_id = game.get_role(sql_executor, 0)

        if user_id != game_master_id:
            del sql_executor
            flask_restful.abort(404, msg=f"You do not seem to be game master of game {game_id}")

        # incidents_list : those who submitted orders after deadline
        incidents_list = incidents.Incident.list_by_game_id(sql_executor, game_id)

        assert game is not None

        # all info
        late_list = [(o[1], o[2], o[3], o[4], o[5]) for o in incidents_list]

        del sql_executor

        data = {'incidents': late_list}
        return data, 200


@API.resource('/game-incidents2/<game_id>')
class GameIncidents2Ressource(flask_restful.Resource):  # type: ignore
    """ GameIncidents2Ressource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, float]]], int]:  # pylint: disable=R0201
        """
        Gets list of roles which have produced an incident2 for given game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-incidents2/<game_id> - GET - getting which incidents2 occured for game id=%s", game_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # incidents_list : those who submitted orders after deadline
        incidents_list = incidents2.Incident2.list_by_game_id(sql_executor, game_id)
        late_list = [(o[1], o[2], o[3]) for o in incidents_list]

        del sql_executor

        data = {'incidents': late_list}
        return data, 200


@API.resource('/game-replacements/<game_id>')
class GameReplacementsRessource(flask_restful.Resource):  # type: ignore
    """ GameReplacementsRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, float, int]]], int]:  # pylint: disable=R0201
        """
        Gets list of roles which have produced an replacements for given game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-v/<game_id> - GET - getting which replacements occured for game id=%s", game_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # replacements_list : those who entered or quitted the game
        replacements_list = replacements.Replacement.list_by_game_id(sql_executor, game_id)

        # find game master
        assert game is not None
        game_master_id = game.get_role(sql_executor, 0)
        del sql_executor

        if not game.anonymous:

            late_list = [(o[1], o[2], o[3], o[4]) for o in replacements_list]
            data = {'replacements': late_list}
            return data, 200

        # game is anonymous, access is restricted

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        if user_id == game_master_id:

            late_list = [(o[1], o[2], o[3], o[4]) for o in replacements_list]
            data = {'replacements': late_list}
            return data, 200

        # check moderator rights

        # get moderator list
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/moderators"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
        the_moderators = req_result.json()

        # check pseudo in moderator list
        if pseudo in the_moderators:
            late_list = [(o[1], o[2], o[3], o[4]) for o in replacements_list]
            data = {'replacements': late_list}
            return data, 200

        # ofuscate (not game master)
        late_list = [(o[1], o[2] if o[1] == 0 else -1, o[3], o[4]) for o in replacements_list]
        data = {'replacements': late_list}
        return data, 200


@API.resource('/game-dropouts/<game_id>')
class GameDropoutsRessource(flask_restful.Resource):  # type: ignore
    """ GameDropoutsRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, float]]], int]:  # pylint: disable=R0201
        """
        Gets list of roles which have produced an dropout for given game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-dropouts/<game_id> - GET - getting which dropouts occured for game id=%s", game_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # dropouts_list : those who quitted the game
        dropouts_list = dropouts.Dropout.list_by_game_id(sql_executor, game_id)
        late_list = [(o[1], o[2], o[3]) for o in dropouts_list]

        del sql_executor

        data = {'dropouts': late_list}
        return data, 200


@API.resource('/all-game-dropouts')
class AllGamesDropoutsRessource(flask_restful.Resource):  # type: ignore
    """ AllGamesDropoutsRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, int, float]]], int]:  # pylint: disable=R0201
        """
        Gets list of roles which have produced an dropout
        EXPOSED
        """

        mylogger.LOGGER.info("/game-dropouts/<game_id> - GET - getting which dropouts occured")

        sql_executor = database.SqlExecutor()
        late_list = dropouts.Dropout.inventory(sql_executor)
        del sql_executor

        data = {'dropouts': late_list}
        return data, 200


@API.resource('/game-notes/<game_id>')
class GameNoteRessource(flask_restful.Resource):  # type: ignore
    """  GameNoteRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Insert note in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-notes/<game_id> - POST - creating new note game id=%s", game_id)

        args = NOTE_PARSER.parse_args(strict=True)

        role_id = args['role_id']
        content = args['content']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is player for role ?
        assert game is not None
        expected_id = game.get_role(sql_executor, role_id)

        # must be player
        if user_id != expected_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the player who is in charge")

        # create note here
        note = notes.Note(int(game_id), role_id, content)
        note.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': "Ok note inserted"}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Retrieve note in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-notes/<game_id> - GET - retrieving note game id=%s", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        player_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # check user has right to read not - must be player of game master

        # check there is a game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(sql_executor, player_id)
        if role_id is None:
            del sql_executor
            flask_restful.abort(403, msg=f"You do not seem to play or master game {game_id}")

        # retrieve note here
        assert role_id is not None
        content = notes.Note.content_by_game_id_role_num(sql_executor, game_id, role_id)

        del sql_executor

        data = {'content': content}
        return data, 200


@API.resource('/game-export/<game_id>')
class GameExportRessource(flask_restful.Resource):  # type: ignore
    """ GameExportRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Export all data about a game in JSON format
        EXPOSED
        """

        mylogger.LOGGER.info("/game-export/<game_id> - GET - getting JSON export game id=%s", game_id)

        # create an executor
        sql_executor = database.SqlExecutor()

        # to access really database of players
        debug_mode = False

        # perform the extraction
        status, message, content = exporter.export_data(game_id, sql_executor, debug_mode)

        # delete executor
        del sql_executor

        if not status:
            flask_restful.abort(400, msg=f"Exportation failed with error: '{message}'!")

        data = {'msg': message, 'content': content}
        return data, 200


@API.resource('/game-incidents-manage/<game_id>/<role_id>/<advancement>')
class GameIncidentsManageRessource(flask_restful.Resource):  # type: ignore
    """ GameIncidentsManageRessource """

    def delete(self, game_id: int, role_id: int, advancement: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Deletes an incident in game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-incidents-manage/<game_id> - DELETE - deleting incident for game id=%s", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game with id {game_id} doesn't exist")

        # check this is game_master
        assert game is not None
        if game.get_role(sql_executor, 0) != user_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # find incident
        incident = incidents.Incident(int(game_id), int(role_id), int(advancement), 0, 0)

        # delete incident
        assert incident is not None
        incident.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok incident removed if present'}
        return data, 200


@API.resource('/game-dropouts-manage/<game_id>/<role_id>/<player_id>')
class GameDropoutsManageRessource(flask_restful.Resource):  # type: ignore
    """ GameDropoutsManageRessource """

    def delete(self, game_id: int, role_id: int, player_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Deletes an dropout in game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-dropouts-manage/<game_id> - DELETE - deleting dropout for game id=%s", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game with id {game_id} doesn't exist")

        # check this is game_master
        assert game is not None
        if game.get_role(sql_executor, 0) != user_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # find dropout
        dropout = dropouts.Dropout(int(game_id), int(role_id), int(player_id))

        # delete dropout
        assert dropout is not None
        dropout.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok dropout removed if present'}
        return data, 200


@API.resource('/game-cancel-last-adjudication/<game_id>')
class GameCancelLastAdjudicationRessource(flask_restful.Resource):  # type: ignore
    """ GameCancelLastAdjudicationRessource """

    def delete(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Cancels last adjudication of game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-cancel-last-adjudication/<game_id> - DELETE - canceling last adjudication  game id=%s", game_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game with id {game_id} doesn't exist")

        # check this is game_master
        assert game is not None
        if game.get_role(sql_executor, 0) != user_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # check game is archive
        if not game.archive:
            del sql_executor
            flask_restful.abort(400, msg="Game is not archive")

        # check game is ongoing
        if game.current_state != 1:
            del sql_executor
            flask_restful.abort(400, msg="Game is not ongoing")

        # get current_advancement
        last_advancement_played = game.current_advancement - 1

        # check game as a transition
        last_transition = transitions.Transition.find_by_game_advancement(sql_executor, game_id, last_advancement_played)

        if not last_transition:
            del sql_executor
            flask_restful.abort(400, msg="There is not last transition")

        # extract transition data
        assert last_transition is not None

        # situation
        the_situation = json.loads(last_transition.situation_json)
        the_ownerships = the_situation['ownerships']
        the_units = the_situation['units']
        the_dislodged_units = the_situation['dislodged_ones']
        the_forbiddens = the_situation['forbiddens']

        # purge previous ownerships
        for (_, center_num, role_num) in ownerships.Ownership.list_by_game_id(sql_executor, int(game_id)):
            ownership = ownerships.Ownership(int(game_id), center_num, role_num)
            ownership.delete_database(sql_executor)

        # purge previous units
        for (_, type_num, role_num, zone_num, zone_dislodged_from_num, fake) in units.Unit.list_by_game_id(sql_executor, int(game_id)):
            unit = units.Unit(int(game_id), type_num, role_num, zone_num, zone_dislodged_from_num, fake)
            unit.delete_database(sql_executor)

        # purge previous forbiddens
        for (_, center_num) in forbiddens.Forbidden.list_by_game_id(sql_executor, int(game_id)):
            forbidden = forbiddens.Forbidden(int(game_id), center_num)
            forbidden.delete_database(sql_executor)

        # insert

        # insert new ownerships
        for center_num, role in the_ownerships.items():
            ownership = ownerships.Ownership(int(game_id), int(center_num), role)
            ownership.update_database(sql_executor)

        # insert new units
        for role_num, the_unit_role in the_units.items():
            for type_num, zone_num in the_unit_role:
                unit = units.Unit(int(game_id), type_num, zone_num, int(role_num), 0, 0)
                unit.update_database(sql_executor)

        # insert new dislodged units
        for role_num, the_unit_role in the_dislodged_units.items():
            for type_num, zone_num, zone_dislodged_from_num in the_unit_role:
                unit = units.Unit(int(game_id), type_num, zone_num, int(role_num), zone_dislodged_from_num, 0)
                unit.update_database(sql_executor)

        # insert new forbiddens
        for region_num in the_forbiddens:
            forbidden = forbiddens.Forbidden(int(game_id), region_num)
            forbidden.update_database(sql_executor)

        # remove orders
        for (_, rol_id, _, zone_num, _, _) in orders.Order.list_by_game_id(sql_executor, game_id):
            order = orders.Order(int(game_id), rol_id, 0, zone_num, 0, 0)
            order.delete_database(sql_executor)

        # orders
        the_orders1 = json.loads(last_transition.orders_json)
        the_fakes_units = the_orders1['fake_units']
        the_orders = the_orders1['orders']

        # insert new fake units
        for (_, type_num, zone_num, role_num, _, _) in the_fakes_units:
            unit = units.Unit(int(game_id), type_num, zone_num, int(role_num), 0, 1)
            unit.update_database(sql_executor)

        # insert new orders
        for (_, role_num, order_type, zone_num, passive_num, dest_num) in the_orders:
            order = orders.Order(int(game_id), role_num, order_type, zone_num, passive_num, dest_num)
            order.update_database(sql_executor)

        # rollback game
        game.rollback()
        game.update_database(sql_executor)

        # delete transition
        last_transition.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': f'Ok last adjudication {last_advancement_played} cancelled'}
        return data, 200


@API.resource('/tournaments/<game_name>')
class TournamentRessource(flask_restful.Resource):  # type: ignore
    """ TournamentRessource """

    def get(self, game_name: str) -> typing.Tuple[typing.Optional[typing.Dict[str, typing.Any]], int]:  # pylint: disable=R0201
        """
        Get all information about tournament
        EXPOSED
        """

        mylogger.LOGGER.info("/tournaments/<game_name> - GET- retrieving data of tournament from game name=%s", game_name)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_name(sql_executor, game_name)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game {game_name} doesn't exist")

        assert game is not None

        game_id = game.identifier

        # find the tournament from game
        game_tournaments = groupings.Grouping.list_by_game_id(sql_executor, game_id)

        # no tournament for that game : legal (return empty dict)
        if not game_tournaments:
            data = None
            del sql_executor
            return data, 200

        # more than one tournament for that game : internal error actually
        if len(game_tournaments) != 1:
            del sql_executor
            flask_restful.abort(404, msg=f"ERROR : Game {game_name} has more than one tournament")

        # the id of tournament
        tournament_ids = [g[0] for g in game_tournaments]
        tournament_id = tournament_ids[0]

        # the tournament
        tournament = tournaments.Tournament.find_by_identifier(sql_executor, tournament_id)
        if tournament is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a tournament with identifier {tournament_id}")

        assert tournament is not None

        tournament_name = tournament.name

        # director of that tournament
        tournament_directors = assignments.Assignment.list_by_tournament_id(sql_executor, tournament_id)

        # more than one director for that game : internal error actually
        if len(tournament_directors) != 1:
            del sql_executor
            flask_restful.abort(404, msg=f"ERROR : Tournament {tournament_name} has more than one director")

        director_ids = [a[1] for a in tournament_directors]
        director_id = director_ids[0]

        # games of that tournament
        tournament_games = groupings.Grouping.list_by_tournament_id(sql_executor, int(tournament_id))
        game_ids = [g[1] for g in tournament_games]

        del sql_executor

        data = {'identifier': tournament_id, 'name': tournament_name, 'director_id': director_id, 'games': game_ids}

        return data, 200

    def put(self, game_name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Change a tournament (just the name)
        EXPOSED
        """

        mylogger.LOGGER.info("/tournaments/<game_name> - PUT - changing tournament from game name=%s", game_name)

        args = TOURNAMENT_PARSER.parse_args(strict=True)

        name = args['name']
        # game_id not used

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_name(sql_executor, game_name)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game {game_name} doesn't exist")

        assert game is not None

        game_id = game.identifier

        # find the tournament from game
        game_tournaments = groupings.Grouping.list_by_game_id(sql_executor, game_id)
        if not game_tournaments:
            del sql_executor
            flask_restful.abort(400, msg="The game appears not to be in any tournament")

        # the id of tournament
        tournament_id: typing.Optional[int] = None
        for tourn_id, _ in game_tournaments:
            tournament_id = tourn_id
            break
        assert tournament_id is not None

        # the object tournament
        tournament = tournaments.Tournament.find_by_identifier(sql_executor, tournament_id)
        if tournament is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Tournament with identfier {tournament_id} doesn't exist")

        assert tournament is not None

        # check actual change
        if tournament.name == name:
            del sql_executor
            flask_restful.abort(404, msg="Tournament already has this name!")

        # check there is not already a tournament by that name
        other_tournament = tournaments.Tournament.find_by_name(sql_executor, name)
        if other_tournament is not None:
            del sql_executor
            flask_restful.abort(404, msg=f"A tournament with name {name} already exists")

        # check that user is the creator of the tournament
        if user_id != tournament.get_director(sql_executor):
            del sql_executor
            flask_restful.abort(404, msg="You do not seem to be director of that tournament")

        # change the name
        tournament.name = name
        tournament.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'name': name, 'msg': 'Ok renamed'}
        return data, 200

    def delete(self, game_name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Deletes a tournament
        EXPOSED
        """

        mylogger.LOGGER.info("/tournaments/<game_name> - DELETE - deleting tournament from game name=%s", game_name)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_name(sql_executor, game_name)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game {game_name} doesn't exist")

        assert game is not None

        game_id = game.identifier

        # find the tournament from game
        game_tournaments = groupings.Grouping.list_by_game_id(sql_executor, game_id)
        if not game_tournaments:
            del sql_executor
            flask_restful.abort(400, msg="The game appears not to be in any tournament")

        # the id of tournament
        tournament_id: typing.Optional[int] = None
        for tourn_id, _ in game_tournaments:
            tournament_id = tourn_id
            break
        assert tournament_id is not None

        # the object tournament
        tournament = tournaments.Tournament.find_by_identifier(sql_executor, tournament_id)
        if tournament is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Tournament with identfier {tournament_id} doesn't exist")

        assert tournament is not None

        name = tournament.name

        # check that user is the creator of the tournament
        if user_id != tournament.get_director(sql_executor):
            del sql_executor
            flask_restful.abort(404, msg="You do not seem to be director of that tournament")

        # delete assignments (there should be only one actually)
        tournament.delete_assignments(sql_executor)

        # delete groupings
        tournament.delete_groupings(sql_executor)

        # finally delete tournament
        tournament.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'name': name, 'msg': 'Ok removed'}
        return data, 200


@API.resource('/tournaments')
class TournamentListRessource(flask_restful.Resource):  # type: ignore
    """ TournamentListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Dict[str, typing.Any]], int]:  # pylint: disable=R0201
        """
        Get list of tournament
        EXPOSED
        """

        mylogger.LOGGER.info("/tournaments - GET- retrieving list of tournaments")

        sql_executor = database.SqlExecutor()
        tournaments_list = tournaments.Tournament.inventory(sql_executor)
        del sql_executor

        data = {str(t.identifier): {'name': t.name} for t in tournaments_list}

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Creates a new tournament
        EXPOSED
        """

        mylogger.LOGGER.info("/tournaments - POST - creating new tournament")

        args = TOURNAMENT_PARSER.parse_args(strict=True)

        name = args['name']
        game_id = args['game_id']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        if not name.isidentifier():
            flask_restful.abort(400, msg=f"Name '{name}' is not a valid name")

        sql_executor = database.SqlExecutor()

        # find the tournament
        tournament = tournaments.Tournament.find_by_name(sql_executor, name)

        if tournament is not None:
            del sql_executor
            flask_restful.abort(400, msg=f"Tournament {name} already exists")

        # check the game is not alreay in a tournament (because we will put the game in the tournament)
        game_tournaments = groupings.Grouping.list_by_game_id(sql_executor, game_id)
        if game_tournaments:
            del sql_executor
            flask_restful.abort(400, msg="The game appears to already be in some other tournament")

        # create tournament here
        identifier = tournaments.Tournament.free_identifier(sql_executor)
        tournament = tournaments.Tournament(identifier, '', )
        _ = tournament.load_json(args)
        tournament.update_database(sql_executor)

        # allocate director to tournament
        tournament.put_director(sql_executor, user_id)

        # put the game in tournament (tournaments must always have at least one game)
        tournament_id = tournament.identifier
        grouping = groupings.Grouping(tournament_id, game_id)
        grouping.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'name': name, 'msg': 'Ok tournament created'}
        return data, 201


@API.resource('/groupings/<tournament_id>')
class GroupingTournamentRessource(flask_restful.Resource):  # type: ignore
    """ GroupingTournamentRessource """

    def post(self, tournament_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Creates or deletes a grouping (a relation game-tournament)
        EXPOSED
        """

        mylogger.LOGGER.info("/groupings - POST - creating/deleting new grouping")

        args = GROUPING_PARSER.parse_args(strict=True)

        game_id = args['game_id']
        delete = args['delete']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check user has right to add allocation - must be director

        sql_executor = database.SqlExecutor()

        # find the tournament
        tournament = tournaments.Tournament.find_by_identifier(sql_executor, tournament_id)
        if tournament is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a tournament with identifier {tournament_id}")

        # find the director
        assert tournament is not None
        director_id = tournament.get_director(sql_executor)

        # check is allowed
        if user_id not in [director_id]:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the director of the tournament")

        # check the game exists
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # action

        if not delete:

            # check the game is not already in another tournament
            tournaments_game = groupings.Grouping.list_by_game_id(sql_executor, game_id)
            if tournaments_game:
                del sql_executor
                flask_restful.abort(400, msg="Seems the game is already in some other tournament")

            grouping = groupings.Grouping(int(tournament_id), int(game_id))
            grouping.update_database(sql_executor)

            sql_executor.commit()
            del sql_executor

            data = {'msg': 'Ok grouping updated or created'}
            return data, 201

        # check the game is not alone in its tournament
        games_tournament = groupings.Grouping.list_by_tournament_id(sql_executor, tournament_id)
        if len(games_tournament) == 1:
            del sql_executor
            flask_restful.abort(400, msg="Seems removing the game from the tournament would make it empty")

        grouping = groupings.Grouping(int(tournament_id), int(game_id))
        grouping.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok grouping deleted if present'}
        return data, 200


@API.resource('/groupings')
class GroupingListRessource(flask_restful.Resource):  # type: ignore
    """ GroupingListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Get list of all groupings (dictionary identifier -> list of games ids)
        EXPOSED
        """

        mylogger.LOGGER.info("/groupings - GET - getting all groupings ")

        sql_executor = database.SqlExecutor()
        groupings_list = groupings.Grouping.inventory(sql_executor)
        del sql_executor

        data = {str(g[0]): [gg[1] for gg in groupings_list if gg[0] == g[0]] for g in groupings_list}
        return data, 200


@API.resource('/assignments')
class AssignmentListRessource(flask_restful.Resource):  # type: ignore
    """ AssignmentListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Get list of all assignements (dictionary identifier -> director_id)
        EXPOSED
        """

        mylogger.LOGGER.info("/assignments - GET - getting all assignments ")

        sql_executor = database.SqlExecutor()
        assignments_list = assignments.Assignment.inventory(sql_executor)
        del sql_executor

        data = {str(a[0]): a[1] for a in assignments_list}
        return data, 200


@API.resource('/tournament-incidents/<tournament_id>')
class TournamentIncidentsRessource(flask_restful.Resource):  # type: ignore
    """ TournamentIncidentsRessource """

    def get(self, tournament_id: int) -> typing.Tuple[typing.List[typing.Tuple[int, int, int, int, float]], int]:  # pylint: disable=R0201
        """
        Gets list of pseudo/alias which have produced an incident delay for given tournament
        EXPOSED
        """

        mylogger.LOGGER.info("/tournament-incidents/<game_id> - GET - getting which incidents delay occured for tournament id=%s", tournament_id)

        sql_executor = database.SqlExecutor()

        # find the tournament
        tournament = tournaments.Tournament.find_by_identifier(sql_executor, tournament_id)
        if tournament is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a tournament with identifier {tournament_id}")

        # games of that tournament
        tournament_games = groupings.Grouping.list_by_tournament_id(sql_executor, int(tournament_id))
        tournament_game_ids = [g[1] for g in tournament_games]

        late_list: typing.List[typing.Tuple[int, int, int, int, float]] = []
        for game_id in tournament_game_ids:

            # find the current players
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            current_players_dict = {a[2]: a[1] for a in allocations_list}

            # incidents_list : those who submitted orders after deadline
            incidents_list = incidents.Incident.list_by_game_id(sql_executor, game_id)

            # select only incidents with current player
            for _, role_id, advancement, player_id, duration_incident, date_incident in incidents_list:
                if role_id not in current_players_dict:
                    continue
                if player_id != current_players_dict[role_id]:
                    continue
                late_list.append((game_id, role_id, advancement, duration_incident, date_incident))

        del sql_executor

        data = late_list
        return data, 200


@API.resource('/tournament-incidents2/<tournament_id>')
class TournamentIncidents2Ressource(flask_restful.Resource):  # type: ignore
    """ TournamentIncidents2Ressource """

    def get(self, tournament_id: int) -> typing.Tuple[typing.List[typing.Tuple[int, int, int, float]], int]:  # pylint: disable=R0201
        """
        Gets list of pseudo/alias which have produced an incident civil disorder for given tournament
        EXPOSED
        """

        mylogger.LOGGER.info("/tournament-incidents2/<game_id> - GET - getting which incidents civil disorder occured for tournament id=%s", tournament_id)

        sql_executor = database.SqlExecutor()

        # find the tournament
        tournament = tournaments.Tournament.find_by_identifier(sql_executor, tournament_id)
        if tournament is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a tournament with identifier {tournament_id}")

        # games of that tournament
        tournament_games = groupings.Grouping.list_by_tournament_id(sql_executor, int(tournament_id))
        tournament_game_ids = [g[1] for g in tournament_games]

        late_list: typing.List[typing.Tuple[int, int, int, float]] = []
        for game_id in tournament_game_ids:
            incidents_list = incidents2.Incident2.list_by_game_id(sql_executor, game_id)
            for _, role_num, advancement, date_incident in incidents_list:
                late_list.append((game_id, role_num, advancement, date_incident))

        del sql_executor

        data = late_list
        return data, 200


@API.resource('/tournament-positions/<tournament_id>')
class TournamentPositionRessource(flask_restful.Resource):  # type: ignore
    """ TournamentPositionRessource """

    def get(self, tournament_id: int) -> typing.Tuple[typing.Dict[int, typing.Dict[str, typing.Any]], int]:  # pylint: disable=R0201
        """
        Gets list of positions of the games of the tournament
        EXPOSED
        """

        mylogger.LOGGER.info("/tournament-positions/<tournament_id> - GET - getting positions for games of tournament id=%s", tournament_id)

        sql_executor = database.SqlExecutor()

        # find the tournament
        tournament = tournaments.Tournament.find_by_identifier(sql_executor, tournament_id)
        if tournament is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a tournament with identifier {tournament_id}")

        # games of that tournament
        tournament_games = groupings.Grouping.list_by_tournament_id(sql_executor, int(tournament_id))
        tournament_game_ids = [g[1] for g in tournament_games]

        position_dict: typing.Dict[int, typing.Dict[str, typing.Any]] = {}
        for game_id in tournament_game_ids:

            # get ownerships
            ownership_dict = {}
            game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
            for _, center_num, role_num in game_ownerships:
                ownership_dict[str(center_num)] = role_num

            # get units
            unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
            dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
            game_units = units.Unit.list_by_game_id(sql_executor, game_id)
            for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
                if fake:
                    pass  # this is confidential
                elif region_dislodged_from_num:
                    dislodged_unit_dict[str(role_num)].append([type_num, zone_num, region_dislodged_from_num])
                else:
                    unit_dict[str(role_num)].append([type_num, zone_num])

            # get forbiddens
            forbidden_list = []
            game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)
            for _, region_num in game_forbiddens:
                forbidden_list.append(region_num)

            position = {
                'ownerships': ownership_dict,
                'dislodged_ones': dislodged_unit_dict,
                'units': unit_dict,
                'forbiddens': forbidden_list,
            }

            position_dict[game_id] = position

        del sql_executor

        data = position_dict
        return data, 200


@API.resource('/revoke/<game_id>')
class RevokeRessource(flask_restful.Resource):  # type: ignore
    """ RevokeRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Revoke game master of the game
        EXPOSED
        """

        mylogger.LOGGER.info("/revoke/<game_id> - POST - revoke game master game id=%s", game_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            del sql_executor
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # check moderator rights

        # get moderator list
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/moderators"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
        the_moderators = req_result.json()

        # check pseudo in moderator list
        if pseudo not in the_moderators:
            del sql_executor
            flask_restful.abort(403, msg="You need to be the game master of the game (or site moderator) so you are not allowed to see the roles of this anonymous game")

        # revoke actually

        # get current game master
        # find the game master
        assert game is not None
        game_master_id = game.get_role(sql_executor, 0)
        if game_master_id is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game master of game with identifier {game_id}")

        # put dangling
        assert game_id is not None
        assert game_master_id is not None
        dangling_role_id = -1
        # cannot fail
        _ = game.put_role(sql_executor, game_master_id, dangling_role_id)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok, game master revoked !'}
        return data, 201


@API.resource('/clear-old-delays')
class ClearOldDelaysRessource(flask_restful.Resource):  # type: ignore
    """ ClearOldDelaysRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        clear old delays
        EXPOSED
        """

        mylogger.LOGGER.info("/clear-old-delays - POST - clear old delays")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        if pseudo != COMMUTER_ACCOUNT:
            flask_restful.abort(403, msg="You do not seem to be site commuter so you are not allowed to clear old delays")

        sql_executor = database.SqlExecutor()
        incidents.Incident.purge_old(sql_executor)
        sql_executor.commit()

        del sql_executor

        data = {'msg': "clear old delays done"}
        return data, 200


@API.resource('/tournament-allocations/<tournament_id>')
class TournamentGameRessource(flask_restful.Resource):  # type: ignore
    """ TournamentGameRessource """

    def get(self, tournament_id: int) -> typing.Tuple[typing.Dict[int, typing.Dict[str, typing.Any]], int]:  # pylint: disable=R0201
        """
        Gets all allocations for the game of the tournamnet
        EXPOSED
        """

        mylogger.LOGGER.info("/tournament-allocations/<game_id> - GET - get getting allocations for game of tournament id=%s", tournament_id)

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # check moderator rights
        # get moderator list
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/creators"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
        the_creators = req_result.json()

        # check pseudo in creator list
        if pseudo not in the_creators:
            flask_restful.abort(403, msg="You do not seem to be site creator so you are not allowed get all players from tournament !")

        sql_executor = database.SqlExecutor()

        # find the tournament
        tournament = tournaments.Tournament.find_by_identifier(sql_executor, tournament_id)
        if tournament is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a tournament with identifier {tournament_id}")

        # games of that tournament
        tournament_games = groupings.Grouping.list_by_tournament_id(sql_executor, int(tournament_id))
        tournament_game_ids = [g[1] for g in tournament_games]

        allocation_dict: typing.Dict[int, typing.Dict[str, typing.Any]] = {}
        for game_id in tournament_game_ids:

            # find the game
            game = games.Game.find_by_identifier(sql_executor, game_id)
            if game is None:
                del sql_executor
                flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

            assert game is not None

            # no anonymous game possible
            if game.anonymous:
                continue

            # get answer
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            allocation = {str(a[1]): a[2] for a in allocations_list}

            allocation_dict[game_id] = allocation

        del sql_executor

        data = allocation_dict

        return data, 200


@API.resource('/tournament-players/<tournament_id>')
class TournamentPlayersRessource(flask_restful.Resource):  # type: ignore
    """ TournamentPlayersRessource """

    def get(self, tournament_id: int) -> typing.Tuple[typing.Dict[int, int], int]:  # pylint: disable=R0201
        """
        Gets all players for the game of the tournamnet
        EXPOSED
        """

        mylogger.LOGGER.info("/tournament-players/<game_id> - GET - get getting allocations for game of tournament id=%s", tournament_id)

        sql_executor = database.SqlExecutor()

        # find the tournament
        tournament = tournaments.Tournament.find_by_identifier(sql_executor, tournament_id)
        if tournament is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a tournament with identifier {tournament_id}")

        # games of that tournament
        tournament_games = groupings.Grouping.list_by_tournament_id(sql_executor, int(tournament_id))
        tournament_game_ids = [g[1] for g in tournament_games]

        players_dict: typing.Dict[int, int] = {}
        for game_id in tournament_game_ids:

            # get answer
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            for alloc in allocations_list:
                if alloc[2] > 0:
                    player_id = alloc[1]
                    if player_id not in players_dict:
                        players_dict[player_id] = 0
                    players_dict[player_id] += 1

        del sql_executor

        # need to sort so not to give any indications on who plays what
        players = sorted(players_dict.keys())
        data = {p: players_dict[p] for p in players}

        return data, 200


@API.resource('/statistics')
class StatisticsRessource(flask_restful.Resource):  # type: ignore
    """ StatisticsRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Get statistics of games, players etc...
        EXPOSED
        """

        mylogger.LOGGER.info("/statistics - GET - getting statistics ")

        sql_executor = database.SqlExecutor()

        # games needing replacement

        full_games_data = sql_executor.execute("select games.identifier, count(*) as filled_count, capacities.value from games join allocations on allocations.game_id=games.identifier join capacities on capacities.game_id=games.identifier group by identifier", need_result=True)

        # keep only the ones where a role is missing
        assert full_games_data is not None
        recruiting_games = [tr[0] for tr in full_games_data if tr[1] < tr[2]]

        # keep only the ongoing ones
        suffering_games = []
        for game_id in recruiting_games:
            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None
            if game.current_state != 1:
                continue
            suffering_games.append(game.name)

        # games stalled, waiting for too long to be complete
        now = int(time.time())
        stalled_games = []
        for game_id in recruiting_games:
            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None
            if game.current_state != 0:
                continue
            if now < game.deadline:
                continue
            stalled_games.append(game.name)

        # a list of games
        games_list = games.Game.inventory(sql_executor)

        # games very late
        limit = int(time.time()) - CRITICAL_DELAY_DAY * 24 * 3600
        dying_games = [g.name for g in games_list if g.current_state == 1 and not g.soloed and not g.end_voted and not g.finished and g.deadline < limit]

        # stats about games

        allocations_list = allocations.Allocation.inventory(sql_executor)
        del sql_executor

        # games we can speak about the players
        ongoing_games = {g.identifier for g in games_list if g.current_state == 1 and not g.archive}

        # players_dict
        game_masters_set = set()
        players_set = set()
        active_masters: typing.Counter[int] = collections.Counter()
        active_players: typing.Counter[int] = collections.Counter()
        for (game_id, player_id, role_id) in allocations_list:
            if game_id not in ongoing_games:
                continue
            if role_id == 0:
                game_masters_set.add(player_id)
                active_masters[player_id] += 1
            else:
                players_set.add(player_id)
                active_players[player_id] += 1

        most_active_master_id = active_masters.most_common(1)[0][0]
        most_active_player_id = active_players.most_common(1)[0][0]

        data = {'dying_games': dying_games, 'stalled_games': stalled_games, 'suffering_games': suffering_games, 'ongoing_games': len(ongoing_games), 'active_game_masters': len(game_masters_set), 'active_players': len(players_set), 'most_active_master': most_active_master_id, 'most_active_player': most_active_player_id}
        return data, 200


@API.resource('/current-worst-annoyers')
class CurrentWorstAnnoyersRessource(flask_restful.Resource):  # type: ignore
    """ CurrentWorstAnnoyersRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Get current worst annoyers (late or giving  up) in current games...
        EXPOSED
        """

        mylogger.LOGGER.info("/current-worst-annoyers - GET - getting current annoyers ")

        sql_executor = database.SqlExecutor()

        # concerned_games
        games_list = games.Game.inventory(sql_executor)
        concerned_games_list = [g.identifier for g in games_list if g.current_state == 1]

        games_dict = {}
        for game_id in concerned_games_list:

            game_data: typing.Dict[str, typing.Any] = {}

            # get game
            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None

            # get name
            game_name = game.name

            # get delays
            game_incidents = incidents.Incident.list_by_game_id(sql_executor, game_id)
            delayers = {d[3] for d in game_incidents}
            delays_number = {d: len([dd for dd in game_incidents if dd[3] == d]) for d in delayers}
            game_data['delays_number'] = delays_number

            # get dropouts
            game_dropouts = dropouts.Dropout.list_by_game_id(sql_executor, game_id)
            quitters = {d[2] for d in game_dropouts}
            dropouts_number = {q: len([qq for qq in game_dropouts if qq[2] == q]) for q in quitters}
            game_data['dropouts_number'] = dropouts_number

            if not (delays_number or dropouts_number):
                continue

            games_dict[game_name] = game_data

        del sql_executor

        data = {'games_dict': games_dict}
        return data, 200


@API.resource('/extract_elo_data')
class ExtractEloDataRessource(flask_restful.Resource):  # type: ignore
    """ ExtractEloDataRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Get information for ELO of players etc...
        EXPOSED
        """

        mylogger.LOGGER.info("/extract_elo_data - GET - getting ELO data ")

        sql_executor = database.SqlExecutor()

        # concerned_games
        games_list = games.Game.inventory(sql_executor)
        concerned_games_list = [g.identifier for g in games_list if g.current_state == 2 and g.used_for_elo == 1]

        # time of spring 01
        first_advancement = 1

        games_dict = {}
        for game_id in concerned_games_list:

            game_data: typing.Dict[str, typing.Any] = {}

            # get start date
            start_transition = transitions.Transition.find_by_game_advancement(sql_executor, game_id, first_advancement)

            if not start_transition:
                # this game was not played
                continue

            assert start_transition is not None
            game_data['start_time_stamp'] = start_transition.time_stamp

            # get players
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            game_data['players'] = {str(a[1]): a[2] for a in allocations_list if a[2] >= 1}

            # get game
            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None

            # get current_advancement
            last_advancement_played = game.current_advancement - 1
            game_data['number_advancement_played'] = game.current_advancement

            # get end date
            end_transition = transitions.Transition.find_by_game_advancement(sql_executor, game_id, last_advancement_played)

            # would lead to division by zero
            if end_transition == start_transition:
                # this game was not played
                continue

            assert end_transition is not None
            game_data['end_time_stamp'] = end_transition.time_stamp

            # get scoring, classic and name
            game_name = game.name
            game_data['scoring'] = game.scoring
            game_data['classic'] = not bool(game.game_type)

            # get ownerships
            game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
            owners = {o[2] for o in game_ownerships}
            centers_number = {o: len([oo for oo in game_ownerships if oo[2] == o]) for o in owners}
            game_data['centers_number'] = centers_number

            # get delays
            game_incidents = incidents.Incident.list_by_game_id(sql_executor, game_id)
            delayers = {d[3] for d in game_incidents}
            delays_number = {d: len([dd for dd in game_incidents if dd[3] == d]) for d in delayers}
            game_data['delays_number'] = delays_number

            # get dropouts
            game_dropouts = dropouts.Dropout.list_by_game_id(sql_executor, game_id)
            quitters = {d[2] for d in game_dropouts}
            dropouts_number = {q: len([qq for qq in game_dropouts if qq[2] == q]) for q in quitters}
            game_data['dropouts_number'] = dropouts_number

            games_dict[game_name] = game_data

        del sql_executor

        data = {'games_dict': games_dict}
        return data, 200


@API.resource('/extract_histo_data')
class ExtractHistoDataRessource(flask_restful.Resource):  # type: ignore
    """ ExtractHistoDataRessource """

    def get(self) -> typing.Tuple[typing.Dict[int, int], int]:  # pylint: disable=R0201
        """
        Get information for historic of number of players for site etc...
        EXPOSED
        """

        mylogger.LOGGER.info("/extract_histo_data - GET - getting histo data ")

        sql_executor = database.SqlExecutor()

        # concerned_games
        games_list = games.Game.inventory(sql_executor)
        concerned_games_list = [g.identifier for g in games_list if g.current_state in [1, 2] and not g.archive]

        # time of spring 01
        first_advancement = 1

        # extract start_time, end_time and players from games
        games_data = []
        for game_id in concerned_games_list:

            # get start date
            start_transition = transitions.Transition.find_by_game_advancement(sql_executor, game_id, first_advancement)

            if not start_transition:
                # this game was not played
                continue

            assert start_transition is not None
            start_time_stamp = start_transition.time_stamp

            # get game
            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None

            # game is ongoing
            if game.current_state == 1:
                end_time_stamp = None

            # game is finished
            if game.current_state == 2:

                # get current_advancement
                last_advancement_played = game.current_advancement - 1

                # get end date
                end_transition = transitions.Transition.find_by_game_advancement(sql_executor, game_id, last_advancement_played)

                assert end_transition is not None

                # would lead to division by zero
                if end_transition == start_transition:
                    # this game was not played
                    continue

                end_time_stamp = end_transition.time_stamp

                # would lead to assert
                if end_time_stamp == start_time_stamp:
                    # this game was not really played (one transition)
                    continue

            # get players (finally)
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            players = [a[1] for a in allocations_list if a[2] >= 1]

            games_data.append((start_time_stamp, end_time_stamp, players))

        del sql_executor

        # build list of events (sorted)
        event_table: typing.Dict[int, typing.List[typing.Tuple[bool, typing.List[int]]]] = {}
        for start_time, end_time, players in games_data:

            if end_time is not None:
                assert end_time > start_time, "game starts after it ends"

            if start_time not in event_table:
                event_table[start_time] = []
            event_table[start_time].append((True, players))

            if end_time is not None:
                if end_time not in event_table:
                    event_table[end_time] = []
                event_table[end_time].append((False, players))

        # make history of number
        list_cur_people = []
        histo_number = {}
        for ev_time, events in sorted(event_table.items(), key=lambda t: t[0]):
            for ev_add, ev_players in events:
                if ev_add:
                    list_cur_people += ev_players
                else:
                    for player in ev_players:
                        list_cur_people.remove(player)
            histo_number[ev_time] = len(set(list_cur_people))

        # clean history of numbers (remove dublins)
        h_number_prec = 0
        histo_number2 = histo_number.copy()
        for h_time, h_number in histo_number.items():
            if h_number == h_number_prec:
                del histo_number2[h_time]
            h_number_prec = h_number

        data = histo_number2
        return data, 200


@API.resource('/extract_histo_tournaments_data')
class ExtractTournamentsHistoDataRessource(flask_restful.Resource):  # type: ignore
    """ ExtractTournamentsHistoDataRessource """

    def get(self) -> typing.Tuple[typing.Dict[int, typing.Dict[str, typing.Any]], int]:  # pylint: disable=R0201
        """
        Get information for historic of number of players for tournaments etc...
        EXPOSED
        """

        mylogger.LOGGER.info("/extract_histo_tournaments_data - GET - getting histo tournament data ")

        sql_executor = database.SqlExecutor()

        # dict game -> tournament
        groupings_dict = {g: t for t, g in groupings.Grouping.inventory(sql_executor)}

        # concerned_games
        games_list = games.Game.inventory(sql_executor)
        concerned_games_list = [g.identifier for g in games_list if g.current_state in [1, 2] and not g.archive]

        # time of spring 01
        first_advancement = 1

        # extract start_time, end_time and players from games
        tournaments_dict: typing.Dict[int, typing.Dict[str, typing.Any]] = {}
        for game_id in concerned_games_list:

            # some game do not have a tournaneent yet
            if game_id not in groupings_dict:
                continue

            # get start date
            start_transition = transitions.Transition.find_by_game_advancement(sql_executor, game_id, first_advancement)

            if not start_transition:
                # this game was not played
                continue

            assert start_transition is not None
            start_time_stamp = start_transition.time_stamp

            # get game
            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None

            # game is ongoing
            if game.current_state == 1:
                end_time_stamp = None

            # game is finished
            if game.current_state == 2:

                # get current_advancement
                last_advancement_played = game.current_advancement - 1

                # get end date
                end_transition = transitions.Transition.find_by_game_advancement(sql_executor, game_id, last_advancement_played)

                assert end_transition is not None

                # would lead to division by zero
                if end_transition == start_transition:
                    # this game was not played
                    continue

                end_time_stamp = end_transition.time_stamp

                # would lead to assert
                if end_time_stamp == start_time_stamp:
                    # this game was not really played (one transition)
                    continue

            # get players (finally)
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            players = {a[1] for a in allocations_list if a[2] >= 1}

            tournament_id = groupings_dict[game_id]
            if tournament_id not in tournaments_dict:
                tournaments_dict[tournament_id] = {}

                # take values
                tournaments_dict[tournament_id]['first_start_time'] = start_time_stamp
                tournaments_dict[tournament_id]['last_start_time'] = start_time_stamp
                tournaments_dict[tournament_id]['first_end_time'] = end_time_stamp
                tournaments_dict[tournament_id]['last_end_time'] = end_time_stamp

                tournaments_dict[tournament_id]['players'] = players
            else:

                # update values
                tournaments_dict[tournament_id]['first_start_time'] = min(start_time_stamp, tournaments_dict[tournament_id]['first_start_time'])
                tournaments_dict[tournament_id]['last_start_time'] = max(start_time_stamp, tournaments_dict[tournament_id]['last_start_time'])
                if end_time_stamp is None:
                    tournaments_dict[tournament_id]['first_end_time'] = None
                    tournaments_dict[tournament_id]['last_end_time'] = None
                else:
                    if tournaments_dict[tournament_id]['first_end_time'] is not None:
                        tournaments_dict[tournament_id]['first_end_time'] = min(end_time_stamp, tournaments_dict[tournament_id]['first_end_time'])
                    if tournaments_dict[tournament_id]['last_end_time'] is not None:
                        tournaments_dict[tournament_id]['last_end_time'] = max(end_time_stamp, tournaments_dict[tournament_id]['last_end_time'])

                tournaments_dict[tournament_id]['players'].update(players)

        del sql_executor

        # need the number of players
        for data in tournaments_dict.values():
            data['affluence'] = len(data['players'])
            del data['players']

        return tournaments_dict, 200


@API.resource('/extract_variants_data')
class ExtractVariantsDataRessource(flask_restful.Resource):  # type: ignore
    """ ExtractVariantsDataRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Dict[str, typing.Any]], int]:  # pylint: disable=R0201
        """
        Get information for historic of number of players for variants etc...
        EXPOSED
        """

        mylogger.LOGGER.info("/extract_variants_data - GET - getting variant data ")

        sql_executor = database.SqlExecutor()

        # concerned_games
        games_list = games.Game.inventory(sql_executor)
        concerned_games_list = [g.identifier for g in games_list if g.current_state in [1, 2] and not g.archive]

        # extract start_time, end_time and players from games
        variants_dict: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
        for game_id in concerned_games_list:

            # get game
            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None

            variant_name = game.variant

            # get players (finally)
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            players = {a[1] for a in allocations_list if a[2] >= 1}

            if variant_name not in variants_dict:

                variants_dict[variant_name] = {}

                variant = variants.Variant.get_by_name(variant_name)
                assert variant is not None
                variants_dict[variant_name]['nb_players'] = variant['roles']['number']

                variants_dict[variant_name]['players'] = players
                variants_dict[variant_name]['games'] = 1

            else:

                variants_dict[variant_name]['players'].update(players)
                variants_dict[variant_name]['games'] += 1

        del sql_executor

        # need the number of players
        for data in variants_dict.values():
            data['affluence'] = len(data['players'])
            del data['players']

        return variants_dict, 200


@API.resource('/tournaments_manager/<tournament_id>')
class TournamentManagerRessource(flask_restful.Resource):  # type: ignore
    """ TournamentManagerRessource """

    def post(self, tournament_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Updates an tournament (director)
        EXPOSED
        """

        mylogger.LOGGER.info("/tournaments_manager/<tournament_id> - PUT - updating director event with id=%s", tournament_id)

        args = TOURNAMENT_PARSER2.parse_args(strict=True)

        director_id = args['director_id']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        # find the tournament
        tournament = tournaments.Tournament.find_by_identifier(sql_executor, tournament_id)
        if tournament is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Tournament {tournament_id} doesn't exist")

        assert tournament is not None

        # check moderator rights

        # get moderator list
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/moderators"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            del sql_executor
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
        the_moderators = req_result.json()

        # check pseudo in moderator list
        if pseudo not in the_moderators:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be site moderator) so you are not allowed to change tournament director")

        # update tournament here
        tournament.put_director(sql_executor, director_id)

        sql_executor.commit()
        del sql_executor

        data = {'identifier': tournament_id, 'msg': 'Ok director updated'}
        return data, 200


@API.resource('/announce-games')
class AnnounceGamesRessource(flask_restful.Resource):  # type: ignore
    """  AnnounceGamesRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Insert declaration in database for all ongoing games
        EXPOSED
        """

        mylogger.LOGGER.info("/announce-games - POST - creating declaration in all ongoing games")

        args = DECLARATION_PARSER2.parse_args(strict=True)

        payload = args['content']

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check user has right to post announce - must be moderator

        # check moderator rights

        # get moderator list
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/moderators"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
        the_moderators = req_result.json()

        # check pseudo in moderator list
        if pseudo not in the_moderators:
            flask_restful.abort(403, msg="You need to be site moderator to post a general announce")

        sql_executor = database.SqlExecutor()

        games_list = sql_executor.execute("select identifier from games", need_result=True)
        if not games_list:
            games_list = []
        games_id_list = [g[0] for g in games_list]

        table: typing.Dict[int, typing.List[int]] = collections.defaultdict(list)
        for game_id in games_id_list:

            # game is not ongoing : ignore
            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None
            if game.current_state != 1:
                continue

            table[game_id] = []

            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            for _, player_id, __ in allocations_list:
                table[game_id].append(player_id)

        # now we simplify

        useful_games: typing.List[int] = []
        iterations = 0

        while True:

            if not table:
                break

            iterations += 1

            # list remaining players
            players = map(int, set.union(*(map(set, table.values()))))  # type: ignore

            # count games per player
            nb_games = {p: len([g for g in table if p in table[g]]) for p in players}

            # take the game  with most isolated players

            best_game = min(table, key=lambda g: min(nb_games[p] for p in table[g]))
            useful_games.append(best_game)

            # reduce the problem
            # 1/ store selected players
            selected = set(table[best_game])

            # 2/ remove selected players from their games
            for game_id in table:
                table[game_id] = [p for p in table[game_id] if p not in selected]

            # 3/ remove useless games
            table = {k: v for k, v in table.items() if v}

        # use the user_id as role
        role_id = user_id

        role_name = pseudo

        for game_id in useful_games:

            # create declaration here
            with POST_DECLARATION_LOCK:

                if not POST_DECLARATION_REPEAT_PREVENTER.can(int(game_id), role_id):
                    del sql_executor
                    flask_restful.abort(400, msg="You have already declared a very short time ago")

                # create a content
                identifier = contents.Content.free_identifier(sql_executor)
                time_stamp = int(time.time())  # now
                content = contents.Content(identifier, int(game_id), time_stamp, payload)
                content.update_database(sql_executor)

                # create a declaration linked to the content
                declaration = declarations.Declaration(int(game_id), role_id, False, True, identifier)
                declaration.update_database(sql_executor)

                POST_DECLARATION_REPEAT_PREVENTER.did(int(game_id), role_id)

            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None

            subject = f"Un modérateur a posté une déclaration (annonce) dans la partie {game.name}"
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            addressees = []
            for _, player_id, role_id1 in allocations_list:
                if role_id1 != role_id:
                    addressees.append(player_id)
            body = "Bonjour !\n"
            body += "\n"

            body += f"Auteur de la déclaration : {role_name}\n"
            body += "\n"
            body += "Contenu de la déclaration :\n"
            body += "================\n"
            body += payload
            body += "\n"
            body += "================\n"

            body += "Vous pouvez aller consulter la déclaration et y répondre sur le site !\n"
            body += "\n"
            body += "Note : Vous pouvez désactiver cette notification en modifiant un paramètre de votre compte sur le site.\n"
            body += "\n"
            body += "Pour se rendre directement sur la partie :\n"
            body += f"https://diplomania-gen.fr?game={game.name}"

            json_dict = {
                'addressees': " ".join([str(a) for a in addressees]),
                'subject': subject,
                'body': body,
                'type': 'message',
            }

            host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
            port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/mail-players"
            # for a rest API headers are presented differently
            req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
            if req_result.status_code != 200:
                print(f"ERROR from server  : {req_result.text}")
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                del sql_executor
                flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

        sql_executor.commit()
        del sql_executor

        data = {'msg': "Ok announce inserted as declaration in games."}
        return data, 201


@API.resource('/access-submission-logs/<lines>')
class AccessSubmissionLogsRessource(flask_restful.Resource):  # type: ignore
    """ AccessSubmissionLogsRessource """

    def get(self, lines: int) -> typing.Tuple[typing.List[str], int]:  # pylint: disable=R0201
        """
        Simply return logs content
        EXPOSED
        """

        mylogger.LOGGER.info("/access-logs - GET - accessing submission logs lines=%s", lines)

        # extract from log file
        with open(lowdata.SUBMISSION_FILE, encoding='UTF-8') as file:
            log_lines = file.readlines()

        # remove trailing '\n'
        log_lines = [ll.rstrip('\n') for ll in log_lines]

        # take only last part
        log_lines = log_lines[- int(lines):]

        data = log_lines
        return data, 200


@API.resource('/training')
class TrainingRessource(flask_restful.Resource):  # type: ignore
    """ TrainingRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        Submit training orders (and situation)
        EXPOSED
        """

        mylogger.LOGGER.info("/training - POST - submitting orders for training")

        args = TRAINING_PARSER.parse_args(strict=True)

        variant_name = args['variant_name']
        role_id = args['role_id']
        orders_submitted = args['orders']
        situation = args['situation']
        training_advancement = args['advancement']
        names = args['names']

        # extract situation from input

        try:
            the_situation = json.loads(situation)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert situation from json to text ?")

        # get ownerships
        the_ownerships = the_situation['ownerships']
        ownership_dict: typing.Dict[str, int] = {}
        for the_ownership in the_ownerships:
            role_num = the_ownership['role']
            center_num = the_ownership['center_num']
            ownership_dict[str(center_num)] = role_num

        # get units
        the_units = the_situation['units']
        unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        for the_unit in the_units:
            type_num = the_unit['type_unit']
            role_num = the_unit['role']
            zone_num = the_unit['zone']
            unit_dict[str(role_num)].append([type_num, zone_num])

        # get units ad dislodged units
        the_dislodged_ones = the_situation['dislodged_ones']
        dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        for the_unit in the_dislodged_ones:
            type_num = the_unit['type_unit']
            role_num = the_unit['role']
            zone_num = the_unit['zone']
            dislodged_origin_num = the_unit['dislodged_origin']
            dislodged_unit_dict[str(role_num)].append([type_num, zone_num, dislodged_origin_num])

        # get forbiddens
        the_forbiddens = the_situation['forbiddens']
        forbidden_list: typing.List[int] = []
        for the_forbidden in the_forbiddens:
            forbidden_list.append(the_forbidden)

        # extract orders from input (need fakes)

        try:
            the_orders = json.loads(orders_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert orders from json to text ?")

        dummy_game_id = 0
        orders_list = []
        for the_order in the_orders:
            order = orders.Order(dummy_game_id, 0, 0, 0, 0, 0)
            order.load_json(the_order)
            order_export = order.export()
            orders_list.append(order_export)

        orders_list_json = json.dumps(orders_list)

        # fake units (these that are built)

        fake_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        for the_order in the_orders:
            if the_order['order_type'] == 8:
                type_num = the_order['active_unit']['type_unit']
                role_num = the_order['active_unit']['role']
                zone_num = the_order['active_unit']['zone']
                fake_unit_dict[str(role_num)].append([type_num, zone_num])

        # build situation (use the fakes too)
        situation_dict = {
            'ownerships': ownership_dict,
            'dislodged_ones': dislodged_unit_dict,
            'units': unit_dict,
            'fake_units': fake_unit_dict,
            'forbiddens': forbidden_list,
        }
        situation_dict_json = json.dumps(situation_dict)

        # evaluate variant

        variant_dict = variants.Variant.get_by_name(variant_name)
        if variant_dict is None:
            flask_restful.abort(404, msg=f"Variant {variant_name} doesn't exist")
        variant_dict_json = json.dumps(variant_dict)

        # now checking validity of orders

        json_dict = {
            'variant': variant_dict_json,
            'advancement': training_advancement,
            'situation': situation_dict_json,
            'orders': orders_list_json,
            'names': names,
            'role': role_id,
        }

        # post to solver
        host = lowdata.SERVER_CONFIG['SOLVER']['HOST']
        port = lowdata.SERVER_CONFIG['SOLVER']['PORT']
        url = f"{host}:{port}/solve"
        req_result = SESSION.post(url, data=json_dict)

        if 'msg' in req_result.json():
            submission_report = req_result.json()['msg']
        else:
            submission_report = "\n".join([req_result.json()['stderr'], req_result.json()['stdout']])

        # adjudication failed
        if req_result.status_code != 201:
            print(f"ERROR from solve server  : {req_result.text}")
            flask_restful.abort(400, msg=f":-( {submission_report}")

        # extract new report
        orders_result = req_result.json()['orders_result']

        # ok so orders are accepted
        data = {
            'submission_report': submission_report,
            'orders_result': f"{orders_result}"
        }
        return data, 201


@API.resource('/maintain')
class MaintainRessource(flask_restful.Resource):  # type: ignore
    """ MaintainRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=R0201
        """
        maintain
        EXPOSED
        """

        mylogger.LOGGER.info("/maintain - POST - maintain")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(401, msg=f"Bad authentication!:{message}")

        pseudo = req_result.json()['logged_in_as']

        # get admin pseudo
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/pseudo-admin"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get pseudo admin {message}")
        admin_pseudo = req_result.json()

        # check user is admin
        if pseudo != admin_pseudo:
            flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to maintain")

        print("MAINTENANCE - start !!!", file=sys.stderr)

        # sql_executor = database.SqlExecutor()
        #
        # # insert specific code here
        # for game in games.Game.inventory(sql_executor):
        #     print(game.name, file=sys.stderr)
        #     game.update_database(sql_executor)
        #
        # sql_executor.commit()
        #
        # del sql_executor

        print("MAINTENANCE - done !!!", file=sys.stderr)

        data = {'msg': "maintenance done"}
        return data, 200


def create_game_locks() -> None:
    """ create_game_locks """

    # get list of games
    sql_executor = database.SqlExecutor()
    games_list = games.Game.inventory(sql_executor)
    del sql_executor

    # create lock for active games
    for game in games_list:
        if game.current_state != 1:
            continue
        lock = threading.Lock()
        MOVE_GAME_LOCK_TABLE[game.name] = lock


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', required=False, help='mode debug to test stuff', action='store_true')
    args = parser.parse_args()

    mylogger.start_logger(__name__)
    lowdata.load_servers_config()

    orders_logger.start_logger('orders')

    # emergency
    if not database.db_present():

        mylogger.LOGGER.info("Emergency populate procedure")

        sql_executor = database.SqlExecutor()
        populate.populate(sql_executor)
        sql_executor.commit()
        del sql_executor

    # one lock per game is created
    create_game_locks()

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['GAME']['PORT']

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
