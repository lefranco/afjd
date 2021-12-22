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
import moderators
import database


SESSION = requests.Session()

APP = flask.Flask(__name__)
flask_cors.CORS(APP)
API = flask_restful.Api(APP)

PLAYER_PARSER = flask_restful.reqparse.RequestParser()
PLAYER_PARSER.add_argument('pseudo', type=str, required=True)
PLAYER_PARSER.add_argument('password', type=str, required=False)
PLAYER_PARSER.add_argument('email', type=str, required=False)
PLAYER_PARSER.add_argument('email_confirmed', type=int, required=False)
PLAYER_PARSER.add_argument('telephone', type=str, required=False)
PLAYER_PARSER.add_argument('notify', type=int, required=False)
PLAYER_PARSER.add_argument('replace', type=int, required=False)
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
SENDMAIL_PARSER.add_argument('force', type=int, required=True)

NEWS_PARSER = flask_restful.reqparse.RequestParser()
NEWS_PARSER.add_argument('pseudo', type=str, required=True)
NEWS_PARSER.add_argument('content', type=str, required=True)

MODERATOR_PARSER = flask_restful.reqparse.RequestParser()
MODERATOR_PARSER.add_argument('player_pseudo', type=str, required=True)
MODERATOR_PARSER.add_argument('delete', type=int, required=True)

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
        sql_executor = database.SqlExecutor()
        player = players.Player.find_by_pseudo(sql_executor, pseudo)
        del sql_executor

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
        sql_executor = database.SqlExecutor()
        player = players.Player.find_by_pseudo(sql_executor, pseudo)
        del sql_executor

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

        sql_executor = database.SqlExecutor()

        player = players.Player.find_by_pseudo(sql_executor, pseudo)

        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} does not exist")

        if args['residence']:
            residence_provided = args['residence']
            if not players.check_country(residence_provided):
                del sql_executor
                flask_restful.abort(404, msg=f"Residence '{residence_provided}' is not a valid country code")

        if args['nationality']:
            nationality_provided = args['nationality']
            if not players.check_country(nationality_provided):
                del sql_executor
                flask_restful.abort(404, msg=f"Nationality '{nationality_provided}' is not a valid country code")

        if args['time_zone']:
            timezone_provided = args['time_zone']
            if not players.check_timezone(timezone_provided):
                del sql_executor
                flask_restful.abort(404, msg=f"Time zone '{timezone_provided}' is not a time zone")

        assert player is not None
        email_before = player.email
        changed = player.load_json(args)
        if not changed:

            del sql_executor

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
                del sql_executor
                flask_restful.abort(400, msg=f"Failed to store email code!:{message}")
            if not PREVENT_MAIL_CHECKING:
                if not mailer.send_mail_checker(code, email_after):
                    del sql_executor
                    flask_restful.abort(400, msg=f"Failed to send email to {email_after}")

        player.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'pseudo': pseudo, 'msg': 'Ok updated'}
        return data, 200

    def delete(self, pseudo: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Deletes a player
        EXPOSED
        """

        mylogger.LOGGER.info("/players/<pseudo> - DELETE - removing one player pseudo=%s", pseudo)

        sql_executor = database.SqlExecutor()

        player = players.Player.find_by_pseudo(sql_executor, pseudo)

        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} doesn't exist")

        assert player is not None
        player_id = player.identifier

        # get all allocations of the player
        host = lowdata.SERVER_CONFIG['GAME']['HOST']
        port = lowdata.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/player-allocations/{player_id}"
        jwt_token = flask.request.headers.get('AccessToken')
        req_result = SESSION.get(url, headers={'AccessToken': f"{jwt_token}"})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(400, msg=f"Allocation check failed!:{message}")
        json_dict = req_result.json()
        allocations_dict = json_dict

        if allocations_dict:
            del sql_executor
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
            del sql_executor
            flask_restful.abort(400, msg=f"User removal failed!:{message}")

        # delete player from here
        player.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

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

        sql_executor = database.SqlExecutor()
        players_list = players.Player.inventory(sql_executor)
        del sql_executor

        data = {str(p.identifier): {'pseudo': p.pseudo, 'family_name': p.family_name, 'first_name': p.first_name, 'residence': p.residence, 'nationality': p.nationality, 'time_zone': p.time_zone, 'email_confirmed': p.email_confirmed, 'replace': p.replace} for p in players_list}

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

        sql_executor = database.SqlExecutor()

        player = players.Player.find_by_pseudo(sql_executor, pseudo)

        if player is not None:
            del sql_executor
            flask_restful.abort(400, msg=f"Player {pseudo} already exists")

        if not pseudo.isidentifier():
            del sql_executor
            flask_restful.abort(400, msg=f"Pseudo '{pseudo}' is not a valid pseudo")

        # cannot have a void residence
        if args['residence']:
            residence_provided = args['residence']
            if not players.check_country(residence_provided):
                del sql_executor
                flask_restful.abort(404, msg=f"Residence '{residence_provided}' is not a valid country code")
        else:
            args['residence'] = players.default_country()

        # cannot have a void nationality
        if args['nationality']:
            nationality_provided = args['nationality']
            if not players.check_country(nationality_provided):
                del sql_executor
                flask_restful.abort(404, msg=f"Nationality '{nationality_provided}' is not a valid country code")
        else:
            args['nationality'] = players.default_country()

        # cannot have a void timezone
        if args['time_zone']:
            timezone_provided = args['time_zone']
            if not players.check_timezone(timezone_provided):
                del sql_executor
                flask_restful.abort(404, msg=f"Time zone '{timezone_provided}' is not a time zone")
        else:
            args['time_zone'] = players.default_timezone()

        # create player here
        identifier = players.Player.free_identifier(sql_executor)

        player = players.Player(identifier, '', '', False, '', False, False, '', '', '', '', '')
        _ = player.load_json(args)

        player.update_database(sql_executor)

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
            del sql_executor
            flask_restful.abort(400, msg=f"Failed to store email code!:{message}")
        if not PREVENT_MAIL_CHECKING:
            if not mailer.send_mail_checker(code, email_after):
                del sql_executor
                flask_restful.abort(400, msg=f"Failed to send email to {email_after}")

        # create player on users server
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/add"
        req_result = SESSION.post(url, json={'user_name': pseudo, 'password': args['password']})
        if req_result.status_code != 201:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(400, msg=f"User creation failed!:{message}")

        sql_executor.commit()
        del sql_executor

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
        except:  # noqa: E722 pylint: disable=bare-except
            flask_restful.abort(400, msg="Bad selection. Use a space separated list of numbers")

        mylogger.LOGGER.info("/players-select - POST - get getting some players only pseudo (email and telephone are confidential)")

        sql_executor = database.SqlExecutor()
        players_list = players.Player.inventory(sql_executor)
        del sql_executor

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
        force = args['force']

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
        except:  # noqa: E722 pylint: disable=bare-except
            flask_restful.abort(400, msg="Bad addressees. Use a space separated list of numbers")

        sql_executor = database.SqlExecutor()

        addressees: typing.List[str] = list()
        for addressee_id in addressees_list:
            pseudo_dest = players.Player.find_by_identifier(sql_executor, addressee_id)
            if pseudo_dest is None:
                del sql_executor
                flask_restful.abort(404, msg=f"Failed to find pseudo with id={addressee_id}")
            assert pseudo_dest is not None
            # does not want to receive notifications
            if not pseudo_dest.notify:
                # however force parameters makes them be still sent
                if not force:
                    continue
            pseudo_dest_email = pseudo_dest.email
            addressees.append(pseudo_dest_email)

        # can happen that nobody is actually interested
        if addressees:
            status = mailer.send_mail(subject, body, addressees)
            if not status:
                del sql_executor
                flask_restful.abort(400, msg="Failed to send at least one message")

        del sql_executor

        nb_mails = len(addressees)
        data = {'msg': f"Ok {nb_mails} email(s) successfully sent"}
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

        sql_executor = database.SqlExecutor()

        player = players.Player.find_by_pseudo(sql_executor, pseudo)

        if player is None:
            del sql_executor
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
            del sql_executor
            flask_restful.abort(400, msg=f"Wrong code!:{message}")

        player.email_confirmed = True

        player.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

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

        sql_executor = database.SqlExecutor()
        news_content = newss.News.content(sql_executor)
        del sql_executor

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

        sql_executor = database.SqlExecutor()

        player = players.Player.find_by_pseudo(sql_executor, pseudo)

        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} does not exist")

        # TODO improve this with real admin account
        if pseudo != 'Palpatine':
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to change news!")

        content = args['content']

        # create news here
        news = newss.News(content)
        news.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok news created'}
        return data, 201


@API.resource('/player-telephone/<pseudo>')
class PlayerTelephoneRessource(flask_restful.Resource):  # type: ignore
    """ PlayerTelephoneRessource """

    def get(self, pseudo: str) -> typing.Tuple[typing.Dict[str, str], int]:  # pylint: disable=no-self-use
        """
        Provides the phone number of a player
        EXPOSED
        """

        mylogger.LOGGER.info("/player-telephone - GET - get the phone number of player pseudo=%s", pseudo)

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
        pseudo_requester = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        requester = players.Player.find_by_pseudo(sql_executor, pseudo_requester)

        if requester is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Requesting player {pseudo_requester} does not exist")

        # TODO improve this with real admin account
        if pseudo_requester != 'Palpatine':
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to get phone number!")

        contact = players.Player.find_by_pseudo(sql_executor, pseudo)

        if contact is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Contact player {pseudo} does not exist")

        del sql_executor

        assert contact is not None
        telephone = contact.telephone

        data = {'telephone': telephone}
        return data, 200


@API.resource('/player-email/<pseudo>')
class PlayerEmailRessource(flask_restful.Resource):  # type: ignore
    """ PlayerEmailRessource """

    def get(self, pseudo: str) -> typing.Tuple[typing.Dict[str, str], int]:  # pylint: disable=no-self-use
        """
        Provides the email address of a player
        EXPOSED
        """

        mylogger.LOGGER.info("/player-email - GET - get the email address of player pseudo=%s", pseudo)

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
        pseudo_requester = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        requester = players.Player.find_by_pseudo(sql_executor, pseudo_requester)

        if requester is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Requesting player {pseudo_requester} does not exist")

        # TODO improve this with real admin account
        if pseudo_requester != 'Palpatine':
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to get email address!")

        contact = players.Player.find_by_pseudo(sql_executor, pseudo)

        if contact is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Contact player {pseudo} does not exist")

        del sql_executor

        assert contact is not None
        email = contact.email

        data = {'email': email}
        return data, 200


@API.resource('/find-player-from-email/<email>')
class FindPlayerFromEmailRessource(flask_restful.Resource):  # type: ignore
    """ FindPlayerFromEmailRessource """

    def get(self, email: str) -> typing.Tuple[typing.Dict[str, str], int]:  # pylint: disable=no-self-use
        """
        Provides the pseudo from the email address
        EXPOSED
        """

        mylogger.LOGGER.info("/find-player-from-email - GET - get the pseudo from the email address=%s", email)

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
        pseudo_requester = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        requester = players.Player.find_by_pseudo(sql_executor, pseudo_requester)

        if requester is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Requesting player {pseudo_requester} does not exist")

        # TODO improve this with real admin account
        if pseudo_requester != 'Palpatine':
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to get pseudo from email address!")

        email2pseudo = {p.email: p.pseudo for p in players.Player.inventory(sql_executor)}

        if email not in email2pseudo:
            del sql_executor
            flask_restful.abort(404, msg=f"No player with email {email} found")

        del sql_executor

        pseudo = email2pseudo[email]

        data = {'pseudo': pseudo}
        return data, 200


@API.resource('/moderators')
class ModeratorListRessource(flask_restful.Resource):  # type: ignore
    """ ModeratorListRessource """

    def get(self) -> typing.Tuple[typing.List[str], int]:  # pylint: disable=no-self-use
        """
        Provides list of all moderators
        EXPOSED
        """

        mylogger.LOGGER.info("/moderators - GET - get getting all moderators")

        sql_executor = database.SqlExecutor()
        moderators_list = moderators.Moderator.inventory(sql_executor)
        del sql_executor

        data = [m[0] for m in moderators_list]

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Creates/Deletes a moderator
        EXPOSED
        """

        mylogger.LOGGER.info("/moderators - POST - creating/deleting new moderator")

        args = MODERATOR_PARSER.parse_args(strict=True)
        player_pseudo = args['player_pseudo']
        delete = args['delete']

        mylogger.LOGGER.info("player_pseudo=%s delete=%s", player_pseudo, delete)

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

        # check user has right to add/remove moderator (admin)

        # TODO improve this with real admin account
        if pseudo != 'Palpatine':
            flask_restful.abort(403, msg="You are not allowed to add/remove moderator!")

        sql_executor = database.SqlExecutor()

        player = players.Player.find_by_pseudo(sql_executor, player_pseudo)

        if player is None:
            del sql_executor
            flask_restful.abort(400, msg=f"Player {player_pseudo} does not exist")

        if not delete:
            moderator = moderators.Moderator(player_pseudo)
            moderator.update_database(sql_executor)

            sql_executor.commit()
            del sql_executor

            data = {'msg': 'Ok moderator updated or created'}
            return data, 201

        moderator = moderators.Moderator(player_pseudo)
        moderator.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok moderator deleted if present'}
        return data, 200


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

        sql_executor = database.SqlExecutor()
        populate.populate(sql_executor)
        sql_executor.commit()
        del sql_executor

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
