#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import random
import json
import time
import sys
import threading

import waitress
import flask
import flask_cors
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore
import requests

import mylogger
import lowdata
import populate
import players
import newss
import moderators
import blacklisteds
import creators
import ratings
import ratings2
import ratings3
import teasers
import events
import registrations
import timezones
import addresses
import submissions
import emails
import site_image
import database
import contents
import messages


SESSION = requests.Session()

APP = flask.Flask(__name__)
flask_cors.CORS(APP)
API = flask_restful.Api(APP)

PLAYER_PARSER = flask_restful.reqparse.RequestParser()
PLAYER_PARSER.add_argument('pseudo', type=str, required=True)
PLAYER_PARSER.add_argument('password', type=str, required=False)
PLAYER_PARSER.add_argument('email', type=str, required=False)
PLAYER_PARSER.add_argument('email_status', type=int, required=False)
PLAYER_PARSER.add_argument('notify_deadline', type=int, required=False)
PLAYER_PARSER.add_argument('notify_adjudication', type=int, required=False)
PLAYER_PARSER.add_argument('notify_message', type=int, required=False)
PLAYER_PARSER.add_argument('notify_replace', type=int, required=False)
PLAYER_PARSER.add_argument('newsletter', type=int, required=False)
PLAYER_PARSER.add_argument('first_name', type=str, required=False)
PLAYER_PARSER.add_argument('family_name', type=str, required=False)
PLAYER_PARSER.add_argument('residence', type=str, required=False)
PLAYER_PARSER.add_argument('nationality', type=str, required=False)

PLAYERS_SELECT_PARSER = flask_restful.reqparse.RequestParser()
PLAYERS_SELECT_PARSER.add_argument('selection', type=str, required=True)

CHECK_EMAIL_PARSER = flask_restful.reqparse.RequestParser()
CHECK_EMAIL_PARSER.add_argument('pseudo', type=str, required=True)
CHECK_EMAIL_PARSER.add_argument('code', type=int, required=True)

SEND_PLAYERS_EMAIL_PARSER = flask_restful.reqparse.RequestParser()
SEND_PLAYERS_EMAIL_PARSER.add_argument('addressees', type=str, required=True)
SEND_PLAYERS_EMAIL_PARSER.add_argument('subject', type=str, required=True)
SEND_PLAYERS_EMAIL_PARSER.add_argument('body', type=str, required=True)
SEND_PLAYERS_EMAIL_PARSER.add_argument('type', type=str, required=True)

NEWS_PARSER = flask_restful.reqparse.RequestParser()
NEWS_PARSER.add_argument('topic', type=str, required=True)
NEWS_PARSER.add_argument('content', type=str, required=True)

MODERATOR_PARSER = flask_restful.reqparse.RequestParser()
MODERATOR_PARSER.add_argument('player_pseudo', type=str, required=True)
MODERATOR_PARSER.add_argument('delete', type=int, required=True)

CREATOR_PARSER = flask_restful.reqparse.RequestParser()
CREATOR_PARSER.add_argument('player_pseudo', type=str, required=True)
CREATOR_PARSER.add_argument('delete', type=int, required=True)

ELO_UPDATE_PARSER = flask_restful.reqparse.RequestParser()
ELO_UPDATE_PARSER.add_argument('elo_list', type=str, required=True)
ELO_UPDATE_PARSER.add_argument('teaser', type=str, required=True)

REGULARITY_UPDATE_PARSER = flask_restful.reqparse.RequestParser()
REGULARITY_UPDATE_PARSER.add_argument('regularity_list', type=str, required=True)

RELIABILITY_UPDATE_PARSER = flask_restful.reqparse.RequestParser()
RELIABILITY_UPDATE_PARSER.add_argument('reliability_list', type=str, required=True)

EVENT_PARSER = flask_restful.reqparse.RequestParser()
EVENT_PARSER.add_argument('name', type=str, required=False)
EVENT_PARSER.add_argument('start_date', type=str, required=False)
EVENT_PARSER.add_argument('start_hour', type=str, required=False)
EVENT_PARSER.add_argument('end_date', type=str, required=False)
EVENT_PARSER.add_argument('location', type=str, required=False)
EVENT_PARSER.add_argument('external', type=str, required=False)
EVENT_PARSER.add_argument('description', type=str, required=False)
EVENT_PARSER.add_argument('summary', type=str, required=False)

SITE_IMAGE_PARSER = flask_restful.reqparse.RequestParser()
SITE_IMAGE_PARSER.add_argument('legend', type=str, required=True)
SITE_IMAGE_PARSER.add_argument('image', type=str, required=True)

EVENT_PARSER2 = flask_restful.reqparse.RequestParser()
EVENT_PARSER2.add_argument('manager_id', type=int, required=True)

REGISTRATION_PARSER = flask_restful.reqparse.RequestParser()
REGISTRATION_PARSER.add_argument('delete', type=int, required=True)
REGISTRATION_PARSER.add_argument('comment', type=str, required=True)

REGISTRATION_UPDATE_PARSER = flask_restful.reqparse.RequestParser()
REGISTRATION_UPDATE_PARSER.add_argument('player_id', type=int, required=True)
REGISTRATION_UPDATE_PARSER.add_argument('value', type=int, required=True)

DATA_SUBMISSION_PARSER = flask_restful.reqparse.RequestParser()
DATA_SUBMISSION_PARSER.add_argument('time_zone', type=str, required=True)
DATA_SUBMISSION_PARSER.add_argument('ip_address', type=str, required=True)

RESCUE_PLAYER_PARSER = flask_restful.reqparse.RequestParser()
RESCUE_PLAYER_PARSER.add_argument('rescued_user', type=str, required=True)
RESCUE_PLAYER_PARSER.add_argument('access_token', type=str, required=True)

MESSAGE_PARSER = flask_restful.reqparse.RequestParser()
MESSAGE_PARSER.add_argument('dest_user_id', type=int, required=True)
MESSAGE_PARSER.add_argument('content', type=str, required=True)

REMOVE_MESSAGE_PARSER = flask_restful.reqparse.RequestParser()
REMOVE_MESSAGE_PARSER.add_argument('message_id', type=int, required=True)

# pseudo must be at least that size
LEN_PSEUDO_MIN = 3

# event name must be at most that size
LEN_EVENT_MAX = 50

# max size in bytes of image (after b64)
# let 's say one Mo
MAX_SIZE_IMAGE = (4 / 3) * 1000000

# allow to remove old messages
TIMEOUT_REMOVE_MESSAGE_DAYS = 30

# account allowed to update ratings
COMMUTER_ACCOUNT = "TheCommuter"

# to avoid repeat messages/declarations
NO_REPEAT_DELAY_SEC = 15

# how many days after which account may be suppressed if nothing happens on it
# eighteen months
IDLE_DAY_TIMEOUT = 18 * 30.5

# admin id
ADDRESS_ADMIN = 1


class RepeatPreventer(typing.Dict[int, float]):
    """ Table """

    def can(self, user_id: int) -> bool:
        """ can """

        if user_id not in self:
            return True

        now = time.time()
        return now > self[user_id] + NO_REPEAT_DELAY_SEC

    def did(self, user_id: int) -> None:
        """ did """

        # do it
        now = time.time()
        self[user_id] = now

        # house clean
        obsoletes = [k for (k, v) in self.items() if v < now - NO_REPEAT_DELAY_SEC]
        for key in obsoletes:
            del self[key]


def email_rescue_message(pseudo: str, access_token: str) -> typing.Tuple[str, str]:
    """ email_rescue_message """

    url = f"https://diplomania-gen.fr?rescue=1&pseudo={pseudo}&token={access_token}"

    subject = "Ceci est un courriel pour récupérer l'accès à votre compte dont vous avez oublié le mot de passe !"
    body = "Bonjour !\n"
    body += "\n"
    body += f"Vous recevez ce courriel pour recupérer votre compte avec le pseudo {pseudo}."
    body += "\n"
    body += "Cliquez sur le lien ci-dessous :"
    body += "\n"
    body += url
    body += "\n"
    body += "Si vous n'êtes pas à l'origine de sa création, ignorez le (déclarez un incident si cela se répète)"
    body += "\n"
    return subject, body


def email_greeting_message(pseudo: str, code: int) -> typing.Tuple[str, str]:
    """ email_greeting_message """

    subject = "Ceci est un courriel de bienvenue sur le site !"
    body = "Bonjour !\n"
    body += "\n"
    body += f"Vous recevez cet courriel parce que vous avez créé le compte avec le pseudo {pseudo}."
    body += "\n"
    body += f"Si vous êtes bien à l'origine de sa création, rendez-vous dans le menu mon compte/valider mon mail et entrez le code {code}"
    body += "\n"
    body += "Merci et bienvenue sur le site."
    body += "\n"
    return subject, body


