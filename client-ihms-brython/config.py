""" config """

# pylint: disable=wrong-import-order, wrong-import-position


import json


# timeout for server requests
TIMEOUT_SERVER = 10

# to display state of a game
STATE_CODE_TABLE = {'en attente': 0, 'en cours': 1, 'terminée': 2, 'distinguée': 3}

DECLARATIONS_TYPE = 0
MESSAGES_TYPE = 1

# how many days after which account may be suppressed if nothing happens on it
IDLE_DAY_TIMEOUT = 365

# load servers list from json data file
with open("./config/servers.json", "r", encoding="utf-8") as read_file:
    SERVER_CONFIG = json.load(read_file)

# load country list from json data file
with open("./data/country_list.json", "r", encoding="utf-8") as read_file:
    COUNTRY_CODE_TABLE = json.load(read_file)

# load timezone list from json data file
with open("./data/timezone_list.json", "r", encoding="utf-8") as read_file:
    TIMEZONE_CODE_TABLE = json.load(read_file)

# load scoring list from json data file
with open("./data/scoring_list.json", "r", encoding="utf-8") as read_file:
    SCORING_CODE_TABLE = json.load(read_file)

# yellow before that
APPROACH_DELAY_SEC = 24 * 60 * 60

# grey after that
CRITICAL_DELAY_DAY = 7

# orange after that
SLIGHT_DELAY_SEC = 5

# colours
ALL_ORDERS_IN_COLOUR = 'Chartreuse'

CRITICAL_COLOUR = 'Grey'
PASSED_GRACE_COLOUR = 'Maroon'
PASSED_DEADLINE_COLOUR = 'Red'
SLIGHTLY_PASSED_DEADLINE_COLOUR = 'DarkOrange'
APPROACHING_DEADLINE_COLOUR = 'Yellow'

NEED_REPLACEMENT = 'Pink'
MY_RATING = 'Blue'
