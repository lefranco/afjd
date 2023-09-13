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
import lighted_units
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
import exporter


SESSION = requests.Session()

APP = flask.Flask(__name__)
flask_cors.CORS(APP)
API = flask_restful.Api(APP)

GAME_PARSER = flask_restful.reqparse.RequestParser()
GAME_PARSER.add_argument('name', type=str, required=True)
GAME_PARSER.add_argument('description', type=str, required=False)
GAME_PARSER.add_argument('variant', type=str, required=False)
GAME_PARSER.add_argument('archive', type=int, required=False)
GAME_PARSER.add_argument('anonymous', type=int, required=False)
GAME_PARSER.add_argument('nomessage_game', type=int, required=False)
GAME_PARSER.add_argument('nomessage_current', type=int, required=False)
GAME_PARSER.add_argument('nopress_game', type=int, required=False)
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

# for game parameter alteration
GAME_PARSER2 = flask_restful.reqparse.RequestParser()
GAME_PARSER2.add_argument('used_for_elo', type=int, required=False)
GAME_PARSER2.add_argument('fast', type=int, required=False)
GAME_PARSER2.add_argument('nomessage_game', type=int, required=False)
GAME_PARSER2.add_argument('nopress_game', type=int, required=False)

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

LIGHT_PARSER = flask_restful.reqparse.RequestParser()
LIGHT_PARSER.add_argument('zone_num', type=int, required=True)


# a little welcome message to new games
WELCOME_TO_GAME = "Bienvenue sur cette partie gérée par le serveur de l'AFJD"

# creates some locks for some critical sections (where there can only be one at same time)
# there is one lock per ongoing game
# waitress uses threads, not processes
MOVE_GAME_LOCK_TABLE: typing.Dict[str, threading.Lock] = {}

# to avoid repeat messages/declarations
NO_REPEAT_DELAY_SEC = 15


def apply_visibility(variant_name: str, role_id: int, ownership_dict: typing.Dict[str, int], dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]], unit_dict: typing.Dict[str, typing.List[typing.List[int]]], forbidden_list: typing.List[int], orders_list: typing.List[typing.List[int]], fake_units_list: typing.List[typing.List[int]], lighted_unit_zones_list: typing.List[int]) -> None:
    """ apply_visibility
    this will change the parameters
    """

    # load the visibility data
    location = './data'
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

    # effect of the light
    lighted_regions = {zone2region[str(z)] for z in lighted_unit_zones_list}

    # seen region
    seen_regions = occupied_regions | adjacent_regions | lighted_regions

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


