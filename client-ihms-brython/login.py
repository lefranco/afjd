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
        storage['LOGIN_TIME'] = time.time()
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

def logout_callback(_) -> None:
    """ logout_callback """

    effective = False
    if 'PSEUDO' in storage:
        del storage['PSEUDO']
        effective = True
    if 'JWT_TOKEN'in storage:
        del storage['JWT_TOKEN']
        effective = True
    if 'LOGIN_TIME'in storage:
        del storage['LOGIN_TIME']
        effective = True
    if effective:
        InfoDialog("OK", f"Successful logout", remove_after=config.REMOVE_AFTER)


my_panel = html.DIV(id="login")

form1 = html.FORM()

legend_pseudo = html.LEGEND("pseudo")
form1 <= legend_pseudo
input_pseudo = html.INPUT(type="text", value="")
form1 <= input_pseudo
form1 <= html.BR()

legend_password = html.LEGEND("password")
form1 <= legend_password
input_password = html.INPUT(type="password", value="")
form1 <= input_password
form1 <= html.BR()

input_login = html.INPUT(type="submit", value="login")
input_login.bind("click", login_callback)
form1 <= input_login
form1 <= html.BR()

my_panel <= form1
my_panel <= html.BR()

form2 = html.FORM()

input_forgot = html.INPUT(type="submit", value="forgot password")
input_forgot.bind("click", forgot_callback)
form2 <= input_forgot
form2 <= html.BR()

my_panel <= form2
my_panel <= html.BR()

form3 = html.FORM()

input_logout = html.INPUT(type="submit", value="logout")
input_logout.bind("click", logout_callback)
form3 <= input_logout
form3 <= html.BR()

my_panel <= form3

def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
