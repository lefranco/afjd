""" profiler """


import time

START_TIME = time.time()

import json  # pylint: disable=wrong-import-order,wrong-import-position # noqa: E402

from browser import ajax   # pylint: disable=import-error,wrong-import-position # noqa: E402
from browser.local_storage import storage  # pylint: disable=import-error,wrong-import-position # noqa: E402


ADDRESS_ADMIN = "1"


class Measure:
    """ Measure """

    def __init__(self, name):
        self._name = name
        now = time.time()
        self._start = now
        self._stop = None

    def terminate(self):
        """ terminate """
        now = time.time()
        self._stop = now

    def duration(self):
        """ duration """
        return self._stop - self._start

    def __str__(self):
        elapsed = self.duration()
        elapsed_ms = round(elapsed * 1000.)
        return f"{self._name} : {elapsed_ms}ms"


class Profiler:
    """ Profiler """

    def __init__(self):
        self._measures = []
        self._current = None
        self._start = time.time()
        self._stop = None
        self._sum = 0.
        self._elapsed = None

    def start(self, name):
        """ start """

        if self._current:
            return

        new_measure = Measure(name)
        self._current = new_measure

    def stop(self):
        """ stop """

        if not self._current:
            return

        cur_measure = self._current
        cur_measure.terminate()
        self._measures.append(cur_measure)
        self._current = None

        # sum up
        self._sum += cur_measure.duration()

        # in case this is last
        self._stop = time.time()
        self._elapsed = self._stop - self._start

    def send_report(self, pseudo, version, destination, timeout):
        """ send_report """

        def reply_callback(_):
            pass

        def noreply_callback():
            pass

        subject = f"stats for {pseudo} ({self._elapsed})"
        body = ""
        body += f"{self}"
        body += "\n\n"
        body += f"overhead profiler {ELAPSED=}"
        body += "\n\n"
        body += f"sum {self._sum}"
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
        return "\n".join([str(m) for m in self._measures])


PROFILER = Profiler()

END_TIME = time.time()
ELAPSED = END_TIME - START_TIME
