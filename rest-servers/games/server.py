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

import waitress
import flask
import flask_cors  # type: ignore
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore
import requests

import mylogger
import populate
import allocations
import ownerships
import units
import orders
import forbiddens
import transitions
import reports
import games
import messages
import declarations
import variants
import database
import visits
import lowdata

# a little welcome message to new games
WELCOME_TO_GAME = "Bienvenue sur cette partie gérée par le serveur de l'AFJD"

DIPLOMACY_SEASON_CYCLE = [1, 2, 1, 2, 3]

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
GAME_PARSER.add_argument('silent', type=int, required=False)
GAME_PARSER.add_argument('cumulate', type=int, required=False)
GAME_PARSER.add_argument('fast', type=int, required=False)
GAME_PARSER.add_argument('deadline', type=int, required=False)
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

ALLOCATION_PARSER = flask_restful.reqparse.RequestParser()
ALLOCATION_PARSER.add_argument('game_id', type=int, required=True)
ALLOCATION_PARSER.add_argument('player_pseudo', type=str, required=True)
ALLOCATION_PARSER.add_argument('delete', type=int, required=True)
ALLOCATION_PARSER.add_argument('pseudo', type=str, required=False)

ROLE_ALLOCATION_PARSER = flask_restful.reqparse.RequestParser()
ROLE_ALLOCATION_PARSER.add_argument('game_id', type=int, required=True)
ROLE_ALLOCATION_PARSER.add_argument('player_pseudo', type=str, required=True)
ROLE_ALLOCATION_PARSER.add_argument('role_id', type=int, required=True)
ROLE_ALLOCATION_PARSER.add_argument('delete', type=int, required=True)
ROLE_ALLOCATION_PARSER.add_argument('pseudo', type=str, required=False)

SUBMISSION_PARSER = flask_restful.reqparse.RequestParser()
SUBMISSION_PARSER.add_argument('role_id', type=int, required=True)
SUBMISSION_PARSER.add_argument('orders', type=str, required=True)
SUBMISSION_PARSER.add_argument('names', type=str, required=True)
SUBMISSION_PARSER.add_argument('pseudo', type=str, required=False)

ADJUDICATION_PARSER = flask_restful.reqparse.RequestParser()
ADJUDICATION_PARSER.add_argument('names', type=str, required=True)
ADJUDICATION_PARSER.add_argument('pseudo', type=str, required=False)

SIMULATION_PARSER = flask_restful.reqparse.RequestParser()
SIMULATION_PARSER.add_argument('variant_name', type=str, required=True)
SIMULATION_PARSER.add_argument('orders', type=str, required=True)
SIMULATION_PARSER.add_argument('center_ownerships', type=str, required=True)
SIMULATION_PARSER.add_argument('units', type=str, required=True)
SIMULATION_PARSER.add_argument('names', type=str, required=True)

RECTIFICATION_PARSER = flask_restful.reqparse.RequestParser()
RECTIFICATION_PARSER.add_argument('center_ownerships', type=str, required=True)
RECTIFICATION_PARSER.add_argument('units', type=str, required=True)
RECTIFICATION_PARSER.add_argument('forbiddens', type=str, required=True)
RECTIFICATION_PARSER.add_argument('pseudo', type=str, required=False)

DECLARATION_PARSER = flask_restful.reqparse.RequestParser()
DECLARATION_PARSER.add_argument('role_id', type=int, required=True)
DECLARATION_PARSER.add_argument('content', type=str, required=True)
DECLARATION_PARSER.add_argument('pseudo', type=str, required=False)

MESSAGE_PARSER = flask_restful.reqparse.RequestParser()
MESSAGE_PARSER.add_argument('role_id', type=int, required=True)
MESSAGE_PARSER.add_argument('dest_role_id', type=int, required=True)
MESSAGE_PARSER.add_argument('content', type=str, required=True)
MESSAGE_PARSER.add_argument('pseudo', type=str, required=False)

