""" config """

# pylint: disable=wrong-import-order, wrong-import-position


from json import load


# timeout for server requests
TIMEOUT_SERVER = 10

# to display state of a game
STATE_CODE_TABLE = {'en attente': 0, 'en cours': 1, 'terminée': 2, 'distinguée': 3}

DECLARATIONS_TYPE = 0
MESSAGES_TYPE = 1

# how many days after which account may be suppressed if nothing happens on it
# two years
IDLE_DAY_TIMEOUT = 2 * 365

# load servers list from json data file
with open("./config/servers.json", "r", encoding="utf-8") as read_file:
    SERVER_CONFIG = load(read_file)

# load country list from json data file
with open("./data/country_list.json", "r", encoding="utf-8") as read_file:
    COUNTRY_CODE_TABLE = load(read_file)

# load timezone list from json data file
with open("./data/timezone_list.json", "r", encoding="utf-8") as read_file:
    TIMEZONE_CODE_TABLE = load(read_file)

# load scoring list from json data file
with open("./data/scoring_list.json", "r", encoding="utf-8") as read_file:
    SCORING_CODE_TABLE = load(read_file)

# load game types list from json data file
with open("./data/game_type_list.json", "r", encoding="utf-8") as read_file:
    GAME_TYPES_CODE_TABLE = load(read_file)

# default is first one
VARIANT_NAMES_DICT = {
    'standard': 7,
    'standard_pds': 7,
    'coldwar': 2,
    'grandeguerre': 2,
    'franceautriche': 2,
    'hundred': 3,
    'coldwar_redux': 4,
    'mediterranee': 5,
    'egeemonie': 6,
    'spiceislands': 7,
    'successionautriche': 9,
    'moderne': 10,
    'crowded': 11,
}


# yellow before that
APPROACH_DELAY_SEC = 24 * 60 * 60

# grey after that
CRITICAL_DELAY_DAY = 7

# orange after that
SLIGHT_DELAY_SEC = 5

# colours
ALL_ORDERS_IN_COLOUR = 'Chartreuse'

SOLOED_COLOUR = 'Cyan'
FINISHED_COLOUR = 'Silver'

CRITICAL_COLOUR = 'Maroon'
PASSED_GRACE_COLOUR = 'Red'
PASSED_DEADLINE_COLOUR = 'Orange'
SLIGHTLY_PASSED_DEADLINE_COLOUR = 'Gold'
APPROACHING_DEADLINE_COLOUR = 'Yellow'

NEED_START = 'Green'
NEED_PLAYERS = 'Pink'
NEED_REPLACEMENT = 'Fuchsia'
MY_RATING = 'Cyan'

FORCED_VARIANT_NAME = "standard"