def email_checker_message(code: int) -> typing.Tuple[str, str]:
    """ email_checker_message """

    subject = "Ceci est un courriel pour vérifier votre adresse courriel !"
    body = "Bonjour !\n"
    body += "\n"
    body += "Vous recevez ce courriel pour valider votre compte."
    body += "\n"
    body += f"Si vous êtes bien à l'origine de sa création, rendez-vous dans le menu mon compte/valider mon mail et entrez le code {code}"
    body += "\n"
    body += "Merci et bonnes parties."
    body += "\n"
    return subject, body


def suppress_account_message(pseudo: str) -> typing.Tuple[str, str]:
    """ suppress_account_message """

    subject = f"Message de suppression de compte {pseudo} sur le site https://diplomania-gen.fr (AFJD)"
    body = "Bonjour !\n"
    body += "\n"
    body += "Ton compte sur le site a été supprimé !"
    body += "\n"
    body += "\n"

    # in case admin is acting
    body += "Cas particulier : si tu n'es pas à l'origine de cette suppression mais l'administrateur, le message ci-dessous t'est adressé :"
    body += "\n"
    body += " ================="
    body += "\n"
    body += f"Tu as créé un compte sur Diplomania.fr mais tu ne t'es pas connecté depuis très longtemps ({IDLE_DAY_TIMEOUT / 30.5} mois)."
    body += "\n"
    body += "Tu t'es inscrit dans des parties mais tu ne les as pas jouées, créant ainsi une forte frustration chez les autres joueurs."
    body += "\n"
    body += "Plusieurs comptes se ressemblent et ont le même courriel, dont le tien."
    body += "\n"
    body += "Bref, nous avons donc dû supprimer ton compte. Nous ne pouvons conserver pléthore de comptes inutiles."
    body += "\n"
    body += "Bien sûr, si tu souhaites te réinscrire, tu pourras le faire sans problème sur le site ou n'hésite pas à nous écrire."
    body += "\n"
    body += "Ludiquement"
    body += "\n"
    body += "================="

    return subject, body


def event_registration_message(event_name: str, value: int) -> typing.Tuple[str, str]:
    """ event_registration_message """

    subject = f"Le statut de votre inscription dans l'événement {event_name} a été modifié"
    body = "Bonjour !\n"
    body += "\n"
    if value < 0:
        body += "Votre inscription a été refusée :-( !\n"
    elif value > 0:
        body += "Votre inscription a été acceptée :-) !\n"
    else:
        body += "Votre inscription a été remise en attente :-o !\n"
    body += "\n"
    body += "Vous pouvez contacter l'organisateur depuis le site\n"
    body += "\n"
    body += "Pour se rendre directement sur l'événement :\n"
    body += f"https://diplomania-gen.fr?event={event_name}"
    return subject, body


@API.resource('/player-identifiers/<pseudo>')
class PlayerIdentifierRessource(flask_restful.Resource):  # type: ignore
    """ PlayerIdentifierRessource """

    def get(self, pseudo: str) -> typing.Tuple[int, int]:
        """
        From name get identifier
        EXPOSED
        """

        # not logged because too much log
        #  mylogger.LOGGER.info("/player-identifiers/<pseudo> - GET - retrieving identifier from  player pseudo=%s", pseudo)

        # find data
        sql_executor = database.SqlExecutor()
        player = players.Player.find_by_pseudo(sql_executor, pseudo)
        del sql_executor

        if player is None:
            flask_restful.abort(404, msg=f"Player {pseudo} doesn't exist")

        assert player is not None
        return player.identifier, 200


@API.resource('/resend-code')
class ResendCodeRessource(flask_restful.Resource):  # type: ignore
    """ ResendCodeRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Request new verification code
        EXPOSED
        """

        mylogger.LOGGER.info("/resend-code - POST - ask resend verification code")

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

        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        player = players.Player.find_by_pseudo(sql_executor, pseudo)
        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} does not exist")

        # get a code
        code = random.randint(1000, 9999)

        assert player is not None
        email_player = player.email

        # put in database
        email = emails.Email(email_player, code)
        email.update_database(sql_executor)

        # get a message
        subject, body = email_checker_message(code)
        json_dict = {
            'subject': subject,
            'body': body,
            'addressees': email_player,
        }

        # send email
        host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
        port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/send-email"
        req_result = SESSION.post(url, headers={'AccessToken': jwt_token}, json=json_dict)
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(400, msg=f"Failed to send email to {email_player} : {message}")

        sql_executor.commit()
        del sql_executor

        data = {'pseudo': pseudo, 'msg': 'Ok verification code generated and sent'}
        return data, 200


@API.resource('/players/<pseudo>')
class PlayerRessource(flask_restful.Resource):  # type: ignore
    """ PlayerRessource """

    def get(self, pseudo: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

        # exception : we have both token and pseudo
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

    def put(self, pseudo: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Updates all info about a player
        EXPOSED
        """

        args = PLAYER_PARSER.parse_args(strict=True)

        mylogger.LOGGER.info("/players/<pseudo> - PUT - updating a player pseudo=%s", pseudo)

        # update player on users server if there is a password
        if args['password']:
            host = lowdata.SERVER_CONFIG['USER']['HOST']
            port = lowdata.SERVER_CONFIG['USER']['PORT']
            url = f"{host}:{port}/change"
            json_dict = {'user_name': pseudo, 'password': args['password']}
            jwt_token = flask.request.headers.get('AccessToken')
            req_result = SESSION.post(url, headers={'Authorization': f"Bearer {jwt_token}"}, json=json_dict)
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

        # exception : we have both token and pseudo
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

        assert player is not None
        email_before = player.email
        changed = player.load_json(args)
        if not changed:

            del sql_executor

            data = {'pseudo': pseudo, 'msg': 'Ok but no change !'}
            return data, 200

        email_after = player.email
        if email_after != email_before:
            email_player = email_after

            # player is now unconfirmed
            player.email_status = 0

            # get a code
            code = random.randint(1000, 9999)

            # put in database
            email = emails.Email(email_player, code)
            email.update_database(sql_executor)

            # get a message
            subject, body = email_checker_message(code)
            json_dict = {
                'subject': subject,
                'body': body,
                'addressees': email_player,
            }

            # send email
            host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
            port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
            url = f"{host}:{port}/send-email"
            req_result = SESSION.post(url, headers={'AccessToken': jwt_token}, json=json_dict)
            if req_result.status_code != 200:
                mylogger.LOGGER.error("ERROR = %s", req_result.text)
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                del sql_executor
                flask_restful.abort(400, msg=f"Failed to send email to {email_player} : {message}")

        player.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'pseudo': pseudo, 'msg': 'Ok updated'}
        return data, 200

    def delete(self, pseudo: str) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Deletes a player
        EXPOSED
        """

        mylogger.LOGGER.info("/players/<pseudo> - DELETE - removing one player pseudo=%s", pseudo)

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

        # exception : we have both token and pseudo
        if req_result.json()['logged_in_as'] != pseudo:
            flask_restful.abort(403, msg="Wrong authentication!")

        sql_executor = database.SqlExecutor()

        player = players.Player.find_by_pseudo(sql_executor, pseudo)

        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} doesn't exist")

        assert player is not None
        player_id = player.identifier

        # check player has no committements

        # ----------------------
        # first checks locally (players)
        # ----------------------

        # cannot quit if commuter
        if pseudo == COMMUTER_ACCOUNT:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} is commuter")

        # cannot quit if blacklisted
        blacklisted_ones_list = blacklisteds.Blacklisted.inventory(sql_executor)
        if pseudo in [m[0] for m in blacklisted_ones_list]:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} is a blacklisted")

        # cannot quit if creator
        creators_list = creators.Creator.inventory(sql_executor)
        if pseudo in [m[0] for m in creators_list]:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} is a creator")

        # cannot quit if  moderator
        moderators_list = moderators.Moderator.inventory(sql_executor)
        if pseudo in [m[0] for m in moderators_list]:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} is a moderator")

        # cannot quit if admin
        admin_pseudo = players.Player.find_admin_pseudo(sql_executor)
        if pseudo == admin_pseudo:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} is a admin")

        # player cannot quit if allocation (play in game)

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
            flask_restful.abort(400, msg=f"Player {pseudo} is still in a game")

        # ----------------------
        # all is ok
        # ----------------------

        # replaced by admin as event manager
        for event in events.Event.inventory(sql_executor):
            if event.manager_id == player_id:
                event.manager_id = ADDRESS_ADMIN
                event.update_database(sql_executor)

        # remove all incidents, dropouts, all replacements
        host = lowdata.SERVER_CONFIG['GAME']['HOST']
        port = lowdata.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/vaporize-player/{player_id}"
        jwt_token = flask.request.headers.get('AccessToken')
        req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"})

        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            flask_restful.abort(400, msg=f"Failed to vaporize player {message}")

        # notify player
        email_player = player.email

        # get a message
        subject, body = suppress_account_message(pseudo)
        json_dict = {
            'subject': subject,
            'body': body,
            'addressees': email_player,
        }

        # send email
        host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
        port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/send-email"
        req_result = SESSION.post(url, headers={'AccessToken': jwt_token}, json=json_dict)
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(400, msg=f"Failed to send email to {email_player} : {message}")

        # remove registration to all event
        registrations.Registration.delete_by_player_id(sql_executor, player_id)

        # delete player from timezone table
        timezones.Timezone.delete_by_player_id(sql_executor, player_id)

        # delete player from ip addresses table
        addresses.Address.delete_by_player_id(sql_executor, player_id)

        # delete player from submissions table
        submissions.Submission.delete_by_player_id(sql_executor, player_id)

        # delete player from messages (private messages)
        messages.Message.delete_by_player_id(sql_executor, player_id)

        # delete player from users server (that will implicitly check we have rights)
        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/remove"
        json_dict = {'user_name': pseudo}
        jwt_token = flask.request.headers.get('AccessToken')
        req_result = SESSION.post(url, headers={'Authorization': f"Bearer {jwt_token}"}, json=json_dict)
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