@API.resource('/variants/<name>')
class VariantIdentifierRessource(flask_restful.Resource):  # type: ignore
    """ VariantIdentifierRessource """

    def get(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, name: str) -> typing.Tuple[int, int]:
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

    def post(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
            flask_restful.abort(404, msg="Game is not ongoing")

        # game must be gameover
        if not game.game_over():
            flask_restful.abort(404, msg="Game is not finished")

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

    def get(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def put(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
                    flask_restful.abort(400, msg=f"You cannot set a deadline in the past from now !:'{date_desc}' (GMT)")

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

                # check enough players

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
                game.push_deadline()
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

            elif current_state_before == 2 and game.current_state == 3:

                # ----
                # we are distinguishing the game
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

    def delete(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def put(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get pseudo admin {message}")
        admin_pseudo = req_result.json()

        # check user is admin
        if pseudo != admin_pseudo:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to alter a game!")

        assert game is not None
        changed = game.load_json(args)
        if not changed:

            del sql_executor

            data = {'name': name, 'msg': 'Ok but no change !'}
            return data, 200

        game.update_database(sql_executor)
        sql_executor.commit()

        del sql_executor

        data = {'name': name, 'msg': 'Ok altered'}
        return data, 200


CREATE_GAME_LOCK = threading.Lock()


@API.resource('/games')
class GameListRessource(flask_restful.Resource):  # type: ignore
    """ GameListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Get list of all games (dictionary identifier -> name)
        EXPOSED
        """

        mylogger.LOGGER.info("/games - GET - get getting all games names")

        sql_executor = database.SqlExecutor()
        games_list = games.Game.inventory(sql_executor)
        del sql_executor

        data = {str(g.identifier): {'name': g.name, 'variant': g.variant, 'description': g.description, 'deadline': g.deadline, 'current_advancement': g.current_advancement, 'current_state': g.current_state, 'archive': g.archive, 'fast': g.fast, 'anonymous': g.anonymous, 'grace_duration': g.grace_duration, 'scoring': g.scoring, 'nopress_game': g.nopress_game, 'nomessage_game': g.nomessage_game, 'nopress_current': g.nopress_current, 'nomessage_current': g.nomessage_current, 'nb_max_cycles_to_play': g.nb_max_cycles_to_play, 'used_for_elo': g.used_for_elo} for g in games_list}
        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Creates a new game
        EXPOSED
        """

        mylogger.LOGGER.info("/games - POST - creating new game name")

        args = GAME_PARSER.parse_args(strict=True)

        name = args['name']

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

        # pay more attention to deadline
        entered_deadline = args['deadline']

        if entered_deadline is not None:

            # check it
            deadline_date = datetime.datetime.fromtimestamp(entered_deadline, datetime.timezone.utc)

            # cannot be in past
            if deadline_date < datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=1):
                date_desc = deadline_date.strftime('%Y-%m-%d %H:%M:%S')
                flask_restful.abort(400, msg=f"You cannot set a deadline in the past :'{date_desc}' (GMT)")

        else:

            # create it
            time_stamp = time.time()
            forced_deadline = int(time_stamp)
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
            game = games.Game(identifier, '', '', '', False, False, False, False, False, False, False, '', 0, 0, False, 0, 0, False, 0, False, 0, False, False, False, False, 0, 0, 0, 0, 0, 0)
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

            # allocate game master to game
            game.put_role(sql_executor, user_id, 0)

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
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                flask_restful.abort(404, msg=f"Failed to get id from pseudo for {passive_pseudo} : {message}")
            passive_user_id = req_result.json()

            # allocate passive to game
            game.put_role(sql_executor, passive_user_id, role_id)

        sql_executor.commit()
        del sql_executor

        data = {'name': name, 'msg': 'Ok game created'}
        return data, 201


@API.resource('/games-select')
class GameSelectListRessource(flask_restful.Resource):  # type: ignore
    """ GameSelectListRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self) -> typing.Tuple[typing.List[int], int]:
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


@API.resource('/allocations')
class AllocationListRessource(flask_restful.Resource):  # type: ignore
    """ AllocationListRessource """

    # an allocation is a game-role-pseudo relation where role is -1

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
        if game_master_id is None:
            del sql_executor
            flask_restful.abort(404, msg="There does not seem to be a game master for this game. This should be addressed beforehand...")

        if user_id not in [game_master_id, player_id]:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be either the game master of the game or the concerned player")

        # abort if has a role
        raw_allocations = allocations.Allocation.list_by_game_id(sql_executor, game_id)
        if player_id in [r[1] for r in raw_allocations if r[2] != -1]:
            del sql_executor
            flask_restful.abort(400, msg="You cannot remove or put in the game someone already assigned a role")

        dangling_role_id = -1

        if not delete:
            allocation = allocations.Allocation(game_id, player_id, dangling_role_id)
            allocation.update_database(sql_executor)

            # is if full now ?
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)

            game_capacity = capacities.Capacity.find_by_identifier(sql_executor, game_id)
            if game_capacity is None:
                del sql_executor
                flask_restful.abort(400, msg="Error cound not find capacity of the game")

            assert game_capacity is not None
            if len(allocations_list) >= game_capacity:

                # it is : send notification to game master

                subject = f"La partie {game.name} est maintenant complète !"
                addressees = [game_master_id]
                body = "Bonjour !\n"
                body += "\n"
                body += "Vous pouvez donc démarrer cette partie !\n"
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

        allocation = allocations.Allocation(game_id, player_id, dangling_role_id)
        allocation.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok allocation deleted if present'}
        return data, 200


@API.resource('/role-allocations')
class RoleAllocationListRessource(flask_restful.Resource):  # type: ignore
    """ AllocationListRessource """

    # a role-allocation is a game-role-pseudo relation where role is <> -1

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
                allocation = allocations.Allocation(game_id, player_id, role_id)
                allocation.update_database(sql_executor)

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
            allocation = allocations.Allocation(game_id, player_id, dangling_role_id)
            allocation.update_database(sql_executor)

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
            allocation = allocations.Allocation(game_id, player_id, role_id)
            allocation.update_database(sql_executor)

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
        allocation = allocations.Allocation(game_id, player_id, dangling_role_id)
        allocation.update_database(sql_executor)

        # we have a quitter here
        dropout = dropouts.Dropout(game_id, role_id, player_id)
        dropout.update_database(sql_executor)  # noqa: F821

        sql_executor.commit()
        del sql_executor

        # report
        data = {'msg': 'Ok player role-allocation deleted if present'}
        return data, 200


@API.resource('/game-master/<game_id>')
class GameMasterRessource(flask_restful.Resource):  # type: ignore
    """ GameRoleRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Optional[int], int]:
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

    def get(self, game_id: int) -> typing.Tuple[typing.Optional[int], int]:
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

    def get(self) -> typing.Tuple[typing.Optional[typing.Dict[int, int]], int]:
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

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, player_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, player_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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


@API.resource('/games-ready')
class GamesReadyRessource(flask_restful.Resource):  # type: ignore
    """ GamesReadyRessource """

    def get(self) -> typing.Tuple[typing.List[typing.Tuple[int, int, int]], int]:
        """
        Gets all  games that have all players
        EXPOSED
        """

        mylogger.LOGGER.info("/games-ready - GET - get getting all games ready")

        sql_executor = database.SqlExecutor()
        full_games_data = sql_executor.execute("select games.identifier, count(*) as filled_count, capacities.value from games join allocations on allocations.game_id=games.identifier join capacities on capacities.game_id=games.identifier group by identifier", need_result=True)
        del sql_executor

        # keep only the ones where no role is missing
        assert full_games_data is not None
        data = [tr[0] for tr in full_games_data if tr[1] >= tr[2]]

        return data, 200


@API.resource('/games-recruiting')
class GamesRecruitingRessource(flask_restful.Resource):  # type: ignore
    """ GamesRecruitingRessource """

    def get(self) -> typing.Tuple[typing.List[typing.Tuple[int, int, int]], int]:
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


@API.resource('/game-light-unit/<game_id>/<role_id>')
class GameLightUnitRessource(flask_restful.Resource):  # type: ignore
    """ GameLightUnitRessource """

    def post(self, game_id: int, role_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Lights a unit of a game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-light-unit/<game_id>/<role_id> - POST - light a unit game id=%s role_id=%s", game_id, role_id)

        args = LIGHT_PARSER.parse_args(strict=True)
        zone_submitted = args['zone_num']

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check the game position is protected
        assert game is not None
        variant_name = game.variant
        variant_data = variants.Variant.get_by_name(variant_name)
        assert variant_data is not None
        visibility_restricted = variant_data['visibility_restricted']
        if not visibility_restricted:
            del sql_executor
            flask_restful.abort(404, msg="This game is in a variant for which visibility of game position is not restricted !")

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

        # who is player for role ?
        assert game is not None
        player_id = game.get_role(sql_executor, int(role_id))

        # must be player
        if user_id != player_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the player who corresponds to this role")

        # light the unit
        game_units = units.Unit.list_by_game_id(sql_executor, game_id)
        zone_role_game_units = [(u[2], u[3]) for u in game_units]

        # unit must exist
        if (int(zone_submitted), int(role_id)) not in zone_role_game_units:
            del sql_executor
            flask_restful.abort(403, msg="There does not seem to exist such a unit")

        # create the light
        lighted_unit = lighted_units.LightedUnit(int(game_id), int(zone_submitted), int(role_id))
        lighted_unit.update_database(sql_executor)
        sql_executor.commit()

        del sql_executor

        data = {'msg': 'Ok unit enlighted'}
        return data, 201


@API.resource('/game-restricted-positions/<game_id>/<role_id>')
class GameRestrictedPositionRessource(flask_restful.Resource):  # type: ignore
    """ GameRestrictedPositionRessource """

    def get(self, game_id: int, role_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Gets position of the game (restricted : foggy variant mainly)
        EXPOSED
        """

        mylogger.LOGGER.info("/game-restricted-positions/<game_id>/<role_id> - GET - getting restricted position for game id=%s role id=%s", game_id, role_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check the game position is protected
        assert game is not None
        variant_name = game.variant
        variant_data = variants.Variant.get_by_name(variant_name)
        assert variant_data is not None
        visibility_restricted = variant_data['visibility_restricted']
        if not visibility_restricted:
            del sql_executor
            flask_restful.abort(404, msg="This game is in a variant for which visibility of game position is not restricted !")

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

        # who is player for role ?
        assert game is not None
        player_id = game.get_role(sql_executor, int(role_id))

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

        # must be player, game master or admin
        if user_id != player_id and pseudo != admin_pseudo:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the player or game master who corresponds to this role or site administrator")

        # get ownerships
        ownership_dict: typing.Dict[str, int] = {}
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
        forbidden_list: typing.List[int] = []
        game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)
        for _, region_num in game_forbiddens:
            forbidden_list.append(region_num)

        # special : get lighted units
        all_lighted_game_units = lighted_units.LightedUnit.list_by_game_id(sql_executor, game_id)
        all_lighted_zones = [lz[1] for lz in all_lighted_game_units]

        lighted_unit_zones_list: typing.List[int] = []
        game_units = units.Unit.list_by_game_id(sql_executor, game_id)
        for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
            if fake:
                continue
            if region_dislodged_from_num:
                continue
            if zone_num not in all_lighted_zones:
                continue
            lighted_unit_zones_list.append(zone_num)

        # game not ongoing or game master or game actually finished : you get get a clear picture
        if game.current_state != 1 or int(role_id) == 0 or (game.current_advancement % 5 == 4 and (game.current_advancement + 1) // 5 >= game.nb_max_cycles_to_play):
            del sql_executor
            data = {
                'ownerships': ownership_dict,
                'dislodged_ones': dislodged_unit_dict,
                'units': unit_dict,
                'forbiddens': forbidden_list,
                'lighted_units_zones': lighted_unit_zones_list,
            }
            return data, 200

        del sql_executor

        orders_list2: typing.List[typing.List[int]] = []
        fake_units_list2: typing.List[typing.List[int]] = []

        # now we can start hiding stuff
        # this will update last parameters
        apply_visibility(variant_name, role_id, ownership_dict, dislodged_unit_dict, unit_dict, forbidden_list, orders_list2, fake_units_list2, lighted_unit_zones_list)

        data = {
            'ownerships': ownership_dict,
            'dislodged_ones': dislodged_unit_dict,
            'units': unit_dict,
            'forbiddens': forbidden_list,
            'lighted_units_zones': lighted_unit_zones_list,
        }

        return data, 200


@API.resource('/game-positions/<game_id>')
class GamePositionRessource(flask_restful.Resource):  # type: ignore
    """ GamePositionRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
        variant_name = game.variant
        variant_data = variants.Variant.get_by_name(variant_name)
        assert variant_data is not None
        visibility_restricted = variant_data['visibility_restricted']
        if visibility_restricted:
            del sql_executor
            flask_restful.abort(404, msg="This game is in a variant for which visibility of game position is restricted !")

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

        # no light
        lighted_unit_zones_list: typing.List[int] = []

        del sql_executor

        data = {
            'ownerships': ownership_dict,
            'dislodged_ones': dislodged_unit_dict,
            'units': unit_dict,
            'forbiddens': forbidden_list,
            'lighted_units_zones': lighted_unit_zones_list,
        }
        return data, 200


@API.resource('/game-restricted-reports/<game_id>/<role_id>')
class GameRestrictedReportRessource(flask_restful.Resource):  # type: ignore
    """ GameRestrictedReportRessource """

    def get(self, game_id: int, role_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Gets the restrcited report of adjudication for the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-reports/<game_id>/<role_id> - GET - getting restricted report game id=%s role_id=%s", game_id, role_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check the game position is protected
        assert game is not None
        variant_name = game.variant
        variant_data = variants.Variant.get_by_name(variant_name)
        assert variant_data is not None
        visibility_restricted = variant_data['visibility_restricted']
        if not visibility_restricted:
            del sql_executor
            flask_restful.abort(404, msg="This game is in a variant for which visibility of game position is not restricted !")

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

        # game not ongoing or game master or game actually finished : you get get a clear picture
        if game.current_state != 1 or int(role_id) == 0 or (game.current_advancement % 5 == 4 and (game.current_advancement + 1) // 5 >= game.nb_max_cycles_to_play):
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

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
        variant_name = game.variant
        variant_data = variants.Variant.get_by_name(variant_name)
        assert variant_data is not None
        visibility_restricted = variant_data['visibility_restricted']
        if visibility_restricted:
            del sql_executor
            flask_restful.abort(404, msg="This game is in a variant for which visibility of game position is restricted !")

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


@API.resource('/game-restricted-transitions/<game_id>/<advancement>/<role_id>')
class GameRestrictedTransitionRessource(flask_restful.Resource):  # type: ignore
    """ GameRestrictedTransitionRessource """

    def get(self, game_id: int, advancement: int, role_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Gets the full restricted report  (transition : postions + orders + report) of adjudication for the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-restricted-transitions/<game_id>/<advancement>/<role_id> - GET - getting transition game id=%s advancement=%s role id=%s ", game_id, advancement, role_id)

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # check the game position is protected
        assert game is not None
        variant_name = game.variant
        variant_data = variants.Variant.get_by_name(variant_name)
        assert variant_data is not None
        visibility_restricted = variant_data['visibility_restricted']
        if not visibility_restricted:
            del sql_executor
            flask_restful.abort(404, msg="This game is in a variant for which visibility of game position is not restricted !")

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

        # game not ongoing or game master or game actually finished : you get get a clear picture
        if game.current_state != 1 or int(role_id) == 0 or (game.current_advancement % 5 == 4 and (game.current_advancement + 1) // 5 >= game.nb_max_cycles_to_play):
            del sql_executor
            data = {'time_stamp': transition.time_stamp, 'situation': the_situation, 'orders': the_orders, 'report_txt': report_txt}
            return data, 200

        # get a partial picture of things
        del sql_executor

        ownership_dict = the_situation['ownerships']
        dislodged_unit_dict = the_situation['dislodged_ones']
        unit_dict = the_situation['units']
        forbidden_list = the_situation['forbiddens']

        # TEMPORARY PATCH
        # TODO REMOVE AFTER SUPRRESION OF TWO FIRST FOG TEST GAMES
        # AND AFTER RE TEST NEW FOG GAME
        if 'lighted_unit_zones_list'not in the_situation:
            the_situation['lighted_unit_zones_list'] = []
        lighted_unit_zones_list = the_situation['lighted_unit_zones_list']

        orders_list = the_orders['orders']
        fake_units_list = the_orders['fake_units']

        # this will update last parameters
        apply_visibility(variant_name, role_id, ownership_dict, dislodged_unit_dict, unit_dict, forbidden_list, orders_list, fake_units_list, lighted_unit_zones_list)

        data = {'time_stamp': transition.time_stamp, 'situation': {'ownerships': ownership_dict, 'dislodged_ones': dislodged_unit_dict, 'units': unit_dict, 'forbiddens': forbidden_list}, 'orders': {'orders': orders_list, 'fake_units': fake_units_list}, 'report_txt': "---"}
        return data, 200


@API.resource('/game-transitions/<game_id>/<advancement>')
class GameTransitionRessource(flask_restful.Resource):  # type: ignore
    """ GameTransitionRessource """

    def get(self, game_id: int, advancement: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
        variant_name = game.variant
        variant_data = variants.Variant.get_by_name(variant_name)
        assert variant_data is not None
        visibility_restricted = variant_data['visibility_restricted']
        if visibility_restricted:
            del sql_executor
            flask_restful.abort(404, msg="This game is in a variant for which visibility of game position is restricted !")

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

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[int, int], int]:
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

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

        # must be game master
        if user_id != game_master_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

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

            # handle definitive boolean
            # game master forced player to agree to adjudicate
            status, late, unsafe, missing, adjudicated, debug_message = agree.fake_post(game_id, role_id, True, adjudication_names, sql_executor)

        # end of protected section

        if not status:
            del sql_executor  # noqa: F821
            flask_restful.abort(400, msg=f"Failed to agree (forced) to adjudicate : {debug_message}")

        # this may have caused player to be late
        if late:
            subject = f"L'arbitre de la partie {game.name} a forcé votre accord, ce qui vous inflige un retard !"
            game_id = game.identifier
            allocations_list = allocations.Allocation.list_by_role_id_game_id(sql_executor, role_id, game_id)
            addressees = []
            for _, player_id, __ in allocations_list:
                addressees.append(player_id)

            body = "Bonjour !\n"
            body += "\n"
            body += "L'arbitre a forcé votre accord sur cette partie et vous étiez en retard !\n"
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

                subject = f"La partie {game.name} a avancé (avec l'aide de l'arbitre)!"
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
                payload = ""
                if game.last_season():
                    payload = "Attention, dernier automne !"
                elif game.last_year():
                    payload = "Attention, dernière année !"
                if payload:
                    notify_last_line(sql_executor, game_id, payload)  # noqa: F821

        sql_executor.commit()  # noqa: F821
        del sql_executor  # noqa: F821

        data = {'late': late, 'unsafe': unsafe, 'missing': missing, 'adjudicated': adjudicated, 'debug_message': debug_message, 'msg': "Forced!"}
        return data, 201


@API.resource('/game-commute-agree-solve/<game_id>')
class GameCommuteAgreeSolveRessource(flask_restful.Resource):  # type: ignore
    """ GameCommuteAgreeSolveRessource """

    def post(self, game_id: int) -> typing.Tuple[None, int]:
        """
        Commute agree to solve from after deadline to now by a clockwork
        EXPOSED
        """
        mylogger.LOGGER.info("/game-commute-agree-solve/<game_id> - POST - commute agreeing from clockwork to solve with orders game id=%s", game_id)

        args = COMMUTE_AGREE_PARSER.parse_args(strict=True)

        adjudication_names = args['adjudication_names']

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

        # game must not be actually finished
        if game.current_advancement % 5 == 4 and (game.current_advancement + 1) // 5 >= game.nb_max_cycles_to_play:
            del sql_executor
            flask_restful.abort(403, msg="Game seems to be actually finished")

        # begin of protected section
        with MOVE_GAME_LOCK_TABLE[game.name]:

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
                del sql_executor
                flask_restful.abort(400, msg="There is at least a role that does not seem to have submitted orders yet")

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
                status, _, __, ___, adjudicated, debug_message = agree.fake_post(game_id, role_id, 1, adjudication_names, sql_executor)
                if not status:
                    break
                if adjudicated:
                    break

        # end of protected section

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
            payload = ""
            if game.last_season():
                payload = "Attention, dernier automne ! !"
            elif game.last_year():
                payload = "Attention, dernière année !"
            if payload:
                notify_last_line(sql_executor, game_id, payload)  # noqa: F821

        sql_executor.commit()  # noqa: F821
        del sql_executor  # noqa: F821

        return None, 201


@API.resource('/game-orders/<game_id>')
class GameOrderRessource(flask_restful.Resource):  # type: ignore
    """ GameOrderRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
        player_id = game.get_role(sql_executor, role_id)

        # must be player
        if user_id != player_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the player who corresponds to this role")

        # not allowed for game master
        if role_id == 0 and not game.archive:
            del sql_executor
            flask_restful.abort(403, msg="Submitting orders is not possible for game master for non archive games")

        # archive games and fast games stick to agree now
        if game.fast or game.archive:
            if definitive_value == 2:
                del sql_executor
                flask_restful.abort(403, msg="Submitting agreement after deadine is not possible for fast or archive games")

        # begin of protected section
        with MOVE_GAME_LOCK_TABLE[game.name]:

            # must not be game over
            if game.game_over():
                del sql_executor
                flask_restful.abort(403, msg="Game is finished !")

            # check orders are required
            # needed list : those who need to submit orders
            if role_id != 0:
                actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
                needed_list = [o[1] for o in actives_list]
                if role_id not in needed_list:
                    del sql_executor
                    flask_restful.abort(403, msg="This role does not seem to require any orders")

            # extract orders from input
            try:
                the_orders = json.loads(orders_submitted)
            except json.JSONDecodeError:
                del sql_executor
                flask_restful.abort(400, msg="Did you convert orders from json to text ?")

            # check the phase
            for the_order in the_orders:
                if game.current_advancement % 5 in [0, 2]:
                    if the_order['order_type'] not in [1, 2, 3, 4, 5]:
                        flask_restful.abort(400, msg="Seems we have a move phase, you must provide move orders! (or more probably, you submitted twice or game changed just before you submitted)")
                if game.current_advancement % 5 in [1, 3]:
                    if the_order['order_type'] not in [6, 7]:
                        flask_restful.abort(400, msg="Seems we have a retreat phase, you must provide retreat orders! (or more probably, you submitted twice or game changed just before you submitted")
                if game.current_advancement % 5 in [4]:
                    if the_order['order_type'] not in [8, 9]:
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

            # special : get lighted units
            all_lighted_game_units = lighted_units.LightedUnit.list_by_game_id(sql_executor, game_id)  # noqa: F821
            all_lighted_zones = [lz[1] for lz in all_lighted_game_units]

            lighted_unit_zones_list: typing.List[int] = []
            game_units = units.Unit.list_by_game_id(sql_executor, game_id)  # noqa: F821
            for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
                if fake:
                    continue
                if region_dislodged_from_num:
                    continue
                if zone_num not in all_lighted_zones:
                    continue
                lighted_unit_zones_list.append(zone_num)

            # situation: get forbiddens
            forbidden_list = []
            game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)  # noqa: F821
            for _, region_num in game_forbiddens:
                forbidden_list.append(region_num)

            orders_list2: typing.List[typing.List[int]] = []
            fake_units_list2: typing.List[typing.List[int]] = []

            # apply visibility if the game position is protected
            variant_name = game.variant
            variant_data = variants.Variant.get_by_name(variant_name)
            assert variant_data is not None
            visibility_restricted = variant_data['visibility_restricted']
            if visibility_restricted:
                # now we can start hiding stuff
                # this will update last parameters
                apply_visibility(variant_name, role_id, ownership_dict, dislodged_unit_dict, unit_dict, forbidden_list, orders_list2, fake_units_list2, lighted_unit_zones_list)

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

                print(f"ERROR from solve server  : {req_result.text}", file=sys.stderr)
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
            status, late, unsafe, missing, adjudicated, debug_message = agree.fake_post(game_id, role_id, definitive_value, adjudication_names, sql_executor)  # noqa: F821

        # end of protected section

        if not status:
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
                    del sql_executor
                    flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

                # declaration from system
                payload = ""
                if game.last_season():
                    payload = "Attention, dernier automne ! !"
                elif game.last_year():
                    payload = "Attention, dernière année !"
                if payload:
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
                    del sql_executor
                    flask_restful.abort(400, msg=f"Failed to set power {role_id} in disorder : {message}")

        sql_executor.commit()  # noqa: F821
        del sql_executor  # noqa: F821

        data = {'late': late, 'unsafe': unsafe, 'missing': missing, 'adjudicated': adjudicated, 'debug_message': debug_message, 'msg': submission_report}

        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

        # must be game master
        if user_id != game_master_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

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

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

        # apply visibility if the game position is protected
        variant_name = game.variant
        variant_data = variants.Variant.get_by_name(variant_name)
        assert variant_data is not None
        visibility_restricted = variant_data['visibility_restricted']
        if visibility_restricted:

            # situation: get ownerships
            ownership_dict: typing.Dict[str, int] = {}
            game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)  # noqa: F821
            for _, center_num, role_num in game_ownerships:
                ownership_dict[str(center_num)] = role_num

            # now we can start hiding stuff
            # need these two parameters
            dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = {}
            forbidden_list: typing.List[int] = []
            lighted_unit_zones_list: typing.List[int] = []

            orders_list2: typing.List[typing.List[int]] = []
            fake_units_list2: typing.List[typing.List[int]] = []

            # this will update last parameters
            apply_visibility(variant_name, role_id, ownership_dict, dislodged_unit_dict, unit_dict, forbidden_list, orders_list2, fake_units_list2, lighted_unit_zones_list)

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

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[int]], int]:
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
            if pseudo not in the_moderators:
                del sql_executor
                flask_restful.abort(403, msg="You do not seem to play or master the game (or to be site moderator) so you are not alowed to see the submissions!")

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


