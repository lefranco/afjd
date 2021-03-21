""" debug """

# pylint: disable=pointless-statement, expression-not-assigned


import sys

from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser import alert  # pylint: disable=import-error


class Out:
    """ Out """
    def write(self, out):  # pylint: disable=no-self-use
        """ write """
        InfoDialog("DEBUG", out)


class Err:
    """ Err """
    def write(self, err):  # pylint: disable=no-self-use
        """ write """
        alert(err)


sys.stdout = Out()
sys.stderr = Err()
