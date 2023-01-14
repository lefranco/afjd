#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import argparse
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

        status = mailer.send_mail(subject, body, [EMAIL_SUPPORT])
        if not status:
            flask_restful.abort(400, msg="Failed to send message to support")

        data = {'msg': 'Email was send successfully to support'}
        return data, 200


@API.resource('/send-email')
class SendEmailRessource(flask_restful.Resource):  # type: ignore
    """ SendEmailRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        send an email
        PROTECTED : called only by player block (account creation/email change)
        """

        mylogger.LOGGER.info("/send-email - POST - sending one email")

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

        status = mailer.send_mail(subject, body, addressees_list)
        if not status:
            flask_restful.abort(400, msg="Failed to send message to player")

        data = {'msg': 'Email was send successfully'}
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

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
