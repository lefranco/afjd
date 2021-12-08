""" profiler """


import time
import json

from browser import ajax   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import config

VERSION = "optimisée v2"


class Measure:
    """ Measure """

    def __init__(self):
        now = time.time()
        self._start = now
        self._stop = None

    def terminate(self):
        """ terminate """

        now = time.time()
        self._stop = now

    def __str__(self):
        elapsed = self._stop - self._start
        elapsed_ms = round(elapsed * 1000.)
        return f"{elapsed_ms}ms"


class Profiler:
    """ Profiler """

    def __init__(self):
        self._table = dict()
        self._current = None
        self._start = time.time()
        self._stop = None
        self._elapsed = None

    def start(self, name):
        """ start """

        prev_name = self._current
        if prev_name:
            old_measure = self._table[prev_name]
            old_measure.terminate()
        new_measure = Measure()
        self._table[name] = new_measure
        self._current = name

    def stop(self):
        """ stop """

        prev_name = self._current
        old_measure = self._table[prev_name]
        old_measure.terminate()
        self._stop = time.time()
        self._elapsed = self._stop - self._start

    def send_report(self, pseudo):
        """ send_report """

        def reply_callback(_):
            pass

        subject = f"stats jouer la partie pour {pseudo}"
        body = ""
        body += f"{self}"
        body += "\n\n"
        body += f"version : {VERSION}"
        body += "\n\n"

        addressed_user_name = 'Palpatine'

        players_dict = common.get_players()
        if not players_dict:
            return

        addressed_id = players_dict[addressed_user_name]
        addressees = [addressed_id]
        json_dict = {
            'pseudo': pseudo,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'force': 1,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def __str__(self):
        return f"{self._elapsed}s\n\n" + "\n".join([f"{n} : {m}" for n, m in self._table.items()])
