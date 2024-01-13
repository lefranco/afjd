""" profiler

usage :

import profiler


profiler.PROFILER.start_mes("my games")
profiler.PROFILER.start_mes("preambule")

<code to profile>

profiler.PROFILER.stop_mes()
profiler.PROFILER.stop_mes()

pseudo = storage['PSEUDO'] if 'PSEUDO' in storage else '???'
version = storage['VERSION']
destination = config.SERVER_CONFIG['PLAYER']['HOST'], config.SERVER_CONFIG['EMAIL']['PORT']
timeout = config.TIMEOUT_SERVER

profiler.PROFILER.send_report(pseudo, version, destination, timeout)

"""

# pylint: disable=wrong-import-order, wrong-import-position

from time import time

START_TIME = time()

before_json = time()
from json import dumps
after_json = time()
import_json_time = after_json - before_json

from browser import ajax  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

before_user_config = time()
import user_config
after_user_config = time()
import_user_config_time = after_user_config - before_user_config

ADDRESS_ADMIN = "1"


# debug
DEBUG = False


class Measure:
    """ Measure """

    def __init__(self, legend, parent):
        self._legend = legend
        self._start_time = time()
        self._stop_time = None
        self._parent_measure = parent
        self._sub_measures = []

    def terminate(self):
        """ terminate """
        self._stop_time = time()

    def insert_sub_measure(self, sub_measure):
        """ insert_sub_measure """
        self._sub_measures.append(sub_measure)

    def list_sub_measures(self):
        """ list_sub_measures """
        return self._sub_measures

    def parent_measure(self):
        """ parent_measure """
        return self._parent_measure

    def duration(self):
        """ duration """
        return self._stop_time - self._start_time

    def __str__(self):
        elapsed = self.duration()
        elapsed_ms = round(elapsed * 1000.)
        return f"{self._legend} : {elapsed_ms}ms"


DEPTH = 0


class Profiler:
    """ Profiler """

    def __init__(self):
        self._main_measure = None
        self._current_measure = None

    def start_mes(self, legend):
        """ start """

        global DEPTH

        if DEBUG:
            print(f"{' '*DEPTH}start_mes({legend})")
            DEPTH += 1

        if self._main_measure is None:
            self._main_measure = Measure("root", None)
            self._current_measure = self._main_measure

        cur_measure = self._current_measure
        new_measure = Measure(legend, cur_measure)
        cur_measure.insert_sub_measure(new_measure)
        self._current_measure = new_measure

    def stop_mes(self):
        """ terminate """

        global DEPTH

        if DEBUG:
            DEPTH -= 1
            print(f"{' '*DEPTH}stop_mes()")

        cur_measure = self._current_measure
        cur_measure.terminate()
        self._current_measure = cur_measure.parent_measure()
        assert self._current_measure is not None, "Terminating too many measures"

    def send_report(self, pseudo, version, destination, timeout):
        """ send_report """

        def reply_callback(_):
            pass

        def noreply_callback():
            pass

        assert self._current_measure is self._main_measure, "Not terminating enough measures"

        cur_measure = self._current_measure
        cur_measure.terminate()

        elapsed = cur_measure.duration()

        subject = f"stats for {pseudo} ({elapsed})"
        body = ""
        body += f"{self}"
        body += "\n\n"
        body += f"overhead profiler {ELAPSED=}"
        body += "\n"
        body += f"{import_json_time=}"
        body += "\n"
        body += f"{import_user_config_time=}"
        body += "\n\n"
        body += f"config : {user_config.CONFIG}"
        body += "\n\n"
        body += f"version : {version}"
        body += "\n\n"

        json_dict = {
            'addressees': ADDRESS_ADMIN,
            'subject': subject,
            'body': body,
            'type': 'profile',
        }

        host, port = destination
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=timeout, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

        # reset
        self._main_measure = None

    def __str__(self):

        result = ""

        def rec_display(level, measure):
            nonlocal result
            ratio = (measure.duration() / elapsed) * 100
            result += f"{'    '*level}{measure} ({ratio:.2f}%) {'+'*round(ratio)}\n"
            for sub_mes in measure.list_sub_measures():
                rec_display(level + 1, sub_mes)

        cur_measure = self._current_measure
        elapsed = cur_measure.duration()

        rec_display(1, self._main_measure)
        return result


PROFILER = Profiler()

END_TIME = time()
ELAPSED = END_TIME - START_TIME
