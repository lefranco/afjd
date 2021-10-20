#!/usr/bin/env python3


"""
File : agree.py

Handles the agreement to solve
"""
import typing

import database
import definitives


def clear(game_id: int, sql_executor: database.SqlExecutor) -> None:
    """ clear for a game the agreements"""

    for (_, role_num, _) in definitives.Definitive.list_by_game_id(sql_executor, int(game_id)):
        definitive = definitives.Definitive(int(game_id), role_num, False)
        definitive.delete_database(sql_executor)


def retrieve(game_id: int, role_id: int, sql_executor: database.SqlExecutor) -> typing.List[typing.Tuple[int, int, int]]:
    """ retrieves for a game the agreements """

    assert role_id is not None
    if role_id == 0:
        definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
    else:
        definitives_list = definitives.Definitive.list_by_game_id_role_num(sql_executor, game_id, role_id)
    return definitives_list


def post(game_id: int, role_id: int, definitive_value: bool, names: str, sql_executor: database.SqlExecutor) -> None:
    """ post an agreement in a game (or a disagreement) """

    # update db here
    if role_id == 0:
        definitive = definitives.Definitive(int(game_id), role_id, definitive_value)
        definitive.update_database(sql_executor)  # noqa: F821
    else:
        definitive = definitives.Definitive(int(game_id), role_id, definitive_value)
        definitive.update_database(sql_executor)  # noqa: F821

    if not definitive_value:
        return

    # TODO
    # if still some agreement missing, return

    # TODO
    # connect adjudication here


if __name__ == '__main__':
    assert False, "Do not run this script"
