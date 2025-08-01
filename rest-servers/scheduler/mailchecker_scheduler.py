#!/usr/bin/env python3


"""
File : mailcheckerer_scheduler.py

Check emails sender still OK
"""

import typing

import requests
import flask_restful  # type: ignore

import mylogger
import lowdata


# need one
SESSION = requests.Session()

# admin id
EMAIL_ADMIN = "jeremie.lefrancois@gmail.com"


def email_checking_message() -> typing.Tuple[str, str]:
    """ email_checking_message """

    subject = "Ceci est un courriel de verification que les courriels partent bien du site !"
    body = "Bonjour !\n"
    body += "\n"
    body += "Vous recevez cet courriel parce que vous êtes administrateur du site."
    body += "\n"
    body += "\n"
    return subject, body


def run() -> None:
    """ mailchecker scheduler """

    admin_pseudo = EMAIL_ADMIN

    # get a message
    subject, body = email_checking_message()
    json_dict = {
        'subject': subject,
        'body': body,
        'email': admin_pseudo,
    }

    # send it (no token)
    host = lowdata.SERVER_CONFIG['EMAIL']['HOST']
    port = lowdata.SERVER_CONFIG['EMAIL']['PORT']
    url = f"{host}:{port}/send-email-simple"
    req_result = SESSION.post(url, data=json_dict)
    if req_result.status_code != 200:
        mylogger.LOGGER.error("ERROR = %s", req_result.text)
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        mylogger.LOGGER.error("Mailchecker Scheduler ERROR...")
        flask_restful.abort(400, msg=f"Failed to send email to {admin_pseudo} : {message}")

    mylogger.LOGGER.info("Mailchecker Scheduler SUCCESS...")


if __name__ == '__main__':
    assert False, "Do not run this script directly"