CREATE_PLAYER_LOCK = threading.Lock()


@API.resource('/players')
class PlayerListRessource(flask_restful.Resource):  # type: ignore
    """ PlayerListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Provides list of all pseudo data (all players)
        EXPOSED
        """

        mylogger.LOGGER.info("/players - GET - get getting all players only public information (email is confidential)")

        sql_executor = database.SqlExecutor()
        players_list = players.Player.inventory(sql_executor)
        del sql_executor

        data = {str(p.identifier): {'pseudo': p.pseudo, 'family_name': p.family_name, 'first_name': p.first_name, 'residence': p.residence, 'nationality': p.nationality, 'email_status': p.email_status, 'notify_replace': p.notify_replace} for p in players_list}

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Creates a new player
        EXPOSED
        """

        args = PLAYER_PARSER.parse_args(strict=True)
        pseudo = args['pseudo']

        mylogger.LOGGER.info("/players - POST - creating new player pseudo=%s", pseudo)

        if not (pseudo.isidentifier() and pseudo.isascii()):
            flask_restful.abort(400, msg=f"Pseudo '{pseudo}' is not a valid pseudo")

        if len(pseudo) < LEN_PSEUDO_MIN:
            flask_restful.abort(400, msg=f"Pseudo '{pseudo}' is too short")

        # cannot have a void residence
        if args['residence']:
            residence_provided = args['residence']
            if not players.check_country(residence_provided):
                flask_restful.abort(404, msg=f"Residence '{residence_provided}' is not a valid country code")
        else:
            args['residence'] = players.default_country()

        # cannot have a void nationality
        if args['nationality']:
            nationality_provided = args['nationality']
            if not players.check_country(nationality_provided):
                flask_restful.abort(404, msg=f"Nationality '{nationality_provided}' is not a valid country code")
        else:
            args['nationality'] = players.default_country()

        sql_executor = database.SqlExecutor()

        with CREATE_PLAYER_LOCK:

            player = players.Player.find_by_pseudo(sql_executor, pseudo)

            if player is not None:
                del sql_executor
                flask_restful.abort(400, msg=f"Player {pseudo} already exists")

            player2 = players.Player.find_by_similar_pseudo(sql_executor, pseudo)
            if player2 is not None:
                pseudo2 = player2.pseudo
                del sql_executor
                flask_restful.abort(400, msg=f"Player with similar pseudo '{pseudo2}' already exists")

            # create player here
            identifier = players.Player.free_identifier(sql_executor)
            player = players.Player(identifier, '', '', False, False, False, False, False, False, '', '', '', '')
            _ = player.load_json(args)
            player.update_database(sql_executor)

            # create player on users server
            host = lowdata.SERVER_CONFIG['USER']['HOST']
            port = lowdata.SERVER_CONFIG['USER']['PORT']
            url = f"{host}:{port}/add"
            json_dict = {'user_name': pseudo, 'password': args['password']}
            req_result = SESSION.post(url, json=json_dict)
            if req_result.status_code != 201:
                mylogger.LOGGER.error("ERROR = %s", req_result.text)
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                del sql_executor
                flask_restful.abort(400, msg=f"User creation failed!:{message}")

            mylogger.LOGGER.info("/players - POST - player with pseudo=%s created on user server side...", pseudo)
            # we do not create an entry for checking email since we do not have a token yet

        # send email
        email_newcommer = args['email']

        # get a code
        code = random.randint(1000, 9999)

        # put in database
        email = emails.Email(email_newcommer, code)
        email.update_database(sql_executor)

        # get a message
        subject, body = email_greeting_message(pseudo, code)
        json_dict = {
            'subject': subject,
            'body': body,
            'email': email_newcommer,
        }

        # send it (no token)
        host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
        port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/send-email-simple"
        req_result = SESSION.post(url, json=json_dict)
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(400, msg=f"Failed to send email to {email_newcommer} : {message}")

        sql_executor.commit()
        del sql_executor

        data = {'pseudo': pseudo, 'msg': 'Ok player created'}
        return data, 201


@API.resource('/players-short')
class PlayerShortListRessource(flask_restful.Resource):  # type: ignore
    """ PlayerShortListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Provides list of all pseudo (all players) - only identifier
        EXPOSED
        """

        mylogger.LOGGER.info("/players - GET - get getting all players only identifier")

        sql_executor = database.SqlExecutor()
        players_list = players.Player.inventory(sql_executor)
        del sql_executor

        data = {str(p.identifier): {'pseudo': p.pseudo} for p in players_list}

        return data, 200


@API.resource('/players-select')
class PlayerSelectListRessource(flask_restful.Resource):  # type: ignore
    """ PlayerSelectListRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
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

        mylogger.LOGGER.info("/players-select - POST - get getting some players only pseudo (email is confidential)")

        sql_executor = database.SqlExecutor()
        players_list = players.Player.inventory(sql_executor)
        del sql_executor

        data = {str(p.identifier): {'pseudo': p.pseudo, 'family_name': p.family_name, 'first_name': p.first_name, 'residence': p.residence, 'nationality': p.nationality} for p in players_list if p.identifier in selection_list}

        return data, 200


@API.resource('/mail-players')
class MailPlayersListRessource(flask_restful.Resource):  # type: ignore
    """ MailPlayersListRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Sends an email to a list of players
        EXPOSED
        """

        mylogger.LOGGER.info("/mail-players - POST - sending emails to a list of players")

        args = SEND_PLAYERS_EMAIL_PARSER.parse_args(strict=True)

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

        # any token goes
        pseudo = req_result.json()['logged_in_as']

        subject = args['subject']
        body = args['body']
        addressees_submitted = args['addressees']
        type_ = args['type']

        # I can get for type :
        #  forced
        #      'late' : deadline passed and player is late
        #             : master forced agreement and player is late
        #      'start_stop' : game started, stopped, complete and ready
        #      'reminder' : please enter order/agreement or just welcome and come in to play
        #      'profile' : profile (sending profiling information)
        #  not forced
        #      'message' : press or message in game
        #      'adjudication' : game has moved (from master/automaton/player)
        #      'deadline' : deadline is approaching
        #      'replace' : need a replacement

        if type_ not in ['late', 'start_stop', 'reminder', 'profile', 'message', 'adjudication', 'deadline', 'replace']:
            flask_restful.abort(400, msg="Unknown type.")

        try:
            addressees_list = list(map(int, addressees_submitted.split()))
        except:  # noqa: E722 pylint: disable=bare-except
            flask_restful.abort(400, msg="Bad addressees. Use a space separated list of numbers")

        sql_executor = database.SqlExecutor()

        addressees: typing.List[str] = []
        for addressee_id in addressees_list:

            # get player
            pseudo_dest = players.Player.find_by_identifier(sql_executor, addressee_id)
            if pseudo_dest is None:
                del sql_executor
                flask_restful.abort(404, msg=f"Failed to find pseudo with id={addressee_id}")
            assert pseudo_dest is not None

            # decide if send

            if type_ == 'deadline':
                # does not want to receive deadline approaching notifications
                if not pseudo_dest.notify_deadline:
                    continue

            if type_ == 'message':
                # does not want to receive private_message/message/press notifications
                if not pseudo_dest.notify_message:
                    continue

            if type_ == 'adjudication':
                # does not want to receive adjudication notifications
                if not pseudo_dest.notify_adjudication:
                    continue

            # security
            if type_ == 'replace':
                # does not want to receive replacement notifications
                if not pseudo_dest.notify_replace:
                    continue

            pseudo_dest_email = pseudo_dest.email
            addressees.append(pseudo_dest_email)

        # can happen that nobody is actually interested
        if addressees:

            addressees_str = ','.join(addressees)

            json_dict = {
                'subject': subject,
                'body': body,
                'addressees': addressees_str,
            }

            # send email
            host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
            port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
            url = f"{host}:{port}/send-email"
            req_result = SESSION.post(url, headers={'AccessToken': jwt_token}, json=json_dict)
            if req_result.status_code != 200:
                mylogger.LOGGER.error("ERROR = %s", req_result.text)
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                del sql_executor
                flask_restful.abort(400, msg=f"Failed to send email to at least one destinee : {message}")

        del sql_executor

        nb_mails = len(addressees)
        data = {'msg': f"Ok {nb_mails} email(s) successfully posted using {pseudo} account"}
        return data, 200


