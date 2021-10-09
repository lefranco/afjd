""" login """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time
import datetime

from browser import document, html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common


def check_token():
    """ check_token """

    status = True

    def reply_callback(req):
        """ reply_callback """
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error checking token: {req_result['message']}")
            elif 'msg' in req_result:

                #  alert(f"Problem checking token: {req_result['msg']}")
                messages = "<br>".join(req_result['msg'].split('\n'))
                InfoDialog("OK", f"Votre jeton d'authentification a expiré.<br>Vous devez juste vous loguer à nouveau {messages}", remove_after=config.REMOVE_AFTER)
            else:
                alert("Undocumented issue from server")
            logout()
            nonlocal status
            status = False

    if 'PSEUDO' not in storage:
        return

    if 'JWT_TOKEN' not in storage:
        # should not happen
        return

    # check authentication from user server
    host = config.SERVER_CONFIG['USER']['HOST']
    port = config.SERVER_CONFIG['USER']['PORT']
    url = f"{host}:{port}/verify"

    json_dict = dict()

    # check token : need token
    # note : since we access directly to the user server, we present the token in a slightly different way
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


def login_callback(_):
    """ login_callback """

    def reply_callback(req):
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error logging in: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem logging in: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return
        storage['PSEUDO'] = pseudo
        storage['JWT_TOKEN'] = req_result['AccessToken']
        time_stamp = time.time()
        storage['LOGIN_TIME'] = str(time_stamp)
        InfoDialog("OK", f"Logué avec succès en tant que {pseudo}", remove_after=config.REMOVE_AFTER)
        show_login()

    pseudo = input_pseudo.value
    password = input_password.value

    host = config.SERVER_CONFIG['USER']['HOST']
    port = config.SERVER_CONFIG['USER']['PORT']
    url = f"{host}:{port}/login"

    json_dict = {
        'user_name': pseudo,
        'password': password
    }

    # login (getting token) : no need for token
    ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


def forgot_callback(_):
    """ forgot_callback """

    alert("Désolé: la récupération du mot de passe n'est pas encore implémentée - vous pouvez contacter le support (cf. page d'accueil) qui vous forcera un nouveau mot de passe")


def logout():
    """ logout """

    effective = False
    if 'PSEUDO' in storage:
        del storage['PSEUDO']
        effective = True
    if 'LOGIN_TIME' in storage:
        del storage['LOGIN_TIME']
        effective = True
    show_login()
    return effective


def logout_callback(_):
    """ logout_callback """
    effective = logout()
    if effective:
        InfoDialog("OK", "Délogué avec succès", remove_after=config.REMOVE_AFTER)


my_panel = html.DIV(id="login")

form1 = html.FORM()


form1 <= html.B("Pas de compte ? Crééz-le à partir du menu 'mon compte'...")
form1 <= html.BR()
form1 <= html.BR()

legend_pseudo = html.LEGEND("pseudo")
form1 <= legend_pseudo

PROPOSED_PSEUDO = ""
if 'PSEUDO' in storage:
    PROPOSED_PSEUDO = storage['PSEUDO']

input_pseudo = html.INPUT(type="text", value=PROPOSED_PSEUDO)
form1 <= input_pseudo
form1 <= html.BR()

legend_password = html.LEGEND("mot de passe")
form1 <= legend_password
input_password = html.INPUT(type="password", value="")
form1 <= input_password
form1 <= html.BR()

form1 <= html.BR()

input_login = html.INPUT(type="submit", value="connexion")
input_login.bind("click", login_callback)
form1 <= input_login
form1 <= html.BR()

my_panel <= form1
my_panel <= html.BR()

form2 = html.FORM()

input_forgot = html.INPUT(type="submit", value="mot de passe oublié")
input_forgot.bind("click", forgot_callback)
form2 <= input_forgot
form2 <= html.BR()

my_panel <= form2
my_panel <= html.BR()

form3 = html.FORM()

input_logout = html.INPUT(type="submit", value="déconnexion")
input_logout.bind("click", logout_callback)
form3 <= input_logout
form3 <= html.BR()

my_panel <= form3


def show_login():
    """  show_login """

    log_message = html.DIV()
    if 'PSEUDO' in storage:
        log_message <= "Logué en tant que "
        log_message <= html.B(storage['PSEUDO'])
    else:
        log_message <= "En visite..."

    if 'LOGIN_TIME' in storage:
        # this is local time
        time_stamp = float(storage['LOGIN_TIME'])
        date_desc = datetime.datetime.fromtimestamp(time_stamp)
        log_message <= f", depuis {date_desc} (temps local)"

    show_login_panel = html.DIV(id="show_login")
    show_login_panel.attrs['style'] = 'text-align: left'
    show_login_panel <= log_message

    if 'show_login' in document:
        del document['show_login']

    document <= show_login_panel


def render(panel_middle):
    """ render """

    panel_middle <= my_panel
