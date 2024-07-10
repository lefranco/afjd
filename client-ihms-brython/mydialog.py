""" rewrite of dialog module from Brython """

# pylint: disable=pointless-statement, expression-not-assigned


from browser import document, html, window, alert  # pylint: disable=import-error

# pylint: disable=invalid-name
style_sheet = """
:root {
    --brython-dialog-font-family: Arial;
    --brython-dialog-font-size: 100%;
    --brython-dialog-bgcolor: #fff;
    --brython-dialog-border-color: #000;
    --brython-dialog-title-bgcolor: CadetBlue;
    --brython-dialog-title-color: #fff;
    --brython-dialog-close-bgcolor: #fff;
    --brython-dialog-close-color: #000;
}

.brython-dialog-main {
    font-family: var(--brython-dialog-font-family);
    font-size: var(--brython-dialog-font-size);
    background-color: var(--brython-dialog-bgcolor);
    left: 10px;
    top: 10px;
    border-style: solid;
    border-color: var(--brython-dialog-border-color);
    border-width: 1px;
    z-index: 10;
}

.brython-dialog-title {
    background-color: var(--brython-dialog-title-bgcolor);
    color: var(--brython-dialog-title-color);
    border-style: solid;
    border-color: var(--brython-dialog-border-color);
    border-width: 0px 0px 1px 0px;
    padding: 0.4em;
    cursor: default;
}

.brython-dialog-close {
    float: right;
    background-color: var(--brython-dialog-close-bgcolor);
    color: var(--brython-dialog-close-color);
    cursor: default;
    padding: 0.1em;
}

.brython-dialog-panel {
    box-sizing: border-box;
    padding:0.2em;
}

.brython-dialog-message {
    padding-right: 0.6em;
}

.brython-dialog-button {
    margin: 0.5em;
}
"""

REMOVE_AFTER_SEC = 5


POPUP_OCCUPATION = {n : None for n in range(5)}


class Dialog(html.DIV):
    """Basic, moveable dialog box with a title bar, optional
    "Ok" / "Cancel" buttons.
    The "Ok" button is the attribute "ok_button" of the dialog object.
    Supports drag and drop on the document.
    A dialog has an attribute "panel" that can contain elements.
    Method close() removes the dialog box.
    """

    def __init__(self, title="", ok_cancel=False, default_css=True):

        if default_css:
            for stylesheet in document.styleSheets:
                if stylesheet.ownerNode.id == "brython-dialog":
                    break
            else:
                document <= html.STYLE(style_sheet, id="brython-dialog")

        html.DIV.__init__(self, style={"position": 'absolute'}, Class="brython-dialog-main")

        # Put popup
        document <= self

        self.title_bar = html.DIV(html.SPAN(title), Class="brython-dialog-title")
        self <= self.title_bar
        self.close_button = html.SPAN("&times;", Class="brython-dialog-close")
        self.title_bar <= self.close_button
        self.close_button.bind("click", self.close)
        self.panel = html.DIV(Class="brython-dialog-panel")
        self <= self.panel

        if ok_cancel:
            ok_cancel_zone = html.DIV(style={"text-align": "center"})
            ok, cancel = "Ok", "Cancel"
            if isinstance(ok_cancel, (list, tuple)):
                if not len(ok_cancel) == 2:
                    raise ValueError(
                        f"ok_cancel expects 2 elements, got {len(ok_cancel)}")
                ok, cancel = ok_cancel
            self.ok_button = html.BUTTON(ok, Class="brython-dialog-button")
            self.cancel_button = html.BUTTON(cancel, Class="brython-dialog-button")
            self.cancel_button.bind("click", self.close)
            ok_cancel_zone <= self.ok_button + self.cancel_button
            self <= ok_cancel_zone

        cstyle = window.getComputedStyle(self)

        # Center horizontally and vertically
        width = round(float(cstyle.width[:-2]) + 0.5)
        self.left = int((window.innerWidth - width) / 2)
        # left to document scrollTop
        adjust_left = round(document.scrollingElement.scrollLeft)
        self.left += adjust_left
        self.style.left = f'{self.left}px'

        height = round(float(cstyle.height[:-2]) + 0.5)
        self.top = int((window.innerHeight - height) / 2)
        # top is relative to document scrollTop
        adjust_top = round(document.scrollingElement.scrollTop)
        self.top += adjust_top
        self.style.top = f'{self.top}px'

        # Take occupation slot if available
        for popup_pos, occupant in POPUP_OCCUPATION.items():
            if not occupant:
                POPUP_OCCUPATION[popup_pos] = self
                self.popup_pos = popup_pos
                break
        else:
            alert("Trop de popups !")
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
                self.left += window.innerWidth // 4
                self.top += window.innerHeight // 4
            case 2:
                self.left -= window.innerWidth // 4
                self.top += window.innerHeight // 4
            case 3:
                self.left -= window.innerWidth // 4
                self.top -= window.innerHeight // 4
            case 4:
                self.left += window.innerWidth // 4
                self.top -= window.innerHeight // 4

        self.title_bar.bind("mousedown", self.mousedown)
        self.title_bar.bind("touchstart", self.mousedown)
        self.title_bar.bind("mouseup", self.mouseup)
        self.title_bar.bind("touchend", self.mouseup)
        self.bind("leave", self.mouseup)
        self.is_moving = False
        self.initial = [0, 0]  # defined at init

    def close(self, *_):
        """ close """
        
        # Free occupation slot
        if self.popup_pos >= 0:
            POPUP_OCCUPATION[self.popup_pos] = None
            
        self.remove()

    def mousedown(self, event):
        """ mousedown """
        document.bind("mousemove", self.mousemove)
        document.bind("touchmove", self.mousemove)
        self.is_moving = True
        self.initial = [self.left - event.x, self.top - event.y]
        # prevent default behaviour to avoid selecting the moving element
        event.preventDefault()

    def mousemove(self, event):
        """ mousemove """
        if not self.is_moving:
            return

        # set new moving element coordinates
        self.left = self.initial[0] + event.x
        self.top = self.initial[1] + event.y

    def mouseup(self, _):
        """ mouseup """
        self.is_moving = False
        document.unbind("mousemove")
        document.unbind("touchmove")


class InfoDialog(Dialog):
    """Dialog box with an information message and no "Ok / Cancel" button."""

    def __init__(self, title, message, confirm=False, default_css=True):
        """If remove_after is set, number of seconds after which the dialog is
        removed."""
        Dialog.__init__(self, title, default_css=default_css)
        self.panel <= html.DIV(message)
        if confirm:
            self.ok_button = html.BUTTON("OK", Class="brython-dialog-button")
            self.panel <= html.P()
            self.panel <= html.DIV(self.ok_button, style={"text-align": "center"})
            self.ok_button.bind("click", lambda ev: self.close())
        else:
            window.setTimeout(self.close, REMOVE_AFTER_SEC * 1000)
