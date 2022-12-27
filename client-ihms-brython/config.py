""" config """

# pylint: disable=wrong-import-order, wrong-import-position

import profiler

profiler.PROFILER.start_mes("inside config.py...")

import json


# timeout for server requests
TIMEOUT_SERVER = 10

# timeout for message when OK
REMOVE_AFTER = 5

# to display state of a game
STATE_CODE_TABLE = {'en attente': 0, 'en cours': 1, 'terminée': 2, 'distinguée': 3}

DECLARATIONS_TYPE = 0
MESSAGES_TYPE = 1

# load servers list from json data file
profiler.PROFILER.start_mes("server config...")
with open("./config/servers.json", "r", encoding="utf-8") as read_file:
    SERVER_CONFIG = json.load(read_file)
profiler.PROFILER.stop_mes()

# load country list from json data file
profiler.PROFILER.start_mes("country codes...")
with open("./data/country_list.json", "r", encoding="utf-8") as read_file:
    COUNTRY_CODE_TABLE = json.load(read_file)
profiler.PROFILER.stop_mes()

# load timezone list from json data file
profiler.PROFILER.start_mes("timezones...")
with open("./data/timezone_list.json", "r", encoding="utf-8") as read_file:
    TIMEZONE_CODE_TABLE = json.load(read_file)
profiler.PROFILER.stop_mes()

# load scoring list from json data file
profiler.PROFILER.start_mes("scoring codes...")
with open("./data/scoring_list.json", "r", encoding="utf-8") as read_file:
    SCORING_CODE_TABLE = json.load(read_file)
profiler.PROFILER.stop_mes()

# colours
ALL_AGREEMENTS_IN_COLOUR = 'Chartreuse'
ALL_ORDERS_IN_COLOUR = 'Chartreuse'

PASSED_GRACE_COLOUR = 'Red'
PASSED_DEADLINE_COLOUR = 'DarkOrange'
APPROACHING_DEADLINE_COLOUR = 'Yellow'

NEED_REPLACEMENT = 'Pink'
MY_RATING = 'Blue'

profiler.PROFILER.stop_mes()
