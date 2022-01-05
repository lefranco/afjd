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
import index  # circular import

MY_PANEL = html.DIV(id="login")
MY_PANEL.attrs['style'] = 'display: table'


def login():
    """ login """

    def login_callback(_):
        """ login_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la connexion : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la connexion : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but still refresh window
                render(PANEL_MIDDLE)

                return

            storage['PSEUDO'] = pseudo
            storage['JWT_TOKEN'] = req_result['AccessToken']
            time_stamp = time.time()
            storage['LOGIN_TIME'] = str(time_stamp)
            InfoDialog("OK", f"Connecté avec succès en tant que {pseudo} - cette information est rappelée en bas de la page", remove_after=config.REMOVE_AFTER)
            show_login()

            # goto directly to page my games
            index.load_option(None, 'mes parties')

        pseudo = input_pseudo.value
        if not pseudo:
            alert("Il manque le pseudo !")
            render(PANEL_MIDDLE)
            return

        password = input_password.value
        if not password:
            alert("Il manque le mot de passe !")
            render(PANEL_MIDDLE)
            return

        if pseudo.find("@") != -1:
            alert("Attention, c'est le pseudo qui est demandé, pas le courriel !")
            render(PANEL_MIDDLE)
            return

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

        alert("Désolé: la récupération du mot de passe n'est pas encore implémentée - vous pouvez contacter le support (cf. page d'accueil / onglet 'déclarer un incident') qui vous forcera un nouveau mot de passe")

        render(PANEL_MIDDLE)

    def logout_callback(_):
        """ logout_callback """

        effective = logout()

        if not effective:
            alert("Déjà déconnecté !")
        else:
            InfoDialog("OK", "Déconnecté avec succès", remove_after=config.REMOVE_AFTER)

        render(PANEL_MIDDLE)

    # begins here

    sub_panel = html.DIV(id='sub_panel')

    # --
    form1 = html.FORM()

    form1 <= html.DIV("Pas de compte ? Créez-le à partir du menu 'mon compte'...", Class='note')
    form1 <= html.BR()

    proposed_pseudo = ""
    if 'PSEUDO' in storage:
        proposed_pseudo = storage['PSEUDO']

    fieldset = html.FIELDSET()
    legend_pseudo = html.LEGEND("Pseudo", title="Attention la casse est importante")
    fieldset <= legend_pseudo
    input_pseudo = html.INPUT(type="text", value=proposed_pseudo)
    fieldset <= input_pseudo
    form1 <= fieldset

    fieldset = html.FIELDSET()
    legend_password = html.LEGEND("Mot de passe", title="Notez le dans un coin !")
    fieldset <= legend_password
    input_password = html.INPUT(type="password", value="")
    fieldset <= input_password
    form1 <= fieldset
    form1 <= html.BR()

    input_login = html.INPUT(type="submit", value="connexion")
    input_login.bind("click", login_callback)
    form1 <= input_login

    sub_panel <= form1
    sub_panel <= html.BR()
    sub_panel <= html.BR()

    # --
    form2 = html.FORM()

    input_forgot = html.INPUT(type="submit", value="mot de passe oublié")
    input_forgot.bind("click", forgot_callback)
    form2 <= input_forgot

    sub_panel <= form2
    sub_panel <= html.BR()
    sub_panel <= html.BR()

    # --
    form3 = html.FORM()

    input_logout = html.INPUT(type="submit", value="déconnexion")
    input_logout.bind("click", logout_callback)
    form3 <= input_logout

    sub_panel <= form3

    return sub_panel


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

    if PANEL_MIDDLE is not None:
        render(PANEL_MIDDLE)

    return effective


def check_token():
    """ check_token """

    status = True

    def reply_callback(req):
        nonlocal status
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la vérification du jeton d'authentification : {req_result['message']}")
            elif 'msg' in req_result:

                messages = "<br>".join(req_result['msg'].split('\n'))
                InfoDialog("OK", f"Votre jeton d'authentification a expiré.<br>Vous devez juste vous loguer à nouveau {messages}", remove_after=config.REMOVE_AFTER)
            else:
                alert("Réponse du serveur imprévue et non documentée")
            logout()
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

    json_dict = {}

    # check token : need token
    # note : since we access directly to the user server, we present the token in a slightly different way
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


def show_login():
    """  show_login """

    log_message = html.DIV()
    if 'PSEUDO' in storage:
        log_message <= "Connecté en tant que "
        log_message <= html.B(storage['PSEUDO'])
    else:
        log_message <= "En visite..."

    if 'LOGIN_TIME' in storage:
        # this is local time
        time_stamp = round(float(storage['LOGIN_TIME']))
        date_desc = datetime.datetime.fromtimestamp(time_stamp)
        log_message <= f", depuis {date_desc} (temps local)"

    show_login_panel = html.DIV(id="show_login")
    show_login_panel.attrs['style'] = 'text-align: left'
    show_login_panel <= log_message

    if 'show_login' in document:
        del document['show_login']

    document <= show_login_panel


PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    PANEL_MIDDLE = panel_middle

    MY_PANEL.clear()

    login_panel = login()

    if login_panel:
        MY_PANEL <= html.H2("Identifiez-vous pour accéder aux ressources protégées")
        MY_PANEL <= login_panel

    PANEL_MIDDLE <= MY_PANEL
