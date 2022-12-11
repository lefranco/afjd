""" user_config """

# pylint: disable=wrong-import-order, wrong-import-position

from browser import window  # pylint: disable=import-error

CONFIG = "User Config detected : \n"

CONFIG += f"Cookies enabled: {window.navigator.cookieEnabled}\n"

try:
    CONFIG += f"Connection Speed: {window.navigator.connection.downlink}\n"
except:  # noqa: E722 pylint: disable=bare-except
    CONFIG += "Failed to get connection speed\n"

try:
    CONFIG += f"Connection Effective Type: {window.navigator.connection.effectiveType}\n"
except:  # noqa: E722 pylint: disable=bare-except
    CONFIG += "Failed to get connection effective type\n"

try:
    CONFIG += f"Connection Type: {window.navigator.connection.type}\n"
except:  # noqa: E722 pylint: disable=bare-except
    CONFIG += "Failed to get connection type\n"

try:
    CONFIG += f"Memory: {window.navigator.deviceMemory}\n"
except:  # noqa: E722 pylint: disable=bare-except
    CONFIG += "Failed to get Memory data\n"

CONFIG += f"Language: {window.navigator.language}\n"

CONFIG += f"User Agent: {window.navigator.userAgent}\n"