@API.resource('/players-emails')
class PlayerEmailsListRessource(flask_restful.Resource):  # type: ignore
    """ PlayerEmailsListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Provides list of all pseudo (all players) and the emails
        EXPOSED
        """

        mylogger.LOGGER.info("/players-emails - GET - get getting all players pseudo and email")

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

        # check user has right to get list of emails (moderator or admin)

        admin_pseudo = players.Player.find_admin_pseudo(sql_executor)
        moderators_list = moderators.Moderator.inventory(sql_executor)
        the_moderators = [m[0] for m in moderators_list]

        if not (pseudo in the_moderators or pseudo == admin_pseudo):
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to get list of emails (need to be moderator or admin)!")

        players_list = players.Player.inventory(sql_executor)
        del sql_executor

        data = {p.pseudo: (p.email, p.family_name, p.first_name, p.email_status, p.newsletter) for p in players_list}

        return data, 200


@API.resource('/check-email')
class CheckEmailRessource(flask_restful.Resource):  # type: ignore
    """ CheckEmailRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Checks a couple pseudo/code for email in database
        EXPOSED
        """

        mylogger.LOGGER.info("/check-email - POST - checking pseudo/code")

        args = CHECK_EMAIL_PARSER.parse_args(strict=True)
        pseudo = args['pseudo']
        code = args['code']

        sql_executor = database.SqlExecutor()

        player = players.Player.find_by_pseudo(sql_executor, pseudo)
        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} does not exist")

        assert player is not None
        email_player = player.email

        email = emails.Email.find_by_value(sql_executor, email_player)
        if email is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Email {email_player} does not exists")

        assert email is not None
        if email.code != code:
            del sql_executor
            flask_restful.abort(401, msg="Code is incorrect")

        # player is now unconfirmed
        player.email_status = 1
        player.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'pseudo': pseudo, 'msg': 'Ok code is correct'}
        return data, 200


@API.resource('/news')
class NewsRessource(flask_restful.Resource):  # type: ignore
    """ NewsRessource """

    def get(self) -> typing.Tuple[typing.Any, int]:
        """
        Provides the latest news
        EXPOSED
        """

        mylogger.LOGGER.info("/news - GET - get the latest news (admin and modo) + chats + server time")

        sql_executor = database.SqlExecutor()

        admin_content = newss.News.content(sql_executor, 'admin')
        modo_content = newss.News.content(sql_executor, 'modo')
        glory_content = newss.News.content(sql_executor, 'glory')

        raised_content = newss.News.content(sql_executor, 'raised')
        members_content = newss.News.content(sql_executor, 'members')

        del sql_executor

        # get chats contents
        host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
        port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/chat-messages"
        req_result = SESSION.get(url)
        chats_content = []
        if req_result.status_code == 200:
            chats_content = req_result.json()

        server_time = time.time()

        data = {'admin': admin_content, 'modo': modo_content, 'glory': glory_content, 'raised': raised_content, 'members': members_content, 'chats': chats_content, 'server_time': server_time}

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Creates a new news
        EXPOSED
        """

        mylogger.LOGGER.info("/news - POST - changing the news")

        args = NEWS_PARSER.parse_args(strict=True)

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

        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        player = players.Player.find_by_pseudo(sql_executor, pseudo)

        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} does not exist")

        topic = args['topic']

        if topic == 'admin':

            admin_pseudo = players.Player.find_admin_pseudo(sql_executor)
            if pseudo != admin_pseudo:
                del sql_executor
                flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to change news!")

        elif topic == 'modo':

            requester = players.Player.find_by_pseudo(sql_executor, pseudo)

            if requester is None:
                del sql_executor
                flask_restful.abort(404, msg=f"Requesting player {pseudo} does not exist")

            moderators_list = moderators.Moderator.inventory(sql_executor)
            the_moderators = [m[0] for m in moderators_list]
            if pseudo not in the_moderators:
                del sql_executor
                flask_restful.abort(403, msg="You are not allowed to change moderator news! (need to be moderator)")

        elif topic == 'glory':

            requester = players.Player.find_by_pseudo(sql_executor, pseudo)

            if requester is None:
                del sql_executor
                flask_restful.abort(404, msg=f"Requesting player {pseudo} does not exist")

            creators_list = creators.Creator.inventory(sql_executor)
            the_creators = [c[0] for c in creators_list]
            if pseudo not in the_creators:
                del sql_executor
                flask_restful.abort(403, msg="You are not allowed to change glorious! (need to be creator)")

        elif topic in ['raised', 'members']:

            requester = players.Player.find_by_pseudo(sql_executor, pseudo)

            if requester is None:
                del sql_executor
                flask_restful.abort(404, msg=f"Requesting player {pseudo} does not exist")

            if pseudo != COMMUTER_ACCOUNT:
                flask_restful.abort(403, msg="You are not allowed to change raised/members! (need to be commuter)")

        else:
            del sql_executor
            flask_restful.abort(400, msg="What is this topic ?")

        content = args['content']

        # protection from "surrogates not allowed"
        content_safe = content.encode('utf-8', errors='ignore').decode()

        # create news here
        news = newss.News(topic, content_safe)
        news.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': f'Ok news/glory ({topic}) created'}
        return data, 201


@API.resource('/player-information/<pseudo_player>')
class PlayerEmailRessource(flask_restful.Resource):  # type: ignore
    """ PlayerEmailRessource """

    def get(self, pseudo_player: str) -> typing.Tuple[typing.Dict[str, str], int]:
        """
        Provides the information (email address) of a player
        EXPOSED
        """

        mylogger.LOGGER.info("/player-email - GET - get the email address of player pseudo=%s", pseudo_player)

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

        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        requester = players.Player.find_by_pseudo(sql_executor, pseudo)

        if requester is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Requesting player {pseudo} does not exist")

        moderators_list = moderators.Moderator.inventory(sql_executor)
        the_moderators = [m[0] for m in moderators_list]
        if pseudo not in the_moderators:
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to get email address! (need to be moderator)")

        contact = players.Player.find_by_pseudo(sql_executor, pseudo_player)

        if contact is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Contact player {pseudo_player} does not exist")

        del sql_executor

        assert contact is not None
        email = contact.email

        data = {'email': email}
        return data, 200


@API.resource('/remove-newsletter/<pseudo_player>')
class RemoveNewsletterRessource(flask_restful.Resource):  # type: ignore
    """ RemoveNewsletterRessource """

    def post(self, pseudo_player: str) -> typing.Tuple[typing.Dict[str, str], int]:
        """
        Patch newsletter bit for a player (he complained !)
        EXPOSED
        """

        mylogger.LOGGER.info("/remove-newsletter - POST - remove newsletter pseudo=%s", pseudo_player)

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

        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        requester = players.Player.find_by_pseudo(sql_executor, pseudo)

        if requester is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Requesting player {pseudo} does not exist")

        moderators_list = moderators.Moderator.inventory(sql_executor)
        the_moderators = [m[0] for m in moderators_list]
        if pseudo not in the_moderators:
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to changed newsletters of someone! (need to be moderator)")

        wild = players.Player.find_by_pseudo(sql_executor, pseudo_player)

        if wild is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Wild player {pseudo_player} does not exist")

        assert wild is not None
        wild.newsletter = False
        wild.update_database(sql_executor)
        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok wild patched'}
        return data, 200


@API.resource('/confirm-email/<pseudo_player>')
class ConfirmEmailRessource(flask_restful.Resource):  # type: ignore
    """ ConfirmEmailRessource """

    def post(self, pseudo_player: str) -> typing.Tuple[typing.Dict[str, str], int]:
        """
        Patch email confirmed bit for a player (he received stuff ok !)
        EXPOSED
        """

        mylogger.LOGGER.info("/confirm-email - POST - confirm email pseudo=%s", pseudo_player)

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

        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        requester = players.Player.find_by_pseudo(sql_executor, pseudo)

        if requester is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Requesting player {pseudo} does not exist")

        moderators_list = moderators.Moderator.inventory(sql_executor)
        the_moderators = [m[0] for m in moderators_list]
        if pseudo not in the_moderators:
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to changed confirmation status of someone! (need to be moderator)")

        received = players.Player.find_by_pseudo(sql_executor, pseudo_player)

        if received is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Receiving player {pseudo_player} does not exist")

        assert received is not None
        received.email_status = 1
        received.update_database(sql_executor)
        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok receiving patched confirmed'}
        return data, 200


@API.resource('/unconfirm-email/<pseudo_player>')
class UnConfirmEmailRessource(flask_restful.Resource):  # type: ignore
    """ UnConfirmEmailRessource """

    def post(self, pseudo_player: str) -> typing.Tuple[typing.Dict[str, str], int]:
        """
        Patch email confirmed bit for a player (unsure !)
        EXPOSED
        """

        mylogger.LOGGER.info("/unconfirm-email - POST - confirm email pseudo=%s", pseudo_player)

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

        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        requester = players.Player.find_by_pseudo(sql_executor, pseudo)

        if requester is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Requesting player {pseudo} does not exist")

        moderators_list = moderators.Moderator.inventory(sql_executor)
        the_moderators = [m[0] for m in moderators_list]
        if pseudo not in the_moderators:
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to changed confirmation status of someone! (need to be moderator)")

        received = players.Player.find_by_pseudo(sql_executor, pseudo_player)

        if received is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Receiving player {pseudo_player} does not exist")

        assert received is not None
        received.email_status = 0
        received.update_database(sql_executor)
        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok receiving patched unconfirmed'}
        return data, 200


@API.resource('/error-set-email/<pseudo_player>')
class ErrorSetEmailRessource(flask_restful.Resource):  # type: ignore
    """ ErrorSetEmailRessource """

    def post(self, pseudo_player: str) -> typing.Tuple[typing.Dict[str, str], int]:
        """
        Put email as error for player
        EXPOSED
        """

        mylogger.LOGGER.info("/error-set-email - POST - email pseudo=%s", pseudo_player)

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

        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        requester = players.Player.find_by_pseudo(sql_executor, pseudo)

        if requester is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Requesting player {pseudo} does not exist")

        moderators_list = moderators.Moderator.inventory(sql_executor)
        the_moderators = [m[0] for m in moderators_list]
        if pseudo not in the_moderators:
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to changed confirmation status of someone! (need to be moderator)")

        received = players.Player.find_by_pseudo(sql_executor, pseudo_player)

        if received is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Receiving player {pseudo_player} does not exist")

        assert received is not None
        received.email_status = 2
        received.update_database(sql_executor)
        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok email unconfirmed'}
        return data, 200


@API.resource('/blacklisteds')
class BlacklistedListRessource(flask_restful.Resource):  # type: ignore
    """ BlacklistedListRessource """

    def get(self) -> typing.Tuple[typing.List[str], int]:
        """
        Provides list of all blacklisted ones
        EXPOSED
        """

        mylogger.LOGGER.info("/blacklisteds - GET - get getting all blacklisteds")

        sql_executor = database.SqlExecutor()
        blacklisted_ones_list = blacklisteds.Blacklisted.inventory(sql_executor)
        del sql_executor

        data = [c[0] for c in blacklisted_ones_list]

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Creates/Deletes a blacklisted
        EXPOSED
        """

        mylogger.LOGGER.info("/blacklisteds - POST - creating/deleting new blacklisted")

        args = CREATOR_PARSER.parse_args(strict=True)
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

        sql_executor = database.SqlExecutor()

        admin_pseudo = players.Player.find_admin_pseudo(sql_executor)
        if pseudo != admin_pseudo:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to edit the list of blacklisted ones!")

        player = players.Player.find_by_pseudo(sql_executor, player_pseudo)

        if player is None:
            del sql_executor
            flask_restful.abort(400, msg=f"Player {player_pseudo} does not exist")

        if not delete:
            blacklisted = blacklisteds.Blacklisted(player_pseudo)
            blacklisted.update_database(sql_executor)

            sql_executor.commit()
            del sql_executor

            data = {'msg': 'Ok blacklisted one updated or created'}
            return data, 201

        blacklisted = blacklisteds.Blacklisted(player_pseudo)
        blacklisted.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok blacklisted deleted if present'}
        return data, 200


