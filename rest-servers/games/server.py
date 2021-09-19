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
import definitives
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

GAMES_SELECT_PARSER = flask_restful.reqparse.RequestParser()
GAMES_SELECT_PARSER.add_argument('selection', type=str, required=True)

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

RECTIFICATION_PARSER = flask_restful.reqparse.RequestParser()
RECTIFICATION_PARSER.add_argument('ownerships', type=str, required=True)
RECTIFICATION_PARSER.add_argument('units', type=str, required=True)
RECTIFICATION_PARSER.add_argument('pseudo', type=str, required=False)

SUBMISSION_PARSER = flask_restful.reqparse.RequestParser()
SUBMISSION_PARSER.add_argument('role_id', type=int, required=True)
SUBMISSION_PARSER.add_argument('orders', type=str, required=True)
SUBMISSION_PARSER.add_argument('definitive', type=int, required=False)
SUBMISSION_PARSER.add_argument('names', type=str, required=True)
SUBMISSION_PARSER.add_argument('pseudo', type=str, required=False)

SUBMISSION_PARSER2 = flask_restful.reqparse.RequestParser()
SUBMISSION_PARSER2.add_argument('role_id', type=int, required=True)
SUBMISSION_PARSER2.add_argument('names', type=str, required=True)
SUBMISSION_PARSER2.add_argument('pseudo', type=str, required=False)

SUBMISSION_PARSER3 = flask_restful.reqparse.RequestParser()
SUBMISSION_PARSER3.add_argument('role_id', type=int, required=True)
SUBMISSION_PARSER3.add_argument('orders', type=str, required=True)
SUBMISSION_PARSER3.add_argument('pseudo', type=str, required=False)

ADJUDICATION_PARSER = flask_restful.reqparse.RequestParser()
ADJUDICATION_PARSER.add_argument('names', type=str, required=True)
ADJUDICATION_PARSER.add_argument('pseudo', type=str, required=False)

SIMULATION_PARSER = flask_restful.reqparse.RequestParser()
SIMULATION_PARSER.add_argument('variant_name', type=str, required=True)
SIMULATION_PARSER.add_argument('orders', type=str, required=True)
SIMULATION_PARSER.add_argument('units', type=str, required=True)
SIMULATION_PARSER.add_argument('names', type=str, required=True)

DECLARATION_PARSER = flask_restful.reqparse.RequestParser()
DECLARATION_PARSER.add_argument('role_id', type=int, required=True)
DECLARATION_PARSER.add_argument('anonymous', type=int, required=True)
DECLARATION_PARSER.add_argument('content', type=str, required=True)
DECLARATION_PARSER.add_argument('pseudo', type=str, required=False)

MESSAGE_PARSER = flask_restful.reqparse.RequestParser()
MESSAGE_PARSER.add_argument('role_id', type=int, required=True)
MESSAGE_PARSER.add_argument('dest_role_ids', type=str, required=True)
MESSAGE_PARSER.add_argument('content', type=str, required=True)
MESSAGE_PARSER.add_argument('pseudo', type=str, required=False)

VISIT_PARSER = flask_restful.reqparse.RequestParser()
VISIT_PARSER.add_argument('role_id', type=int, required=True)
VISIT_PARSER.add_argument('pseudo', type=str, required=False)

