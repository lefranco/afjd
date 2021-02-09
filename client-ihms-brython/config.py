""" config """

# config of servers

SERVER_CONFIG = dict()

SERVER_CONFIG['USER'] = dict()
SERVER_CONFIG['USER']['HOST'] = "https://afjd1.eu.ngrok.io"
SERVER_CONFIG['USER']['PORT'] = 443

SERVER_CONFIG['EMAIL'] = dict()
SERVER_CONFIG['EMAIL']['HOST'] = "https://afjd2.eu.ngrok.io"
SERVER_CONFIG['EMAIL']['PORT'] = 443

SERVER_CONFIG['PLAYER'] = dict()
SERVER_CONFIG['PLAYER']['HOST'] = "https://afjd3.eu.ngrok.io"
SERVER_CONFIG['PLAYER']['PORT'] = 443

SERVER_CONFIG['GAME'] = dict()
SERVER_CONFIG['GAME']['HOST'] = "https://afjd4.eu.ngrok.io"
SERVER_CONFIG['GAME']['PORT'] = 443

SERVER_CONFIG['SOLVER'] = dict()
SERVER_CONFIG['SOLVER']['HOST'] = "https://afjd5.eu.ngrok.io"
SERVER_CONFIG['SOLVER']['PORT'] = 443

# timeout for server requests
TIMEOUT_SERVER = 2

# timeout for message when OK
REMOVE_AFTER = 5
