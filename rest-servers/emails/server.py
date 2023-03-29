#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import argparse
import queue
import threading
import time
import requests

import waitress
import flask
import flask_cors
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore

import lowdata
import mylogger
import populate
import database
import mailer


APP = flask.Flask(__name__)
flask_cors.CORS(APP)
API = flask_restful.Api(APP)

SESSION = requests.Session()

SEND_EMAIL_PARSER = flask_restful.reqparse.RequestParser()
SEND_EMAIL_PARSER.add_argument('subject', type=str, required=True)
SEND_EMAIL_PARSER.add_argument('body', type=str, required=True)
SEND_EMAIL_PARSER.add_argument('addressees', type=str, required=True)

SEND_EMAIL_SUPPORT_PARSER = flask_restful.reqparse.RequestParser()
SEND_EMAIL_SUPPORT_PARSER.add_argument('subject', type=str, required=True)
SEND_EMAIL_SUPPORT_PARSER.add_argument('body', type=str, required=True)

SEND_EMAIL_WELCOME_PARSER = flask_restful.reqparse.RequestParser()
SEND_EMAIL_WELCOME_PARSER.add_argument('subject', type=str, required=True)
SEND_EMAIL_WELCOME_PARSER.add_argument('body', type=str, required=True)
SEND_EMAIL_WELCOME_PARSER.add_argument('email', type=str, required=True)


# time to wait after sending a message
PAUSE_BETWEEN_SENDS_SEC = 10

# time to wait after failure
PAUSE_BETWEEN_RETRIES_SEC = 15 * 60

# how many failures before saying failed
MAX_ERROR_COUNTER_FAILURE = 3

# to transmit messages to send
MESSAGE_QUEUE: queue.Queue[typing.Tuple[typing.Optional[str], str, str, str]] = queue.Queue()


def sender_threaded_procedure() -> None:
    """ does the actual sending of messages """

    with APP.app_context():

        error_counter = 0

        while True:

            # from queue
            pseudo, subject, body, addressee = MESSAGE_QUEUE.get()

            if pseudo is None:
                mylogger.LOGGER.info("actually sending an email to %s using no account", addressee)
            else:
                mylogger.LOGGER.info("actually sending an email to %s using account %s", addressee, pseudo)

            # send
            status, exception = mailer.send_mail(subject, body, addressee)

            # send ok
            if status:
                error_counter = 0
                time.sleep(PAUSE_BETWEEN_SENDS_SEC)
                continue

            # Failed !

            # log
            if pseudo is None:
                mylogger.LOGGER.info("*** Failed sending an email to %s using no account", addressee)
            else:
                mylogger.LOGGER.info("*** Failed sending an email to %s using account %s", addressee, pseudo)

            subject2 = "Echec à l'envoi d'un message !"

            # make and send email report (unsure to be successful)
            body2 = ""
            body2 += f"Destinataire : {addressee}"
            body2 += "\n"
            body2 += f"Sujet : {subject}"
            body2 += "\n"
            if pseudo is not None:
                body2 += f"Compte utilisé : {pseudo}"
                body2 += "\n"
            body2 += f"Exception produite : {exception}"
            body2 += "\n"
            status2, _ = mailer.send_mail(subject2, body2, EMAIL_SUPPORT)

            if not status2:
                mylogger.LOGGER.info("*** Also failed to send report to admin !")

            # put failed message back on queue
            MESSAGE_QUEUE.put((pseudo, subject, body, addressee))

            # count errors
            error_counter += 1
            if error_counter >= MAX_ERROR_COUNTER_FAILURE:
                mylogger.LOGGER.error("*** GIVING UP SENDING EMAILS FOR THE MOMENT")
                time.sleep(PAUSE_BETWEEN_RETRIES_SEC)
                mylogger.LOGGER.error("*** NOW RESUMING SENDING EMAILS...")


@API.resource('/send-email-welcome')
class SendMailWelcomeRessource(flask_restful.Resource):  # type: ignore
    """ SendMailWelcomeRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Sends an email of welcome
        EXPOSED
        """

        mylogger.LOGGER.info("/send-mail-welcome - POST - sending welcome email")

        args = SEND_EMAIL_WELCOME_PARSER.parse_args(strict=True)

        subject = args['subject']
        body = args['body']
        email_newcommer = args['email']

        MESSAGE_QUEUE.put((None, subject, body, email_newcommer))

        data = {'msg': 'Email was successfully queued to be sent to newcomer'}
        return data, 200


@API.resource('/send-email-support')
class SendMailSupportRessource(flask_restful.Resource):  # type: ignore
    """ SendMailSupportRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Sends an email to support
        EXPOSED
        """

        mylogger.LOGGER.info("/send-mail-support - POST - sending email to support")

        args = SEND_EMAIL_SUPPORT_PARSER.parse_args(strict=True)

        subject = args['subject']
        body = args['body']

        MESSAGE_QUEUE.put((None, subject, body, EMAIL_SUPPORT))

        data = {'msg': 'Email was successfully queued to be sent to support'}
        return data, 200


@API.resource('/send-email')
class SendEmailRessource(flask_restful.Resource):  # type: ignore
    """ SendEmailRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        send an email
        PROTECTED : called only by player block (account creation/email change)
        """

        mylogger.LOGGER.info("/send-email - POST - sending email")

        args = SEND_EMAIL_PARSER.parse_args(strict=True)

        subject = args['subject']
        body = args['body']
        addressees = args['addressees']
        addressees_list = addressees.split(',')

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

        # any token goes
        pseudo = req_result.json()['logged_in_as']

        for addressee in addressees_list:
            MESSAGE_QUEUE.put((pseudo, subject, body, addressee))

        data = {'msg': 'Email was successfully queued to be sent'}
        return data, 200


def load_support_config() -> None:
    """ load_support_config """

    support_config = lowdata.ConfigFile('./config/support.ini')
    for support in support_config.section_list():

        assert support == 'support', "Section name is not 'support' in support configuration file"
        support_data = support_config.section(support)

    global EMAIL_SUPPORT
    EMAIL_SUPPORT = support_data['EMAIL_SUPPORT']


EMAIL_SUPPORT = ''


# ---------------------------------
# main
# ---------------------------------


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', required=False, help='mode debug to test stuff', action='store_true')
    args = parser.parse_args()

    mylogger.start_logger(__name__)
    lowdata.load_servers_config()
    load_support_config()
    mailer.load_mail_config(APP)

    # emergency
    if not database.db_present():

        mylogger.LOGGER.info("Emergency populate procedure")

        sql_executor = database.SqlExecutor()
        populate.populate(sql_executor)
        sql_executor.commit()
        del sql_executor

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['EMAIL']['PORT']

    # use separate thread to send messages
    sender_thread = threading.Thread(target=sender_threaded_procedure, daemon=True)
    sender_thread.start()

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
