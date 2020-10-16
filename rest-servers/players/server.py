#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import random

import flask
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore
import requests

import mylogger
import lowdata
import populate
import mailer
import players
import database

SESSION = requests.Session()

APP = flask.Flask(__name__)
API = flask_restful.Api(APP)

PLAYER_PARSER = flask_restful.reqparse.RequestParser()
PLAYER_PARSER.add_argument('pseudo', type=str, required=True)
PLAYER_PARSER.add_argument('password', type=str, required=False)
PLAYER_PARSER.add_argument('email', type=str, required=False)
PLAYER_PARSER.add_argument('email_confirmed', type=str, required=False)
PLAYER_PARSER.add_argument('telephone', type=str, required=False)
PLAYER_PARSER.add_argument('replace', type=str, required=False)
PLAYER_PARSER.add_argument('first_name', type=str, required=False)
PLAYER_PARSER.add_argument('family_name', type=str, required=False)
PLAYER_PARSER.add_argument('country', type=str, required=False)
PLAYER_PARSER.add_argument('time_zone', type=str, required=False)

EMAIL_PARSER = flask_restful.reqparse.RequestParser()
EMAIL_PARSER.add_argument('pseudo', type=str, required=True)
EMAIL_PARSER.add_argument('code', type=str, required=True)

# to avoid sending emails in debug phase
PREVENT_MAIL_CHECKING = True


@API.resource('/player_identifiers/<pseudo>')
class PlayerIdentifierRessource(flask_restful.Resource):  # type: ignore
    """ PlayerIdentifierRessource """

    def get(self, pseudo: str) -> typing.Tuple[int, int]:  # pylint: disable=no-self-use
        """
        From name get identifier
        EXPOSED
        """

        mylogger.LOGGER.info("/player_identifiers/<pseudo> - GET - retrieving identifier from  player pseudo=%s", pseudo)

        # find data
        player = players.Player.find_by_pseudo(pseudo)
        if player is None:
            flask_restful.abort(404, msg=f"Player {player} doesn't exist")

        assert player is not None
        return player.identifier, 200