@API.resource('/creators')
class CreatorListRessource(flask_restful.Resource):  # type: ignore
    """ CreatorListRessource """

    def get(self) -> typing.Tuple[typing.List[str], int]:
        """
        Provides list of all creators
        EXPOSED
        """

        mylogger.LOGGER.info("/creators - GET - get getting all creators")

        sql_executor = database.SqlExecutor()
        creators_list = creators.Creator.inventory(sql_executor)
        del sql_executor

        data = [c[0] for c in creators_list]

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Creates/Deletes a creator
        EXPOSED
        """

        mylogger.LOGGER.info("/creators - POST - creating/deleting new creator")

        args = CREATOR_PARSER.parse_args(strict=True)
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

        sql_executor = database.SqlExecutor()

        admin_pseudo = players.Player.find_admin_pseudo(sql_executor)
        if pseudo != admin_pseudo:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to edit the list of creators!")

        player = players.Player.find_by_pseudo(sql_executor, player_pseudo)

        if player is None:
            del sql_executor
            flask_restful.abort(400, msg=f"Player {player_pseudo} does not exist")

        if not delete:
            creator = creators.Creator(player_pseudo)
            creator.update_database(sql_executor)

            sql_executor.commit()
            del sql_executor

            data = {'msg': 'Ok creator updated or created'}
            return data, 201

        creator = creators.Creator(player_pseudo)
        creator.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok creator deleted if present'}
        return data, 200


@API.resource('/moderators')
class ModeratorListRessource(flask_restful.Resource):  # type: ignore
    """ ModeratorListRessource """

    def get(self) -> typing.Tuple[typing.List[str], int]:
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

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Creates/Deletes a moderator
        EXPOSED
        """

        mylogger.LOGGER.info("/moderators - POST - creating/deleting new moderator")

        args = MODERATOR_PARSER.parse_args(strict=True)
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

        sql_executor = database.SqlExecutor()

        admin_pseudo = players.Player.find_admin_pseudo(sql_executor)   # noqa: F821
        if pseudo != admin_pseudo:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to edit the list of moderators!")

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


@API.resource('/pseudo-admin')
class PseudoAdminRessource(flask_restful.Resource):  # type: ignore
    """ CheckAdminRessource """

    def get(self) -> typing.Tuple[typing.Optional[str], int]:
        """
        Give pseudo of admin (for users module)
        EXPOSED
        """

        mylogger.LOGGER.info("/pseudo-admin - POST - get admin pseudo")
        sql_executor = database.SqlExecutor()
        admin_pseudo = players.Player.find_admin_pseudo(sql_executor)
        del sql_executor

        data = admin_pseudo
        return data, 200


