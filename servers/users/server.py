#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import argparse
import datetime
import time
import threading

import waitress
import flask
import flask_cors
import flask_jwt_extended
import werkzeug.security
import requests

import lowdata
import mylogger
import populate
import users
import logins
import failures
import database

SESSION = requests.Session()


APP = flask.Flask(__name__)
flask_cors.CORS(APP)

# Setup the Flask-JWT-Extended extension
SECRET_CONFIG = lowdata.ConfigFile('./config/secret.ini')
SECRET_DATA = SECRET_CONFIG.section('JWT_SECRET_KEY')
APP.config['JWT_SECRET_KEY'] = SECRET_DATA['key']

# how long token is valid - beware they say no more than several hours...
LOGIN_TOKEN_DURATION_DAY = 20

# how long token is valid - beware they say no more than several hours...
RESCUE_TOKEN_DURATION_MIN = 15

# how long token is valid - beware they say no more than several hours...
USURP_TOKEN_DURATION_MIN = 10

# Seems JWT variable is not used in this implementation but could be later on...
JWT = flask_jwt_extended.JWTManager(APP)

# to avoid repeat logins
NO_LOGIN_REPEAT_DELAY_SEC = 15

# to avoid repeat rescue
NO_RESCUE_REPEAT_DELAY_SEC = 300

# ---------------------------------
# users
# ---------------------------------


class RepeatPreventer(typing.Dict[str, float]):
    """ Table """

    def __init__(self, no_repeat_delay_sec: int):
        self._no_repeat_delay_sec = no_repeat_delay_sec
        super().__init__()

    def can(self, user_name: str) -> bool:
        """ can """

        if user_name not in self:
            return True

        now = time.time()
        return now > self[user_name] + self._no_repeat_delay_sec

    def did(self, user_name: str) -> None:
        """ did """

        # do it
        now = time.time()
        self[user_name] = now

        # house clean
        obsoletes = [k for (k, v) in self.items() if v < now - self._no_repeat_delay_sec]
        for key in obsoletes:
            del self[key]


@APP.route('/add', methods=['POST'])
def add_user() -> typing.Tuple[typing.Any, int]:
    """
    add an user account
    PROTECTED (called by players block)
    """

    mylogger.LOGGER.info("/add - POST - adding one user")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    assert flask.request.json is not None
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
def remove_user() -> typing.Tuple[typing.Any, int]:
    """
    remove an user account
    PROTECTED (called by players block)
    """

    mylogger.LOGGER.info("/remove - POST - removing one user")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    assert flask.request.json is not None
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
def change_user() -> typing.Tuple[typing.Any, int]:
    """
    change password of an account
    PROTECTED (called by players block)
    """

    mylogger.LOGGER.info("/change - POST - updating one user (change password)")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    assert flask.request.json is not None
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


LOGIN_REPEAT_PREVENTER = RepeatPreventer(NO_LOGIN_REPEAT_DELAY_SEC)
LOGIN_LOCK = threading.Lock()

RESCUE_REPEAT_PREVENTER = RepeatPreventer(NO_RESCUE_REPEAT_DELAY_SEC)
RESCUE_LOCK = threading.Lock()


@APP.route('/login', methods=['POST'])
def login_user() -> typing.Tuple[typing.Any, int]:
    """
    Provide a method to create access tokens. The create_access_token()
    function is used to actually generate the token, and you can return
    it to the caller however you choose.
    EXPOSED : called by all ihms that have a login/password input
    """

    mylogger.LOGGER.info("/login - POST - login in a user")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    assert flask.request.json is not None
    user_name = flask.request.json.get('user_name', None)
    if not user_name:
        return {"msg": "Missing user_name parameter"}, 400

    password = flask.request.json.get('password', None)
    if not password:
        return flask.jsonify({"msg": "Missing password parameter"}), 400

    # not mandatory
    ip_address = flask.request.json.get('ip_address', 'none')

    sql_executor = database.SqlExecutor()

    with LOGIN_LOCK:

        if not LOGIN_REPEAT_PREVENTER.can(user_name):
            del sql_executor
            return flask.jsonify({"msg": f"You have already tried to login a very short time ago. There must be at least {NO_LOGIN_REPEAT_DELAY_SEC} secs between two attempts..."}), 400

        LOGIN_REPEAT_PREVENTER.did(user_name)

        user = users.User.find_by_name(sql_executor, user_name)

        if user is None:

            del sql_executor
            return flask.jsonify({"msg": "User does not exist"}), 404

        if not werkzeug.security.check_password_hash(user.pwd_hash, password):

            # we keep a trace of the failure if user exists
            failure = failures.Failure(user_name, ip_address)
            failure.update_database(sql_executor)

            sql_executor.commit()
            del sql_executor
            return flask.jsonify({"msg": "Invalid password"}), 403

        # we keep a trace of the login
        login = logins.Login(user_name, ip_address)
        login.update_database(sql_executor)

    sql_executor.commit()
    del sql_executor

    # Identity can be any data that is json serializable
    access_token = flask_jwt_extended.create_access_token(identity=user_name, expires_delta=datetime.timedelta(days=LOGIN_TOKEN_DURATION_DAY))
    return flask.jsonify(AccessToken=access_token, TokenDurationDays=LOGIN_TOKEN_DURATION_DAY), 200