@API.resource('/all-player-games-orders-submitted')
class AllPlayerGamesOrdersSubmittedRessource(flask_restful.Resource):  # type: ignore
    """ AllPlayerGamesOrdersSubmittedRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Dict[int, typing.List[int]]], int]:
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

    def get(self) -> typing.Tuple[typing.Dict[int, typing.Dict[int, int]], int]:
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

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
            print(f"ERROR from solve server  : {req_result.text}", file=sys.stderr)
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

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

        before_time = time.time()


        after_time = time.time()
        print(f"date-last-game-declarations-OPT : ELAPSED {after_time - before_time}sec", file=sys.stderr)

        declarations_list = declarations.Declaration.last_date_by_player_id(sql_executor, player_id)
        dict_time_stamp = dict(declarations_list)

        del sql_executor

        data = {'dict_time_stamp': dict_time_stamp}
        return data, 200


@API.resource('/date-last-game-messages')
class DateLastGameMessagesRessource(flask_restful.Resource):  # type: ignore
    """  DateLastGameMessagesRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

        before_time = time.time()

        messages_list = messages.Message.last_date_by_player_id(sql_executor, player_id)
        dict_time_stamp = dict(messages_list)

        after_time = time.time()
        print(f"date-last-game-messages-OPT : ELAPSED {after_time - before_time}sec", file=sys.stderr)

        del sql_executor

        data = {'dict_time_stamp': dict_time_stamp}
        return data, 200


