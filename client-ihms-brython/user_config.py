""" user_config """

# pylint: disable=wrong-import-order, wrong-import-position

from browser import window  # pylint: disable=import-error

CONFIG = "User Config detected : \n"

try:
    CONFIG += f"Cookies enabled: {window.navigator.cookieEnabled}\n"
except:  # noqa: E722 pylint: disable=bare-except
    CONFIG += "Failed to get cookies anabled\n"

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

try:
    CONFIG += f"Language: {window.navigator.language}\n"
except:  # noqa: E722 pylint: disable=bare-except
    CONFIG += "Failed to get Language\n"

try:
    CONFIG += f"User Agent: {window.navigator.userAgent}\n"
except:  # noqa: E722 pylint: disable=bare-except
    CONFIG += "Failed to get User Agent\n"

try:
    CONFIG += f"Concurrency: {window.navigator.hardwareConcurrency}\n"
except:  # noqa: E722 pylint: disable=bare-except
    CONFIG += "Failed to get Concurrency\n"
