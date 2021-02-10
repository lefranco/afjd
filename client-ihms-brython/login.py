""" login """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config


def noreply_callback(_):
    """ noreply_callback """
    print("noreply_callback")
    alert("Problem (no answer from server)")


def login_callback(_) -> None:
    """ login_callback """

    print(f"login_callback {input_pseudo.value=} {input_password.value=}")

    def reply_callback(req):
        print("reply_callback")
        print(f"{req=}")
        req_result = json.loads(req.text)
        print(f"{req_result=}")
        if req.status != 200:
            alert(f"Problem : {req_result['msg']}")
            return
        print(f"{req_result=}")
        storage['PSEUDO'] = pseudo
        storage['JWT_TOKEN'] = req_result['AccessToken']
        InfoDialog("OK", f"Successful login as {pseudo}", remove_after=config.REMOVE_AFTER)

    pseudo = input_pseudo.value
    password = input_password.value

    host = config.SERVER_CONFIG['USER']['HOST']
    port = config.SERVER_CONFIG['USER']['PORT']
    url = f"{host}:{port}/login"

    json_dict = {
        'user_name': pseudo,
        'password': password
    }

    ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)


def forgot_callback(_) -> None:
    """ forgot_callback """
    alert("Sorry: Forgot password is not implemented yet")

my_panel = html.DIV(id="login")

form = html.FORM()
my_panel <= form

legend_pseudo = html.LEGEND("pseudo")
form <= legend_pseudo
input_pseudo = html.INPUT(type="text", value="")
form <= input_pseudo
form <= html.BR()

legend_password = html.LEGEND("password")
form <= legend_password
input_password = html.INPUT(type="password", value="")
form <= input_password
form <= html.BR()

input_login = html.INPUT(type="submit", value="login")
input_login.bind("click", login_callback)
form <= input_login
form <= html.BR()

input_forgot = html.INPUT(type="submit", value="forgot password")
input_forgot.bind("click", forgot_callback)
form <= input_forgot
form <= html.BR()


def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
