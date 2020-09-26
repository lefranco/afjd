#!/usr/bin/env python3

"""
File : mylogger.py

Policy :
Critical : Handling system synchronization commands
Error : TBD
Warning : Messages sent to players
Info : Messages of interest for the game
Debug : None (interfers with PIL)

"""
import logging
import logging.handlers

FILE = './logdir/solver.log'

# global
LOGGER: logging.Logger = None  # type: ignore


def start_logger(name: str) -> None:
    "Function to be called once to start the logging mechanics"

    # create a standard handler
    template = "%(asctime)s - %(levelname)s - %(message)s"
    # more details for debug
    # "%(asctime)s - %(levelname)s - %(filename)s l.%(lineno)s %(funcName)s() - %(message)s"
    formatter = logging.Formatter(template)
    handler = logging.handlers.WatchedFileHandler(FILE)
    handler.setFormatter(formatter)

    # configure logging
    # keep this to  INFO because :
    # 1) DEBUG does not work at pythoanywhere for some reason
    # 2) DEBUG introduces traces pollution by PILLOW
    logging.basicConfig(level=logging.INFO)

    # link logging to handler
    global LOGGER
    LOGGER = logging.getLogger(name)
    LOGGER.addHandler(handler)

    # not on console
    LOGGER.propagate = False


if __name__ == '__main__':
    assert False, "Do not run this script"
