#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import json
import argparse

import waitress
import flask
import flask_cors
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore

import mylogger
import lowdata
import solver

APP = flask.Flask(__name__)
flask_cors.CORS(APP)
API = flask_restful.Api(APP)


SOLVER_PARSER = flask_restful.reqparse.RequestParser()
SOLVER_PARSER.add_argument('variant', type=str, required=True)
SOLVER_PARSER.add_argument('advancement', type=int, required=True)
SOLVER_PARSER.add_argument('situation', type=str, required=True)
SOLVER_PARSER.add_argument('orders', type=str, required=True)
SOLVER_PARSER.add_argument('role', type=int, required=False)
SOLVER_PARSER.add_argument('names', type=str, required=True)


@API.resource('/solve')
class SolveRessource(flask_restful.Resource):  # type: ignore
    """ SolveRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:  # pylint: disable=no-self-use
        """
        Performs an adjudication
        EXPOSED (since there can be simulation)
        """

        mylogger.LOGGER.info("/solve - POST - solver called")

        args = SOLVER_PARSER.parse_args(strict=True)

        variant_submitted = args['variant']

        try:
            variant = json.loads(variant_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert variant from json to text ?")

        advancement = int(args['advancement'])

        situation_submitted = args['situation']

        try:
            situation = json.loads(situation_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert situation from json to text ?")

        orders_submitted = args['orders']

        try:
            orders = json.loads(orders_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert orders from json to text ?")

        role = None
        if args['role'] is not None and args['role'] != 0:
            role = int(args['role'])

        names_submitted = args['names']

        try:
            names = json.loads(names_submitted)
        except json.JSONDecodeError:
            flask_restful.abort(400, msg="Did you convert names from json to text ?")


        print(" solve input : {situation=}")
        print(" solve input : {orders=}")
        print(" solve input : {names=}")

        returncode, stderr, stdout, situation_result, orders_result = solver.solve(variant, advancement, situation, orders, role, names)

        if returncode != 0:

            data_error = {
                'stderr': stderr,
                'stdout': stdout,
            }

            return data_error, 404

        print(" solve output : {situation_result=}")
        print(" solve output : {orders_result=}")

        data = {
            'stderr': stderr,
            'stdout': stdout,
            'situation_result': situation_result,
            'orders_result': orders_result,
        }

        return data, 201


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', required=False, help='mode debug to test stuff', action='store_true')
    args = parser.parse_args()

    mylogger.start_logger(__name__)
    lowdata.load_servers_config()

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['SOLVER']['PORT']

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
