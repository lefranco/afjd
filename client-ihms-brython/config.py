""" config """

import json


# timeout for server requests
TIMEOUT_SERVER = 2

# timeout for message when OK
REMOVE_AFTER = 10

# to display state of a game
STATE_CODE_TABLE = {'en attente': 0, 'en cours': 1, 'terminée': 2}

DECLARATIONS_TYPE = 0
MESSAGES_TYPE = 1

# load servers list from json data file
with open("./config/servers.json", "r") as read_file:
    SERVER_CONFIG = json.load(read_file)

# load country list from json data file
with open("./data/country_list.json", "r") as read_file:
    COUNTRY_CODE_TABLE = json.load(read_file)

# load timezone list from json data file
with open("./data/timezone_list.json", "r") as read_file:
    TIMEZONE_CODE_TABLE = json.load(read_file)

PASSED_GRACE_COLOR = 'red'
PASSED_DEADLINE_COLOR = 'orange'
APPROACHING_DEADLINE_COLOR = 'yellow'


#  kept to show how to write json file
#  x = json.dumps(SERVER_CONFIG, indent=4)
#  print(x)