@API.resource('/game-visits/<game_id>/<visit_type>')
class GameVisitsRessource(flask_restful.Resource):  # type: ignore
    """  GameVisitsRessource """

    def post(self, game_id: int, visit_type: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, game_id: int, visit_type: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, visit_type: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
        expected_id = game.get_role(sql_executor, role_id)

        # must be player
        if user_id != expected_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the player who is in charge")

        # game must be ongoing
        if game.current_state != 1:
            del sql_executor
            flask_restful.abort(403, msg="Game does not seem to be ongoing")

        # create vote here
        vote = votes.Vote(int(game_id), role_id, bool(value))
        vote.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': "Ok vote inserted"}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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


@API.resource('/player-incidents/<player_id>')
class PlayerIncidentsRessource(flask_restful.Resource):  # type: ignore
    """ PlayerIncidentsRessource """

    def get(self, player_id: int) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int]]], int]:
        """
        Gets list of roles which have produced an incident for given player
        EXPOSED
        """

        mylogger.LOGGER.info("/player-incidents/<game_id> - GET - getting which incidents occured for player id=%s", player_id)

        sql_executor = database.SqlExecutor()

        # incidents_list : those who submitted orders after deadline
        incidents_list = incidents.Incident.list_by_player_id(sql_executor, player_id)

        # only outputs game_id and game_advancement
        late_list = [(o[0], o[2]) for o in incidents_list]

        del sql_executor

        data = {'incidents': late_list}
        return data, 200


