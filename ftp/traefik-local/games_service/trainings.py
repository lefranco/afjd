#!/usr/bin/env python3


"""
File : trainings.py

Handles the variants
"""
import typing
import json
import pathlib
import os

import mylogger

LOCATION = './trainings'
EXTENSION = '.json'


class Training:
    """ Class for handling a training """

    @staticmethod
    def get_by_name(name: str) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """ class lookup : finds training from file """

        full_name_file = pathlib.Path(LOCATION, name).with_suffix(EXTENSION)

        if not full_name_file.exists():
            mylogger.LOGGER.error("File training is not a file %s", name)
            return None

        with open(full_name_file, 'r', encoding="utf-8") as file_ptr:
            try:
                json_data = json.load(file_ptr)
            except:  # noqa: E722 pylint: disable=bare-except
                mylogger.LOGGER.error("File training raised an exception %s", name)
                return None

        assert isinstance(json_data, dict)
        return json_data

    @staticmethod
    def get_dict() -> typing.Dict[str, str]:
        """ class lookup : return list of available variants """

        training_dict = {}
        for name_file in os.listdir(LOCATION):

            full_name_file = pathlib.Path(LOCATION, name_file)
            if full_name_file.suffix != EXTENSION:
                continue

            with open(full_name_file, 'r', encoding="utf-8") as file_ptr:
                try:
                    json_data = json.load(file_ptr)
                except:  # noqa: E722 pylint: disable=bare-except
                    mylogger.LOGGER.error("File training raised an exception %s", full_name_file)
                    continue

            if 'title' not in json_data:
                mylogger.LOGGER.error("File training misses a title %s", full_name_file)
                continue

            training_title = json_data['title']

            training_dict[training_title] = full_name_file.stem

        return training_dict


if __name__ == '__main__':
    assert False, "Do not run this script"
