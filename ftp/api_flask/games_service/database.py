#!/usr/bin/env python3


"""
File : database.py

Interface with the sqlite database
"""
import sqlite3
import typing
import pathlib
import unicodedata
import lzma
import base64
import time
import datetime
import traceback
import os
import pwd
import grp


# Easier than root
USERNAME = 'ubuntu'
GROUPNAME = 'ubuntu'

# File holding the SQLITE database
FILE = "./db/games.db"

STR_SEPARATOR = ';'
BYTES_SEPARATOR = b';'

STR_SEPARATOR_SUBSTITUTE_FOR_TEXT = ':'
BYTES_SEPARATOR_SUBSTITUTE_FOR_TEXT = b':'

STR_SEPARATOR_SUBSTITUTE_FOR_UNREADABLE = '|'
BYTES_SEPARATOR_SUBSTITUTE_FOR_UNREADABLE = b'|'


def rmdiacritics(field_content: str) -> str:
    '''
    Return the base character of field_content, by "removing" any
    diacritics like accents or curls and strokes and the like.
    '''
    result = ''
    for char in field_content:
        desc = unicodedata.name(char)
        cutoff = desc.find(' WITH ')
        if cutoff != -1:
            desc = desc[:cutoff]
            try:
                char = unicodedata.lookup(desc)
            except KeyError:
                assert False, f"Removing WITH ... produced an invalid name for {char}"
        result += char
    return result


def sanitize_field(field_content: str) -> str:
    """ Any str to something that goes into the database """

    assert isinstance(field_content, str), "Sanitize applicable only to strings"
    without_diacritics = rmdiacritics(field_content)
    without_separator = without_diacritics.replace(STR_SEPARATOR, STR_SEPARATOR_SUBSTITUTE_FOR_TEXT)
    return without_separator


def compress_text(text: str) -> str:
    """ compresses text that can be long """
    byte_form = text.encode(errors='ignore')
    compressed = lzma.compress(byte_form)
    a85 = base64.a85encode(compressed)
    assert BYTES_SEPARATOR_SUBSTITUTE_FOR_UNREADABLE not in a85
    removed_semicolon = a85.replace(BYTES_SEPARATOR, BYTES_SEPARATOR_SUBSTITUTE_FOR_UNREADABLE)
    return removed_semicolon.decode('ascii')


def uncompress_text(unreadable_str: str) -> str:
    """ uncompresses text that can be long """
    unreadable = unreadable_str.encode('ascii')
    restored_semicolon = unreadable.replace(BYTES_SEPARATOR_SUBSTITUTE_FOR_UNREADABLE, BYTES_SEPARATOR)
    compressed_back = base64.a85decode(restored_semicolon)
    byte_form_back = lzma.decompress(compressed_back)
    text_back = byte_form_back.decode()
    return text_back


def db_remove() -> None:
    """ For testing puprpose"""

    db_file = pathlib.Path(FILE)
    if not db_file.is_file():
        return
    db_file.unlink()


def db_present() -> bool:
    """ Answers the question"""

    db_file = pathlib.Path(FILE)
    return db_file.is_file()


TRACE_FILE = "./SqlExecutor.log"
STACK_LIMIT = 4
ONGOING_TRANSACTIONS = []


def log_stack(create: bool, uuid_str: str) -> None:
    """ log_stack (not used) """

    # the time
    now = time.time()
    date_now_gmt = datetime.datetime.utcfromtimestamp(now)
    date_now_gmt_str = date_now_gmt.strftime("%Y-%m-%d %H:%M:%S %f")

    # the stack
    raw_stack = traceback.extract_stack(limit=STACK_LIMIT)
    stack = traceback.format_list(raw_stack)
    stack_str = ''.join(stack)

    # into the file
    with open(TRACE_FILE, "a", encoding="utf-8") as write_file:

        # the action
        if create:
            write_file.write("=====^^^======\n")
        write_file.write(f"{date_now_gmt_str} : {'CREATING' if create else 'DELETING'} {uuid_str} : called by :\n")
        write_file.write(f"{stack_str}\n")
        if not create:
            write_file.write("=====vvv======\n")

        # the current set
        if create:
            ONGOING_TRANSACTIONS.append(uuid_str)
        else:
            ONGOING_TRANSACTIONS.remove(uuid_str)

        if not create:
            if ONGOING_TRANSACTIONS:
                write_file.write(f"Now : {' '.join(map(lambda u: u.split('-')[0], ONGOING_TRANSACTIONS))}\n")


def db_create() -> None:
    """ Create database (once for all)"""

    # Path object
    db_file = pathlib.Path(FILE)

    # Actual creation of db (file)
    conn = sqlite3.connect(db_file)
    conn.close()

    # Change rights of file (better not be root)
    uid = pwd.getpwnam(USERNAME).pw_uid
    gid = grp.getgrnam(GROUPNAME).gr_gid
    os.chown(db_file, uid, gid)


class SqlExecutor:
    """ Object capable of executing sql requests """

    def __init__(self) -> None:

        # for watching (not used)
        #  self.uuid = uuid.uuid4()
        #  log_stack(True, str(self.uuid))

        # actual work
        self._connection = sqlite3.connect(FILE, detect_types=sqlite3.PARSE_DECLTYPES)

    def execute(self, command: str, parameters: typing.Optional[typing.Tuple[typing.Any, ...]] = None, need_result: bool = False) -> typing.Optional[typing.List[typing.Any]]:
        """ Executes a sql command """

        # Note : ignoring Ctrl-C is not possible in flask-rest context

        cursor = self._connection.cursor()
        if parameters:
            cursor.execute(command, parameters)
        else:
            cursor.execute(command)
        result = cursor.fetchall() if need_result else None
        cursor.close()

        return result

    def commit(self) -> None:
        """ commit """
        self._connection.commit()  # necessary otherwise nothing happens

    def __del__(self) -> None:

        # actual work
        self._connection.close()

        # for watching (not used)
        #  if sys.is_finalizing():
        #      print(f"WARNING : {self.uuid} SURVIVED (it is being deleted at finalization time)")
        #      return
        #  log_stack(False, str(self.uuid))


if __name__ == '__main__':
    assert False, "Do not run this script"
