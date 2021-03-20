""" debug """

# pylint: disable=pointless-statement, expression-not-assigned


import sys

from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser import document, alert, html

class Out:
    def write(self, out):
        InfoDialog("DEBUG", out)

class Err:
    def write(self, err):
        alert(err)

sys.stdout = Out()
sys.stderr = Err()

