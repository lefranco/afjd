#!/usr/bin/env python3


"""
File : extracter_scheduler.py

Get data from HelloAsso
"""

import time

import requests

import mylogger
import lowdata


# easy on server
TIMEOUT_SERVER = 5

# root
SERVER = "https://api.helloasso.com"

# for getting token
TOKEN_DOMAIN = "oauth2/token"

# for getting data
ORGANIZATIONS_DOMAIN = 'v5/organizations'
SLUG = 'association-francophone-des-joueurs-de-diplomacy'

# need one
SESSION = requests.Session()


def run(jwt_token: str, client_id: str, client_secret: str) -> None:
    """ extracter scheduler """

    json_dict = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }

    req_result = SESSION.post(f"{SERVER}/{TOKEN_DOMAIN}", data=json_dict)
    if req_result.status_code != 200:
        mylogger.LOGGER.error("ERROR = %s", req_result.text)
        return

    # easy on server
    time.sleep(5)

    result_json = req_result.json()

    if 'access_token' not in result_json:
        mylogger.LOGGER.error("ERROR NO TOKEN")
        return

    access_token = result_json['access_token']

    page_index = 1
    target_form = None
    done = False
    raised = 0
    members = []
    while not done:

        req_result = SESSION.get(f"{SERVER}/{ORGANIZATIONS_DOMAIN}/{SLUG}/payments?pageIndex={page_index}", headers={'Authorization': f"Bearer {access_token}"})
        if req_result.status_code != 200:
            mylogger.LOGGER.error("ERROR = %s", req_result.text)
            return

        # easy on server
        time.sleep(5)

        result_json = req_result.json()

        if 'data' not in result_json:
            mylogger.LOGGER.error("ERROR NO DATA")
            return

        data = result_json['data']

        for datum in data:

            # extract form
            form_name = datum['order']['formName']

            # no form => first form = target form
            if target_form is None:
                target_form = form_name

            # different form from first => we are done
            if form_name != target_form:
                done = True
                break

            # extract payer information
            payer_name = f"{datum['payer']['firstName'].title()} {datum['payer']['lastName'].title()}"

            # extract amout (given in cents)
            amount = int(datum['amount'] // 100)

            # store for output
            members.append(payer_name)
            raised += amount

        page_index += 1

    # easy on server
    time.sleep(5)

    # put in database raised

    json_dict2 = {
        'topic': 'raised',
        'content': raised
    }

    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/news"
    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, json=json_dict2)
    if req_result.status_code != 201:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to store hello asso data (raised)")
        return

    # easy on server
    time.sleep(5)

    # put in database members

    json_dict3 = {
        'topic': 'members',
        'content': ', '.join(members)
    }

    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/news"
    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, json=json_dict3)
    if req_result.status_code != 201:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to store hello asso data (members)")
        return


if __name__ == '__main__':
    assert False, "Do not run this script directly"