VOTE_PARSER = flask_restful.reqparse.RequestParser()
VOTE_PARSER.add_argument('role_id', type=int, required=True)
VOTE_PARSER.add_argument('value', type=int, required=True)
VOTE_PARSER.add_argument('pseudo', type=str, required=False)


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

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_name(sql_executor, name)

        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game {name} doesn't exist")

        del sql_executor

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

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_name(sql_executor, name)

        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Game {name} doesn't exist")

        del sql_executor

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

        mylogger.LOGGER.info("pseudo=%s", pseudo)

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

            del sql_executor

            data = {'name': name, 'msg': 'Ok but no change !'}
            return data, 200

        # special : game changed state
        if game.current_state != current_state_before:

            if current_state_before == 0 and game.current_state == 1:

                # check enough players
                nb_players_allocated = game.number_allocated(sql_executor)
                variant_name = game.variant
                variant_data = variants.Variant.get_by_name(variant_name)
                assert variant_data is not None
                number_players_expected = variant_data['roles']['number']

                if nb_players_allocated < number_players_expected:

                    del sql_executor

                    data = {'name': name, 'msg': 'Not enough players !'}
                    return data, 400

                if nb_players_allocated > number_players_expected:

                    del sql_executor

                    data = {'name': name, 'msg': 'Too many players !'}
                    return data, 400

                game.start(sql_executor)

                # notify players

                subject = f"La partie {game.name} a démarré !"
                game_id = game.identifier
                allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
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

                # notify players

                subject = f"La partie {game.name} s'est terminée !"
                game_id = game.identifier
                allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
                addressees = list()
                for _, player_id, __ in allocations_list:
                    addressees.append(player_id)
                body = "Vous ne pouvez plus jouer dans cette partie !"

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

        game.update_database(sql_executor)

        del sql_executor

        data = {'name': name, 'msg': 'Ok updated'}
        return data, 200

    def delete(self, name: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
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
        if game.current_state != 2:
            del sql_executor
            flask_restful.abort(400, msg=f"Game {name} is not terminated")

        # delete allocations
        game.delete_allocations(sql_executor)

        # and position
        game.delete_position(sql_executor)

        game_id = game.identifier

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

        # delete contents
        for (identifier, _, _, _) in contents.Content.list_by_game_id(sql_executor, int(game_id)):
            content = contents.Content(identifier, 0, 0, '')
            content.delete_database(sql_executor)

        # delete declarations
        for (_, _, _, content_id) in declarations.Declaration.list_by_game_id(sql_executor, int(game_id)):
            declaration = declarations.Declaration(0, 0, False, content_id)
            declaration.delete_database(sql_executor)

        # delete messages
        for (_, _, _, content_id) in messages.Message.list_by_game_id(sql_executor, int(game_id)):
            message = messages.Message(0, 0, 0, content_id)
            message.delete_database(sql_executor)

        # finally delete game
        assert game is not None
        game.delete_database(sql_executor)

        del sql_executor

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

        sql_executor = database.SqlExecutor()

        games_list = games.Game.inventory(sql_executor)

        del sql_executor

        data = {str(g.identifier): {'name': g.name, 'variant': g.variant, 'deadline': g.deadline, 'current_advancement': g.current_advancement, 'current_state': g.current_state} for g in games_list}
        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Creates a new game
        EXPOSED
        """

        mylogger.LOGGER.info("/games - POST - creating new game name")

        args = GAME_PARSER.parse_args(strict=True)

        name = args['name']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("name=%s", name)
        mylogger.LOGGER.info("pseudo=%s", pseudo)

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

        if not name.isidentifier():
            flask_restful.abort(400, msg=f"Name '{name}' is not a valid name")

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_name(sql_executor, name)
        if game is not None:
            del sql_executor
            flask_restful.abort(400, msg=f"Game {name} already exists")

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
        identifier = games.Game.free_identifier(sql_executor)
        game = games.Game(identifier, '', '', '', False, False, False, False, False, 0, 0, False, 0, False, 0, False, False, False, False, 0, 0, 0, 0, 0, 0, 0, 0)
        _ = game.load_json(args)
        game.update_database(sql_executor)

        # make position for game
        game.create_position(sql_executor)

        game_id = game.identifier

        # add a little report
        time_stamp = int(time.time())
        report = reports.Report(game_id, time_stamp, WELCOME_TO_GAME)
        report.update_database(sql_executor)

        # add a capacity
        # TODO : get correct value from variant
        value = 8
        capacity = capacities.Capacity(game_id, value)
        capacity.update_database(sql_executor)

        # add that all players are active (those who own a center - that will do)
        game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
        active_roles = {o[2] for o in game_ownerships}
        for role_num in active_roles:
            active = actives.Active(int(game_id), role_num)
            active.update_database(sql_executor)

        # allocate game master to game
        game.put_role(sql_executor, user_id, 0)

        del sql_executor

        data = {'name': name, 'msg': 'Ok game created'}
        return data, 201


@API.resource('/games-select')
class GameSelectListRessource(flask_restful.Resource):  # type: ignore
    """ GameSelectListRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Provides list of some games ( selected by identifier)
        Should be a get but has parameters
        parameter is a space separated string of ints
        EXPOSED
        """

        mylogger.LOGGER.info("/games-select - POST - get getting some games only name")

        args = GAMES_SELECT_PARSER.parse_args(strict=True)

        selection_submitted = args['selection']

        mylogger.LOGGER.info("selection_submitted=%s", selection_submitted)

        try:
            selection_list = list(map(int, selection_submitted.split()))
        except:  # noqa: E722 pylint: disable=bare-except
            flask_restful.abort(400, msg="Bad selection. Use a space separated list of numbers")

        sql_executor = database.SqlExecutor()

        games_list = games.Game.inventory(sql_executor)

        del sql_executor

        data = {str(g.identifier): {'name': g.name, 'variant': g.variant, 'deadline': g.deadline, 'current_advancement': g.current_advancement, 'current_state': g.current_state} for g in games_list if g.identifier in selection_list}
        return data, 200


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

        sql_executor = database.SqlExecutor()

        allocations_list = allocations.Allocation.inventory(sql_executor)
        data = [{'game': a[0], 'master': a[1]} for a in allocations_list if a[2] == 0]

        del sql_executor

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
        mylogger.LOGGER.info("pseudo=%s", pseudo)

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

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # find the game master
        assert game is not None
        game_master_id = game.get_role(sql_executor, 0)

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

            del sql_executor

            data = {'msg': 'Ok allocation updated or created'}
            return data, 201

        allocation = allocations.Allocation(game_id, player_id, dangling_role_id)
        allocation.delete_database(sql_executor)

        del sql_executor

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
        deletes : That will create a -1 role allocation
        EXPOSED
        """

        mylogger.LOGGER.info("/role-allocations - POST - creating/deleting new role-allocation")

        args = ROLE_ALLOCATION_PARSER.parse_args(strict=True)

        game_id = args['game_id']
        player_pseudo = args['player_pseudo']
        role_id = args['role_id']
        delete = args['delete']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("game_id=%s player_pseudo=%s role_id=%s delete=%s", game_id, player_pseudo, role_id, delete)
        mylogger.LOGGER.info("pseudo=%s", pseudo)

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

        del sql_executor

        # report
        data = {'msg': 'Ok player role-allocation deleted if present'}
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

        sql_executor = database.SqlExecutor()

        allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)

        del sql_executor

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

        if req_result.json() != player_id:
            flask_restful.abort(404, msg=f"Only player can get player allocations")

        sql_executor = database.SqlExecutor()

        allocations_list = allocations.Allocation.list_by_player_id(sql_executor, player_id)

        del sql_executor

        data = {str(a[0]): a[2] for a in allocations_list}
        return data, 200


