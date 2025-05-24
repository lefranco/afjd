""" utility to display popups """

# pylint: disable=pointless-statement, expression-not-assigned


from browser import html, window  # pylint: disable=import-error
from browser.widgets.dialog import Dialog  # pylint: disable=import-error


REMOVE_AFTER_SEC = 5


class Popup(Dialog):
    """ Slightly home made popup """

    def __init__(self, title, canvas, content, buttons):

        # parent class
        # inforce can_close to False
        Dialog.__init__(self, title, can_close=False)

        # make it resizeable
        self.attrs['style'] += 'resize: both; overflow: auto;'

        # close button at the top
        close_button = html.INPUT(type="submit", value="Fermer", Class='btn-inside')
        close_button.bind('click', self.close)
        close_button.bind('touchstart', self.close)  # for some reason
        self.panel <= close_button
        self.panel <= html.BR()

        # put image if there is one
        if canvas:
            self.panel <= canvas
            self.panel <= html.BR()

        # put content if there is some (text)
        if content:
            self.panel <= content
            self.panel <= html.BR()

        # put button(s) if there is one/some (to access full information usually)
        if buttons:
            for button in buttons:
                self.panel <= button
                button.bind('click', self.close)
                self.panel <= " "

        self.bind('touchstart', self.on_touch_start)

    def on_touch_start(self, ev):  # pylint: disable=invalid-name
        """ on_touch_start """
        ev.preventDefault()
        self.bind('touchmove', self.on_touch_move)
        self.bind('touchend', self.on_touch_end)

    def on_touch_move(self, ev):  # pylint: disable=invalid-name
        """ on_touch_move """
        touched = ev.touches[0]
        self.style.left = f"{touched.clientX}px"
        self.style.top = f"{touched.clientY}px"

    def on_touch_end(self, ev):  # pylint: disable=invalid-name
        """ on_touch_end """
        ev.preventDefault()
        self.unbind('touchmove')
        self.unbind('touchend')


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
        Dialog.__init__(self, title, **kargs, can_close=False)
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
