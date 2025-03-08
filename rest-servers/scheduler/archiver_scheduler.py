#!/usr/bin/env python3


"""
File : archiver_scheduler.py

Archive finished games
"""

import typing

import requests

import mylogger
import lowdata


SESSION = requests.Session()


def run(jwt_token: str) -> None:
    """ archiver_scheduler """

    # ========================
    # archive finished games
    # ========================

    json_dict: typing.Dict[str, typing.Any] = {}

    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/archive-finished-games"
    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to perform Archiving")
        return

    # all done !
    mylogger.LOGGER.info("=== Hurray, Archiving was performed !")


if __name__ == '__main__':
    assert False, "Do not run this script directly"
