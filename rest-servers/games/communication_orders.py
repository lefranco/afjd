#!/usr/bin/env python3


"""
File : communication_orders.py

Handles the stored communication orders
"""
import typing

import database


class CommunicationOrder:
    """ Class for handling an communication order """

    @staticmethod
    def list_by_game_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int, int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        communication_orders_found = sql_executor.execute("SELECT * FROM communication_orders where game_id = ?", (game_id,), need_result=True)
        if not communication_orders_found:
            return []
        return communication_orders_found

    @staticmethod
    def list_by_game_id_role_num(sql_executor: database.SqlExecutor, game_id: int, role_num: int) -> typing.List[typing.Tuple[int, int, int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        communication_orders_found = sql_executor.execute("SELECT * FROM communication_orders where game_id = ? and role_num = ?", (game_id, role_num), need_result=True)
        if not communication_orders_found:
            return []
        return communication_orders_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS communication_orders")
        sql_executor.execute("CREATE TABLE communication_orders (game_id INTEGER, role_num INTEGER, order_type_num INTEGER, active_unit_zone_num INTEGER, passive_unit_zone_num INTEGER, destination_zone_num INTEGER)")

    def __init__(self, game_id: int, role_num: int, order_type_num: int, active_unit_zone_num: int, passive_unit_zone_num: int, destination_zone_num: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

        assert isinstance(order_type_num, int), "order_type_num must be an int"
        self._order_type_num = order_type_num

        assert isinstance(active_unit_zone_num, int), "active_unit_zone_num must be an int"
        self._active_unit_zone_num = active_unit_zone_num

        assert isinstance(passive_unit_zone_num, int), "passive_unit_zone_num must be an int"
        self._passive_unit_zone_num = passive_unit_zone_num

        assert isinstance(destination_zone_num, int), "destination_zone_num must be an int"
        self._destination_zone_num = destination_zone_num

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO communication_orders (game_id, role_num, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num) VALUES (?, ?, ?, ?, ?, ?)", (self._game_id, self._role_num, self._order_type_num, self._active_unit_zone_num, self._passive_unit_zone_num, self._destination_zone_num))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM communication_orders WHERE game_id = ? AND role_num = ? AND active_unit_zone_num = ?", (self._game_id, self._role_num, self._active_unit_zone_num))

    def load_json(self, json_dict: typing.Dict[str, typing.Any]) -> None:
        """ Load from dict """

        # special
        self._role_num = json_dict['active_unit']['role']

        # mandatory
        self._order_type_num = json_dict['order_type']
        self._active_unit_zone_num = json_dict['active_unit']['zone']

        # not mandatory
        if 'passive_unit' in json_dict:
            self._passive_unit_zone_num = json_dict['passive_unit']['zone']
        if 'destination_zone' in json_dict:
            self._destination_zone_num = json_dict['destination_zone']

    def export(self) -> typing.Tuple[int, int, int, int, int]:
        """ for passing to solver """
        return self._role_num, self._order_type_num, self._active_unit_zone_num, self._passive_unit_zone_num, self._destination_zone_num

    def __str__(self) -> str:
        return f"game_id={self._game_id} role_num={self._role_num} order_type_num={self._order_type_num} active_unit_zone_num={self._active_unit_zone_num} passive_unit_zone_num={self._passive_unit_zone_num} destination_zone_num={self._destination_zone_num}"


if __name__ == '__main__':
    assert False, "Do not run this script"
