#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import collections
import json
import datetime

import flask
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore
import requests

import mylogger
import populate
import mailer
import allocations
import ownerships
import units
import orders
import forbiddens
import reports
import games
import variants
import database
import lowdata

DIPLOMACY_SEASON_CYCLE = [1, 2, 1, 2, 3]

SESSION = requests.Session()

APP = flask.Flask(__name__)
API = flask_restful.Api(APP)

GAME_PARSER = flask_restful.reqparse.RequestParser()
GAME_PARSER.add_argument('name', type=str, required=True)
GAME_PARSER.add_argument('description', type=str, required=False)
GAME_PARSER.add_argument('variant', type=str, required=False)
GAME_PARSER.add_argument('archive', type=int, required=False)
GAME_PARSER.add_argument('anonymous', type=int, required=False)
GAME_PARSER.add_argument('silent', type=int, required=False)
GAME_PARSER.add_argument('cumulate', type=int, required=False)
GAME_PARSER.add_argument('fast', type=int, required=False)
GAME_PARSER.add_argument('deadline', type=str, required=False)
GAME_PARSER.add_argument('speed_moves', type=int, required=False)
GAME_PARSER.add_argument('cd_possible_moves', type=int, required=False)
GAME_PARSER.add_argument('speed_retreats', type=int, required=False)
GAME_PARSER.add_argument('cd_possible_retreats', type=int, required=False)
GAME_PARSER.add_argument('speed_adjustments', type=int, required=False)
GAME_PARSER.add_argument('cd_possible_builds', type=int, required=False)
GAME_PARSER.add_argument('cd_possible_removals', type=int, required=False)
GAME_PARSER.add_argument('play_weekend', type=int, required=False)
GAME_PARSER.add_argument('manual', type=int, required=False)
GAME_PARSER.add_argument('access_code', type=int, required=False)
GAME_PARSER.add_argument('access_restriction_reliability', type=int, required=False)
GAME_PARSER.add_argument('access_restriction_regularity', type=int, required=False)
GAME_PARSER.add_argument('access_restriction_performance', type=int, required=False)
GAME_PARSER.add_argument('current_advancement', type=int, required=False)
GAME_PARSER.add_argument('nb_max_cycles_to_play', type=int, required=False)
GAME_PARSER.add_argument('victory_centers', type=int, required=False)
GAME_PARSER.add_argument('current_state', type=int, required=False)
GAME_PARSER.add_argument('pseudo', type=str, required=False)

GAME_DELETE_PARSER = flask_restful.reqparse.RequestParser()
GAME_DELETE_PARSER.add_argument('pseudo', type=str, required=False)

ALLOCATION_PARSER = flask_restful.reqparse.RequestParser()
ALLOCATION_PARSER.add_argument('game_id', type=int, required=True)
ALLOCATION_PARSER.add_argument('player_id', type=int, required=True)
ALLOCATION_PARSER.add_argument('role_id', type=int, required=True)
ALLOCATION_PARSER.add_argument('pseudo', type=str, required=False)

SUBMISSION_PARSER = flask_restful.reqparse.RequestParser()
SUBMISSION_PARSER.add_argument('role_id', type=int, required=True)
SUBMISSION_PARSER.add_argument('pseudo', type=str, required=False)
SUBMISSION_PARSER.add_argument('orders', type=str, required=True)
SUBMISSION_PARSER.add_argument('names', type=str, required=True)

RETRIEVE_PARSER = flask_restful.reqparse.RequestParser()
RETRIEVE_PARSER.add_argument('role_id', type=int, required=True)
RETRIEVE_PARSER.add_argument('pseudo', type=str, required=False)

ADJUDICATION_PARSER = flask_restful.reqparse.RequestParser()
ADJUDICATION_PARSER.add_argument('pseudo', type=str, required=False)
ADJUDICATION_PARSER.add_argument('names', type=str, required=True)

