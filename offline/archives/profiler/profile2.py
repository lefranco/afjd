
# avant tout
import time
LOG  = []
BEFORE = time.time()
def log_time(desc):
    global BEFORE
    now = time.time()
    LOG.append(f"{desc} {now-BEFORE}s")

# au fil de l'eau
log_time("<action>")


# a la fin
alert(f"{LOG=}")