@API.resource('/players/<pseudo>')
class PlayerRessource(flask_restful.Resource):  # type: ignore
    """ PlayerRessource """

    def get(self, pseudo: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Gets all info about a player
        EXPOSED
        """

        mylogger.LOGGER.info("/players/<pseudo> - GET - retrieving one player pseudo=%s", pseudo)

        # IMPORTANT : check from user server user is pseudo
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify-user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Not allowed for retrieve!:{message}")

        # find data
        player = players.Player.find_by_pseudo(pseudo)
        if player is None:
            flask_restful.abort(404, msg=f"Player {pseudo} doesn't exist")

        assert player is not None
        data = player.save_json()
        return data, 200

    def put(self, pseudo: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Updates all info about a player
        EXPOSED
        """

        args = PLAYER_PARSER.parse_args(strict=True)

        mylogger.LOGGER.info("/players/<pseudo> - PUT - updating a player pseudo=%s", pseudo)

        # update player on users server if there is a password
        if args['password']:
            mylogger.LOGGER.info("Special :  updating a password")
            host = lowdata.SERVER_CONFIG['USER']['HOST']
            port = lowdata.SERVER_CONFIG['USER']['PORT']
            url = f"{host}:{port}/change-user"
            jwt_token = flask.request.headers.get('access_token')
            req_result = SESSION.post(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo, 'password': args['password']})
            if req_result.status_code != 201:
                mylogger.LOGGER.error("ERROR = %s", req_result.text)
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                flask_restful.abort(400, msg=f"User modification failed!:{message}")
            data = {'pseudo': pseudo, 'msg': 'Ok updated'}
            return data, 200

        # check from user server user is pseudo
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify-user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Not allowed for update!:{message}")

        player = players.Player.find_by_pseudo(pseudo)
        if player is None:
            flask_restful.abort(404, msg=f"Player {pseudo} does not exist")

        assert player is not None
        email_before = player.email
        changed = player.load_json(args)
        if not changed:
            data = {'pseudo': pseudo, 'msg': 'Ok but no change !'}
            return data, 200

        email_after = player.email
        if email_after != email_before:

            player.email_confirmed = False
            code = random.randint(1000, 9999)

            # store the email/code in secure server
            host = lowdata.SERVER_CONFIG['USER']['HOST']
            port = lowdata.SERVER_CONFIG['USER']['PORT']
            url = f"{host}:{port}/add-email"
            req_result = SESSION.post(url, json={'email_value': email_after, 'code': code})
            if req_result.status_code != 200:
                mylogger.LOGGER.error("ERROR = %s", req_result.text)
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                flask_restful.abort(400, msg=f"Failed to store email code!:{message}")
            if not PREVENT_MAIL_CHECKING:
                mailer.send_mail_checker(code, email_after)

        player.update_database()
        data = {'pseudo': pseudo, 'msg': 'Ok updated'}
        return data, 200

    def delete(self, pseudo: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Deletes a player
        EXPOSED
        """

        mylogger.LOGGER.info("/players/<pseudo> - DELETE - removing one player pseudo=%s", pseudo)

        player = players.Player.find_by_pseudo(pseudo)
        if player is None:
            flask_restful.abort(204, msg=f"Player {pseudo} doesn't exist")

        assert player is not None
        player_id = player.identifier

        # get all allocations of the player
        host = lowdata.SERVER_CONFIG['GAME']['HOST']
        port = lowdata.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations-players/{player_id}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"User removal failed!:{message}")
        json_dict = req_result.json()
        allocations_dict = json_dict

        if allocations_dict:
            flask_restful.abort(400, msg="Utilisateur encore dans une partie")

        # delete player from users server (that will implicitly check we have rights)
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/remove'user"
        jwt_token = flask.request.headers.get('access_token')
        req_result = SESSION.post(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"User removal failed!:{message}")

        # delete player from here
        player.delete_database()

        return {}, 200


@API.resource('/players')
class PlayerListRessource(flask_restful.Resource):  # type: ignore
    """ PlayerListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Provides list of all pseudo (all players)
        EXPOSED
        """

        mylogger.LOGGER.info("/players - GET - get getting all players only pseudo (rest is confidential)")

        players_list = players.Player.inventory()
        data = {str(p.identifier): p.pseudo for p in players_list}

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Creates a new player
        EXPOSED
        """

        mylogger.LOGGER.info("/players - POST - creating new player")

        args = PLAYER_PARSER.parse_args(strict=True)
        pseudo = args['pseudo']

        mylogger.LOGGER.info("pseudo=%s", pseudo)

        player = players.Player.find_by_pseudo(pseudo)
        if player is not None:
            flask_restful.abort(404, msg=f"Player {pseudo} already exists")

        # create player on users server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/add-user"
        req_result = SESSION.post(url, json={'user_name': pseudo, 'password': args['password']})
        if req_result.status_code != 201:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"User creation failed!:{message}")

        # create player here
        identifier = players.Player.free_identifier()
        player = players.Player(identifier, '', '', False, '', False, '', '', '', '')
        _ = player.load_json(args)
        player.update_database()

        # send email confirmation
        email_after = player.email
        code = random.randint(1000, 9999)

        # store the email/code in secure server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/add-email"
        req_result = SESSION.post(url, json={'email_value': email_after, 'code': code})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Failed to store email code!:{message}")
        if not PREVENT_MAIL_CHECKING:
            mailer.send_mail_checker(code, email_after)

        data = {'pseudo': pseudo, 'msg': 'Ok player created'}
        return data, 201


@API.resource('/emails')
class EmailRessource(flask_restful.Resource):  # type: ignore
    """ EmailRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Checks a couple pseudo/code for email in database
        EXPOSED
        """

        mylogger.LOGGER.info("/emails - POST - checking pseudo/code")

        args = EMAIL_PARSER.parse_args(strict=True)
        pseudo = args['pseudo']

        mylogger.LOGGER.info("pseudo=%s", pseudo)

        player = players.Player.find_by_pseudo(pseudo)
        if player is None:
            flask_restful.abort(404, msg=f"Player {pseudo} does not exist")

        assert player is not None
        email_player = player.email

        code = args['code']

        # check code from user server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/verify-email"
        req_result = SESSION.get(url, json={'email_value': email_player, 'code': code})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Wrong code!:{message}")

        player.email_confirmed = True
        player.update_database()

        return {}, 200


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
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    APP.run(debug=True, port=port)


if __name__ == '__main__':
    main()
