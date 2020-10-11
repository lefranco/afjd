#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing
import json

import flask
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore

import mylogger
import lowdata
import solver

APP = flask.Flask(__name__)
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

        args = SOLVER_PARSER.parse_args()

        variant_json = args['variant']
        variant = json.loads(variant_json)

        advancement = int(args['advancement'])

        situation_json = args['situation']
        situation = json.loads(situation_json)

        orders_json = args['orders']
        orders = json.loads(orders_json)

        role = None
        if args['role'] is not None and args['role'] != 0:
            role = int(args['role'])

        names_json = args['names']
        names = json.loads(names_json)

        returncode, stderr, stdout, situation_result, orders_result = solver.solve(variant, advancement, situation, orders, role, names)

        if returncode != 0:

            data_error = {
                'stderr': stderr,
                'stdout': stdout,
            }

            return data_error, 404

        data = {
            'stderr': stderr,
            'stdout': stdout,
            'situation_result': situation_result,
            'orders_result': orders_result,
        }

        return data, 201


def main() -> None:
    """ main """

    mylogger.start_logger(__name__)
    lowdata.load_servers_config()

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['SOLVER']['PORT']
    APP.run(debug=True, port=port)


if __name__ == '__main__':
    main()
