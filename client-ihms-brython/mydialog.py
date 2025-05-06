""" utility to display popups """

# pylint: disable=pointless-statement, expression-not-assigned


from browser import html, window  # pylint: disable=import-error
from browser.widgets.dialog import Dialog, InfoDialog  # pylint: disable=import-error


REMOVE_AFTER_SEC = 5


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


POPUP_OCCUPATION = {n: None for n in range(5)}


class Relocatable:
    """ add relocatable property to brython Dialog classes """

    def __init__(self):

        # Take occupation slot if available
        for popup_pos, occupant in POPUP_OCCUPATION.items():
            if not occupant:
                POPUP_OCCUPATION[popup_pos] = self
                self.popup_pos = popup_pos
                break
        else:
            self.popup_pos = -1

        # Move popup according to slot taken
        # Occupation map as below:
        #
        # 3       4
        #     0
        # 2       1
        #
        match self.popup_pos:
            # case 0 (only one popup) or -1 (too many popups) : no move (centered)
            case 1:
                self.left += window.innerWidth // 4  # pylint: disable=no-member
                self.top += window.innerHeight // 4  # pylint: disable=no-member
            case 2:
                self.left -= window.innerWidth // 4  # pylint: disable=no-member
                self.top += window.innerHeight // 4  # pylint: disable=no-member
            case 3:
                self.left -= window.innerWidth // 4  # pylint: disable=no-member
                self.top -= window.innerHeight // 4  # pylint: disable=no-member
            case 4:
                self.left += window.innerWidth // 4  # pylint: disable=no-member
                self.top -= window.innerHeight // 4  # pylint: disable=no-member

    def close(self):
        """ Free occupation slot """
        if self.popup_pos >= 0:
            POPUP_OCCUPATION[self.popup_pos] = None


class MyDialog(Dialog, Relocatable):
    """ RelocatableDialog """

    def __init__(self, title, **kargs):
        Dialog.__init__(self, title, **kargs)
        Relocatable.__init__(self)

    def close(self, *args):
        """ close """
        Relocatable.close(self)
        Dialog.close(self, *args)


class MyInfoDialog(InfoDialog, Relocatable):
    """ RelocatableInfoDialog """

    def __init__(self, title, message, **kargs):
        InfoDialog.__init__(self, title, message, **kargs)
        Relocatable.__init__(self)

    def close(self, *args):
        """ close """
        Relocatable.close(self)
        InfoDialog.close(self, *args)


def info_go(message):
    """ Information that will automatically dissapear """

    MyInfoDialog('Information', str(message), remove_after=REMOVE_AFTER_SEC)


def info_stay(message):
    """ Information that will persist until OK is pressed """

    MyInfoDialog('Information', str(message), ok="OK")