RECTIFICATION_PARSER = flask_restful.reqparse.RequestParser()
RECTIFICATION_PARSER.add_argument('pseudo', type=str, required=False)
RECTIFICATION_PARSER.add_argument('center_ownerships', type=str, required=True)
RECTIFICATION_PARSER.add_argument('units', type=str, required=True)
RECTIFICATION_PARSER.add_argument('forbiddens', type=str, required=True)


@API.resource('/variants/<name>')
class VariantIdentifierRessource(flask_restful.Resource):  # type: ignore
    """ from name get identifier """

    def get(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ getter """

        mylogger.LOGGER.info("R of CRUD - retrieving variant json file %s", name)

        if not name.isalnum():
            flask_restful.abort(400, msg=f"Variant {name} is incorrect as a name")

        # find data
        variant = variants.Variant.get_by_name(name)
        if variant is None:
            flask_restful.abort(404, msg=f"Variant {name} doesn't exist")

        assert variant is not None
        return variant, 200


@API.resource('/game_identifiers/<name>')
class GameIdentifierRessource(flask_restful.Resource):  # type: ignore
    """ from name get identifier """

    def get(self, name: str) -> typing.Tuple[int, int]:  # pylint: disable=no-self-use
        """ getter """

        mylogger.LOGGER.info("R of CRUD - retrieving one game (just identifier) %s", name)

        # find data
        game = games.Game.find_by_name(name)
        if game is None:
            flask_restful.abort(404, msg=f"Game {name} doesn't exist")

        assert game is not None
        return game.identifier, 200


@API.resource('/games/<name>')
class GameRessource(flask_restful.Resource):  # type: ignore
    """ shows a single game item and lets you delete a game item """

    def get(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ getter """

        mylogger.LOGGER.info("R of CRUD - retrieving one game %s", name)

        # find data
        game = games.Game.find_by_name(name)
        if game is None:
            flask_restful.abort(404, msg=f"Game {name} doesn't exist")

        assert game is not None
        data = game.save_json()

        return data, 200

    def put(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ updater """

        mylogger.LOGGER.info("U of CRUD - put - updating a game %s", name)

        args = GAME_PARSER.parse_args()
        pseudo = args['pseudo']

        game = games.Game.find_by_name(name)
        if game is None:
            flask_restful.abort(404, msg=f"Game {name} does not exist")

        if pseudo == '':
            flask_restful.abort(404, msg="Need a pseudo to modify game")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify_user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player_identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")

        user_id = req_result.json()

        # check this is game_master
        assert game is not None
        if game.get_role(0) != user_id:
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        current_state_before = game.current_state
        assert game is not None
        changed = game.load_json(args)
        if not changed:
            data = {'name': name, 'msg': 'Ok but no change !'}
            return data, 200

        # some additional changes
        if game.current_state != current_state_before:

            if current_state_before == 0 and game.current_state == 1:

                # check enough players
                nb_players_allocated = game.number_allocated()
                variant_name = game.variant
                variant_data = variants.Variant.get_by_name(variant_name)
                assert variant_data is not None
                number_players_expected = variant_data['roles']['number']
                if nb_players_allocated < number_players_expected:
                    data = {'name': name, 'msg': 'Not enough players !'}
                    return data, 400

                game.start()

            if current_state_before == 1 and game.current_state == 2:

                # no check ?
                game.terminate()

        game.update_database()

        data = {'name': name, 'msg': 'Ok updated'}
        return data, 200

    def delete(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ deleter """

        mylogger.LOGGER.info("D of CRUD - delete  removing one game %s", name)

        args = GAME_DELETE_PARSER.parse_args()
        pseudo = args['pseudo']

        # delete game from here
        game = games.Game.find_by_name(name)
        if game is None:
            flask_restful.abort(404, msg=f"Game {name} doesn't exist")

        if pseudo == '':
            flask_restful.abort(404, msg="Need a pseudo to delete game")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify_user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player_identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check this is game_master
        assert game is not None
        if game.get_role(0) != user_id:
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # delete game
        assert game is not None
        game.delete_database()

        # and allocations
        game.delete_allocations()

        return {}, 200


@API.resource('/games')
class GameListRessource(flask_restful.Resource):  # type: ignore
    """ shows a list of all games, and lets you POST to add new games """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ lister """

        mylogger.LOGGER.warning("get getting all games only name")

        games_list = games.Game.inventory()
        data = {str(g.identifier): g.name for g in games_list}

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ creater """

        args = GAME_PARSER.parse_args()
        name = args['name']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("C of CRUD - post - creating new game %s", name)

        game = games.Game.find_by_name(name)
        if game is not None:
            flask_restful.abort(404, msg=f"Game {name} already exists")

        if pseudo == '':
            flask_restful.abort(404, msg="Need a pseudo to create game")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify_user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player_identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # create game here
        identifier = games.Game.free_identifier()
        game = games.Game(identifier, '', '', '', False, False, False, False, False, '', 0, False, 0, False, 0, False, False, False, False, 0, 0, 0, 0, 0, 0, 0, 0)
        _ = game.load_json(args)
        game.update_database()

        # make position for game
        game.create_position()

        # allocate game master to game
        game.put_role(user_id, 0)

        data = {'name': name, 'msg': 'Ok game created'}
        return data, 201


@API.resource('/allocations')
class AllocationListRessource(flask_restful.Resource):  # type: ignore
    """ shows a list of all allocations, and lets you POST to add new allocations """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ creater """

        args = ALLOCATION_PARSER.parse_args()
        game_id = args['game_id']
        player_id = args['player_id']
        role_id = args['role_id']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("C of CRUD - post - creating new allocation %s/%s/%s", game_id, player_id, role_id)

        if pseudo == '':
            flask_restful.abort(404, msg="Need a pseudo to join/put in game")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify_user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player_identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check user has right to add allocation

        # who is game master ?
        game = games.Game.find_by_identifier(game_id)
        assert game is not None
        game_master_id = game.get_role(0)

        if user_id not in [game_master_id, player_id]:
            flask_restful.abort(403, msg="You do not seem to be either the game master of the game or the concerned player")

        allocation = allocations.Allocation(game_id, player_id, role_id)
        allocation.update_database()

        data = {'msg': 'Ok allocation updated or created'}
        return data, 201

    def delete(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ deleter """

        args = ALLOCATION_PARSER.parse_args()
        game_id = args['game_id']
        player_id = args['player_id']
        role_id = args['role_id']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("D of CRUD - delete - deleting allocation %s/%s", game_id, player_id)

        if pseudo == '':
            flask_restful.abort(404, msg="Need a pseudo to quit/remove from game")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify_user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player_identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check user has right to delete allocation

        # who is game master ?
        game = games.Game.find_by_identifier(game_id)
        assert game is not None
        game_master_id = game.get_role(0)

        if user_id not in [game_master_id, player_id]:
            flask_restful.abort(403, msg="You do not seem to be either the game master of the game or the concerned player")

        allocation = allocations.Allocation(game_id, player_id, role_id)
        allocation.delete_database()

        data = {'msg': 'Ok allocation deleted if present'}
        return data, 200


@API.resource('/allocations_games/<game_id>')
class AllocationGameRessource(flask_restful.Resource):  # type: ignore
    """ shows a list of all allocations, and lets you POST to add new allocations """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ lister """

        mylogger.LOGGER.warning("get getting allocations for game %s", game_id)

        allocations_list = allocations.Allocation.list_by_game_id(game_id)

        data = {str(a[1]): a[2] for a in allocations_list}

        return data, 200


@API.resource('/allocations_players/<player_id>')
class AllocationPlayerRessource(flask_restful.Resource):  # type: ignore
    """ shows a list of all allocations, and lets you POST to add new allocations """

    def get(self, player_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ lister """

        mylogger.LOGGER.warning("get getting allocations for player %s", player_id)

        allocations_list = allocations.Allocation.list_by_player_id(player_id)

        data = {str(a[0]): a[2] for a in allocations_list}

        return data, 200


@API.resource('/game_positions/<game_id>')
class GamePositionRessource(flask_restful.Resource):  # type: ignore
    """ shows a list of all allocations, and lets you POST to add new game position """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ called to rectify position """

        args = RECTIFICATION_PARSER.parse_args()
        pseudo = args['pseudo']
        ownerships_submitted = args['center_ownerships']
        units_submitted = args['units']
        forbiddens_submitted = args['forbiddens']

        the_ownerships = json.loads(ownerships_submitted)
        the_units = json.loads(units_submitted)
        the_forbiddens = json.loads(forbiddens_submitted)

        mylogger.LOGGER.info("U of CRUD - update - rectifying position %s", game_id)

        if pseudo == '':
            flask_restful.abort(404, msg="Need a pseudo to rectify position in game")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify_user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player_identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check user has right to submit orders

        # who is player for role ?
        game = games.Game.find_by_identifier(game_id)
        assert game is not None
        game_master_id = game.get_role(0)

        # must be game master
        if user_id != game_master_id:
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # store position

        # purge previous ownerships
        for (_, center_num, role_num) in ownerships.Ownership.list_by_game_id(int(game_id)):
            ownership = ownerships.Ownership(int(game_id), center_num, role_num)
            ownership.delete_database()

        # purge previous units
        for (_, type_num, role_num, zone_num, region_dislodged_from_num, fake) in units.Unit.list_by_game_id(int(game_id)):
            unit = units.Unit(int(game_id), type_num, role_num, zone_num, region_dislodged_from_num, fake)
            unit.delete_database()

        # purge previous forbiddens
        for (_, center_num) in forbiddens.Forbidden.list_by_game_id(int(game_id)):
            forbidden = forbiddens.Forbidden(int(game_id), center_num)
            forbidden.delete_database()

        # insert new ownerships
        for the_ownership in the_ownerships:
            center_num = the_ownership['center_num']
            role = the_ownership['role']
            ownership = ownerships.Ownership(int(game_id), center_num, role)
            ownership.update_database()

        # insert new units
        for the_unit in the_units:
            type_num = the_unit['type_unit']
            zone_num = the_unit['zone']
            role_num = the_unit['role']
            region_dislodged_from_num = the_unit['dislodged_origin'] if 'dislodged_origin' in the_unit else 0
            fake = the_unit['fake'] if 'fake' in the_unit else 0
            unit = units.Unit(int(game_id), type_num, zone_num, role_num, region_dislodged_from_num, fake)
            unit.update_database()

        # insert new forbiddens
        for the_forbidden in the_forbiddens:
            region_num = the_forbidden['region_num']
            forbidden = forbiddens.Forbidden(int(game_id), region_num)
            forbidden.update_database()

        data = {'msg': 'Ok position rectified'}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ lister """

        mylogger.LOGGER.warning("get getting position for game %s", game_id)

        # get ownerships
        ownership_dict = dict()
        game_ownerships = ownerships.Ownership.list_by_game_id(game_id)
        for _, center_num, role_num in game_ownerships:
            ownership_dict[str(center_num)] = role_num

        # get units
        unit_dict = collections.defaultdict(list)
        dislodged_unit_dict = collections.defaultdict(list)
        game_units = units.Unit.list_by_game_id(game_id)
        for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
            if fake:
                pass  # this is confidential
            elif region_dislodged_from_num:
                dislodged_unit_dict[str(role_num)].append([type_num, zone_num, region_dislodged_from_num])
            else:
                unit_dict[str(role_num)].append([type_num, zone_num])

        # get forbiddens
        forbidden_list = list()
        game_forbiddens = forbiddens.Forbidden.list_by_game_id(game_id)
        for _, region_num in game_forbiddens:
            forbidden_list.append(region_num)

        data = {
            'ownerships': ownership_dict,
            'dislodged_ones': dislodged_unit_dict,
            'units': unit_dict,
            'forbiddens': forbidden_list,
        }
        return data, 200


@API.resource('/game_reports/<game_id>')
class GameReportRessource(flask_restful.Resource):  # type: ignore
    """ get a game report """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ called to retrieve orders """

        mylogger.LOGGER.info("R of CRUD - get - getting game report  %s", game_id)

        report = reports.Report.find_by_identifier(game_id)
        assert report is not None

        content = report.content
        data = {'content': content}

        return data, 200


@API.resource('/game_orders/<game_id>')
class GameOrderRessource(flask_restful.Resource):  # type: ignore
    """ shows a list of all allocations, and lets you POST to add new game orders """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ called to submit orders """

        args = SUBMISSION_PARSER.parse_args()
        role_id = args['role_id']
        pseudo = args['pseudo']
        names = args['names']
        orders_submitted = args['orders']

        mylogger.LOGGER.info("C of CRUD - post - creating new orders %s/%s", game_id, role_id)

        if pseudo == '':
            flask_restful.abort(404, msg="Need a pseudo to submit orders in game")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify_user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player_identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check user has right to submit orders

        # who is player for role ?
        game = games.Game.find_by_identifier(game_id)
        assert game is not None
        game_master_id = game.get_role(0)
        player_id = game.get_role(role_id)

        # can be player of game master
        if user_id not in [game_master_id, player_id]:
            flask_restful.abort(403, msg="You do not seem to be either the game master of the game or the player who is in charge")

        # put in database fake units - units for build orders
        # we cannot remove all fake units since at this point we do not know if build will be successful
        the_orders = json.loads(orders_submitted)
        for the_order in the_orders:
            if the_order['order_type'] == 8:
                type_num = the_order['active_unit']['type_unit']
                role_num = the_order['active_unit']['role']
                zone_num = the_order['active_unit']['zone']
                fake_unit = units.Unit(int(game_id), type_num, zone_num, role_num, 0, True)
                # remove if present already
                fake_unit.delete_database()
                # insert
                fake_unit.update_database()

        # now checking validity of orders

        # evaluate variant
        variant_name = game.variant
        variant_dict = variants.Variant.get_by_name(variant_name)
        if variant_dict is None:
            flask_restful.abort(404, msg=f"Variant {variant_name} doesn't exist")
        variant_dict_json = json.dumps(variant_dict)

        # evaluate situation

        # situation: get ownerships
        ownership_dict = dict()
        game_ownerships = ownerships.Ownership.list_by_game_id(game_id)
        for _, center_num, role_num in game_ownerships:
            ownership_dict[str(center_num)] = role_num

        # situation: get units
        game_units = units.Unit.list_by_game_id(game_id)
        unit_dict = collections.defaultdict(list)
        fake_unit_dict = collections.defaultdict(list)
        dislodged_unit_dict = collections.defaultdict(list)
        for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
            if fake:
                fake_unit_dict[str(role_num)].append([type_num, zone_num])
            elif region_dislodged_from_num:
                dislodged_unit_dict[str(role_num)].append([type_num, zone_num, region_dislodged_from_num])
            else:
                unit_dict[str(role_num)].append([type_num, zone_num])

        # situation: get forbiddens
        forbidden_list = list()
        game_forbiddens = forbiddens.Forbidden.list_by_game_id(game_id)
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

        orders_list = list()
        the_orders = json.loads(orders_submitted)
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
            'role' : role_id,
        }

        # post to solver
        host = lowdata.SERVER_CONFIG['SOLVER']['HOST']
        port = lowdata.SERVER_CONFIG['SOLVER']['PORT']
        url = f"{host}:{port}/solve"
        req_result = SESSION.post(url, data=json_dict)
        submission_report = "\n".join([req_result.json()['stderr'], req_result.json()['stdout']])

        # adjudication failed
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to submit orders {message} : {submission_report}")

        # ok so orders are accepted

        # store orders

        # purge previous

        # get list
        if int(role_id) != 0:
            previous_orders =  orders.Order.list_by_game_id_role_num(int(game_id), role_id)
        else:
            previous_orders =  orders.Order.list_by_game_id(int(game_id))

        # purge
        for (_, role_num, _, zone_num, _, _) in previous_orders:
            order = orders.Order(int(game_id), role_num, 0, zone_num, 0, 0)
            order.delete_database()
            print(order)

        # insert new ones
        for the_order in the_orders:
            order = orders.Order(int(game_id), 0, 0, 0, 0, 0)
            order.load_json(the_order)
            order.update_database()

            # special case : build : create a fake unit
            # this was done before submitting
            # we tolerate that some extra fake unit may persist from previous submission

        data = {'msg': f"Ok orders submitted {submission_report}"}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ called to retrieve orders """

        args = RETRIEVE_PARSER.parse_args()
        role_id = args['role_id']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("R of CRUD - get - getting back orders %s/%s", game_id, role_id)

        if pseudo == '':
            flask_restful.abort(404, msg="Need a pseudo to retrieve orders in game")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify_user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player_identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")
        user_id = req_result.json()

        # check user has right to get orders

        # who is player for role ?
        game = games.Game.find_by_identifier(game_id)
        assert game is not None
        game_master_id = game.get_role(0)
        player_id = game.get_role(role_id)

        # can be player of game master
        if user_id not in [game_master_id, player_id]:
            flask_restful.abort(403, msg="You do not seem to be either the game master of the game or the player who is in charge")

        # get orders
        if role_id:
            orders_list = orders.Order.list_by_game_id_role_num(game_id, role_id)
        else:
            orders_list = orders.Order.list_by_game_id(game_id)

        # get fake units
        if role_id:
            units_list = units.Unit.list_by_game_id_role_num(game_id, role_id)
        else:
            units_list = units.Unit.list_by_game_id(game_id)
        fake_units_list = [u for u in units_list if u[5]]

        data = {
            'orders': orders_list,
            'fake_units': fake_units_list,
        }
        return data, 200


@API.resource('/game_adjudications/<game_id>')
class GameAdjudicationRessource(flask_restful.Resource):  # type: ignore
    """ shows a list of all allocations, and lets you POST to add new game orders """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """ creater """

        args = ADJUDICATION_PARSER.parse_args()
        pseudo = args['pseudo']
        names = args['names']

        mylogger.LOGGER.info("C of CRUD - post - adjudicating %s", game_id)

        if pseudo == '':
            flask_restful.abort(404, msg="Need a pseudo to adjudicate in game")

        # check authentication from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify_user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")

        # get player identifier
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player_identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to get id from pseudo {message}")

        user_id = req_result.json()

        # check user has right to adjudicate

        # who is game master ?
        game = games.Game.find_by_identifier(game_id)
        assert game is not None
        game_master_id = game.get_role(0)

        # must be game master
        if user_id != game_master_id:
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # evaluate variant
        variant_name = game.variant
        variant_dict = variants.Variant.get_by_name(variant_name)
        if variant_dict is None:
            flask_restful.abort(404, msg=f"Variant {variant_name} doesn't exist")

        variant_dict_json = json.dumps(variant_dict)

        # evaluate situation

        # situation: get ownerships
        ownership_dict = dict()
        game_ownerships = ownerships.Ownership.list_by_game_id(game_id)
        for _, center_num, role_num in game_ownerships:
            ownership_dict[str(center_num)] = role_num

        # situation: get units
        game_units = units.Unit.list_by_game_id(game_id)
        unit_dict = collections.defaultdict(list)
        fake_unit_dict = collections.defaultdict(list)
        dislodged_unit_dict = collections.defaultdict(list)
        for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
            if fake:
                fake_unit_dict[str(role_num)].append([type_num, zone_num])
            elif region_dislodged_from_num:
                dislodged_unit_dict[str(role_num)].append([type_num, zone_num, region_dislodged_from_num])
            else:
                unit_dict[str(role_num)].append([type_num, zone_num])

        # situation: get forbiddens
        forbidden_list = list()
        game_forbiddens = forbiddens.Forbidden.list_by_game_id(game_id)
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

        # evaluate orders
        orders_list = list()
        game_orders = orders.Order.list_by_game_id(game_id)
        for _, role_num, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num in game_orders:
            orders_list.append([role_num, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num])
        orders_list_json = json.dumps(orders_list)

        json_dict = {
            'variant': variant_dict_json,
            'advancement': game.current_advancement,
            'situation': situation_dict_json,
            'orders': orders_list_json,
            'names': names,
        }

        # post to solver
        host = lowdata.SERVER_CONFIG['SOLVER']['HOST']
        port = lowdata.SERVER_CONFIG['SOLVER']['PORT']
        url = f"{host}:{port}/solve"
        req_result = SESSION.post(url, data=json_dict)
        adjudication_report = "\n".join([req_result.json()['stderr'], req_result.json()['stdout']])

        # adjudication failed
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to adjudicate {message} : {adjudication_report}")


        # extract new position
        situation_result = req_result.json()['situation_result']
        the_ownerships = situation_result['ownerships']
        the_units = situation_result['units']
        the_dislodged_units = situation_result['dislodged_ones']
        the_forbiddens = situation_result['forbiddens']

        # store new position in database

        # purge

        # purge previous ownerships
        for (_, center_num, role_num) in ownerships.Ownership.list_by_game_id(int(game_id)):
            ownership = ownerships.Ownership(int(game_id), center_num, role_num)
            ownership.delete_database()

        # purge previous units
        for (_, type_num, role_num, zone_num, region_dislodged_from_num, fake) in units.Unit.list_by_game_id(int(game_id)):
            unit = units.Unit(int(game_id), type_num, role_num, zone_num, region_dislodged_from_num, fake)
            unit.delete_database()

        # purge previous forbiddens
        for (_, center_num) in forbiddens.Forbidden.list_by_game_id(int(game_id)):
            forbidden = forbiddens.Forbidden(int(game_id), center_num)
            forbidden.delete_database()

        # insert

        # insert new ownerships
        for center_num, role in the_ownerships.items():
            ownership = ownerships.Ownership(int(game_id), int(center_num), role)
            ownership.update_database()

        # insert new units
        for role_num, the_unit_role in the_units.items():
            for type_num, zone_num in the_unit_role:
                unit = units.Unit(int(game_id), type_num, zone_num, int(role_num), 0, 0)
                unit.update_database()

        # insert new dislodged units
        for role_num, the_unit_role in the_dislodged_units.items():
            for type_num, zone_num, region_dislodged_from_num in the_unit_role:
                unit = units.Unit(int(game_id), type_num, zone_num, int(role_num), region_dislodged_from_num, 0)
                unit.update_database()

        # insert new forbiddens
        for region_num in the_forbiddens:
            forbidden = forbiddens.Forbidden(int(game_id), region_num)
            forbidden.update_database()

        # remove orders
        for (_, role_id, _, zone_num, _, _) in orders.Order.list_by_game_id(game_id):
            order = orders.Order(int(game_id), role_id, 0, zone_num, 0, 0)
            order.delete_database()

        # extract new report
        orders_result = req_result.json()['orders_result']
        orders_result_simplified = orders_result

        # get current date
        date_now = datetime.datetime.now()
        date_desc = date_now.strftime('%Y-%m-%d %H:%M:%S')

        content = f"{date_desc}:\n\n{orders_result_simplified}"
        report = reports.Report(int(game_id), content)
        report.update_database()

        # update season
        game.advance()
        game.update_database()

        data = {'msg': f"Ok adjudication performed and game updated : {adjudication_report}"}
        return data, 201


def main() -> None:
    """ main """

    mylogger.start_logger(__name__)
    lowdata.load_servers_config()
    mailer.load_mail_config(APP)

    # emergency
    if not database.db_present():
        mylogger.LOGGER.info("Emergency populate procedure")
        populate.populate()

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    APP.run(debug=True, port=port)


if __name__ == '__main__':
    main()