@API.resource('/priviledged')
class PriviledgedListRessource(flask_restful.Resource):  # type: ignore
    """ PriviledgedListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Union[typing.List[str], typing.Optional[str]]], int]:
        """
        Provides list of all priviledged (creators, moderators and admin)
        EXPOSED
        """

        mylogger.LOGGER.info("/priviledged - GET - get getting all priviledged")

        sql_executor = database.SqlExecutor()
        creators_list = creators.Creator.inventory(sql_executor)
        moderators_list = moderators.Moderator.inventory(sql_executor)
        admin_pseudo = players.Player.find_admin_pseudo(sql_executor)
        del sql_executor

        c_list = [c[0] for c in creators_list]
        m_list = [m[0] for m in moderators_list]

        return {'creators': c_list, 'moderators': m_list, 'admin': admin_pseudo}, 200


@API.resource('/elo_rating/<classic>')
class EloClassicRessource(flask_restful.Resource):  # type: ignore
    """ EloClassicRessource """

    def get(self, classic: int) -> typing.Tuple[typing.List[typing.Tuple[int, int, int, int, int, int, int]], int]:
        """
        Provides ratings by classic and role
        EXPOSED
        """

        mylogger.LOGGER.info("/elo_rating - GET - get by classic")

        sql_executor = database.SqlExecutor()
        ratings_list = ratings.Rating.list_by_classic(sql_executor, bool(int(classic)))

        del sql_executor

        return ratings_list, 200


@API.resource('/elo_rating/<classic>/<role_id>')
class EloClassicRoleRessource(flask_restful.Resource):  # type: ignore
    """ EloClassicRoleRessource """

    def get(self, classic: int, role_id: int) -> typing.Tuple[typing.List[typing.Tuple[int, int, int, int, int, int, int]], int]:
        """
        Provides ELO ratings by classic and role
        EXPOSED
        """

        mylogger.LOGGER.info("/elo_rating - GET - get by classic and role")

        sql_executor = database.SqlExecutor()
        ratings_list = ratings.Rating.list_by_classic_role_id(sql_executor, bool(int(classic)), role_id)
        del sql_executor

        return ratings_list, 200


@API.resource('/elo_rating')
class RawEloRessource(flask_restful.Resource):  # type: ignore
    """ RawEloRessource """

    def get(self) -> typing.Tuple[str, int]:
        """
        Provides the elo teaser
        EXPOSED
        """

        mylogger.LOGGER.info("/news - GET - get the elo teaser")

        sql_executor = database.SqlExecutor()
        teaser_content = teasers.Teaser.content(sql_executor)
        del sql_executor

        data = teaser_content

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Update elo data
        EXPOSED
        """

        mylogger.LOGGER.info("/elo_rating - POST - update elo and elo teaser")

        args = ELO_UPDATE_PARSER.parse_args(strict=True)

        elo_list_submitted = args['elo_list']
        teaser_submitted = args['teaser']

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

        if pseudo != COMMUTER_ACCOUNT:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be site commuter so you are not allowed to update ELO data")

        try:
            elo_list = json.loads(elo_list_submitted)
        except json.JSONDecodeError:
            del sql_executor   # noqa: F821
            flask_restful.abort(400, msg="Did you convert elo table from json to text ?")

        # put the raw ratings
        ratings.Rating.create_table(sql_executor)   # noqa: F821
        for elo in elo_list:
            rating = ratings.Rating(*elo)
            rating.update_database(sql_executor)   # noqa: F821

        # put the teaser
        teaser = teasers.Teaser(teaser_submitted)
        teaser.update_database(sql_executor)   # noqa: F821

        sql_executor.commit()   # noqa: F821
        del sql_executor   # noqa: F821

        data = {'msg': "ELO update done"}
        return data, 200


@API.resource('/reliability_rating')
class ReliabilityRessource(flask_restful.Resource):  # type: ignore
    """ ReliabilityRessource """

    def get(self) -> typing.Tuple[typing.List[typing.Tuple[int, int, int, int]], int]:
        """
        Provides reliability ratings
        EXPOSED
        """

        mylogger.LOGGER.info("/reliability_rating - GET")

        sql_executor = database.SqlExecutor()
        ratings_list = ratings3.Rating3.list(sql_executor)
        del sql_executor

        return ratings_list, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        maintain
        EXPOSED
        """

        mylogger.LOGGER.info("/reliability_rating - POST - update regularity")

        args = RELIABILITY_UPDATE_PARSER.parse_args(strict=True)

        reliability_list_submitted = args['reliability_list']

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

        if pseudo != COMMUTER_ACCOUNT:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be site commuter so you are not allowed to update reliability data")

        try:
            reliability_list = json.loads(reliability_list_submitted)
        except json.JSONDecodeError:
            del sql_executor
            flask_restful.abort(400, msg="Did you convert reliability table from json to text ?")

        # put the raw ratings
        ratings3.Rating3.create_table(sql_executor)   # noqa: F821
        for reliability in reliability_list:
            rating = ratings3.Rating3(*reliability)
            rating.update_database(sql_executor)   # noqa: F821

        sql_executor.commit()   # noqa: F821
        del sql_executor   # noqa: F821

        data = {'msg': "reliability update done"}
        return data, 200


@API.resource('/regularity_rating')
class RegularityRessource(flask_restful.Resource):  # type: ignore
    """ RegularityRessource """

    def get(self) -> typing.Tuple[typing.List[typing.Tuple[int, int, int, int, int]], int]:
        """
        Provides regularity ratings
        EXPOSED
        """

        mylogger.LOGGER.info("/regularity_rating - GET")

        sql_executor = database.SqlExecutor()
        ratings_list = ratings2.Rating2.list(sql_executor)
        del sql_executor

        return ratings_list, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        update regularity data
        EXPOSED
        """

        mylogger.LOGGER.info("/regularity_rating - POST - update regularity")

        args = REGULARITY_UPDATE_PARSER.parse_args(strict=True)

        regularity_list_submitted = args['regularity_list']

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

        if pseudo != COMMUTER_ACCOUNT:
            del sql_executor   # noqa: F821
            flask_restful.abort(403, msg="You do not seem to be site commuter so you are not allowed to update regularity data")

        try:
            regularity_list = json.loads(regularity_list_submitted)
        except json.JSONDecodeError:
            del sql_executor
            flask_restful.abort(400, msg="Did you convert regularity table from json to text ?")

        # put the raw ratings
        ratings2.Rating2.create_table(sql_executor)  # noqa: F821
        for regularity in regularity_list:
            rating = ratings2.Rating2(*regularity)
            rating.update_database(sql_executor)  # noqa: F821

        sql_executor.commit()  # noqa: F821
        del sql_executor  # noqa: F821

        data = {'msg': "regularity update done"}
        return data, 200


@API.resource('/events_manager/<event_id>')
class EventManagerRessource(flask_restful.Resource):  # type: ignore
    """ EventManagerRessource """

    def post(self, event_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Updates an event (manager)
        EXPOSED
        """

        mylogger.LOGGER.info("/events_manager/<event_id> - PUT - updating manager event with id=%s", event_id)

        args = EVENT_PARSER2.parse_args(strict=True)

        manager_id = args['manager_id']

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

        # find the event
        event = events.Event.find_by_identifier(sql_executor, event_id)
        if event is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Event {event_id} doesn't exist")

        assert event is not None

        # check user has right to change event manager (moderator)

        moderators_list = moderators.Moderator.inventory(sql_executor)
        the_moderators = [m[0] for m in moderators_list]
        if pseudo not in the_moderators:
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to change event manager (need to be moderator)")

        # update event here
        event = events.Event(int(event_id), event.name, event.start_date, event.start_hour, event.end_date, event.location, event.external, event.description, event.summary, manager_id)
        event.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'identifier': event_id, 'msg': 'Ok manager updated'}
        return data, 200


@API.resource('/site_image')
class SiteImageRessource(flask_restful.Resource):  # type: ignore
    """ SiteImageRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Updates a new site image
        EXPOSED
        """

        mylogger.LOGGER.info("/site_image - POST - updating site image")

        args = SITE_IMAGE_PARSER.parse_args(strict=True)

        legend = args['legend']

        # protection from "surrogates not allowed"
        legend_safe = legend.encode('utf-8', errors='ignore').decode()

        image_str = args['image']
        image_bytes = image_str.encode()

        if len(image_bytes) > MAX_SIZE_IMAGE:
            flask_restful.abort(404, msg="Too big an image this is, please try a smaller one !")

        sql_executor = database.SqlExecutor()

        image = site_image.SiteImage(legend_safe, image_bytes)
        image.update_database(sql_executor)
        sql_executor.commit()

        data = {'msg': 'Ok inserted'}
        return data, 201

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Provides the site legend + image
        EXPOSED
        """

        mylogger.LOGGER.info("/site_image - GET - get the site legend + image")

        sql_executor = database.SqlExecutor()

        # find the site image
        image_data = site_image.SiteImage.content(sql_executor)

        legend = image_data[0]

        image_bytes = image_data[1]
        image_content = image_bytes.decode() if image_bytes else None

        del sql_executor

        data = {'legend': legend, 'image': image_content}

        return data, 200


@API.resource('/events/<event_id>')
class EventRessource(flask_restful.Resource):  # type: ignore
    """ EventRessource """

    def get(self, event_id: int) -> typing.Tuple[typing.Optional[typing.Dict[str, typing.Any]], int]:
        """
        Get all information about event
        EXPOSED
        """

        mylogger.LOGGER.info("/events/<event_id> - GET- retrieving data of event with id name=%s", event_id)

        sql_executor = database.SqlExecutor()

        # find the event
        event = events.Event.find_by_identifier(sql_executor, event_id)
        if event is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Event {event_id} doesn't exist")

        assert event is not None

        del sql_executor

        data = {'name': event.name, 'start_date': event.start_date, 'start_hour': event.start_hour, 'end_date': event.end_date, 'location': event.location, 'external': event.external, 'description': event.description, 'summary': event.summary, 'manager_id': event.manager_id}

        return data, 200

    def put(self, event_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Updates an event
        EXPOSED
        """

        mylogger.LOGGER.info("/events/<event_id> - PUT - updating event with id=%s", event_id)

        args = EVENT_PARSER.parse_args(strict=True)

        # either name is set (update data)...
        name = args['name']

        start_date = args['start_date']
        start_hour = args['start_hour']
        end_date = args['end_date']
        location = args['location']
        description = args['description']
        summary = args['summary']

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

        sql_executor = database.SqlExecutor()

        # get player identifier
        player = players.Player.find_by_pseudo(sql_executor, pseudo)
        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} doesn't exist")
        assert player is not None
        user_id = player.identifier

        # find the event
        event = events.Event.find_by_identifier(sql_executor, event_id)
        if event is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Event {event_id} doesn't exist")

        assert event is not None

        # check that user is the manager of the event
        if user_id != event.manager_id:
            del sql_executor
            flask_restful.abort(404, msg="You do not seem to be manager of that event")

        if name is not None:

            # check len of name
            if len(name) > LEN_EVENT_MAX:
                del sql_executor
                flask_restful.abort(400, msg=f"Event name {name} is too long")

            # update event here
            event = events.Event(int(event_id), name, start_date, start_hour, end_date, location, event.external, description, summary, user_id)
            event.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'identifier': event_id, 'msg': 'Ok updated'}
        return data, 200

    def delete(self, event_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Deletes an event
        EXPOSED
        """

        mylogger.LOGGER.info("/events/<event_id> - DELETE - deleting event with id=%s", event_id)

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

        sql_executor = database.SqlExecutor()

        # get player identifier
        player = players.Player.find_by_pseudo(sql_executor, pseudo)
        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} doesn't exist")
        assert player is not None
        user_id = player.identifier

        # find the event
        event = events.Event.find_by_identifier(sql_executor, event_id)
        if event is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Event {event_id} doesn't exist")

        assert event is not None

        # check that user is the manager of the event
        if user_id != event.manager_id:
            del sql_executor
            flask_restful.abort(404, msg="You do not seem to be manager of that event")

        # delete registrations
        event.delete_registrations(sql_executor)

        # finally delete event
        event.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'identifier': event_id, 'msg': 'Ok removed'}
        return data, 200


