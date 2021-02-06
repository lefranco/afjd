""" login """

from browser import document, html, ajax
from browser.widgets.dialog import InfoDialog
from browser.local_storage import storage

import config
import json


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


def login_callback(ev) -> None:
    """ login_callback """

    print(f"login_callback {input_pseudo.value=} {input_password.value=}")

    def reply_callback(req):
        print("reply_callback")
        print(f"{req=}")
        req_result = json.loads(req.text)
        print(f"{req_result=}")
        if req.status != 200:
            InfoDialog("KO", f"Il y a eu un problème : {req_result['msg']}", remove_after=config.REMOVE_AFTER)
            return
        print(f"{req_result=}")
        storage['JWT_TOKEN'] = req_result['AccessToken']

    def noreply_callback(req):
        print("noreply_callback")
        InfoDialog("KO", f"Il y a eu un problème (pas de réponse du serveur)", remove_after=config.REMOVE_AFTER)

    pseudo = input_pseudo.value
    password = input_password.value

    host = config.SERVER_CONFIG['USER']['HOST']
    port = config.SERVER_CONFIG['USER']['PORT']
    url = f"{host}:{port}/login"

    ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=2.0, data=json.dumps({'user_name': pseudo, 'password': password}), oncomplete=reply_callback, ontimeout=noreply_callback)


def forgot_callback(ev) -> None:
    """ forgot_callback """
    sorry = InfoDialog("Sorry", "Forgot password is not implemented yet", remove_after=config.REMOVE_AFTER)
    form <= sorry


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
