#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import argparse
import datetime

import flask
import flask_cors  # type: ignore
import flask_jwt_extended  # type: ignore
import werkzeug.security
import waitress

import lowdata
import mylogger
import populate
import users
import logins
import failures
import database


APP = flask.Flask(__name__)
flask_cors.CORS(APP)

# Setup the Flask-JWT-Extended extension
SECRET_CONFIG = lowdata.ConfigFile('./config/secret.ini')
SECRET_DATA = SECRET_CONFIG.section('JWT_SECRET_KEY')
APP.config['JWT_SECRET_KEY'] = SECRET_DATA['key']

# default is 15 minutes - put it to one hour !
APP.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

# Seems JWT variable is not used in this implementation but could be later on...
JWT = flask_jwt_extended.JWTManager(APP)

# ---------------------------------
# users
# ---------------------------------


@APP.route('/add', methods=['POST'])
def add_user() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    add an user account
    PROTECTED (called by players block)
    """

    mylogger.LOGGER.info("/add - POST - adding one user")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    user_name = flask.request.json.get('user_name', None)
    if not user_name:
        return flask.jsonify({"msg": "Missing user_name parameter"}), 400

    password = flask.request.json.get('password', None)
    if not password:
        return flask.jsonify({"msg": "Missing password parameter"}), 400

    sql_executor = database.SqlExecutor()

    user = users.User.find_by_name(sql_executor, user_name)

    if user is not None:
        del sql_executor
        return flask.jsonify({"msg": "User already exists"}), 400

    pwd_hash = werkzeug.security.generate_password_hash(password)
    user = users.User(user_name, pwd_hash)

    user.update_database(sql_executor)

    sql_executor.commit()
    del sql_executor

    return flask.jsonify({"msg": "User was added"}), 201


@APP.route('/remove', methods=['POST'])
@flask_jwt_extended.jwt_required()  # type: ignore   # pylint: disable=no-value-for-parameter
def remove_user() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    remove an user account
    PROTECTED (called by players block)
    """

    mylogger.LOGGER.info("/remove - POST - removing one user")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    user_name = flask.request.json.get('user_name', None)
    if not user_name:
        return {"msg": "Missing user_name parameter"}, 400

    sql_executor = database.SqlExecutor()

    user = users.User.find_by_name(sql_executor, user_name)

    if user is None:
        del sql_executor
        return {"msg": "User does not exist"}, 404

    logged_in_as = flask_jwt_extended.get_jwt_identity()
    if logged_in_as != user_name:
        del sql_executor
        return {"msg": "This is not you ! Good try !"}, 405

    assert user is not None

    user.delete_database(sql_executor)

    sql_executor.commit()
    del sql_executor

    return flask.jsonify({"msg": "User was removed"}), 200


@APP.route('/change', methods=['POST'])
@flask_jwt_extended.jwt_required()  # type: ignore   # pylint: disable=no-value-for-parameter
def change_user() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    change password of an account
    PROTECTED (called by players block)
    """

    mylogger.LOGGER.info("/change - POST - updating one user (change password)")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    user_name = flask.request.json.get('user_name', None)
    if not user_name:
        return {"msg": "Missing user_name parameter"}, 400

    password = flask.request.json.get('password', None)
    if not password:
        return flask.jsonify({"msg": "Missing password parameter"}), 400

    sql_executor = database.SqlExecutor()

    user = users.User.find_by_name(sql_executor, user_name)

    if user is None:
        del sql_executor
        return {"msg": "User does not exist"}, 404

    logged_in_as = flask_jwt_extended.get_jwt_identity()
    if logged_in_as != user_name:
        del sql_executor
        return {"msg": "This is not you ! Good try !"}, 405

    assert user is not None
    pwd_hash = werkzeug.security.generate_password_hash(password)
    user.pwd_hash = pwd_hash

    user.update_database(sql_executor)

    sql_executor.commit()
    del sql_executor

    return flask.jsonify({"msg": "User was changed"}), 201


@APP.route('/login', methods=['POST'])
def login_user() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    Provide a method to create access tokens. The create_access_token()
    function is used to actually generate the token, and you can return
    it to the caller however you choose.
    EXPOSED : called by all ihms that have a login/password input
    """

    mylogger.LOGGER.info("/login - POST - login in a user")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    user_name = flask.request.json.get('user_name', None)
    if not user_name:
        return {"msg": "Missing user_name parameter"}, 400

    password = flask.request.json.get('password', None)
    if not password:
        return flask.jsonify({"msg": "Missing password parameter"}), 400

    sql_executor = database.SqlExecutor()

    user = users.User.find_by_name(sql_executor, user_name)

    if user is None or not werkzeug.security.check_password_hash(user.pwd_hash, password):  # type: ignore

        # we keep a trace of the failure
        failure = failures.Failure(user_name)
        failure.update_database(sql_executor)

        sql_executor.commit()
        del sql_executor

        return flask.jsonify({"msg": "Bad user_name or password"}), 401

    # we keep a trace of the login
    login = logins.Login(user_name)
    login.update_database(sql_executor)

    sql_executor.commit()
    del sql_executor

    # Identity can be any data that is json serializable
    access_token = flask_jwt_extended.create_access_token(identity=user_name)
    return flask.jsonify(AccessToken=access_token), 200