@API.resource('/games-recruiting')
class GamesRecruitingRessource(flask_restful.Resource):  # type: ignore
    """ GamesRecruitingRessource """

    def get(self) -> typing.Tuple[typing.List[typing.Tuple[int, int, int]], int]:  # pylint: disable=no-self-use
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

        ownerships_submitted = args['ownerships']
        units_submitted = args['units']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("ownerships_submitted=%s units_submitted=%s", ownerships_submitted, units_submitted)
        mylogger.LOGGER.info("pseudo=%s", pseudo)

        try:
            the_ownerships = json.loads(ownerships_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert ownerships from json to text ?")

        try:
            the_units = json.loads(units_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert units from json to text ?")

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
        #  user_id = req_result.json()  #  we do not use this variable

        sql_executor = database.SqlExecutor()

        # check user has right to change position - must be admin

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # TODO improve this with real admin account
        if pseudo != 'Palpatine':
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to rectify a position!")

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

        del sql_executor

        data = {'msg': 'Ok position rectified'}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Gets position of the game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-positions/<game_id> - GET - getting position for game id=%s", game_id)

        sql_executor = database.SqlExecutor()

        # get ownerships
        ownership_dict = dict()
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
        forbidden_list = list()
        game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)
        for _, region_num in game_forbiddens:
            forbidden_list.append(region_num)

        del sql_executor

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

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # find the report
        report = reports.Report.find_by_identifier(sql_executor, game_id)
        if report is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Report happens to be missing for {game_id}")

        # extract report data
        assert report is not None
        content = report.content

        del sql_executor

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

        sql_executor = database.SqlExecutor()

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # find the transition
        transition = transitions.Transition.find_by_identifier_advancement(sql_executor, game_id, advancement)
        if transition is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Transition happens to be missing for {game_id} / {advancement}")

        # extract transition data
        assert transition is not None
        the_situation = json.loads(transition.situation_json)
        the_orders = json.loads(transition.orders_json)
        report_txt = transition.report_txt

        del sql_executor

        data = {'situation': the_situation, 'orders': the_orders, 'report_txt': report_txt}
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
        orders_submitted = args['orders']
        definitive_value = args['definitive']
        names = args['names']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("role_id=%s orders_submitted=%s definitive_value=%s names=%s", role_id, orders_submitted, definitive_value, names)
        mylogger.LOGGER.info("pseudo=%s", pseudo)

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
            flask_restful.abort(403, msg="Submitting orders is not possible for game master for non archive games")

        # put in database fake units - units for build orders

        try:
            the_orders = json.loads(orders_submitted)
        except json.JSONDecodeError:
            del sql_executor
            flask_restful.abort(400, msg="Did you convert orders from json to text ?")

        # first we copy the fake units of the role already present and remove them
        game_units = units.Unit.list_by_game_id(sql_executor, game_id)  # noqa: F821
        prev_fake_unit_list: typing.List[typing.List[int]] = list()
        for _, type_num, zone_num, role_num, _, fake in game_units:
            if not fake:
                continue
            if not (role_id == 0 or role_num == int(role_id)):
                continue
            prev_fake_unit_list.append([type_num, zone_num, role_num])
            fake_unit = units.Unit(int(game_id), type_num, zone_num, role_num, 0, True)
            fake_unit.delete_database(sql_executor)  # noqa: F821

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
                fake_unit.update_database(sql_executor)  # noqa: F821

        # now checking validity of orders

        # evaluate variant
        variant_name = game.variant
        variant_dict = variants.Variant.get_by_name(variant_name)
        if variant_dict is None:
            flask_restful.abort(404, msg=f"Variant {variant_name} doesn't exist")
        variant_dict_json = json.dumps(variant_dict)

        # evaluate situation

        # situation: get ownerships
        ownership_dict: typing.Dict[str, int] = dict()
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
                fake_unit_dict[str(role_num)].append([type_num, zone_num])
            elif region_dislodged_from_num:
                dislodged_unit_dict[str(role_num)].append([type_num, zone_num, region_dislodged_from_num])
            else:
                unit_dict[str(role_num)].append([type_num, zone_num])

        # situation: get forbiddens
        forbidden_list = list()
        game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)  # noqa: F821
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
                fake_unit.delete_database(sql_executor)  # noqa: F821

            # we restore the backed up fake units
            for type_num, zone_num, role_num in prev_fake_unit_list:
                fake_unit = units.Unit(int(game_id), type_num, zone_num, role_num, 0, True)
                # insert
                fake_unit.update_database(sql_executor)  # noqa: F821

            del sql_executor

            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Failed to submit orders {message} : {submission_report}")

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
        if role_id != 0:
            if definitive_value is not None:

                # create vote here
                definitive = definitives.Definitive(int(game_id), role_id, bool(definitive_value))
                definitive.update_database(sql_executor)  # noqa: F821

        del sql_executor  # noqa: F821

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
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

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