@API.resource('/events')
class EventListRessource(flask_restful.Resource):  # type: ignore
    """ EventListRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Dict[str, typing.Any]], int]:
        """
        Get list of events
        EXPOSED
        """

        mylogger.LOGGER.info("/events - GET- retrieving list of events")

        sql_executor = database.SqlExecutor()
        events_list = events.Event.inventory(sql_executor)
        nb_registered_table = {e.identifier: len(registrations.Registration.list_by_event_id(sql_executor, int(e.identifier))) for e in events_list}
        del sql_executor

        data = {str(e.identifier): {'name': e.name, 'summary': e.summary, 'nb_registered': nb_registered_table[e.identifier]} for e in events_list}

        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Creates a new event
        EXPOSED
        """

        mylogger.LOGGER.info("/events - POST - creating new event")

        args = EVENT_PARSER.parse_args(strict=True)

        name = args['name']
        start_date = args['start_date']
        start_hour = args['start_hour']
        end_date = args['end_date']
        location = args['location']
        external = bool(int(args['external']))
        description = args['description']
        summary = args['summary']

        # additional filtering on name
        name = name.replace(' ', '_')

        if not (name.isidentifier() and name.isascii()):
            flask_restful.abort(400, msg=f"Name '{name}' is not a valid name")

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

        sql_executor = database.SqlExecutor()

        # get player identifier
        player = players.Player.find_by_pseudo(sql_executor, pseudo)
        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} doesn't exist")
        assert player is not None
        user_id = player.identifier

        # find the event
        event = events.Event.find_by_name(sql_executor, name)

        if event is not None:
            del sql_executor
            flask_restful.abort(400, msg=f"Event {name} already exists")

        # check len of name
        if len(name) > LEN_EVENT_MAX:
            del sql_executor
            flask_restful.abort(400, msg=f"Event name {name} is too long")

        # create event here
        identifier = events.Event.free_identifier(sql_executor)
        event = events.Event(identifier, name, start_date, start_hour, end_date, location, external, description, summary, user_id)
        event.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'name': name, 'msg': 'Ok event created'}
        return data, 201


@API.resource('/registrations/<event_id>')
class RegistrationEventRessource(flask_restful.Resource):  # type: ignore
    """ RegistrationEventRessource """

    def get(self, event_id: int) -> typing.Tuple[typing.List[typing.Tuple[int, int, int, str]], int]:
        """
        Get list of registrations to the event
        EXPOSED
        """

        mylogger.LOGGER.info("/registrations/<event_id> - GET - getting registrations to the event")

        sql_executor = database.SqlExecutor()
        registrations_list = registrations.Registration.list_by_event_id(sql_executor, int(event_id))
        del sql_executor

        data = [(r[1], r[2], r[3], r[4]) for r in sorted(registrations_list, key=lambda rr: rr[2])]

        return data, 200

    def post(self, event_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Creates or deletes a registration (a relation player-event)
        EXPOSED
        """

        mylogger.LOGGER.info("/registrations - POST - creating/deleting new registration")

        args = REGISTRATION_PARSER.parse_args(strict=True)

        delete = args['delete']
        comment = args['comment']

        # protection from "surrogates not allowed"
        comment_safe = comment.encode('utf-8', errors='ignore').decode()

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

        sql_executor = database.SqlExecutor()

        # get player identifier
        player = players.Player.find_by_pseudo(sql_executor, pseudo)
        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} doesn't exist")
        assert player is not None
        user_id = player.identifier

        # find the event
        event = events.Event.find_by_identifier(sql_executor, event_id)
        if event is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be an event with identifier {event_id}")

        assert event is not None

        if event.external:
            del sql_executor
            flask_restful.abort(404, msg="This is an external event : no registration on this site, sorry !")

        # action

        if not delete:

            now = time.time()
            registration = registrations.Registration(int(event_id), user_id, now, 0, comment_safe)
            registration.update_database(sql_executor)

            sql_executor.commit()
            del sql_executor

            data = {'msg': 'Ok registration updated or created'}
            return data, 201

        registration = registrations.Registration(int(event_id), user_id, 0., 0, '')
        registration.delete_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok registration deleted if present'}
        return data, 200

    def put(self, event_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Updates a registration (a relation player-event)
        EXPOSED
        """

        mylogger.LOGGER.info("/registrations - PUT - updating registration")

        args = REGISTRATION_UPDATE_PARSER.parse_args(strict=True)

        player_id = args['player_id']
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

        # we do not check pseudo, we read it from token
        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        # get player identifier
        player = players.Player.find_by_pseudo(sql_executor, pseudo)
        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} doesn't exist")
        assert player is not None
        user_id = player.identifier

        # find the event
        event = events.Event.find_by_identifier(sql_executor, event_id)
        if event is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be an event with identifier {event_id}")
        assert event is not None
        event_name = event.name

        # check that user is the manager of the event
        if user_id != event.manager_id:
            del sql_executor
            flask_restful.abort(404, msg="You do not seem to be manager of that event")

        # check the concerned player exists
        player_concerned = players.Player.find_by_identifier(sql_executor, player_id)
        if player_concerned is None:
            del sql_executor
            flask_restful.abort(404, msg=f"There does not seem to be a player with identifier {player_id}")

        # action
        regis = registrations.Registration.find_date_comment_by_event_id_player_id(sql_executor, event_id, player_id)
        assert regis is not None
        date_, comment = regis

        registration = registrations.Registration(int(event_id), int(player_id), date_, value, comment)
        registration.update_database(sql_executor)

        assert player_concerned is not None
        email_player = player_concerned.email

        # get a message
        subject, body = event_registration_message(event_name, value)
        json_dict = {
            'subject': subject,
            'body': body,
            'addressees': email_player,
        }

        # send email
        host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
        port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/send-email"
        req_result = SESSION.post(url, headers={'AccessToken': jwt_token}, json=json_dict)
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(400, msg=f"Failed to send email to {email_player} : {message}")

        sql_executor.commit()
        del sql_executor

        data = {'msg': 'Ok registration updated if present and email sent to player'}
        return data, 200


