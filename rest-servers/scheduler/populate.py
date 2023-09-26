#!/usr/bin/env python3


"""
File : populate.py

Data : populate database
"""

import mylogger
import database


def populate(sql_executor: database.SqlExecutor) -> None:
    """ inserts all items in database """

    mylogger.LOGGER.warning("Populating...")

    sql_executor = database.SqlExecutor()

    # pass : no table (yet ?)

    del sql_executor


if __name__ == '__main__':
    assert False, "Do not run this script"