@API.resource('/game-no-orders/<game_id>')
class GameNoOrderRessource(flask_restful.Resource):  # type: ignore
    """ GameNoOrderRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Submit civil disorder
        EXPOSED
        """

        mylogger.LOGGER.info("/game-no-orders/<game_id> - POST - submitting civil disorder game id=%s", game_id)

        args = SUBMISSION_PARSER2.parse_args(strict=True)

        role_id = args['role_id']
        names = args['names']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("role_id=%s", role_id)  # names not logged
        mylogger.LOGGER.info("pseudo=%s", pseudo)

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

        # evaluate variant
        variant_name = game.variant
        variant_dict = variants.Variant.get_by_name(variant_name)
        if variant_dict is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Variant {variant_name} doesn't exist")
        variant_dict_json = json.dumps(variant_dict)

        # evaluate situation

        # situation: get ownerships
        ownership_dict: typing.Dict[str, int] = dict()
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
        forbidden_list = list()
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

            del sql_executor

            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
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

        # insert this submisssion
        submission = submissions.Submission(int(game_id), int(role_id))
        submission.update_database(sql_executor)

        del sql_executor

        data = {'msg': f"Ok civil disorder submitted {submission_report}"}
        return data, 201


@API.resource('/game-communication-orders/<game_id>')
class GameCommunicationOrderRessource(flask_restful.Resource):  # type: ignore
    """ GameCommunicationOrderRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Submit communication orders
        EXPOSED
        """

        mylogger.LOGGER.info("/game-communication-orders/<game_id> - POST - submitting communication orders game id=%s", game_id)

        args = SUBMISSION_PARSER3.parse_args(strict=True)

        role_id = args['role_id']
        communication_orders_submitted = args['orders']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("role_id=%s communication_orders_submitted=%s", role_id, communication_orders_submitted)  # names not logged
        mylogger.LOGGER.info("pseudo=%s", pseudo)

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to submit communication orders in game")

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

        del sql_executor  # noqa: F821

        data = {'msg': "Ok communication orders stored"}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
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
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # not allowed for game master
        if role_id == 0:
            del sql_executor
            flask_restful.abort(403, msg="Getting communication orders is not possible for game master")

        # get orders
        assert role_id is not None
        communication_orders_list = communication_orders.CommunicationOrder.list_by_game_id_role_num(sql_executor, game_id, role_id)

        fake_units_list: typing.List[int] = list()

        del sql_executor

        data = {
            'orders': communication_orders_list,
            'fake_units': fake_units_list,
        }
        return data, 200


