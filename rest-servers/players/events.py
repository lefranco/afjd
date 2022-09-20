#!/usr/bin/env python3


"""
File : events.py

Handles the events
"""
import typing
import sqlite3

import database
import registrations

# need to have a limit in sizes of fields
LEN_NAME_MAX = 50
LEN_LOCATION_MAX = 20


class Event:
    """ Class for handling an event """

    @staticmethod
    def free_identifier(sql_executor: database.SqlExecutor) -> int:
        """ finds an new identifier from database to use for this object """
        sql_executor.execute("UPDATE events_counter SET value = value + 1", None, need_result=False)
        counter_found = sql_executor.execute("SELECT value FROM events_counter", None, need_result=True)
        counter = counter_found[0][0]  # type: ignore
        return counter  # type: ignore

    @staticmethod
    def find_by_identifier(sql_executor: database.SqlExecutor, identifier: int) -> typing.Optional['Event']:
        """ class lookup : finds the object in database from identifier """
        events_found = sql_executor.execute("SELECT event_data FROM events where identifier = ?", (identifier,), need_result=True)
        if not events_found:
            return None
        return events_found[0][0]  # type: ignore

    @staticmethod
    def find_by_name(sql_executor: database.SqlExecutor, name: str) -> typing.Optional['Event']:
        """ class lookup : finds the object in database from name """
        events_found = sql_executor.execute("SELECT event_data FROM events where name = ?", (name,), need_result=True)
        if not events_found:
            return None
        return events_found[0][0]  # type: ignore

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List['Event']:
        """ class inventory : gives a list of all objects in database """
        events_found = sql_executor.execute("SELECT event_data FROM events", need_result=True)
        if not events_found:
            return []
        events_list = [e[0] for e in events_found]
        return events_list

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        # create counter
        sql_executor.execute("DROP TABLE IF EXISTS events_counter")
        sql_executor.execute("CREATE TABLE events_counter (value INTEGER)")
        sql_executor.execute("INSERT INTO events_counter (value) VALUES (?)", (0,))

        # create actual table
        sql_executor.execute("DROP TABLE IF EXISTS events")
        sql_executor.execute("CREATE TABLE events (identifier INTEGER UNIQUE PRIMARY KEY, name STR, event_data event)")
        sql_executor.execute("CREATE UNIQUE INDEX name_event ON events (name)")

    def __init__(self, identifier: int, name: str, start_date: str, start_hour: str, end_date: str, location: str, description: str, manager_id: int) -> None:

        assert isinstance(identifier, int), "identifier must be an int"
        self._identifier = identifier

        assert isinstance(name, str), "name must be a str"
        self._name = database.sanitize_field(name)[:LEN_NAME_MAX]

        assert isinstance(start_date, str), "start_date must be a str"
        self._start_date = start_date

        assert isinstance(start_hour, str), "start_hour must be a str"
        self._start_hour = start_hour

        assert isinstance(end_date, str), "end_date must be a str"
        self._end_date = end_date

        assert isinstance(location, str), "location must be a str"
        self._location = database.sanitize_field(location)[:LEN_LOCATION_MAX]

        assert isinstance(description, str), "name must be a str"
        self._description = description

        assert isinstance(manager_id, int), "manager_id must be a int"
        self._manager_id = manager_id

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO events (identifier, name, event_data) VALUES (?, ?, ?)", (self._identifier, self._name, self))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM events WHERE identifier = ?", (self._identifier,))

    def delete_registrations(self, sql_executor: database.SqlExecutor) -> None:
        """  delete registrations """

        event_id = self.identifier
        registrations_list = registrations.Registration.list_by_event_id(sql_executor, event_id)
        for event_id, player_id, date_, approved in registrations_list:
            registration = registrations.Registration(event_id, player_id, date_, approved)
            registration.delete_database(sql_executor)

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def name(self) -> str:
        """ property """
        return self._name

    @property
    def start_date(self) -> str:
        """ property """
        return self._start_date

    @property
    def start_hour(self) -> str:
        """ property """
        return self._start_hour

    @property
    def end_date(self) -> str:
        """ property """
        return self._end_date

    @property
    def location(self) -> str:
        """ property """
        return self._location

    @property
    def description(self) -> str:
        """ property """
        return self._description

    @property
    def manager_id(self) -> int:
        """ property """
        return self._manager_id

    def __str__(self) -> str:
        return f"name={self._name} start_date={self._start_date} start_hour={self._start_hour} end_date={self._end_date} location={self._location} description={self._description} manager_id={self._manager_id} "

    def adapt_event(self) -> bytes:
        """ To put an object in database """
        compressed_description = database.compress_text(self._description)
        return (f"{self._identifier}{database.STR_SEPARATOR}{self._name}{database.STR_SEPARATOR}{self._start_date}{database.STR_SEPARATOR}{self._start_hour}{database.STR_SEPARATOR}{self._end_date}{database.STR_SEPARATOR}{self._location}{database.STR_SEPARATOR}{compressed_description}{database.STR_SEPARATOR}{self._manager_id}").encode('ascii')


def convert_event(buffer: bytes) -> Event:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    identifier = int(tab[0].decode())
    name = tab[1].decode()
    start_date = tab[2].decode()
    start_hour = tab[3].decode()
    end_date = tab[4].decode()
    location = tab[5].decode()

    compressed_description = tab[6].decode()
    description = database.uncompress_text(compressed_description)

    manager_id = int(tab[7].decode())
    event = Event(identifier, name, start_date, start_hour, end_date, location, description, manager_id)
    return event


# Interfaces between python and database
sqlite3.register_adapter(Event, Event.adapt_event)
sqlite3.register_converter('event', convert_event)


if __name__ == '__main__':
    assert False, "Do not run this script"
