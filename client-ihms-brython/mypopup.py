""" utility to display popups """

# pylint: disable=pointless-statement, expression-not-assigned


from browser import html  # pylint: disable=import-error
from browser.widgets.dialog import Dialog  # pylint: disable=import-error


# TODO : move stuff from mydialog.py here


class Popup(Dialog):
    """ Slightly home made popup """

    def __init__(self, title, canvas, content, buttons):

        # parent class
        Dialog.__init__(self, title)

        # make it resizeable
        self.attrs['style'] += 'resize: both; overflow: auto;'

        # put image if there is one
        if canvas:
            self.panel <= canvas
            self.panel <= html.BR()

        # put content if there is some (text)
        if content:
            self.panel <= content
            self.panel <= html.BR()

        # put button if there is one (to access full information)
        if buttons:
            for button in buttons:
                self.panel <= button
                button.bind('click', self.close)
                self.panel <= " "

        self.close_button <= "Fermer"
