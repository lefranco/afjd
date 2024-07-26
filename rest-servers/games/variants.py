#!/usr/bin/env python3


"""
File : games.py

Handles the variants
"""
import typing
import json
import pathlib
import os

import mylogger

LOCATION = './variants'
EXTENSION = '.json'


class Variant:
    """ Class for handling a variant """

    @staticmethod
    def get_by_name(name: str) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """ class lookup : finds variant from file """

        full_name_file = pathlib.Path(LOCATION, name).with_suffix(EXTENSION)

        if not full_name_file.exists():
            mylogger.LOGGER.error("File variant is not a file %s", name)
            return None

        with open(full_name_file, 'r', encoding="utf-8") as file_ptr:
            try:
                json_data = json.load(file_ptr)
            except:  # noqa: E722 pylint: disable=bare-except
                mylogger.LOGGER.error("File variant raised an exception %s", name)
                return None

        assert isinstance(json_data, dict)
        return json_data



if __name__ == '__main__':
    assert False, "Do not run this script"