@API.resource('/player-dropouts/<player_id>')
class PlayerDropoutsRessource(flask_restful.Resource):  # type: ignore
    """ PlayerDropoutsRessource """

    def get(self, player_id: int) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int]]], int]:
        """
        Gets list of games which have produced an dropout for given player
        EXPOSED
        """

        mylogger.LOGGER.info("/player-dropouts/<game_id> - GET - getting which dropouts occured for player id=%s", player_id)

        sql_executor = database.SqlExecutor()

        # dropouts_list : those who quitted the game
        dropouts_list = dropouts.Dropout.list_by_player_id(sql_executor, player_id)

        # only outputs game_id
        drop_list = [(o[0], ) for o in dropouts_list]

        del sql_executor

        data = {'dropouts': drop_list}
        return data, 200


@API.resource('/player-game-incidents')
class PlayerGameIncidentsRessource(flask_restful.Resource):  # type: ignore
    """ PlayerGameIncidentsRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, int, int, float]]], int]:
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

    def get(self) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, float]]], int]:
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

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, typing.Optional[int], int, float]]], int]:
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

        # find the current players
        allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
        current_players_dict = {a[2]: a[1] for a in allocations_list}

        # incidents_list : those who submitted orders after deadline
        incidents_list = incidents.Incident.list_by_game_id(sql_executor, game_id)

        # player_id only provided if not in game at this role (because left or was moved)
        late_list = [(o[1], o[2], o[3] if o[1] not in current_players_dict or o[3] != current_players_dict[o[1]] else None, o[4], o[5]) for o in incidents_list]

        del sql_executor

        data = {'incidents': late_list}
        return data, 200


@API.resource('/game-incidents2/<game_id>')
class GameIncidents2Ressource(flask_restful.Resource):  # type: ignore
    """ GameIncidents2Ressource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, float]]], int]:
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


