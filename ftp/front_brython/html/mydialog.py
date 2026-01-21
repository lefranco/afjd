""" utility to display popups """

# pylint: disable=pointless-statement, expression-not-assigned


from browser import html, window  # pylint: disable=import-error
from browser.widgets.dialog import Dialog  # pylint: disable=import-error


POPUP_TOP = 40
POPUP_LEFT = 60
REMOVE_AFTER_SEC = 5


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

        # parent classes
        Dialog.__init__(self, title, **kargs, default_css=False, can_close=False)
        Relocatable.__init__(self)

    def close(self, *args):
        """ close """
        Relocatable.close(self)
        Dialog.close(self, *args)


class MyInfoDialog(MyDialog):
    """ Customized InfoDialog (we customize and do not use InfoDialog provided since we cannot get close to work properly) """

    def __init__(self, title, message, *, remove_after=None, ok_text=None):

        # parent classes
        MyDialog.__init__(self, title)

        # Put message
        self.panel <= html.DIV(message)

        # Put Ok button
        if ok_text:
            self.ok_button = html.BUTTON(ok_text, Class="brython-dialog-button")
            self.panel <= html.P()
            self.panel <= html.DIV(self.ok_button, style={"text-align": "center"})
            self.ok_button.bind("click", lambda ev: self.remove())

        # Handle timed removal
        if remove_after:
            window.setTimeout(self.close, remove_after * 1000)


def info_go(message):
    """ Information that will automatically dissapear """

    MyInfoDialog('Information', str(message), remove_after=REMOVE_AFTER_SEC)


def info_stay(message):
    """ Information that will persist until OK is pressed """

    MyInfoDialog('Information', str(message), ok_text="OK")
