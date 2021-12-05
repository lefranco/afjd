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
import incidents
import lowdata
import agree

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
GAME_PARSER.add_argument('nomessage', type=int, required=False)
GAME_PARSER.add_argument('nopress', type=int, required=False)
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
SUBMISSION_PARSER.add_argument('adjudication_names', type=str, required=True)
SUBMISSION_PARSER.add_argument('pseudo', type=str, required=False)

AGREE_PARSER = flask_restful.reqparse.RequestParser()
AGREE_PARSER.add_argument('role_id', type=int, required=True)
AGREE_PARSER.add_argument('definitive', type=int, required=False)
AGREE_PARSER.add_argument('adjudication_names', type=str, required=True)
AGREE_PARSER.add_argument('pseudo', type=str, required=False)

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

        # find the game
        sql_executor = database.SqlExecutor()
        game = games.Game.find_by_name(sql_executor, name)
        del sql_executor

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

        # find the game
        sql_executor = database.SqlExecutor()
        game = games.Game.find_by_name(sql_executor, name)
        del sql_executor

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
                del sql_executor
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

            if not game.current_state > current_state_before:
                data = {'name': name, 'msg': 'Transition not allowed'}
                del sql_executor
                return data, 400

            if current_state_before == 0 and game.current_state == 1:

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
                    addressees = list()
                    for _, player_id, __ in allocations_list:
                        addressees.append(player_id)
                    body = "Vous pouvez commencer à jouer dans cette partie !"
                    body += "\n"
                    body += "Pour se rendre directement sur la partie :\n"
                    body += f"https://diplomania-gen.fr?game={game.name}"

                    json_dict = {
                        'pseudo': pseudo,
                        'addressees': " ".join([str(a) for a in addressees]),
                        'subject': subject,
                        'body': body,
                        'force': 1,
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

            if current_state_before == 1 and game.current_state == 2:

                # no check ?
                game.terminate()
                # commited later

                if not (game.fast or game.archive):

                    # notify players
                    subject = f"La partie {game.name} s'est terminée !"
                    game_id = game.identifier
                    allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
                    addressees = list()
                    for _, player_id, __ in allocations_list:
                        addressees.append(player_id)
                    body = "Vous ne pouvez plus jouer dans cette partie !"
                    body += "\n"
                    body += "Pour se rendre directement sur la partie :\n"
                    body += f"https://diplomania-gen.fr?game={game.name}"

                    json_dict = {
                        'pseudo': pseudo,
                        'addressees': " ".join([str(a) for a in addressees]),
                        'subject': subject,
                        'body': body,
                        'force': 1,
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

        game.update_database(sql_executor)
        sql_executor.commit()

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
        if game.current_state == 1:
            del sql_executor
            flask_restful.abort(400, msg=f"Game {name} is ongoing. Terminate it first.")

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

        # and submissions
        for (_, role_num) in submissions.Submission.list_by_game_id(sql_executor, int(game_id)):
            submission = submissions.Submission(int(game_id), role_num)
            submission.delete_database(sql_executor)

        # and agreements
        for (_, role_num, _) in definitives.Definitive.list_by_game_id(sql_executor, int(game_id)):
            definitive = definitives.Definitive(int(game_id), role_num, False)
            definitive.delete_database(sql_executor)

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

        sql_executor.commit()
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

        data = {str(g.identifier): {'name': g.name, 'variant': g.variant, 'description': g.description, 'deadline': g.deadline, 'current_advancement': g.current_advancement, 'current_state': g.current_state, 'fast': g.fast, 'grace_duration': g.grace_duration} for g in games_list}
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

        # cannot have a void scoring
        if args['scoring']:
            scoring_provided = args['scoring']
            if not games.check_scoring(scoring_provided):
                flask_restful.abort(404, msg=f"Scoring '{scoring_provided}' is not a valid scoring code")
        else:
            args['scoring'] = games.default_scoring()

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
                del sql_executor
                flask_restful.abort(400, msg=f"You cannot set a deadline in the past :'{date_desc}' (GMT)")

        else:

            # create it
            time_stamp = time.time()
            forced_deadline = int(time_stamp)
            args['deadline'] = forced_deadline

        # create game here
        identifier = games.Game.free_identifier(sql_executor)
        game = games.Game(identifier, '', '', '', False, False, False, False, False, '', 0, 0, False, 0, 0, False, 0, False, 0, False, False, False, False, 0, 0, 0, 0, 0, 0, 0, 0)
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

        sql_executor.commit()
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

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
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

        sql_executor.commit()
        del sql_executor

        # report
        data = {'msg': 'Ok player role-allocation deleted if present'}
        return data, 200


@API.resource('/game-role/<game_id>')
class GameRoleRessource(flask_restful.Resource):  # type: ignore
    """ GameRoleRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Optional[int], int]:  # pylint: disable=no-self-use
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

    def get(self) -> typing.Tuple[typing.Optional[typing.Dict[int, int]], int]:  # pylint: disable=no-self-use
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

        dict_role_id: typing.Dict[int, int] = dict()
        for game_id, _, role_id in allocations_list:
            dict_role_id[game_id] = role_id

        return dict_role_id, 200


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
                # TODO improve this with real admin account
                if pseudo != 'Palpatine':
                    flask_restful.abort(403, msg="You need to be the game master of the game (or site administrator) to see the roles of this anonymous game")

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
        user_id = req_result.json()

        if user_id != int(player_id):
            flask_restful.abort(403, msg="Only player can get his/her player allocations")

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
            flask_restful.abort(403, msg="You do noty seem to be site administrator so you are not allowed to rectify a position!")

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


@API.resource('/game-force-agree-solve/<game_id>')
class GameForceAgreeSolveRessource(flask_restful.Resource):  # type: ignore
    """ GameForceAgreeSolveRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Force agree to solve with these orders by a game master
        EXPOSED
        """
        mylogger.LOGGER.info("/game-force-agree-solve/<game_id> - POST - force agreeing from game master to solve with orders game id=%s", game_id)

        args = AGREE_PARSER.parse_args(strict=True)

        role_id = args['role_id']
        definitive_value = args['definitive']
        adjudication_names = args['adjudication_names']
        pseudo = args['pseudo']

        if pseudo is None:
            flask_restful.abort(401, msg="Need a pseudo to force agree to solve")

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

        sql_executor = database.SqlExecutor()

        # handle definitive boolean
        # game master forced player to agree to adjudicate
        status, adjudicated, agreement_report = agree.fake_post(game_id, role_id, bool(definitive_value), adjudication_names, sql_executor)

        if not status:
            del sql_executor  # noqa: F821
            flask_restful.abort(400, msg=f"Failed to agree (forced) to adjudicate : {agreement_report}")

        if adjudicated:
            # notify players

            if not (game.fast or game.archive):

                subject = f"La partie {game.name} a avancé (avec l'aide de l'arbitre)!"
                game_id = game.identifier
                allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)
                addressees = list()
                for _, player_id, __ in allocations_list:
                    addressees.append(player_id)
                body = "Vous pouvez continuer à jouer dans cette partie !"
                body += "\n"
                body += "Pour se rendre directement sur la partie :\n"
                body += f"https://diplomania-gen.fr?game={game.name}"

                json_dict = {
                    'pseudo': pseudo,
                    'addressees': " ".join([str(a) for a in addressees]),
                    'subject': subject,
                    'body': body,
                    'force': 0,
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

        if adjudicated:
            data = {'adjudicated': adjudicated, 'msg': f"Ok adjudication was performed (initiated by game master): {agreement_report}"}
        else:
            data = {'adjudicated': adjudicated, 'msg': f"Ok agreement {bool(definitive_value)} stored for role {role_id} (forced by game master) (game adjudication:{agreement_report})"}
        return data, 201


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
        adjudication_names = args['adjudication_names']
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
            del sql_executor
            flask_restful.abort(403, msg="Submitting orders is not possible for game master for non archive games")

        # check orders are required
        # needed list : those who need to submit orders
        if role_id != 0:
            actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
            needed_list = [o[1] for o in actives_list]
            if role_id not in needed_list:
                del sql_executor
                flask_restful.abort(403, msg="This role does not seem to require any orders")

        # put in database fake units - units for build orders

        try:
            the_orders = json.loads(orders_submitted)
        except json.JSONDecodeError:
            del sql_executor
            flask_restful.abort(400, msg="Did you convert orders from json to text ?")

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
            del sql_executor
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

            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"

            del sql_executor
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
        # player submitted orders and agreed (or not) to adjudicate
        status, adjudicated, agreement_report = agree.fake_post(game_id, role_id, bool(definitive_value), adjudication_names, sql_executor)  # noqa: F821

        if not status:
            del sql_executor  # noqa: F821
            flask_restful.abort(400, msg=f"Failed to agree to adjudicate : {agreement_report}")

        if adjudicated:

            if not (game.fast or game.archive):

                # notify players
                subject = f"La partie {game.name} a avancé !"
                game_id = game.identifier
                allocations_list = allocations.Allocation.list_by_game_id(sql_executor, game_id)  # noqa: F821
                addressees = list()
                for _, player_id, __ in allocations_list:
                    addressees.append(player_id)
                body = "Vous pouvez continuer à jouer dans cette partie !"
                body += "\n"
                body += "Pour se rendre directement sur la partie :\n"
                body += f"https://diplomania-gen.fr?game={game.name}"

                json_dict = {
                    'pseudo': pseudo,
                    'addressees': " ".join([str(a) for a in addressees]),
                    'subject': subject,
                    'body': body,
                    'force': 0,
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

        if adjudicated:
            data = {'adjudicated': adjudicated, 'msg': f"Ok adjudication was performed (initiated by player): {agreement_report}"}
        else:
            data = {'adjudicated': adjudicated, 'msg': f"Ok orders submitted {submission_report} and agreement {bool(definitive_value)} stored for role {role_id} (from player) (game adjudication:{agreement_report})"}

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


@API.resource('/game-force-no-orders/<game_id>')
class GameForceNoOrderRessource(flask_restful.Resource):  # type: ignore
    """ GameForceNoOrderRessource """

    def post(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Submit civil disorder
        EXPOSED
        """

        mylogger.LOGGER.info("/game-force-no-orders/<game_id> - POST - submitting civil disorder game id=%s", game_id)

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

        if role_id == 0:
            del sql_executor
            flask_restful.abort(400, msg="Invalid role_id parameter")

        # check orders are required
        # needed list : those who need to submit orders
        actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
        needed_list = [o[1] for o in actives_list]
        if role_id not in needed_list:
            del sql_executor
            flask_restful.abort(403, msg="This role does not seem to require any orders")

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

        sql_executor.commit()
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

        sql_executor.commit()  # noqa: F821
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
    """ GameOrdersSubmittedRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[int]], int]:  # pylint: disable=no-self-use
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

            # TODO improve this with real admin account
            # Admin can still see who passed orders
            if pseudo != 'Palpatine':

                del sql_executor
                flask_restful.abort(403, msg=f"You do not seem to play or master game {game_id} or to be site administrator!")

        # submissions_list : those who submitted orders
        submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
        submitted_list = [o[1] for o in submissions_list]

        # definitives_list : those who agreed to adjudicate with their orders
        definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
        agreed_list = [o[1] for o in definitives_list if o[2]]

        # game is anonymous : you get only information for your own role
        if game.anonymous:
            if role_id is not None and role_id != 0:
                submitted_list = [r for r in submitted_list if r == role_id]
                agreed_list = [r for r in agreed_list if r == role_id]

        # needed list : those who need to submit orders
        actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
        needed_list = [o[1] for o in actives_list]

        del sql_executor

        data = {'submitted': submitted_list, 'agreed': agreed_list, 'needed': needed_list}
        return data, 200


@API.resource('/all-player-games-orders-submitted')
class AllPlayerGamesOrdersSubmittedRessource(flask_restful.Resource):  # type: ignore
    """ AllPlayerGamesOrdersSubmittedRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Dict[int, typing.List[int]]], int]:  # pylint: disable=no-self-use
        """
        Gets list of roles which have submitted orders, orders are missing, orders are not needed for all my games
        EXPOSED
        """

        mylogger.LOGGER.info("/all-player-games-orders-submitted - GET - getting which orders submitted, missing, not needed for all my games")

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

        dict_submitted_list: typing.Dict[int, typing.List[int]] = dict()
        dict_agreed_list: typing.Dict[int, typing.List[int]] = dict()
        dict_needed_list: typing.Dict[int, typing.List[int]] = dict()
        for game_id, _, role_id in allocations_list:

            # submissions_list : those who submitted orders
            submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
            submitted_list = [o[1] for o in submissions_list]

            # definitives_list : those who agreed to adjudicate with their orders
            definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
            agreed_list = [o[1] for o in definitives_list if o[2]]

            # game is anonymous : you get only information for your own role
            game = games.Game.find_by_identifier(sql_executor, game_id)
            assert game is not None
            if game.anonymous:
                if role_id is not None and role_id != 0:
                    submitted_list = [r for r in submitted_list if r == role_id]
                    agreed_list = [r for r in agreed_list if r == role_id]

            dict_submitted_list[game_id] = submitted_list
            dict_agreed_list[game_id] = agreed_list

            # needed list : those who need to submit orders
            actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
            needed_list = [o[1] for o in actives_list]
            dict_needed_list[game_id] = needed_list

        del sql_executor

        data = {'dict_submitted': dict_submitted_list, 'dict_agreed': dict_agreed_list, 'dict_needed': dict_needed_list}
        return data, 200


