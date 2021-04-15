#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import random
import argparse

import waitress
import flask
import flask_cors  # type: ignore
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore
import requests

import mylogger
import lowdata
import populate
import mailer
import players
import newss
import database

SESSION = requests.Session()

APP = flask.Flask(__name__)
flask_cors.CORS(APP)
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
PLAYER_PARSER.add_argument('residence', type=str, required=False)
PLAYER_PARSER.add_argument('nationality', type=str, required=False)
PLAYER_PARSER.add_argument('time_zone', type=str, required=False)

PLAYERS_SELECT_PARSER = flask_restful.reqparse.RequestParser()
PLAYERS_SELECT_PARSER.add_argument('selection', type=str, required=True)

EMAIL_PARSER = flask_restful.reqparse.RequestParser()
EMAIL_PARSER.add_argument('pseudo', type=str, required=True)
EMAIL_PARSER.add_argument('code', type=str, required=True)

SENDMAIL_PARSER = flask_restful.reqparse.RequestParser()
SENDMAIL_PARSER.add_argument('pseudo', type=str, required=True)
SENDMAIL_PARSER.add_argument('addressees', type=str, required=True)
SENDMAIL_PARSER.add_argument('subject', type=str, required=True)
SENDMAIL_PARSER.add_argument('body', type=str, required=True)

NEWS_PARSER = flask_restful.reqparse.RequestParser()
NEWS_PARSER.add_argument('pseudo', type=str, required=True)
NEWS_PARSER.add_argument('content', type=str, required=True)


# to avoid sending emails in debug phase
PREVENT_MAIL_CHECKING = False


@API.resource('/player-identifiers/<pseudo>')
class PlayerIdentifierRessource(flask_restful.Resource):  # type: ignore
    """ PlayerIdentifierRessource """

    def get(self, pseudo: str) -> typing.Tuple[int, int]:  # pylint: disable=no-self-use
        """
        From name get identifier
        EXPOSED
        """

        mylogger.LOGGER.info("/player-identifiers/<pseudo> - GET - retrieving identifier from  player pseudo=%s", pseudo)

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
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

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
            url = f"{host}:{port}/change"
            jwt_token = flask.request.headers.get('AccessToken')
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
        url = f"{host}:{port}/verify"
        jwt_token = flask.request.headers.get('AccessToken')
        if not jwt_token:
            flask_restful.abort(400, msg="Missing authentication!")
        req_result = SESSION.get(url, headers={'Authorization': f"Bearer {jwt_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

        player = players.Player.find_by_pseudo(pseudo)
        if player is None:
            flask_restful.abort(404, msg=f"Player {pseudo} does not exist")

        if args['residence']:
            residence_provided = args['residence']
            if not players.check_country(residence_provided):
                flask_restful.abort(404, msg=f"Residence '{residence_provided}' is not a valid country code")

        if args['nationality']:
            nationality_provided = args['nationality']
            if not players.check_country(nationality_provided):
                flask_restful.abort(404, msg=f"Nationality '{nationality_provided}' is not a valid country code")

        if args['time_zone']:
            timezone_provided = args['time_zone']
            if not players.check_timezone(timezone_provided):
                flask_restful.abort(404, msg=f"Time zone '{timezone_provided}' is not a time zone")

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

            json_dict = {
                'email_value': email_after,
                'code': code
            }

            # store the email/code in secure server
            host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
            port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
            url = f"{host}:{port}/emails"
            req_result = SESSION.post(url, data=json_dict)
            if req_result.status_code != 201:
                mylogger.LOGGER.error("ERROR = %s", req_result.text)
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                flask_restful.abort(400, msg=f"Failed to store email code!:{message}")
            if not PREVENT_MAIL_CHECKING:
                if not mailer.send_mail_checker(code, email_after):
                    flask_restful.abort(400, msg=f"Failed to send email to {email_after}")

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
            flask_restful.abort(404, msg=f"Player {pseudo} doesn't exist")

        assert player is not None
        player_id = player.identifier

        # get all allocations of the player
        host = lowdata.SERVER_CONFIG['GAME']['HOST']
        port = lowdata.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/player-allocations/{player_id}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Allocation check failed!:{message}")
        json_dict = req_result.json()
        allocations_dict = json_dict

        if allocations_dict:
            flask_restful.abort(400, msg="Player is still in a game")

        # delete player from users server (that will implicitly check we have rights)
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/remove"
        jwt_token = flask.request.headers.get('AccessToken')
        req_result = SESSION.post(url, headers={'Authorization': f"Bearer {jwt_token}"}, json={'user_name': pseudo})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"User removal failed!:{message}")

        # delete player from here
        player.delete_database()

        data = {'pseudo': pseudo, 'msg': 'Ok removed'}
        return data, 200


@API.resource('/players')
class PlayerListRessource(flask_restful.Resource):  # type: ignore
    """ PlayerListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Provides list of all pseudo (all players)
        EXPOSED
        """

        mylogger.LOGGER.info("/players - GET - get getting all players only pseudo (email and telephone are confidential)")

        players_list = players.Player.inventory()
        data = {str(p.identifier): {'pseudo': p.pseudo, 'family_name': p.family_name, 'first_name': p.first_name, 'residence': p.residence, 'nationality': p.nationality, 'time_zone': p.time_zone} for p in players_list}

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
            flask_restful.abort(400, msg=f"Player {pseudo} already exists")

        if not pseudo.isidentifier():
            flask_restful.abort(400, msg=f"Pseudo '{pseudo}' is not a valid pseudo")

        if args['residence']:
            residence_provided = args['residence']
            if not players.check_country(residence_provided):
                flask_restful.abort(404, msg=f"Residence '{residence_provided}' is not a valid country code")

        if args['nationality']:
            nationality_provided = args['nationality']
            if not players.check_country(nationality_provided):
                flask_restful.abort(404, msg=f"Nationality '{nationality_provided}' is not a valid country code")

        if args['time_zone']:
            timezone_provided = args['time_zone']
            if not players.check_timezone(timezone_provided):
                flask_restful.abort(404, msg=f"Time zone '{timezone_provided}' is not a time zone")

        # create player on users server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/add"
        req_result = SESSION.post(url, json={'user_name': pseudo, 'password': args['password']})
        if req_result.status_code != 201:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"User creation failed!:{message}")

        # create player here
        identifier = players.Player.free_identifier()
        player = players.Player(identifier, '', '', False, '', False, '', '', '', '', '')
        _ = player.load_json(args)
        player.update_database()

        # send email confirmation
        email_after = player.email
        code = random.randint(1000, 9999)

        json_dict = {
            'email_value': email_after,
            'code': code
        }

        # store the email/code in secure server
        host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
        port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/emails"
        req_result = SESSION.post(url, data=json_dict)
        if req_result.status_code != 201:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Failed to store email code!:{message}")
        if not PREVENT_MAIL_CHECKING:
            if not mailer.send_mail_checker(code, email_after):
                flask_restful.abort(400, msg=f"Failed to send email to {email_after}")

        data = {'pseudo': pseudo, 'msg': 'Ok player created'}
        return data, 201