VISIT_PARSER = flask_restful.reqparse.RequestParser()
VISIT_PARSER.add_argument('role_id', type=int, required=True)
VISIT_PARSER.add_argument('pseudo', type=str, required=False)


@API.resource('/variants/<name>')
class VariantIdentifierRessource(flask_restful.Resource):  # type: ignore
    """ VariantIdentifierRessource """

    def get(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
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

    def get(self, name: str) -> typing.Tuple[int, int]:  # pylint: disable=no-self-use
        """
        From name get identifier
        EXPOSED
        Note : currently not used
        """

        mylogger.LOGGER.info("/game-identifiers/<name> - GET - retrieving identifier of game name=%s", name)

        # find data
        game = games.Game.find_by_name(name)
        if game is None:
            flask_restful.abort(404, msg=f"Game {name} doesn't exist")

        assert game is not None
        return game.identifier, 200


@API.resource('/games/<name>')
class GameRessource(flask_restful.Resource):  # type: ignore
    """ GameRessource """

    def get(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Get all information about game
        EXPOSED
        """

        mylogger.LOGGER.info("/games/<name> - GET- retrieving data of game name=%s", name)

        # find data
        game = games.Game.find_by_name(name)
        if game is None:
            flask_restful.abort(404, msg=f"Game {name} doesn't exist")

        assert game is not None
        data = game.save_json()

        return data, 200

    def put(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Updates information about a game
        EXPOSED
        """

        mylogger.LOGGER.info("/games/<name> - PUT - updating game name=%s", name)

        args = GAME_PARSER.parse_args(strict=True)
        pseudo = args['pseudo']

        game = games.Game.find_by_name(name)
        if game is None:
            flask_restful.abort(404, msg=f"Game {name} does not exist")

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to modify game")

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
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

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

        # check this is game_master
        assert game is not None
        if game.get_role(0) != user_id:
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # pay more attention to deadline
        entered_deadline = args['deadline']

        if entered_deadline is not None:

            # check it
            deadline_date = datetime.datetime.fromtimestamp(entered_deadline, datetime.timezone.utc)

            # cannot be in past
            if deadline_date < datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=1):
                date_desc = deadline_date.strftime('%Y-%m-%d %H:%M:%S')
                flask_restful.abort(400, msg=f"You cannot set a deadline in the past :'{date_desc}' (GMT)")

        # keep a note of game state before
        current_state_before = game.current_state

        assert game is not None
        changed = game.load_json(args)
        if not changed:
            data = {'name': name, 'msg': 'Ok but no change !'}
            return data, 200

        # special : game changed state
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
                if nb_players_allocated > number_players_expected:
                    data = {'name': name, 'msg': 'Too many players !'}
                    return data, 400

                game.start()

                # notify players

                subject = f"La partie {game.name} a démarré !"
                game_id = game.identifier
                allocations_list = allocations.Allocation.list_by_game_id(game_id)
                addressees = list()
                for _, player_id, __ in allocations_list:
                    addressees.append(player_id)
                body = "Vous pouvez commencer à jouer dans cette partie !"

                json_dict = {
                    'pseudo': pseudo,
                    'addressees': " ".join([str(a) for a in addressees]),
                    'subject': subject,
                    'body': body,
                }

                host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
                port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
                url = f"{host}:{port}/mail-players"
                # for a rest API headers are presented differently
                req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
                if req_result.status_code != 200:
                    print(f"ERROR from server  : {req_result.text}")
                    message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                    flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

            if current_state_before == 1 and game.current_state == 2:

                # no check ?
                game.terminate()

        game.update_database()

        data = {'name': name, 'msg': 'Ok updated'}
        return data, 200

    def delete(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Deletes a game
        EXPOSED
        """

        mylogger.LOGGER.info("/games/<name> - DELETE - deleting game name=%s", name)

        # delete game from here
        game = games.Game.find_by_name(name)
        if game is None:
            flask_restful.abort(404, msg=f"Game {name} doesn't exist")

        assert game is not None
        if game.current_state != 2:
            flask_restful.abort(400, msg=f"Game {name} is not terminated")

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

        # we do not check pseudo, we read it from token
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

        # check this is game_master
        assert game is not None
        if game.get_role(0) != user_id:
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # delete allocations
        game.delete_allocations()

        # and position
        game.delete_position()

        # and report
        game_id = game.identifier
        report = reports.Report.find_by_identifier(game_id)
        assert report is not None
        report.delete_database()

        # finally delete game
        assert game is not None
        game.delete_database()

        data = {'name': name, 'msg': 'Ok removed'}
        return data, 200


@API.resource('/games')
class GameListRessource(flask_restful.Resource):  # type: ignore
    """ GameListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Get list of all games (dictionary identifier -> name)
        EXPOSED
        """

        mylogger.LOGGER.info("/games - GET - get getting all games names")

        games_list = games.Game.inventory()
        data = {str(g.identifier): {'name': g.name, 'variant': g.variant, 'deadline': g.deadline, 'current_advancement': g.current_advancement, 'current_state': g.current_state} for g in games_list}

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Creates a new game
        EXPOSED
        """

        mylogger.LOGGER.info("/games - POST - creating new game")

        args = GAME_PARSER.parse_args(strict=True)
        name = args['name']

        mylogger.LOGGER.info("game name=%s", name)

        pseudo = args['pseudo']

        game = games.Game.find_by_name(name)
        if game is not None:
            flask_restful.abort(400, msg=f"Game {name} already exists")

        if not name.isidentifier():
            flask_restful.abort(400, msg=f"Name '{name}' is not a valid name")

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to create game")

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
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

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

        # create game here
        identifier = games.Game.free_identifier()
        game = games.Game(identifier, '', '', '', False, False, False, False, False, 0, 0, False, 0, False, 0, False, False, False, False, 0, 0, 0, 0, 0, 0, 0, 0)
        _ = game.load_json(args)
        game.update_database()

        # make position for game
        game.create_position()

        # add a little report
        game_id = game.identifier
        time_stamp = int(time.time())
        report = reports.Report(game_id, time_stamp, WELCOME_TO_GAME)
        report.update_database()

        # allocate game master to game
        game.put_role(user_id, 0)

        data = {'name': name, 'msg': 'Ok game created'}
        return data, 201


@API.resource('/allocations')
class AllocationListRessource(flask_restful.Resource):  # type: ignore
    """ AllocationListRessource """

    # an allocation is a game-role-pseudo relation where role is -1

    def get(self) -> typing.Tuple[typing.List[typing.Dict[str, typing.Any]], int]:  # pylint: disable=no-self-use
        """
        Get list of all allocations only game master (dictionary identifier -> name)
        EXPOSED
        """

        mylogger.LOGGER.info("/allocations - GET - get getting all game master allocations")

        allocations_list = allocations.Allocation.inventory()
        data = [{'game': a[0], 'master': a[1]} for a in allocations_list if a[2] == 0]

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Creates or deletes an allocation (a relation player-role-game)
        EXPOSED
        """

        mylogger.LOGGER.info("/allocations - POST - creating/deleting new allocation")

        args = ALLOCATION_PARSER.parse_args(strict=True)
        game_id = args['game_id']
        player_pseudo = args['player_pseudo']
        delete = args['delete']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("game_id=%s player_pseudo=%s delete=%s", game_id, player_pseudo, delete)

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to join/put or quit/remolve in game")

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
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

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

        # find the game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is game master ?
        assert game is not None
        game_master_id = game.get_role(0)

        if user_id not in [game_master_id, player_id]:
            flask_restful.abort(403, msg="You do not seem to be either the game master of the game or the concerned player")

        # abort if has a role
        raw_allocations = allocations.Allocation.list_by_game_id(game_id)
        if player_id in [r[1] for r in raw_allocations if r[2] != -1]:
            flask_restful.abort(400, msg="You cannot remove or put in the game someone already assigned a role")

        dangling_role_id = -1

        if not delete:
            allocation = allocations.Allocation(game_id, player_id, dangling_role_id)
            allocation.update_database()
            data = {'msg': 'Ok allocation updated or created'}
            return data, 201

        allocation = allocations.Allocation(game_id, player_id, dangling_role_id)
        allocation.delete_database()
        data = {'msg': 'Ok allocation deleted if present'}
        return data, 200


@API.resource('/role-allocations')
class RoleAllocationListRessource(flask_restful.Resource):  # type: ignore
    """ AllocationListRessource """

    # a role-allocation is a game-role-pseudo relation where role is <> -1

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Creates or deletes an role allocation (a relation player-role-game)
        creates : There should be a single -1 role allacation
        deletes : That will creare a -1 role allacation
        EXPOSED
        """

        mylogger.LOGGER.info("/role-allocations - POST - creating/deleting new role-allocation")

        args = ROLE_ALLOCATION_PARSER.parse_args(strict=True)
        game_id = args['game_id']
        player_pseudo = args['player_pseudo']
        role_id = args['role_id']
        delete = args['delete']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("game_id=%s role_id=%s player_pseudo=%s delete=%s", role_id, game_id, player_pseudo, delete)

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to move role in game")

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
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

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

        # find the game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is game master ?
        assert game is not None
        game_master_id = game.get_role(0)

        if user_id != game_master_id:
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # game master of game can neither be added (changed) not removed

        if not delete:
            if game_master_id == player_id:
                flask_restful.abort(400, msg="You cannot put the game master as a player in the game")
        else:
            if game_master_id == player_id:
                flask_restful.abort(400, msg="You cannot remove the game master from the game")

        if not delete:
            # delete dangling
            dangling_role_id = -1
            allocation = allocations.Allocation(game_id, player_id, dangling_role_id)
            allocation.delete_database()
            # put role
            allocation = allocations.Allocation(game_id, player_id, role_id)
            allocation.update_database()
            # report
            data = {'msg': 'Ok role-allocation updated or created'}
            return data, 201

        # delete role
        allocation = allocations.Allocation(game_id, player_id, role_id)
        allocation.delete_database()
        # put dangling
        dangling_role_id = -1
        allocation = allocations.Allocation(game_id, player_id, dangling_role_id)
        allocation.update_database()
        # report
        data = {'msg': 'Ok role-allocation deleted if present'}
        return data, 200


@API.resource('/game-allocations/<game_id>')
class AllocationGameRessource(flask_restful.Resource):  # type: ignore
    """ AllocationGameRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Gets all allocations for the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-allocations/<game_id> - GET - get getting allocations for game id=%s", game_id)

        allocations_list = allocations.Allocation.list_by_game_id(game_id)

        data = {str(a[1]): a[2] for a in allocations_list}

        return data, 200


@API.resource('/player-allocations/<player_id>')
class AllocationPlayerRessource(flask_restful.Resource):  # type: ignore
    """ AllocationPlayerRessource """

    def get(self, player_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Gets all allocations for the player
        Note : here because data is in this database
        EXPOSED
        """

        mylogger.LOGGER.info("/player-allocations/<player_id> - GET - get getting allocations for player player_id=%s", player_id)

        allocations_list = allocations.Allocation.list_by_player_id(player_id)

        data = {str(a[0]): a[2] for a in allocations_list}

        return data, 200


@API.resource('/game-positions/<game_id>')
class GamePositionRessource(flask_restful.Resource):  # type: ignore
    """ GamePositionRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Changes position of a game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-positions/<game_id> - POST - rectifying position game id=%s", game_id)

        args = RECTIFICATION_PARSER.parse_args(strict=True)
        pseudo = args['pseudo']
        ownerships_submitted = args['center_ownerships']
        units_submitted = args['units']
        forbiddens_submitted = args['forbiddens']

        try:
            the_ownerships = json.loads(ownerships_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert ownerships from json to text ?")

        try:
            the_units = json.loads(units_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert units from json to text ?")

        try:
            the_forbiddens = json.loads(forbiddens_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert forbiddens from json to text ?")

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to rectify position in game")

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
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

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

        # check user has right to change position - must be game master

        # find the game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is player for role ?
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
        """
        Gets position of the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-positions/<game_id> - GET - getting position for game id=%s", game_id)

        # get ownerships
        ownership_dict = dict()
        game_ownerships = ownerships.Ownership.list_by_game_id(game_id)
        for _, center_num, role_num in game_ownerships:
            ownership_dict[str(center_num)] = role_num

        # get units
        unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
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


@API.resource('/game-reports/<game_id>')
class GameReportRessource(flask_restful.Resource):  # type: ignore
    """ GameReportRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Gets the report of adjudication for the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-reports/<game_id> - GET - getting report game id=%s", game_id)

        # check the game exists
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # find the report
        report = reports.Report.find_by_identifier(game_id)
        if report is None:
            flask_restful.abort(404, msg=f"Report happens to be missing for {game_id}")

        # extract report data
        assert report is not None
        content = report.content
        data = {'content': content}

        return data, 200


@API.resource('/game-transitions/<game_id>/<advancement>')
class GameTransitionRessource(flask_restful.Resource):  # type: ignore
    """ GameTransitionRessource """

    def get(self, game_id: int, advancement: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Gets the full report  (transition : postions + orders + report) of adjudication for the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-transitions/<game_id>/<advancement> - GET - getting transition game id=%s advancement=%s", game_id, advancement)

        # check the game exists
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # find the transition
        transition = transitions.Transition.find_by_identifier_advancement(game_id, advancement)
        if transition is None:
            flask_restful.abort(404, msg=f"Transition happens to be missing for {game_id} / {advancement}")

        # extract transition data
        assert transition is not None
        situation = json.loads(transition.situation_json)
        orders = json.loads(transition.orders_json)
        report_txt = transition.report_txt
        data = {'situation': situation, 'orders': orders, 'report_txt': report_txt}

        return data, 200


@API.resource('/game-orders/<game_id>')
class GameOrderRessource(flask_restful.Resource):  # type: ignore
    """ GameOrderRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Submit orders
        EXPOSED
        """

        mylogger.LOGGER.info("/game-orders/<game_id> - POST - submitting orders game id=%s", game_id)

        args = SUBMISSION_PARSER.parse_args(strict=True)
        role_id = args['role_id']

        mylogger.LOGGER.info("role_id=%s", role_id)

        pseudo = args['pseudo']
        names = args['names']
        orders_submitted = args['orders']

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to submit orders in game")

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
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

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

        # check user has right to submit orders - must be player

        # find the game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is player for role ?
        assert game is not None
        player_id = game.get_role(role_id)

        # must be player or game master
        if user_id != player_id:
            flask_restful.abort(403, msg="You do not seem to be the player who corresponds to this role")

        # put in database fake units - units for build orders

        try:
            the_orders = json.loads(orders_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert orders from json to text ?")

        # first we copy the fake units of the role already present and remove them
        game_units = units.Unit.list_by_game_id(game_id)
        prev_fake_unit_list: typing.List[typing.List[int]] = list()
        for _, type_num, zone_num, role_num, _, fake in game_units:
            if not fake:
                continue
            if not (role_id == 0 or role_num == int(role_id)):
                continue
            prev_fake_unit_list.append([type_num, zone_num, role_num])
            fake_unit = units.Unit(int(game_id), type_num, zone_num, role_num, 0, True)
            fake_unit.delete_database()

        # then we put the incoming ones in the database
        inserted_fake_unit_list: typing.List[typing.List[int]] = list()
        for the_order in the_orders:
            if the_order['order_type'] == 8:
                type_num = the_order['active_unit']['type_unit']
                role_num = the_order['active_unit']['role']
                zone_num = the_order['active_unit']['zone']
                inserted_fake_unit_list.append([type_num, zone_num, role_num])
                fake_unit = units.Unit(int(game_id), type_num, zone_num, role_num, 0, True)
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
                fake_unit.delete_database()

            # we restore the backed up fake units
            for type_num, zone_num, role_num in prev_fake_unit_list:
                fake_unit = units.Unit(int(game_id), type_num, zone_num, role_num, 0, True)
                # insert
                fake_unit.update_database()

            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Failed to submit orders {message} : {submission_report}")

        # ok so orders are accepted

        # store orders

        # purge previous

        # get list
        if int(role_id) != 0:
            previous_orders = orders.Order.list_by_game_id_role_num(int(game_id), role_id)
        else:
            previous_orders = orders.Order.list_by_game_id(int(game_id))

        # purge
        for (_, role_num, _, zone_num, _, _) in previous_orders:
            order = orders.Order(int(game_id), role_num, 0, zone_num, 0, 0)
            order.delete_database()

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

        # check user has right to get orders - must be player or game master

        # check there is a game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(player_id)
        if role_id is None:
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # get orders
        assert role_id is not None
        if role_id == 0:
            orders_list = orders.Order.list_by_game_id(game_id)
        else:
            orders_list = orders.Order.list_by_game_id_role_num(game_id, role_id)

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


@API.resource('/game-orders-submitted/<game_id>')
class GameOrdersSubmittedRessource(flask_restful.Resource):  # type: ignore
    """ GameOrderRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.List[int], int]:  # pylint: disable=no-self-use
        """
        Gets list of roles which have submitted orders
        EXPOSED
        """

        mylogger.LOGGER.info("/game-orders-submitted/<game_id> - GET - getting which orders submitted game id=%s", game_id)

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

        # check user has right to get orders - must game master

        # check there is a game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(player_id)
        if role_id is None:
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # get orders
        assert role_id is not None
        orders_list = orders.Order.list_by_game_id(game_id)

        roles_list = list(set([o[1] for o in orders_list]))

        # TODO : change if we decide to hide this information

        data = roles_list
        return data, 200


@API.resource('/game-adjudications/<game_id>')
class GameAdjudicationRessource(flask_restful.Resource):  # type: ignore
    """ GameAdjudicationRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Performs adjudication of game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-adjudications/<game_id> - POST - adjudicating game id=%s", game_id)

        args = ADJUDICATION_PARSER.parse_args(strict=True)
        pseudo = args['pseudo']
        names = args['names']

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to adjudicate in game")

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
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

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

        # check user has right to adjudicate - must be game master

        # find the game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is game master ?
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
        orders_from_game = orders.Order.list_by_game_id(game_id)
        for game_num, role_num, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num in orders_from_game:
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

        if 'msg' in req_result.json():
            adjudication_report = req_result.json()['msg']
        else:
            adjudication_report = "\n".join([req_result.json()['stderr'], req_result.json()['stdout']])

        # adjudication failed
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Failed to adjudicate {message} : {adjudication_report}")

        # adjudication successful : backup for transition archive

        # position for transition vv ====

        # get ownerships
        ownership_dict = dict()
        game_ownerships = ownerships.Ownership.list_by_game_id(game_id)
        for _, center_num, role_num in game_ownerships:
            ownership_dict[str(center_num)] = role_num

        # get units
        unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
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

        position_transition_dict = {
            'ownerships': ownership_dict,
            'dislodged_ones': dislodged_unit_dict,
            'units': unit_dict,
            'forbiddens': forbidden_list,
        }

        # position for transition ^^ ====

        # orders for transition vv ====
        orders_transition_list = orders.Order.list_by_game_id(game_id)

        units_transition_list = units.Unit.list_by_game_id(game_id)
        fake_units_transition_list = [u for u in units_transition_list if u[5]]

        orders_transition_dict = {
            'orders': orders_transition_list,
            'fake_units': fake_units_transition_list,
        }

        # orders for transition ^^ ====

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

        # date for database (actually unused)
        time_stamp = int(time.time())

        # make report
        date_now = datetime.datetime.now()
        date_desc = date_now.strftime('%Y-%m-%d %H:%M:%S')
        report_txt = f"{date_desc}:\n{orders_result_simplified}"

        # put report in database
        report = reports.Report(int(game_id), time_stamp, report_txt)
        report.update_database()

        # put transition in database
        # important : need to be same as when getting situation
        position_transition_dict_json = json.dumps(position_transition_dict)
        orders_transition_dict_json = json.dumps(orders_transition_dict)
        transition = transitions.Transition(int(game_id), game.current_advancement, position_transition_dict_json, orders_transition_dict_json, report_txt)
        transition.update_database()

        # update season
        game.advance()
        game.update_database()

        data = {'msg': f"Ok adjudication performed and game updated : {adjudication_report}"}
        return data, 201


@API.resource('/simulation')
class SimulationRessource(flask_restful.Resource):  # type: ignore
    """ SimulationRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Performs a simulation
        EXPOSED
        """

        mylogger.LOGGER.info("/simulation - POST - simulation")

        args = SIMULATION_PARSER.parse_args(strict=True)
        variant_name = args['variant_name']
        names = args['names']
        ownerships_submitted = args['center_ownerships']
        units_submitted = args['units']
        orders_submitted = args['orders']

        # evaluate variant
        variant_dict = variants.Variant.get_by_name(variant_name)
        if variant_dict is None:
            flask_restful.abort(404, msg=f"Variant {variant_name} doesn't exist")

        variant_dict_json = json.dumps(variant_dict)

        # evaluate situation

        try:
            the_ownerships = json.loads(ownerships_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert ownerships from json to text ?")

        try:
            the_units = json.loads(units_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert units from json to text ?")

        # situation: get ownerships
        ownership_dict = dict()
        for the_ownership in the_ownerships:
            center_num = the_ownership['center_num']
            role = the_ownership['role']
            ownership_dict[str(center_num)] = role

        # situation: get units
        unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        for the_unit in the_units:
            type_num = the_unit['type_unit']
            zone_num = the_unit['zone']
            role_num = the_unit['role']
            unit_dict[str(role_num)].append([type_num, zone_num])

        # no fake unit at this point
        fake_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = dict()

        # no dislodged unit at this point
        dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = dict()

        # no forbiddens at this point
        forbidden_list: typing.List[int] = list()

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
        orders_list = list()

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
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(404, msg=f"Failed to adjudicate {message} : {adjudication_report}")

        # extract new report
        orders_result = req_result.json()['orders_result']
        orders_result_simplified = orders_result

        data = {
            'msg': f"Ok adjudication performed : {adjudication_report}",
            'result': f"{orders_result_simplified}"}
        return data, 201


@API.resource('/game-messages/<game_id>')
class GameMessageRessource(flask_restful.Resource):  # type: ignore
    """  GameMessageRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Insert message in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-messages/<game_id> - POST - creating new message game id=%s", game_id)

        args = MESSAGE_PARSER.parse_args(strict=True)
        role_id = args['role_id']
        dest_role_id = args['dest_role_id']

        mylogger.LOGGER.info("role_id=%s dest_role_id=%s", role_id, dest_role_id)

        pseudo = args['pseudo']
        content = args['content']

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to insert message in game")

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
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

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

        # check user has right to post message - must be player of game master

        # find the game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is player for role ?
        assert game is not None
        expected_id = game.get_role(role_id)

        # can be player of game master but must correspond
        if user_id != expected_id:
            if role_id == 0:
                flask_restful.abort(403, msg="You do not seem to be the game master of the game")
            else:
                flask_restful.abort(403, msg="You do not seem to be the player who is in charge")

        # create message here
        identifier = messages.Message.free_identifier()
        time_stamp = int(time.time())
        message = messages.Message(identifier, game_id, time_stamp, role_id, dest_role_id, content)
        message.update_database()

        data = {'msg': f"Ok message inserted : {content}"}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
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

        # check user has right to read message - must be player of game master

        # check there is a game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(player_id)
        if role_id is None:
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # TODO : find a way to pass a limit
        limit = None

        # gather messages
        assert role_id is not None
        messages_list = messages.Message.list_by_game_id(game_id)
        messages_list_json = list()
        num = 1
        for _, _, message in sorted(messages_list, key=lambda t: t[2].time_stamp, reverse=True):

            # must be author or addressee
            if role_id not in [message.author_num, message.addressee_num]:
                continue

            messages_list_json.append(message.export())
            num += 1
            if limit is not None and num == limit:
                break

        data = {'messages_list': messages_list_json}
        return data, 200


@API.resource('/game-declarations/<game_id>')
class GameDeclarationRessource(flask_restful.Resource):  # type: ignore
    """  GameDeclarationRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Insert declaration in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-declarations/<game_id> - POST - creating new declaration game id=%s", game_id)

        args = DECLARATION_PARSER.parse_args(strict=True)
        role_id = args['role_id']

        mylogger.LOGGER.info("role_id=%s", role_id)

        pseudo = args['pseudo']
        content = args['content']

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to insert declaration in game")

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
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

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

        # check user has right to post declatation - must be player of game master

        # find the game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is player for role ?
        assert game is not None
        expected_id = game.get_role(role_id)

        # can be player of game master but must correspond
        if user_id != expected_id:
            if role_id == 0:
                flask_restful.abort(403, msg="You do not seem to be the game master of the game")
            else:
                flask_restful.abort(403, msg="You do not seem to be the player who is in charge")

        # create declaration here
        identifier = declarations.Declaration.free_identifier()
        time_stamp = int(time.time())
        declaration = declarations.Declaration(identifier, game_id, time_stamp, role_id, content)
        declaration.update_database()

        data = {'msg': f"Ok declaration inserted : {content}"}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
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

        # check user has right to read declaration - must be player of game master

        # check there is a game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(player_id)
        if role_id is None:
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # TODO : find a way to pass a limit
        limit = None

        # gather declarations
        assert role_id is not None
        declarations_list = declarations.Declaration.list_by_game_id(game_id)
        declarations_list_json = list()
        num = 1
        for _, _, declaration in sorted(declarations_list, key=lambda t: t[2].time_stamp, reverse=True):
            declarations_list_json.append(declaration.export())
            num += 1
            if limit is not None and num == limit:
                break

        data = {'declarations_list': declarations_list_json}
        return data, 200


@API.resource('/game-visits/<game_id>')
class GameVisitRessource(flask_restful.Resource):  # type: ignore
    """  GameVisitRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Insert visit in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-visits/<game_id> - POST - creating new visit game id=%s", game_id)

        args = VISIT_PARSER.parse_args(strict=True)
        role_id = args['role_id']

        mylogger.LOGGER.info("role_id=%s", role_id)

        pseudo = args['pseudo']

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to insert visit in game")

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
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

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

        # check user has right to post visit - must be player of game master

        # find the game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is player for role ?
        assert game is not None
        expected_id = game.get_role(role_id)

        # can be player of game master but must correspond
        if user_id != expected_id:
            if role_id == 0:
                flask_restful.abort(403, msg="You do not seem to be the game master of the game")
            else:
                flask_restful.abort(403, msg="You do not seem to be the player who is in charge")

        # create visit here
        time_stamp = int(time.time())
        visit = visits.Visit(int(game_id), role_id, time_stamp)
        visit.update_database()

        data = {'msg': "Ok visit inserted"}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Retrieve visit in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-visits/<game_id> - GET - retrieving new visit game id=%s", game_id)

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

        # check user has right to read visit - must be player of game master

        # check there is a game
        game = games.Game.find_by_identifier(game_id)
        if game is None:
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id = game.find_role(player_id)
        if role_id is None:
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # retrieve visit here
        assert role_id is not None
        time_stamp = int(time.time())  # serves as default
        visits_list = visits.Visit.list_by_game_id_role_num(game_id, role_id)
        if visits_list:
            visit = visits_list[0]
            _, _, time_stamp = visit

        data = {'time_stamp': time_stamp}
        return data, 200


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
        populate.populate()

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['GAME']['PORT']

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