@API.resource('/game-orders-submitted/<game_id>')
class GameOrdersSubmittedRessource(flask_restful.Resource):  # type: ignore
    """ GameOrderRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[int]], int]:  # pylint: disable=no-self-use
        """
        Gets list of roles which have submitted orders, orders are missing, orders are not needed
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

        # check user has right to get status of orders - must be game master or player in game

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
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # TODO : change if we decide to hide this information
        # we could restrict to game master from here
        #  if role_id != 0:
            #  flask_restful.abort(403, msg=f"You do not seem to master game {game_id}")

        # submissions_list : those who submitted orders
        submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
        submitted_list = [o[1] for o in submissions_list]

        # needed list : those who need to submit orders
        actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
        needed_list = [o[1] for o in actives_list]

        del sql_executor

        data = {'submitted': submitted_list, 'needed': needed_list}
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

        names = args['names']
        pseudo = args['pseudo']

        # names not logged
        mylogger.LOGGER.info("pseudo=%s", pseudo)

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

        sql_executor = database.SqlExecutor()

        # check user has right to adjudicate - must be game master

        # find the game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # who is game master ?
        assert game is not None
        game_master_id = game.get_role(sql_executor, 0)

        # must be game master
        if user_id != game_master_id:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be the game master of the game")

        # evaluate variant
        variant_name = game.variant
        variant_dict = variants.Variant.get_by_name(variant_name)
        if variant_dict is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Variant {variant_name} doesn't exist")

        variant_dict_json = json.dumps(variant_dict)

        # evaluate situation

        # situation: get ownerships
        ownership_dict = dict()
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
        forbidden_list = list()
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

        # evaluate orders
        orders_list = list()
        orders_from_game = orders.Order.list_by_game_id(sql_executor, game_id)
        for _, role_num, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num in orders_from_game:
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

        # position for transition

        # get ownerships
        ownership_dict = dict()
        game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
        for _, center_num, role_num in game_ownerships:
            ownership_dict[str(center_num)] = role_num

        # get units
        unit_dict2: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        dislodged_unit_dict2: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
        game_units = units.Unit.list_by_game_id(sql_executor, game_id)
        for _, type_num, zone_num, role_num, zone_dislodged_from_num, fake in game_units:
            if fake:
                pass  # this is confidential
            elif zone_dislodged_from_num:
                dislodged_unit_dict2[str(role_num)].append([type_num, zone_num, zone_dislodged_from_num])
            else:
                unit_dict2[str(role_num)].append([type_num, zone_num])

        # get forbiddens
        forbidden_list = list()
        game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)
        for _, region_num in game_forbiddens:
            forbidden_list.append(region_num)

        position_transition_dict = {
            'ownerships': ownership_dict,
            'dislodged_ones': dislodged_unit_dict2,
            'units': unit_dict2,
            'forbiddens': forbidden_list,
        }

        # orders for transition
        orders_transition_list = orders.Order.list_by_game_id(sql_executor, game_id)

        units_transition_list = units.Unit.list_by_game_id(sql_executor, game_id)
        fake_units_transition_list = [u for u in units_transition_list if u[5]]

        orders_transition_dict = {
            'orders': orders_transition_list,
            'fake_units': fake_units_transition_list,
        }

        # extract new position
        situation_result = req_result.json()['situation_result']
        the_ownerships = situation_result['ownerships']
        the_units = situation_result['units']
        the_dislodged_units = situation_result['dislodged_ones']
        the_forbiddens = situation_result['forbiddens']

        # extract actives
        the_active_roles = req_result.json()['active_roles']

        # store new position in database

        # purge

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

        # purge actives
        for (_, role_num) in actives.Active.list_by_game_id(sql_executor, int(game_id)):
            active = actives.Active(int(game_id), role_num)
            active.delete_database(sql_executor)

        # purge submissions
        for (_, role_num) in submissions.Submission.list_by_game_id(sql_executor, int(game_id)):
            submission = submissions.Submission(int(game_id), role_num)
            submission.delete_database(sql_executor)

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

        # insert new actives
        for role_num in the_active_roles:
            active = actives.Active(int(game_id), int(role_num))
            active.update_database(sql_executor)

        # keep a copy of orders eligible for communication orders
        communication_eligibles = list()
        for (_, role_id, order_type, zone_num, _, _) in orders.Order.list_by_game_id(sql_executor, game_id):
            if order_type in [4, 7]:
                communication_eligibles.append(zone_num)

        # remove orders
        for (_, role_id, _, zone_num, _, _) in orders.Order.list_by_game_id(sql_executor, game_id):
            order = orders.Order(int(game_id), role_id, 0, zone_num, 0, 0)
            order.delete_database(sql_executor)

        # extract new report
        orders_result = req_result.json()['orders_result']
        orders_result_simplified = orders_result

        # --------------------------
        # get communication orders

        # evaluate communication_orders (only the units with a hld of disperse order)
        communication_orders_list = list()
        communication_orders_from_game = communication_orders.CommunicationOrder.list_by_game_id(sql_executor, game_id)
        for _, role_num, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num in communication_orders_from_game:
            if active_unit_zone_num in communication_eligibles:
                communication_orders_list.append([role_num, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num])

        communication_orders_list_json = json.dumps(communication_orders_list)

        json_dict = {
            'variant': variant_dict_json,
            'advancement': game.current_advancement,
            'situation': situation_dict_json,
            'orders': communication_orders_list_json,
            'names': names,
        }

        # post to solver (for print)
        host = lowdata.SERVER_CONFIG['SOLVER']['HOST']
        port = lowdata.SERVER_CONFIG['SOLVER']['PORT']
        url = f"{host}:{port}/print"
        req_result = SESSION.post(url, data=json_dict)

        # print failed
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Failed to print communication orders {message}")

        # extract printed orders
        communication_orders_content = req_result.json()['orders_content']
        communication_orders_content_tagged = '\n'.join([f"* {ll}" for ll in communication_orders_content.split('\n')])

        # remove communication orders
        for (_, role_id, _, zone_num, _, _) in communication_orders.CommunicationOrder.list_by_game_id(sql_executor, game_id):
            communication_order = communication_orders.CommunicationOrder(int(game_id), role_id, 0, zone_num, 0, 0)
            communication_order.delete_database(sql_executor)

        # --------------------------

        # date for report in database (actually unused)
        time_stamp = int(time.time())

        # make report
        date_now = datetime.datetime.now()
        date_desc = date_now.strftime('%Y-%m-%d %H:%M:%S')
        report_txt = f"{date_desc}:\n{orders_result_simplified}\n{communication_orders_content_tagged}"

        # put report in database
        report = reports.Report(int(game_id), time_stamp, report_txt)
        report.update_database(sql_executor)

        # put transition in database
        # important : need to be same as when getting situation
        position_transition_dict_json = json.dumps(position_transition_dict)
        orders_transition_dict_json = json.dumps(orders_transition_dict)
        transition = transitions.Transition(int(game_id), game.current_advancement, position_transition_dict_json, orders_transition_dict_json, report_txt)
        transition.update_database(sql_executor)

        # update season
        game.advance()
        game.update_database(sql_executor)

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
        ownership_dict: typing.Dict[str, int] = dict()

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
        dest_role_ids_submitted = args['dest_role_ids']
        payload = args['content']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("role_id=%s dest_role_ids_submitted=%s", role_id, dest_role_ids_submitted)  # payload not logged
        mylogger.LOGGER.info("pseudo=%s", pseudo)

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
        # create message here

        # create a content
        identifier = contents.Content.free_identifier(sql_executor)
        time_stamp = int(time.time())  # now
        content = contents.Content(identifier, int(game_id), time_stamp, payload)
        content.update_database(sql_executor)

        # create a message linked to the content
        try:
            dest_role_ids = list(map(int, dest_role_ids_submitted.split()))
        except:  # noqa: E722 pylint: disable=bare-except
            flask_restful.abort(400, msg="Bad list of addresses identifiers. Use a space separated list of numbers")

        for dest_role_id in dest_role_ids:
            message = messages.Message(int(game_id), role_id, dest_role_id, identifier)
            message.update_database(sql_executor)

        nb_addressees = len(dest_role_ids)

        del sql_executor

        data = {'msg': f"Ok {nb_addressees} message(s) inserted"}
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
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # gather messages
        assert role_id is not None
        messages_extracted_list = messages.Message.list_with_content_by_game_id(sql_executor, game_id)

        # get all message
        messages_dict_mess: typing.Dict[int, typing.Tuple[int, int, contents.Content]] = dict()
        messages_dict_dest: typing.Dict[int, typing.List[int]] = collections.defaultdict(list)
        for _, identifier, author_num, addressee_num, time_stamp, content in messages_extracted_list:
            if identifier not in messages_dict_mess:
                messages_dict_mess[identifier] = author_num, time_stamp, content
            messages_dict_dest[identifier].append(addressee_num)

        # extract the ones not concerned
        messages_list: typing.List[typing.Tuple[int, int, typing.List[int], str]] = list()
        for identifier in messages_dict_mess:
            author_num, time_stamp, content = messages_dict_mess[identifier]
            addressees_num = messages_dict_dest[identifier]
            if role_id == author_num or role_id in addressees_num:
                messages_list.append((author_num, time_stamp, addressees_num, content.payload))

        del sql_executor

        data = {
            'messages_list': messages_list,
        }
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
        anonymous = args['anonymous']
        payload = args['content']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("role_id=%s anonymous=%s", role_id, anonymous)  # payload not logged
        mylogger.LOGGER.info("pseudo=%s", pseudo)

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

        sql_executor = database.SqlExecutor()

        # check user has right to post declatation - must be player of game master

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

        # create declaration here

        # create a content
        identifier = contents.Content.free_identifier(sql_executor)
        time_stamp = int(time.time())  # now
        content = contents.Content(identifier, int(game_id), time_stamp, payload)
        content.update_database(sql_executor)

        # create a declaration linked to the content
        declaration = declarations.Declaration(int(game_id), role_id, anonymous, identifier)
        declaration.update_database(sql_executor)

        del sql_executor

        data = {'msg': "Ok declaration inserted."}
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

        sql_executor = database.SqlExecutor()

        # check user has right to read declaration - must be player of game master

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
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # gather declarations
        declarations_list = declarations.Declaration.list_with_content_by_game_id(sql_executor, game_id)

        declarations_list_ret = list()
        for _, author_num, anonymous, time_stamp, content in declarations_list:
            if anonymous and role_id != 0:
                declarations_list_ret.append((anonymous, -1, time_stamp, content.payload))
            else:
                declarations_list_ret.append((anonymous, author_num, time_stamp, content.payload))

        del sql_executor

        data = {'declarations_list': declarations_list_ret}
        return data, 200


