""" check """

from json import dumps, loads

from browser import alert, ajax  # pylint: disable=import-error

import config
import sys


class MyException(Exception):
    def __init__(self, message):
        super().__init__(message)


def check_back_end_present():
    """ check_back_end_present """

    def noreply_callback(_):
        raise MyException("Pas de réponse dans les temps")

    def reply_callback(req):
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au test du back end: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au test du back end : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            raise MyException("Réponse inappropriée")

    json_dict = {}

    host = config.SERVER_CONFIG['USER']['HOST']
    port = config.SERVER_CONFIG['USER']['PORT']
    url = f"{host}:{port}/check"

    # checking backend is alive: do not need a token
    ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)


# check backend is present
try:
    check_back_end_present()
except:  # noqa: E722 pylint: disable=bare-except
    alert("Mmm. Il semble que le back end ne fonctionne pas. Le mieux ? Contacter le bureau de l'Association...")
    raise SystemExit("Fin du programme Brython")