@API.resource('/all-games-orders-submitted')
class AllGamesOrdersSubmittedRessource(flask_restful.Resource):  # type: ignore
    """ AllGamesOrdersSubmittedRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Dict[int, typing.List[int]]], int]:  # pylint: disable=no-self-use
        """
        Gets list of roles which have submitted orders, orders are missing, orders are not needed for all possible games
        EXPOSED
        """

        mylogger.LOGGER.info("/all-games-orders-submitted - GET - getting which orders submitted, missing, not needed for all possible games")

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

        # TODO improve this with real admin account
        if pseudo != 'Palpatine':
            flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to get all games all players submitted!")

        sql_executor = database.SqlExecutor()

        # get list of all games
        allocations_list = allocations.Allocation.inventory(sql_executor)

        # extract list of all games identifiers
        game_id_list = list(set(a[0] for a in allocations_list))

        dict_submitted_list: typing.Dict[int, typing.List[int]] = dict()
        dict_agreed_list: typing.Dict[int, typing.List[int]] = dict()
        dict_needed_list: typing.Dict[int, typing.List[int]] = dict()
        for game_id in game_id_list:

            # submissions_list : those who submitted orders
            submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
            submitted_list = [o[1] for o in submissions_list]
            dict_submitted_list[game_id] = submitted_list

            # definitives_list : those who agreed to adjudicate with their orders
            definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
            agreed_list = [o[1] for o in definitives_list if o[2]]
            dict_agreed_list[game_id] = agreed_list

            # needed list : those who need to submit orders
            actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
            needed_list = [o[1] for o in actives_list]
            dict_needed_list[game_id] = needed_list

        del sql_executor

        data = {'dict_submitted': dict_submitted_list, 'dict_agreed': dict_agreed_list, 'dict_needed': dict_needed_list}
        return data, 200


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

        # get destinees
        try:
            dest_role_ids = list(map(int, dest_role_ids_submitted.split()))
        except:  # noqa: E722 pylint: disable=bare-except
            del sql_executor
            flask_restful.abort(400, msg="Bad list of addresses identifiers. Use a space separated list of numbers")

        # checks relative to no message
        if game.nomessage:

            # find game master
            assert game is not None
            game_master_id = game.get_role(sql_executor, 0)  # noqa: F821

            # is game master sending or are we sending to game master only ?
            if not (user_id == game_master_id or dest_role_ids == [0]):
                del sql_executor
                flask_restful.abort(403, msg="Only game master may send or receive message in 'no message' game")

        # create message here

        # create a content
        identifier = contents.Content.free_identifier(sql_executor)  # noqa: F821
        time_stamp = int(time.time())  # now
        content = contents.Content(identifier, int(game_id), time_stamp, payload)
        content.update_database(sql_executor)  # noqa: F821

        # create a message linked to the content
        for dest_role_id in dest_role_ids:
            message = messages.Message(int(game_id), role_id, dest_role_id, identifier)
            message.update_database(sql_executor)  # noqa: F821

        nb_addressees = len(dest_role_ids)

        sql_executor.commit()  # noqa: F821
        del sql_executor  # noqa: F821

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

        # checks relative to no press
        if game.nopress:

            # find game master
            assert game is not None
            game_master_id = game.get_role(sql_executor, 0)

            # must be game master
            if user_id != game_master_id:
                del sql_executor
                flask_restful.abort(403, msg="Only game master may declare in a 'no press' game")

        # create declaration here

        # create a content
        identifier = contents.Content.free_identifier(sql_executor)
        time_stamp = int(time.time())  # now
        content = contents.Content(identifier, int(game_id), time_stamp, payload)
        content.update_database(sql_executor)

        # create a declaration linked to the content
        declaration = declarations.Declaration(int(game_id), role_id, anonymous, identifier)
        declaration.update_database(sql_executor)

        sql_executor.commit()
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


@API.resource('/date-last-declarations')
class DateLastDeclarationsRessource(flask_restful.Resource):  # type: ignore
    """  DateLastDeclarationsRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
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

        # get list of games in which player is involved
        allocations_list = allocations.Allocation.list_by_player_id(sql_executor, player_id)

        dict_time_stamp: typing.Dict[int, int] = dict()
        for game_id, _, _ in allocations_list:

            # serves as default value (long time ago)
            time_stamp = 0

            # gather declarations
            declarations_list = declarations.Declaration.list_with_content_by_game_id(sql_executor, game_id)
            for _, _, _, time_stamp_found, _ in declarations_list:
                time_stamp = time_stamp_found
                break

            dict_time_stamp[game_id] = time_stamp

        del sql_executor

        data = {'dict_time_stamp': dict_time_stamp}
        return data, 200


