#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing

import flask
import flask_jwt_extended  # type: ignore
import werkzeug.security

import lowdata
import mylogger
import populate
import users
import emails
import database


APP = flask.Flask(__name__)

# Setup the Flask-JWT-Extended extension
SECRET_CONFIG = lowdata.ConfigFile('./config/secret.ini')
SECRET_DATA = SECRET_CONFIG.section('JWT_SECRET_KEY')
APP.config['JWT_SECRET_KEY'] = SECRET_DATA['key']

# Seems JWT variable is not used in this implementation but could be later on...
JWT = flask_jwt_extended.JWTManager(APP)


# ---------------------------------
# users
# ---------------------------------

@APP.route('/add-user', methods=['POST'])
def add_user() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    add an user account
    PROTECTED (called by players block)
    """

    mylogger.LOGGER.info("/add-user - POST - adding one user")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    user_name = flask.request.json.get('user_name', None)
    if not user_name:
        return flask.jsonify({"msg": "Missing user_name parameter"}), 400

    password = flask.request.json.get('password', None)
    if not password:
        return flask.jsonify({"msg": "Missing password parameter"}), 400

    user = users.User.find_by_name(user_name)
    if user is not None:
        return flask.jsonify({"msg": "User already exists"}), 400

    pwd_hash = werkzeug.security.generate_password_hash(password)
    user = users.User(user_name, pwd_hash)
    user.update_database()
    return flask.jsonify({"msg": "User was added"}), 201


@APP.route('/remove-user', methods=['POST'])
@flask_jwt_extended.jwt_required  # type: ignore
def remove_user() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    remove an user account
    PROTECTED (called by players block)
    """

    mylogger.LOGGER.info("/remove-user - POST - removing one user")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    user_name = flask.request.json.get('user_name', None)
    if not user_name:
        return {"msg": "Missing user_name parameter"}, 400

    user = users.User.find_by_name(user_name)
    if user is None:
        return {"msg": "User does not exist"}, 404

    logged_in_as = flask_jwt_extended.get_jwt_identity()
    if logged_in_as != user_name:
        return {"msg": "This is not you ! Good try !"}, 400

    assert user is not None
    user.delete_database()

    return flask.jsonify({"msg": "User was removed"}), 200


@APP.route('/change-user', methods=['POST'])
@flask_jwt_extended.jwt_required  # type: ignore
def change_user() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    change password of an account
    PROTECTED (called by players block)
    """

    mylogger.LOGGER.info("/change-user - POST - updating one user (change password)")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    user_name = flask.request.json.get('user_name', None)
    if not user_name:
        return {"msg": "Missing user_name parameter"}, 400

    password = flask.request.json.get('password', None)
    if not password:
        return flask.jsonify({"msg": "Missing password parameter"}), 400

    user = users.User.find_by_name(user_name)
    if user is None:
        return {"msg": "User does not exist"}, 404

    logged_in_as = flask_jwt_extended.get_jwt_identity()
    if logged_in_as != user_name:
        return {"msg": "This is not you ! Good try !"}, 400

    assert user is not None
    pwd_hash = werkzeug.security.generate_password_hash(password)
    user.pwd_hash = pwd_hash
    user.update_database()
    return flask.jsonify({"msg": "User was changed"}), 201


@APP.route('/login-user', methods=['POST'])
def login_user() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    Provide a method to create access tokens. The create_access_token()
    function is used to actually generate the token, and you can return
    it to the caller however you choose.
    EXPOSED : called by all ihms that have a login/password input
    """

    mylogger.LOGGER.info("/login-user - POST - login in a user")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    user_name = flask.request.json.get('user_name', None)
    if not user_name:
        return {"msg": "Missing user_name parameter"}, 400

    password = flask.request.json.get('password', None)
    if not password:
        return flask.jsonify({"msg": "Missing password parameter"}), 400

    user = users.User.find_by_name(user_name)
    if user is None:
        return flask.jsonify({"msg": "Bad user_name or password"}), 401

    if not werkzeug.security.check_password_hash(user.pwd_hash, password):  # type: ignore
        return flask.jsonify({"msg": "Bad user_name or password"}), 401

    # Identity can be any data that is json serializable
    access_token = flask_jwt_extended.create_access_token(identity=user_name)
    return flask.jsonify(access_token=access_token), 200


@APP.route('/verify-user', methods=['GET'])
@flask_jwt_extended.jwt_required  # type: ignore
def verify_user() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    Protect a view with jwt_required, which requires a valid access token
    in the request to access.
    PROTECTED : not called directly, called by game and player blocks
    """

    mylogger.LOGGER.info("/verify-user - GET - verifying a user")

    # Access the identity of the current user with get_jwt_identity
    logged_in_as = flask_jwt_extended.get_jwt_identity()
    return flask.jsonify(logged_in_as=logged_in_as), 200

# ---------------------------------
# emails
# ---------------------------------


@APP.route('/add-email', methods=['POST'])
def add_email() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    add an email for a player
    PROTECTED : called only by player block (account creation/email change)
    """

    mylogger.LOGGER.info("/add-email - POST - adding/updating one email")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    email_value = flask.request.json.get('email_value', None)
    if not email_value:
        return flask.jsonify({"msg": "Missing email_value parameter"}), 400

    code_str = flask.request.json.get('code', None)
    if not code_str:
        return flask.jsonify({"msg": "Missing code parameter"}), 400
    try:
        code = int(code_str)
    except:  # noqa: E722 pylint: disable=bare-except
        return flask.jsonify({"msg": "Code is not integer"}), 400

    email = emails.Email(email_value, code)
    email.update_database()
    return flask.jsonify({"msg": "Email was added or updated"}), 200


@APP.route('/verify-email', methods=['GET'])
def verify_email() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    Check if code is correct for email.
    PROTECTED : called by block players
    """

    mylogger.LOGGER.info("/verify-email - GET - checking code for email")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    email_value = flask.request.json.get('email_value', None)
    if not email_value:
        return flask.jsonify({"msg": "Missing email parameter"}), 400

    code_str = flask.request.json.get('code', None)
    if not code_str:
        return flask.jsonify({"msg": "Missing code parameter"}), 400
    try:
        code = int(code_str)
    except:  # noqa: E722 pylint: disable=bare-except
        return flask.jsonify({"msg": "Code is not integer"}), 400

    email = emails.Email.find_by_value(email_value)
    if email is None:
        return {"msg": "Email does not exist"}, 404

    if email.code != code:
        return flask.jsonify({"msg": "Code is incorrect"}), 401

    return flask.jsonify({"msg": "Email is correct"}), 200

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
        populate.populate()

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['USER']['PORT']
    APP.run(debug=True, port=port)


if __name__ == '__main__':
    main()
