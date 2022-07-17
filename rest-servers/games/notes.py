#!/usr/bin/env python3


"""
File : notes.py

Handles the stored notes
"""

import database


class Note:
    """ Class for handling an vote """

    @staticmethod
    def content_by_game_id_role_num(sql_executor: database.SqlExecutor, game_id: int, role_num: int) -> str:
        """ class lookup : finds the object in database from fame id """
        content_found = sql_executor.execute("SELECT content from notes where game_id = ? and role_num = ?", (game_id, role_num), need_result=True)
        if not content_found:
            return ""
        compressed_content = content_found[0][0]
        decoded_compressed_content = compressed_content.decode()
        content = database.uncompress_text(decoded_compressed_content)
        return content

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS notes")
        sql_executor.execute("CREATE TABLE notes (game_id INTEGER, role_num INTEGER, content STR)")

    def __init__(self, game_id: int, role_num: int, content: str) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

        assert isinstance(content, str), "content must be an str"
        self._content = content

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM notes WHERE game_id = ? and role_num = ?", (self._game_id, self._role_num))
        compressed_content = database.compress_text(self._content)
        content_database = compressed_content.encode('ascii')
        sql_executor.execute("INSERT OR REPLACE INTO notes (game_id, role_num, content) VALUES (?, ?, ?)", (self._game_id, self._role_num, content_database))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM notes WHERE game_id = ? AND role_num = ?", (self._game_id, self._role_num))

    def __str__(self) -> str:
        return f"game_id={self._game_id} role_num={self._role_num} content={self._content}"


if __name__ == '__main__':
    assert False, "Do not run this script"