@APP.route('/verify', methods=['GET'])
@flask_jwt_extended.jwt_required()  # type: ignore   # pylint: disable=no-value-for-parameter
def verify_user() -> typing.Tuple[typing.Any, int]:
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
def usurp_user() -> typing.Tuple[typing.Any, int]:
    """
    Protect a view with jwt_required, which requires a valid access token
    in the request to access.
    EXPOSED : For an account to get token of another account
    """

    mylogger.LOGGER.info("/usurp - POST - usurping a user")

    # Access the identity of the current user with get_jwt_identity
    logged_in_as = flask_jwt_extended.get_jwt_identity()

    # get admin pseudo
    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/pseudo-admin"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        print(f"ERROR from server  : {req_result.text}")
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        return {"msg": f"Failed to get pseudo admin {message}"}, 404
    admin_pseudo = req_result.json()

    # check user is admin
    if logged_in_as != admin_pseudo:
        return {"msg": "Wrong user_name to perform operation"}, 403

    assert flask.request.json is not None
    usurped_user_name = flask.request.json.get('usurped_user_name', None)
    if not usurped_user_name:
        return {"msg": "Missing usurped_user_name parameter"}, 400

    sql_executor = database.SqlExecutor()
    user = users.User.find_by_name(sql_executor, usurped_user_name)
    del sql_executor

    if user is None:
        return flask.jsonify({"msg": "Bad usurped_user_name"}), 401

    # Identity can be any data that is json serializable
    access_token = flask_jwt_extended.create_access_token(identity=usurped_user_name, expires_delta=datetime.timedelta(minutes=USURP_TOKEN_DURATION_MIN))

    return flask.jsonify(AccessToken=access_token), 200


@APP.route('/rescue', methods=['POST'])
def rescue_user() -> typing.Tuple[typing.Any, int]:
    """
    Provide a method to create access tokens. The create_access_token()
    function is used to actually generate the token, and you can return
    it to the caller however you choose.
    Rescue procedure : password was forgotten
    No need for password, but the token is sent by email
    EXPOSED : called by all ihms that have password forgotten input
    """

    mylogger.LOGGER.info("/rescue - POST - rescue in a user")

    if not flask.request.is_json:
        return flask.jsonify({"msg": "Missing JSON in request"}), 400

    assert flask.request.json is not None
    user_name = flask.request.json.get('user_name', None)
    if not user_name:
        return {"msg": "Missing user_name parameter"}, 400

    sql_executor = database.SqlExecutor()

    with RESCUE_LOCK:

        if not RESCUE_REPEAT_PREVENTER.can(user_name):
            del sql_executor
            return flask.jsonify({"msg": f"You have already tried to rescue a short time ago. There must be at least {NO_RESCUE_REPEAT_DELAY_SEC} secs between two attempts..."}), 400

        RESCUE_REPEAT_PREVENTER.did(user_name)

        user = users.User.find_by_name(sql_executor, user_name)

        if user is None:

            del sql_executor
            return flask.jsonify({"msg": "User does not exist"}), 404

        # TODO keep a trace of the rescue

        del sql_executor

        # Identity can be any data that is json serializable
        access_token = flask_jwt_extended.create_access_token(identity=user_name, expires_delta=datetime.timedelta(minutes=RESCUE_TOKEN_DURATION_MIN))

        json_dict = {
            'rescued_user': user_name,
            'access_token': access_token
        }

        # pass to player module
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/rescue-player"
        req_result = SESSION.post(url, data=json_dict)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            return {"msg": f"Failed to rescue player {message}"}, 404

        return flask.jsonify({}), 200


@APP.route('/logins_list', methods=['POST'])
@flask_jwt_extended.jwt_required()  # type: ignore   # pylint: disable=no-value-for-parameter
def logins_list() -> typing.Tuple[typing.Any, int]:
    """
    Protect a view with jwt_required, which requires a valid access token
    in the request to access.
    EXPOSED : Get list of all logins
    """

    mylogger.LOGGER.info("/logins_list - POST - list of all logins")

    # Access the identity of the current user with get_jwt_identity
    logged_in_as = flask_jwt_extended.get_jwt_identity()

    # get admin pseudo
    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/pseudo-admin"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        print(f"ERROR from server  : {req_result.text}")
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        return {"msg": f"Failed to get pseudo admin {message}"}, 404
    admin_pseudo = req_result.json()

    # check user is admin
    if logged_in_as != admin_pseudo:
        return {"msg": "Wrong user_name to perform operation"}, 403

    sql_executor = database.SqlExecutor()
    login_list = logins.Login.find_all(sql_executor)
    del sql_executor

    return flask.jsonify({"login_list": login_list}), 200


@APP.route('/failures_list', methods=['POST'])
@flask_jwt_extended.jwt_required()  # type: ignore   # pylint: disable=no-value-for-parameter
def failures_list() -> typing.Tuple[typing.Any, int]:
    """
    Protect a view with jwt_required, which requires a valid access token
    in the request to access.
    EXPOSED : Get list of all failures
    """

    mylogger.LOGGER.info("/failures_list - POST - list of all failures (failed logins)")

    # Access the identity of the current user with get_jwt_identity
    logged_in_as = flask_jwt_extended.get_jwt_identity()

    # get admin pseudo
    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/pseudo-admin"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        print(f"ERROR from server  : {req_result.text}")
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        return {"msg": f"Failed to get pseudo admin {message}"}, 404
    admin_pseudo = req_result.json()

    # check user is admin
    if logged_in_as != admin_pseudo:
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
