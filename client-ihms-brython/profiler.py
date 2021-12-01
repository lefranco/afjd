

import time

class Measure:
    def __init__(self):
        now = time.time()
        self._start = now

    def stop(self):
        now = time.time()
        self._stop = now

    def duration(self):
        elapsed = self._stop - self._start
        return elapsed

    def __str__(self) :
        return str(self.duration())

class Profiler:

    def __init__(self):
        self._table = dict()

    def start(self, name) :
        self._table[name] = Measure()

    def stop(self, name) :
        measure = self._table[name]
        measure.stop()

    def __str__(self) :
        return "\n".join([f"{n} : {m}" for n, m in self._table.items()])

