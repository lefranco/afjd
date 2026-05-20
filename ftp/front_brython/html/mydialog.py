""" utility to display popups """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, window, timer  # pylint: disable=import-error
from browser.widgets.dialog import Dialog  # pylint: disable=import-error

POPUP_TOP = 40
POPUP_LEFT = 60
REMOVE_AFTER_SEC = 5


POPUP_OCCUPATION = {n: None for n in range(5)}


class Relocatable:
    """ add relocatable property to brython Dialog classes """

    def __init__(self):

        # By default, no position found
        self.popup_pos = -1

        # Take occupation slot if available
        for popup_pos, occupant in POPUP_OCCUPATION.items():
            if occupant is None:
                POPUP_OCCUPATION[popup_pos] = self
                self.popup_pos = popup_pos
                break

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
        # Initialize first Dialog of Brython to have self.left and self.top
        Dialog.__init__(self, title, **kargs, default_css=False, can_close=False)
        # Apply after positionning logic
        Relocatable.__init__(self)

    def close(self, *args):
        """ Overload to clean dict """
        Relocatable.close(self)       # free slot
        Dialog.close(self, *args)     # let Brython destry graphical component


class MyInfoDialog(MyDialog):
    """ Customized InfoDialog """

    def __init__(self, title, message, *, remove_after=None, ok_text=None):
        MyDialog.__init__(self, title)

        # Put message
        self.panel <= html.DIV(message)

        # Put Ok button
        if ok_text:
            self.ok_button = html.BUTTON(ok_text, Class="brython-dialog-button")
            self.panel <= html.P()
            self.panel <= html.DIV(self.ok_button, style={"text-align": "center"})
            # CRUCIAL : call self.close (not self.remove) to free the slot !
            self.ok_button.bind("click", lambda ev: self.close())

        # Handle timed removal
        if remove_after:
            # Use timer of Brython (cleaner)
            timer.set_timeout(self.close, remove_after * 1000)


def info_go(message):
    """ Information that will automatically disappear """
    MyInfoDialog('Information', str(message), remove_after=REMOVE_AFTER_SEC)


def info_stay(message):
    """ Information that will persist until OK is pressed """
    MyInfoDialog('Information', str(message), ok_text="OK")