@API.resource('/date-last-game-message/<game_id>/<role_id>')
class DateLastGameMessageRessource(flask_restful.Resource):  # type: ignore
    """  DateLastGameMessageRessource """

    def get(self, game_id: int, role_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Gets date of last messages sent to role of game
        EXPOSED
        """

        mylogger.LOGGER.info("/date-last-game-message/<game_id>/<role_id> - GET - getting date last received messages game id=%s role_id=%s", game_id, role_id)

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

        # check there is a game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id_found = game.find_role(sql_executor, player_id)
        if role_id_found is None:
            del sql_executor
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # check the role
        if role_id_found != int(role_id):
            del sql_executor
            flask_restful.abort(403, msg=f"You do not seem to have role {role_id} in game {game_id}")

        # serves as default value (long time ago)
        time_stamp = 0

        assert role_id is not None

        # gather messages
        messages_list = messages.Message.list_with_content_by_game_id(sql_executor, game_id)
        for _, _, _, addressee_num, time_stamp_found, _ in messages_list:

            # must be addressee
            if addressee_num != int(role_id):
                continue

            time_stamp = time_stamp_found
            break

        del sql_executor

        data = {'time_stamp': time_stamp}
        return data, 200


@API.resource('/date-last-game-declaration/<game_id>')
class DateLastGameDeclarationRessource(flask_restful.Resource):  # type: ignore
    """  DateLastGameDeclarationRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Gets date of last declarations of game
        EXPOSED
        """

        mylogger.LOGGER.info("/date-last-game-declaration/<game_id> - GET - getting date last game declarations game id=%s", game_id)

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

        # check user has right to read declaration - must be player of game master

        # check there is a game
        game = games.Game.find_by_identifier(sql_executor, game_id)
        if game is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a game with identifier {game_id}")

        # get the role
        assert game is not None
        role_id_found = game.find_role(sql_executor, player_id)
        if role_id_found is None:
            del sql_executor
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # serves as default value (long time ago)
        time_stamp = 0

        # gather declarations
        declarations_list = declarations.Declaration.list_with_content_by_game_id(sql_executor, game_id)
        for _, _, _, time_stamp_found, _ in declarations_list:
            time_stamp = time_stamp_found
            break

        del sql_executor

        data = {'time_stamp': time_stamp}
        return data, 200


@API.resource('/game-visits/<game_id>/<visit_type>')
class GameVisitRessource(flask_restful.Resource):  # type: ignore
    """  GameVisitRessource """

    def post(self, game_id: int, visit_type: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Insert visit in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-visits/<game_id>/<visit_type> - POST - creating new visit game id=%s visit_type=%s", game_id, visit_type)

        args = VISIT_PARSER.parse_args(strict=True)

        role_id = args['role_id']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("role_id=%s", role_id)
        mylogger.LOGGER.info("pseudo=%s", pseudo)

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

        del sql_executor

        data = {'msg': "Ok visit inserted"}
        return data, 201

    def get(self, game_id: int, visit_type: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Retrieve visit in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-visits/<game_id> - GET - retrieving new visit game id=%s visit_type=%s", game_id, visit_type)

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
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # serves as default (very long time ago)
        time_stamp = 0.

        # retrieve visit here
        assert role_id is not None
        visits_list = visits.Visit.list_by_game_id_role_num(sql_executor, game_id, role_id, visit_type)
        if visits_list:
            visit = visits_list[0]
            _, _, _, time_stamp = visit

        del sql_executor

        data = {'time_stamp': time_stamp}
        return data, 200


@API.resource('/game-definitives/<game_id>')
class GameDefinitiveRessource(flask_restful.Resource):  # type: ignore
    """  GameDefinitiveRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Retrieve definitive in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-definitives/<game_id> - GET - retrieving definitive game id=%s", game_id)

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

        sql_executor = database.SqlExecutor()

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
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # retrieve definitive here
        assert role_id is not None
        if role_id == 0:
            definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
        else:
            definitives_list = definitives.Definitive.list_by_game_id_role_num(sql_executor, game_id, role_id)

        del sql_executor

        data = {'definitives': definitives_list}
        return data, 200


@API.resource('/game-votes/<game_id>')
class GameVoteRessource(flask_restful.Resource):  # type: ignore
    """  GameVoteRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Insert vote in database
        EXPOSED
        """

        mylogger.LOGGER.info("/game-votes/<game_id> - POST - creating new vote game id=%s", game_id)

        args = VOTE_PARSER.parse_args(strict=True)

        role_id = args['role_id']
        value = args['value']
        pseudo = args['pseudo']

        mylogger.LOGGER.info("role_id=%s value=%s", role_id, value)
        mylogger.LOGGER.info("pseudo=%s", pseudo)

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to insert vote in game")

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

        # create vote here
        vote = votes.Vote(int(game_id), role_id, bool(value))
        vote.update_database(sql_executor)

        del sql_executor

        data = {'msg': "Ok vote inserted"}
        return data, 201

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
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
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

        # retrieve vote here
        assert role_id is not None
        if role_id == 0:
            votes_list = votes.Vote.list_by_game_id(sql_executor, game_id)
        else:
            votes_list = votes.Vote.list_by_game_id_role_num(sql_executor, game_id, role_id)

        del sql_executor

        data = {'votes': votes_list}
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
        sql_executor = database.SqlExecutor()
        populate.populate(sql_executor)
        del sql_executor

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['GAME']['PORT']

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
