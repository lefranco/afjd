#!/usr/bin/env python3

"""
File : orders_logger.py

Policy :
Critical : Handling system synchronization commands
Error : TBD
Warning : Messages sent to players
Info : Messages of interest for the game
Debug : None (interfers with PIL)

"""
import logging
import logging.handlers

import lowdata

# global
LOGGER: logging.Logger = None  # type: ignore


def start_logger(name: str) -> None:
    "Function to be called once to start the logging mechanics"

    # create a standard handler
    template = "%(asctime)s - %(levelname)s - %(message)s"
    # more details for debug
    # "%(asctime)s - %(levelname)s - %(filename)s l.%(lineno)s %(funcName)s() - %(message)s"
    formatter = logging.Formatter(template)
    handler = logging.handlers.WatchedFileHandler(lowdata.SUBMISSION_FILE)
    handler.setFormatter(formatter)

    # configure logging
    # Note : DEBUG does not work at pythonanywhere for some reason
    logging.basicConfig(level=logging.INFO)

    # link logging to handler
    global LOGGER
    LOGGER = logging.getLogger(name)
    LOGGER.addHandler(handler)

    # not on console
    LOGGER.propagate = False


if __name__ == '__main__':
    assert False, "Do not run this script"
