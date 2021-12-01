

import time

class Measure:
    def __init__(self):
        now = time.time()
        self._start = now

    def terminate(self):
        now = time.time()
        self._stop = now

    def __str__(self) :
        elapsed = self._stop - self._start
        elapsed_ms = round(elapsed * 1000.)
        return f"{elapsed_ms}ms"

class Profiler:

    def __init__(self):
        self._table = dict()
        self._current = None

    def start(self, name) :
        prev_name = self._current
        if prev_name:
            old_measure = self._table[prev_name]
            old_measure.terminate()
        new_measure = Measure()
        self._table[name] = new_measure
        self._current = name

    def stop(self) :
        prev_name = self._current
        old_measure = self._table[prev_name]
        old_measure.terminate()

    def __str__(self) :
        return "\n".join([f"{n} : {m}" for n, m in self._table.items()])