@API.resource('/date-last-game-messages')
class DateLastGameMessagesRessource(flask_restful.Resource):  # type: ignore
    """  DateLastGameMessagesRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
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

        # get list of games in which player is involved
        allocations_list = allocations.Allocation.list_by_player_id(sql_executor, player_id)

        dict_time_stamp: typing.Dict[int, int] = dict()
        for game_id, _, role_id in allocations_list:

            # serves as default value (long time ago)
            time_stamp = 0

            # gather messages
            messages_list = messages.Message.list_with_content_by_game_id(sql_executor, game_id)
            for _, _, _, addressee_num, time_stamp_found, _ in messages_list:

                # must be addressee
                if addressee_num != int(role_id):
                    continue

                time_stamp = time_stamp_found
                break

            dict_time_stamp[game_id] = time_stamp

        del sql_executor

        data = {'dict_time_stamp': dict_time_stamp}
        return data, 200


@API.resource('/game-visits/<game_id>/<visit_type>')
class GameVisitsRessource(flask_restful.Resource):  # type: ignore
    """  GameVisitsRessource """

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

        sql_executor.commit()
        del sql_executor

        data = {'msg': "Ok visit inserted"}
        return data, 201

    def get(self, game_id: int, visit_type: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
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
            flask_restful.abort(403, msg=f"You do not seem play or master game {game_id}")

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

    def get(self, visit_type: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
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

        dict_time_stamp: typing.Dict[int, int] = dict()
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

        sql_executor.commit()
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


@API.resource('/game-incidents/<game_id>')
class GameIncidentsRessource(flask_restful.Resource):  # type: ignore
    """ GameIncidentsRessource """

    def get(self, game_id: int) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[int, int, float]]], int]:  # pylint: disable=no-self-use
        """
        Gets list of roles which have produced an incident for given game
        EXPOSED
        """

        mylogger.LOGGER.info("/game-incidents/<game_id> - GET - getting which incidents occured for game id=%s", game_id)

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

            # TODO improve this with real admin account
            # Admin can still see who passed orders
            if pseudo != 'Palpatine':

                del sql_executor
                flask_restful.abort(403, msg=f"You do not seem to play or master game {game_id} or to be site administrator!")

        # incidents_list : those who submitted orders after deadline
        incidents_list = incidents.Incident.list_by_game_id(sql_executor, game_id)
        late_list = [(o[1], o[2], o[4]) for o in incidents_list]

        # game is anonymous : you get only information for your own role
        if game.anonymous:
            if role_id is not None and role_id != 0:
                late_list = [ll for ll in late_list if ll[0] == role_id]

        del sql_executor

        data = {'incidents': late_list}
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
        sql_executor.commit()
        del sql_executor

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['GAME']['PORT']

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
