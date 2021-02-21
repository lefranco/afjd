""" config """

import json


# timeout for server requests
TIMEOUT_SERVER = 2

# timeout for message when OK
REMOVE_AFTER = 5

# load servers list from json data file
with open("./config/servers.json", "r") as read_file:
    SERVER_CONFIG = json.load(read_file)

#  kept to show how top write json file
#  x = json.dumps(SERVER_CONFIG, indent=4)
#  print(x)