@API.resource('/submission_data')
class SubmissionDataRessource(flask_restful.Resource):  # type: ignore
    """ SubmissionDataRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.List[typing.Tuple[str, int]]], int]:
        """
        Get list of Time zone, IP addresses and last order input
        EXPOSED
        """

        mylogger.LOGGER.info("/submission_data - GET - getting time zones, ip addresses and last order input")

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

        # check user has right to get list of last timezones, ip addresses and submissions (moderator)

        sql_executor = database.SqlExecutor()

        moderators_list = moderators.Moderator.inventory(sql_executor)
        the_moderators = [m[0] for m in moderators_list]
        if pseudo not in the_moderators:
            del sql_executor
            flask_restful.abort(403, msg="You are not allowed to get list of last ip addresses and submissions (need to be moderator)!")

        # gather data

        time_zones_list = timezones.Timezone.inventory(sql_executor)
        ip_addresses_list = addresses.Address.inventory(sql_executor)
        submissions_list = submissions.Submission.inventory(sql_executor)

        del sql_executor

        data = {'time_zones_list': time_zones_list, 'ip_addresses_list': ip_addresses_list, 'submissions_list': submissions_list}
        return data, 200

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Stores an Time zone, IP address and last submission
        EXPOSED
        """

        args = DATA_SUBMISSION_PARSER.parse_args(strict=True)
        time_zone = args['time_zone']
        ip_address = args['ip_address']

        mylogger.LOGGER.info("/submission_data- POST - stores a timezone,  ipaddress and submission")

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

        pseudo = req_result.json()['logged_in_as']

        sql_executor = database.SqlExecutor()

        player = players.Player.find_by_pseudo(sql_executor, pseudo)
        if player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {pseudo} does not exist")

        assert player is not None

        player_id = player.identifier

        # store a time zone for player
        timezone = timezones.Timezone(player_id, time_zone)
        timezone.update_database(sql_executor)

        # store an ip address for player
        address = addresses.Address(ip_address, player_id)
        address.update_database(sql_executor)

        # store a last submission date for player
        submission = submissions.Submission(player_id)
        submission.update_database(sql_executor)

        sql_executor.commit()

        data = {'pseudo': pseudo, 'msg': 'Ok Time zone, IP address and submission stored'}
        return data, 200


@API.resource('/rescue-player')
class RescuePlayerRessource(flask_restful.Resource):  # type: ignore
    """ RescuePlayerRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Rescue a player
        PROTECTED
        """

        mylogger.LOGGER.info("/rescue-player - POST - rescue a player")

        args = RESCUE_PLAYER_PARSER.parse_args(strict=True)

        rescued_pseudo = args['rescued_user']
        access_token = args['access_token']

        sql_executor = database.SqlExecutor()

        rescued_player = players.Player.find_by_pseudo(sql_executor, rescued_pseudo)
        if rescued_player is None:
            del sql_executor
            flask_restful.abort(404, msg=f"Player {rescued_pseudo} does not exists")
        assert rescued_player is not None

        email_rescued_player = rescued_player.email

        # get a message
        subject, body = email_rescue_message(rescued_pseudo, access_token)

        json_dict = {
            'subject': subject,
            'body': body,
            'email': email_rescued_player,
        }

        # send it
        host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
        port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/send-email-simple"
        req_result = SESSION.post(url, json=json_dict)
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(400, msg=f"Failed to send email to {email_rescued_player} : {message}")

        del sql_executor
        data = {'msg': "rescue message sent"}
        return data, 200


POST_MESSAGE_LOCK = threading.Lock()
POST_MESSAGE_REPEAT_PREVENTER = RepeatPreventer()


@API.resource('/private-messages')
class PrivateMessagesRessource(flask_restful.Resource):  # type: ignore
    """  PrivateMessagesRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Insert private message in database
        EXPOSED
        """

        mylogger.LOGGER.info("/private-messages - POST - creating new message")

        args = MESSAGE_PARSER.parse_args(strict=True)

        dest_user_id = args['dest_user_id']
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

        if not dest_user_id:
            del sql_executor
            flask_restful.abort(400, msg="There should be at least one destinee")

        # create message here
        with POST_MESSAGE_LOCK:

            if not POST_MESSAGE_REPEAT_PREVENTER.can(int(user_id)):
                del sql_executor
                flask_restful.abort(400, msg="You have already messaged a very short time ago")

            # create a content
            identifier = contents.Content.free_identifier(sql_executor)  # noqa: F821
            time_stamp = int(time.time())  # now
            content = contents.Content(identifier, time_stamp, payload_safe)
            content.update_database(sql_executor)  # noqa: F821

            # create a message linked to the content
            read = False
            message = messages.Message(user_id, dest_user_id, read, identifier)
            message.update_database(sql_executor)  # noqa: F821

            POST_MESSAGE_REPEAT_PREVENTER.did(int(user_id))

        subject = "Un utilisateur vous a envoyé un message privé sur le site"
        addressees = []
        addressees.append(dest_user_id)

        body = "Bonjour !\n"
        body += "\n"

        body += f"Auteur du message : {pseudo}\n"
        body += "\n"
        body += "Contenu du message :\n"
        body += "================\n"
        body += payload_safe
        body += "\n"
        body += "================\n"

        body += "Vous pouvez aller consulter le message et y répondre sur le site....\n"
        body += "\n"
        body += "Note : Vous pouvez désactiver cette notification en modifiant un paramètre de votre compte sur le site.\n"

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
        req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, json=json_dict)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            del sql_executor
            flask_restful.abort(400, msg=f"Failed sending notification emails {message}")

        sql_executor.commit()  # noqa: F821
        del sql_executor  # noqa: F821

        data = {'msg': "Ok message inserted"}
        return data, 201

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Gets my private messages
        EXPOSED
        """

        mylogger.LOGGER.info("/private-messages - GET - getting back messages")

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

        # gather messages
        messages_extracted_list = messages.Message.list_with_content_by_player_id(sql_executor, player_id)

        # get all message
        messages_list = [(identifier, author_num, time_stamp, addressees_num, read, content.payload) for identifier, author_num, addressees_num, time_stamp, read, content in messages_extracted_list]

        # mark as read
        sql_executor.execute("UPDATE messages SET read=1 WHERE addressee_num = ?", (player_id,))

        sql_executor.commit()
        del sql_executor

        data = {
            'messages_list': messages_list,
        }
        return data, 200


@API.resource('/private-messages/<message_id>')
class PrivateMessagesDeleteRessource(flask_restful.Resource):  # type: ignore
    """  PrivateMessagesDeleteRessource """

    def delete(self, message_id: int) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Deletes a private message
        EXPOSED
        """

        mylogger.LOGGER.info("/private-messages - GET - deleting message")

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

        # check right to remove
        time_stamp_now = time.time()
        time_stamp, addressee_id, read = messages.Message.addressee_read_by_message_id(sql_executor, message_id)
        old_message = time_stamp < time_stamp_now - TIMEOUT_REMOVE_MESSAGE_DAYS * 24 * 3600
        if not (player_id == addressee_id or read or old_message):
            flask_restful.abort(403, msg=f"Not owner of message {addressee_id=} != {player_id=} or message read or old_message")

        # remove message
        message = messages.Message(0, 0, False, int(message_id))
        message.delete_database(sql_executor)

        # remove content
        content = contents.Content(int(message_id), 0, '')
        content.delete_database(sql_executor)

        sql_executor.commit()

        del sql_executor

        data = {'msg': 'Ok removed'}
        return data, 200


@API.resource('/new-private-messages-received')
class NewPrivateMessageReceivedRessource(flask_restful.Resource):  # type: ignore
    """  NewPrivateMessageReceivedRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Do we have new messages ?
        EXPOSED
        """

        mylogger.LOGGER.info("/new-private-messages-received - GET - new message")

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

        new_messages = messages.Message.list_new_messages_by_player_id(sql_executor, player_id)

        del sql_executor

        data = {'new_messages': new_messages[0][0]}
        return data, 200


@API.resource('/email-status')
class EmailStatusRessource(flask_restful.Resource):  # type: ignore
    """  EmailStatusRessource """

    def get(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Status of my email confirmation ?
        EXPOSED
        """

        mylogger.LOGGER.info("/email-status - GET - status")

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

        player = players.Player.find_by_identifier(sql_executor, player_id)
        del sql_executor

        if player is None:
            flask_restful.abort(404, msg=f"Player with id {player_id} doesn't exist")

        assert player is not None
        data = {'email_status': player.email_status}
        return data, 200


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

        sql_executor = database.SqlExecutor()

        admin_pseudo = players.Player.find_admin_pseudo(sql_executor)
        if pseudo != admin_pseudo:
            del sql_executor
            flask_restful.abort(403, msg="You do not seem to be site administrator so you are not allowed to maintain")

        print("MAINTENANCE - start !!!", file=sys.stderr)

        for player in players.Player.inventory(sql_executor):
            player.update_database(sql_executor)

        sql_executor.commit()

        del sql_executor

        print("MAINTENANCE - done !!!", file=sys.stderr)

        data = {'msg': "maintenance done"}
        return data, 200

# ---------------------------------
# main
# ---------------------------------


def main() -> None:
    """ main """

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
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']

    waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
