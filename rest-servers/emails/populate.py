#!/usr/bin/env python3


"""
File : populate.py

Data : populate database
"""

import mylogger
import emails
import database


def populate_emails(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    emails.Email.create_table(sql_executor)


def populate(sql_executor: database.SqlExecutor) -> None:
    """ inserts all items in database """

    mylogger.LOGGER.warning("Populating...")

    sql_executor = database.SqlExecutor()
    populate_emails(sql_executor)
    del sql_executor


if __name__ == '__main__':
    assert False, "Do not run this script"