@API.resource('/game-dropouts/<game_id>')
class GameDropoutsRessource(flask_restful.Resource):  # type: ignore
    """ GameDropoutsRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, float]]], int]:
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

    def get(self) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, int, float]]], int]:
        """
        Gets list of roles which have produced an dropout
        EXPOSED
        """

        mylogger.LOGGER.info("/game-dropouts/<game_id> - GET - getting which dropouts occured")

        sql_executor = database.SqlExecutor()
        late_list = dropouts.Dropout.inventory(sql_executor)
        sql_executor = database.SqlExecutor()
        del sql_executor

        data = {'dropouts': late_list}
        return data, 200


@API.resource('/game-notes/<game_id>')
class GameNoteRessource(flask_restful.Resource):  # type: ignore
    """  GameNoteRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def delete(self, game_id: int, role_id: int, advancement: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def delete(self, game_id: int, role_id: int, player_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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


@API.resource('/tournaments/<game_name>')
class TournamentRessource(flask_restful.Resource):  # type: ignore
    """ TournamentRessource """

    def get(self, game_name: str) -> typing.Tuple[typing.Optional[typing.Dict[str, typing.Any]], int]:
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

    def delete(self, game_name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Dict[str, typing.Any]], int]:
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

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def post(self, tournament_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def get(self, tournament_id: int) -> typing.Tuple[typing.List[typing.Tuple[int, int, int, int, float]], int]:
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
                if player_id != current_players_dict[role_id]:
                    continue
                late_list.append((game_id, role_id, advancement, duration_incident, date_incident))

        del sql_executor

        data = late_list
        return data, 200


@API.resource('/tournament-incidents2/<tournament_id>')
class TournamentIncidents2Ressource(flask_restful.Resource):  # type: ignore
    """ TournamentIncidents2Ressource """

    def get(self, tournament_id: int) -> typing.Tuple[typing.List[typing.Tuple[int, int, int, float]], int]:
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

    def get(self, tournament_id: int) -> typing.Tuple[typing.Dict[int, typing.Dict[str, typing.Any]], int]:
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

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
        allocation = allocations.Allocation(int(game_id), game_master_id, dangling_role_id)
        allocation.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok, game master revoked !'}
        return data, 201


@API.resource('/clear-old-delays')
class ClearOldDelaysRessource(flask_restful.Resource):  # type: ignore
    """ ClearOldDelaysRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        maintain
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
            flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to clear old delays")

        sql_executor = database.SqlExecutor()
        incidents.Incident.purge_old(sql_executor)
        sql_executor.commit()

        del sql_executor

        data = {'msg': "clear old delays done"}
        return data, 200


@API.resource('/tournament-allocations/<tournament_id>')
class TournamentGameRessource(flask_restful.Resource):  # type: ignore
    """ TournamentGameRessource """

    def get(self, tournament_id: int) -> typing.Tuple[typing.Dict[int, typing.Dict[str, typing.Any]], int]:
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
        url = f"{host}:{port}/moderators"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get list of moderators {message}")
        the_moderators = req_result.json()

        # check pseudo in moderator list
        if pseudo not in the_moderators:
            flask_restful.abort(403, msg="You do not seem to be site moderator so you are not allowed get all players from tournament !")

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

    def get(self, tournament_id: int) -> typing.Tuple[typing.List[int], int]:
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

        players_list: typing.Set[int] = set()
        for game_id in tournament_game_ids:

            # get answer
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            players_list.update([a[1] for a in allocations_list])

        del sql_executor

        # need to sort so not to give any indoications on who plays what
        data = sorted(players_list)

        return data, 200


@API.resource('/statistics')
class StatisticsRessource(flask_restful.Resource):  # type: ignore
    """ StatisticsRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

        # stats about games

        allocations_list = allocations.Allocation.inventory(sql_executor)
        games_list = games.Game.inventory(sql_executor)
        del sql_executor

        # games we can speak about the players
        allowed_games = {g.identifier for g in games_list if g.current_state == 1 and not g.archive}

        # players_dict
        game_masters_set = set()
        players_set = set()
        for (game_id, player_id, role_id) in allocations_list:
            if game_id not in allowed_games:
                continue
            if role_id == 0:
                game_masters_set.add(player_id)
            else:
                players_set.add(player_id)

        data = {'suffering_games': suffering_games, 'ongoing_games': len(allowed_games), 'active_game_masters': len(game_masters_set), 'active_players': len(players_set)}
        return data, 200


@API.resource('/extract_elo_data')
class ExtractEloDataRessource(flask_restful.Resource):  # type: ignore
    """ ExtractEloDataRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
            game_data['classic'] = not game.nomessage_game

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

    def get(self) -> typing.Tuple[typing.Dict[int, int], int]:
        """
        Get information for historic of number of players etc...
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

            game_data: typing.Dict[str, typing.Any] = {}

            # get start date
            start_transition = transitions.Transition.find_by_game_advancement(sql_executor, game_id, first_advancement)

            if not start_transition:
                # this game was not played
                continue

            assert start_transition is not None
            start_time_stamp = start_transition.time_stamp

            # get players
            allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
            players = [a[1] for a in allocations_list if a[2] >= 1]

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
                game_data['number_advancement_played'] = game.current_advancement

                # get end date
                end_transition = transitions.Transition.find_by_game_advancement(sql_executor, game_id, last_advancement_played)

                assert end_transition is not None

                # would lead to division by zero
                if end_transition == start_transition:
                    # this game was not played
                    continue

                end_time_stamp = end_transition.time_stamp

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


@API.resource('/tournaments_manager/<tournament_id>')
class TournamentManagerRessource(flask_restful.Resource):  # type: ignore
    """ TournamentManagerRessource """

    def post(self, tournament_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

            best_game = min(table, key=lambda g: max(nb_games[p] for p in table[g]))
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


@API.resource('/maintain')
class MaintainRessource(flask_restful.Resource):  # type: ignore
    """ MaintainRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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
        #  sql_executor = database.SqlExecutor()

        # TODO : insert specific code here

        #  sql_executor.commit()

        #  del sql_executor
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
