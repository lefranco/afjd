#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import argparse

import waitress
import flask
import flask_cors
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore

import lowdata
import mylogger
import populate
import emails
import database


APP = flask.Flask(__name__)
flask_cors.CORS(APP)
API = flask_restful.Api(APP)

EMAIL_PARSER = flask_restful.reqparse.RequestParser()
EMAIL_PARSER.add_argument('email_value', type=str, required=True)
EMAIL_PARSER.add_argument('code', type=int, required=True)


@API.resource('/emails')
class EmailsRessource(flask_restful.Resource):  # type: ignore
    """ EmailsRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        add an email for a player
        PROTECTED : called only by player block (account creation/email change)
        """

        mylogger.LOGGER.info("/emails - POST - adding/updating one email")

        args = EMAIL_PARSER.parse_args(strict=True)
        email_value = args['email_value']
        code = args['code']

        email = emails.Email(email_value, code)
        email.update_database()

        data = {'msg': 'Email was added or updated'}
        return data, 201

@API.resource('/check-email')
class CheckEmailRessource(flask_restful.Resource):  # type: ignore
    """ CheckEmailRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Check if code is correct for email.
        PROTECTED : called by block players
        """

        mylogger.LOGGER.info("/check-email - POST - checking code for email")

        args = EMAIL_PARSER.parse_args(strict=True)
        email_value = args['email_value']
        code = args['code']

        email = emails.Email.find_by_value(email_value)
        if email is None:
            flask_restful.abort(404, msg=f"Email {email_value} does not exists")

        assert email is not None
        if email.code != code:
            flask_restful.abort(401, msg="Code is incorrect")

        data = {'msg': 'Email is correct'}
        return data, 200

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

    # emergency
    if not database.db_present():
        mylogger.LOGGER.info("Emergency populate procedure")
        populate.populate()

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['EMAIL']['PORT']

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