@API.resource('/players-select')
class PlayerSelectListRessource(flask_restful.Resource):  # type: ignore
    """ PlayerSelectListRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Provides list of some pseudo ( selected by identifier)
        Should be a get but has parameters
        parameter is a space separated string of ints
        EXPOSED
        """

        args = PLAYERS_SELECT_PARSER.parse_args(strict=True)
        selection_submitted = args['selection']
        try:
            selection_list = list(map(int, selection_submitted.split()))
        except:
            flask_restful.abort(400, msg=f"Bad selection. Use a space separated list of numbers")

        mylogger.LOGGER.info("/players-select - POST - get getting some players only pseudo (email and telephone are confidential)")

        players_list = players.Player.inventory()
        data = {str(p.identifier): {'pseudo': p.pseudo, 'family_name': p.family_name, 'first_name': p.first_name, 'residence': p.residence, 'nationality': p.nationality, 'time_zone': p.time_zone} for p in players_list if p.identifier in selection_list}

        return data, 200


@API.resource('/mail-players')
class MailPlayersListRessource(flask_restful.Resource):  # type: ignore
    """ MailPlayersListRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Sends an email to a list of players
        EXPOSED
        """

        mylogger.LOGGER.info("/mail-players - POST - sending emails to a list of players")

        args = SENDMAIL_PARSER.parse_args(strict=True)
        pseudo = args['pseudo']

        mylogger.LOGGER.info("pseudo=%s", pseudo)

        # check from user server user is pseudo
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
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

        subject = args['subject']
        body = args['body']
        addressees_submitted = args['addressees']

        try:
            addressees_list = list(map(int, addressees_submitted.split()))
        except:
            flask_restful.abort(400, msg=f"Bad addressees. Use a space separated list of numbers")

        recipients: typing.List[str] = list()
        for addressee_id in addressees_list:
            pseudo_dest = players.Player.find_by_identifier(addressee_id)
            if pseudo_dest is None:
                flask_restful.abort(404, msg=f"Failed to find pseudo with id={addressee_id}")
            assert pseudo_dest is not None
            pseudo_dest_email = pseudo_dest.email
            recipients.append(pseudo_dest_email)

        status = mailer.send_mail(subject, body, recipients)
        if not status:
            flask_restful.abort(400, msg="Failed to send!")

        data = {'msg': 'Ok emails sent'}
        return data, 200


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

        json_dict = {
            'email_value': email_player,
            'code': code
        }

        # check code from user server
        host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
        port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/check-email"
        req_result = SESSION.post(url, data=json_dict)
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Wrong code!:{message}")

        player.email_confirmed = True
        player.update_database()

        data = {'pseudo': pseudo, 'msg': 'Ok code is correct'}
        return data, 200


@API.resource('/news')
class NewsRessource(flask_restful.Resource):  # type: ignore
    """ NewsRessource """

    def get(self) -> typing.Tuple[typing.Any, int]:  # pylint: disable=no-self-use
        """
        Provides the latest news
        EXPOSED
        """

        mylogger.LOGGER.info("/news - GET - get the latest news")

        news_content = newss.News.content()
        data = news_content

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Creates a new news
        EXPOSED
        """

        mylogger.LOGGER.info("/news - POST - changing the news")

        args = NEWS_PARSER.parse_args(strict=True)
        pseudo = args['pseudo']

        # check from user server user is pseudo
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
            flask_restful.abort(400, msg=f"Bad authentication!:{message}")
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

        player = players.Player.find_by_pseudo(pseudo)
        if player is None:
            flask_restful.abort(404, msg=f"Player {pseudo} does not exist")

        # TODO improve this with real admin account
        if pseudo != 'Palpatine':
            flask_restful.abort(403, msg="You are not allowed to change news!")

        content = args['content']

        # create news here
        news = newss.News(content)
        news.update_database()

        data = {'msg': 'Ok news created'}
        return data, 201


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', required=False, help='mode debug to test stuff', action='store_true')
    args = parser.parse_args()

    mylogger.start_logger(__name__)
    lowdata.load_servers_config()
    mailer.load_mail_config(APP)

    # emergency
    if not database.db_present():
        mylogger.LOGGER.info("Emergency populate procedure")
        populate.populate()

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
