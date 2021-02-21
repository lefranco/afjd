""" config """

import configparser
import collections


# timeout for server requests
TIMEOUT_SERVER = 2

# timeout for message when OK
REMOVE_AFTER = 5


class ConfigFile:
    """    Just reads an ini file   """

    def __init__(self, filename: str):
        self._config = configparser.ConfigParser(inline_comment_prefixes='#',    # do not accept ';'
                                                 empty_lines_in_values=False,    # as it says
                                                 interpolation=None)             # do not use variables

        assert self._config.read(filename, encoding='utf-8'), f"Missing ini file named {filename}"

    def section(self, section_name: str):
        """ Accesses a section of a config file  """
        assert self._config.has_section(section_name), "Missing section in ini file"
        return self._config[section_name]

    def section_list(self):
        """ Accesses the list of sections of a config file  """
        return self._config.sections()

SERVER_CONFIG = collections.defaultdict(dict)

def load_servers_config() -> None:
    """ read servers config """

    global SERVER_CONFIG

    servers_config = ConfigFile('./config/servers.ini')
    for server in servers_config.section_list():
        server_data = servers_config.section(server)
        SERVER_CONFIG[server]['HOST'] = server_data['HOST']
        SERVER_CONFIG[server]['PORT'] = int(server_data['PORT'])

load_servers_config()