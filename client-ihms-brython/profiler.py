""" profiler """


import time

START_TIME = time.time()

import json  # pylint: disable=wrong-import-order,wrong-import-position # noqa: E402

from browser import ajax   # pylint: disable=import-error,wrong-import-position # noqa: E402
from browser.local_storage import storage  # pylint: disable=import-error,wrong-import-position # noqa: E402


ADDRESS_ADMIN = "1"


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
        self._table = {}
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

    def send_report(self, pseudo, version, destination, timeout):
        """ send_report """

        def reply_callback(_):
            pass

        def noreply_callback():
            pass

        subject = f"stats pour {pseudo}"
        body = ""
        body += f"{self}"
        body += "\n\n"
        body += f"overhead profiler {ELAPSED=}"
        body += "\n\n"
        body += f"version : {version}"
        body += "\n\n"

        json_dict = {
            'pseudo': pseudo,
            'addressees': ADDRESS_ADMIN,
            'subject': subject,
            'body': body,
            'force': 1,
        }

        host, port = destination
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=timeout, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    def __str__(self):
        return f"{self._elapsed}s\n\n" + "\n".join([f"{n} : {m}" for n, m in self._table.items()])


END_TIME = time.time()
ELAPSED = END_TIME - START_TIME