@APP.route('/verify', methods=['GET'])
@flask_jwt_extended.jwt_required()  # type: ignore   # pylint: disable=no-value-for-parameter
def verify_user() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    Protect a view with jwt_required, which requires a valid access token
    in the request to access.
    EXPOSED : generally not called directly, called by game and player blocks
       BUT may be called to check validity of token...
    """

    mylogger.LOGGER.info("/verify - GET - verifying a user")

    # Access the identity of the current user with get_jwt_identity
    logged_in_as = flask_jwt_extended.get_jwt_identity()
    return flask.jsonify(logged_in_as=logged_in_as), 200


@APP.route('/usurp', methods=['POST'])
@flask_jwt_extended.jwt_required()  # type: ignore   # pylint: disable=no-value-for-parameter
def usurp_user() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    Protect a view with jwt_required, which requires a valid access token
    in the request to access.
    EXPOSED : For an account to get token of another account
    """

    mylogger.LOGGER.info("/usurp - POST - usurping a user")

    # Access the identity of the current user with get_jwt_identity
    logged_in_as = flask_jwt_extended.get_jwt_identity()

    # TODO improve this with real admin account
    if logged_in_as != 'Palpatine':
        return {"msg": "Wrong user_name to perform operation"}, 403

    usurped_user_name = flask.request.json.get('usurped_user_name', None)
    if not usurped_user_name:
        return {"msg": "Missing usurped_user_name parameter"}, 400

    sql_executor = database.SqlExecutor()
    user = users.User.find_by_name(sql_executor, usurped_user_name)
    del sql_executor

    if user is None:
        return flask.jsonify({"msg": "Bad usurped_user_name"}), 401

    # Identity can be any data that is json serializable
    access_token = flask_jwt_extended.create_access_token(identity=usurped_user_name)
    return flask.jsonify(AccessToken=access_token), 200


@APP.route('/logins_list', methods=['POST'])
@flask_jwt_extended.jwt_required()  # type: ignore   # pylint: disable=no-value-for-parameter
def logins_list() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    Protect a view with jwt_required, which requires a valid access token
    in the request to access.
    EXPOSED : Get list of all logins
    """

    mylogger.LOGGER.info("/logins_list - POST - list of all logins")

    # Access the identity of the current user with get_jwt_identity
    logged_in_as = flask_jwt_extended.get_jwt_identity()

    # TODO improve this with real admin account
    if logged_in_as != 'Palpatine':
        return {"msg": "Wrong user_name to perform operation"}, 403

    sql_executor = database.SqlExecutor()
    login_list = logins.Login.find_all(sql_executor)
    del sql_executor

    return flask.jsonify({"login_list": login_list}), 200


@APP.route('/failures_list', methods=['POST'])
@flask_jwt_extended.jwt_required()  # type: ignore   # pylint: disable=no-value-for-parameter
def failures_list() -> typing.Tuple[typing.Dict[str, typing.Any], int]:
    """
    Protect a view with jwt_required, which requires a valid access token
    in the request to access.
    EXPOSED : Get list of all failures
    """

    mylogger.LOGGER.info("/failures_list - POST - list of all failures (failed logins)")

    # Access the identity of the current user with get_jwt_identity
    logged_in_as = flask_jwt_extended.get_jwt_identity()

    # TODO improve this with real admin account
    if logged_in_as != 'Palpatine':
        return {"msg": "Wrong user_name to perform operation"}, 403

    sql_executor = database.SqlExecutor()
    failure_list = failures.Failure.find_all(sql_executor)
    del sql_executor

    return flask.jsonify({"failure_list": failure_list}), 200

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

        sql_executor = database.SqlExecutor()
        populate.populate(sql_executor)
        sql_executor.commit()
        del sql_executor

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['USER']['PORT']

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
