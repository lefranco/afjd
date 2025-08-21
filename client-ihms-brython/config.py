""" config """

# pylint: disable=wrong-import-order, wrong-import-position


from json import load


# timeout for server requests
TIMEOUT_SERVER = 10

# to display state of a game
STATE_CODE_TABLE = {'en attente': 0, 'en cours': 1, 'archivée': 2, 'distinguée': 3}

DECLARATIONS_TYPE = 0
MESSAGES_TYPE = 1

# how many days after which account may be suppressed if nothing happens on it
# eighteen months
IDLE_DAY_TIMEOUT = 18 * 30.5

# load servers list from json data file
with open("./config/servers.json", "r", encoding="utf-8") as read_file:
    SERVER_CONFIG = load(read_file)

# load country list from json data file
with open("./data/country_list.json", "r", encoding="utf-8") as read_file:
    COUNTRY_CODE_TABLE = load(read_file)

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
    'canton': 7,
    'v1900': 7,
    'westeros': 7,
    'spiceislands': 7,
    'crepusculerome': 8,
    'successionautriche': 9,
    'moderne': 10,
    'crowded': 11,
    'chaos': 34,
}


# before that we warn that deadline is approaching
APPROACH_DELAY_SEC = 24 * 60 * 60

# after that we warn that game is suffering
CRITICAL_DELAY_DAY = 7

# colours
READY_TO_START_COLOUR = 'Chartreuse'

# three possibles ends of the game
SOLOED_COLOUR = 'Cyan'
END_VOTED_COLOUR = 'LightGrey'
FINISHED_COLOUR = 'DarkGrey'

# colors according to position commpared to deadline
CRITICAL_COLOUR = 'Brown'
PASSED_GRACE_COLOUR = 'Red'
PASSED_DEADLINE_COLOUR = 'Orange'
APPROACHING_DEADLINE_COLOUR = 'Yellow'

# after that waiting game should be cancelled
EXPIRED_WAIT_START_COLOUR = 'Chocolate'

# colors for games needing attention
NEED_START = 'YellowGreen'
NEED_REPLACEMENT = 'Fuchsia'
NEED_CANCEL_ANONIMITY = 'Pink'

# colors for games that can be joined
CAN_JOIN = 'LightBlue'

# to distinguish own games
MY_RATING = 'LightGrey'

# to destinguish games in last year
LAST_YEAR = 'LightGrey'

# to see better dest selected
DEST_SELECTED = 'LightGrey'

FORCED_VARIANT_NAME = "standard"

SITE_ADDRESS = "https://diplomania-gen.fr"
