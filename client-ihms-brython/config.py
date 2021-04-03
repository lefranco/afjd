""" config """

import json


# timeout for server requests
TIMEOUT_SERVER = 2

# timeout for message when OK
REMOVE_AFTER = 10

# to display state of a game
STATE_CODE_TABLE = {'en attente': 0, 'en cours': 1, 'terminée': 2}

# load servers list from json data file
with open("./config/servers.json", "r") as read_file:
    SERVER_CONFIG = json.load(read_file)

#  kept to show how top write json file
#  x = json.dumps(SERVER_CONFIG, indent=4)
#  print(x)
