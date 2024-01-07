#!/usr/bin/env python3


"""
File : lowdata.py

"""
import typing
import configparser
import collections
import json
import time


# where to get logs
FILE = './logdir/scheduler.log'


class ConfigFile:
    """    Just reads an ini file   """

    def __init__(self, filename: str) -> None:
        self._config = configparser.ConfigParser(inline_comment_prefixes='#',    # do not accept ';'
                                                 empty_lines_in_values=False,    # as it says
                                                 interpolation=None)             # do not use variables

        assert self._config.read(filename, encoding='utf-8'), f"Missing ini file named {filename}"

    def section(self, section_name: str) -> configparser.SectionProxy:
        """ Accesses a section of a config file  """
        assert self._config.has_section(section_name), "Missing section in ini file"
        return self._config[section_name]

    def section_list(self) -> typing.List[str]:
        """ Accesses the list of sections of a config file  """
        return self._config.sections()


SERVER_CONFIG: typing.Dict[str, typing.Dict[str, typing.Any]] = collections.defaultdict(dict)


def load_servers_config() -> None:
    """ read servers config """

    servers_config = ConfigFile('./config/servers.ini')
    for server in servers_config.section_list():
        server_data = servers_config.section(server)
        SERVER_CONFIG[server]['HOST'] = server_data['HOST']
        SERVER_CONFIG[server]['PORT'] = int(server_data['PORT'])


# simplest is to hard code displays of variants here
INTERFACE_TABLE = {
    'standard': ['diplomania', 'diplomania_daltoniens', 'hasbro'],
    'standard_pds': ['diplomania'],
    'grandeguerre': ['diplomania'],
    'grandeguerreexpansionniste': ['diplomania'],
    'hundred': ['diplomania'],
    'moderne': ['diplomania'],
    'egeemonie': ['diplomania'],
    'mediterranee': ['diplomania'],
    'successionautriche': ['diplomania'],
}


def get_inforced_interface_from_variant(variant: str) -> str:
    """ get_inforced_interface_from_variant """

    # takes the first
    return INTERFACE_TABLE[variant][0]


def read_parameters(variant_name_loaded: str, interface_chosen: str) -> typing.Any:
    """ read_parameters """

    parameters_file_name = f"./variants/{variant_name_loaded}/{interface_chosen}/parameters.json"
    with open(parameters_file_name, "r", encoding="utf-8") as read_file2:
        parameters_read = json.load(read_file2)

    return parameters_read


LAST_TIME = 0.


def start() -> None:
    """ start """

    global LAST_TIME

    # this to know how long it takes
    now_time = time.time()
    LAST_TIME = now_time


def elapsed_then(information: typing.List[str], desc: str) -> None:
    """ elapsed_then """

    global LAST_TIME

    # elapsed
    now_time = time.time()
    elapsed = now_time - LAST_TIME

    # update last time
    LAST_TIME = now_time

    # display
    information.append("--")
    information.append(f"{desc} : {elapsed}")
    information.append("--")


if __name__ == '__main__':
    assert False, "Do not run this script"
