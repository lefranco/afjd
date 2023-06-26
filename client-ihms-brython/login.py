""" login """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time

from browser import document, html, ajax, alert  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import config
import common
import index  # circular import

MY_PANEL = html.DIV(id="login")
MY_PANEL.attrs['style'] = 'display: table-row'


def email_confirmed(pseudo):
    """ email_confirmed """

    email_confirmed_loaded = False

    def reply_callback(req):
        nonlocal email_confirmed_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des informations du compte : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des informations du compte : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        email_confirmed_loaded = req_result['email_confirmed']
        return

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/players/{pseudo}"

    # reading data about account : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return email_confirmed_loaded


PREVIOUS_PSEUDO = None


def login():
    """ login """

    def detect_caps_lock_callback(event):
        """ detect_caps_lock_callback """

        pressed = event.getModifierState("CapsLock")
        if pressed:
            alert("Attention : vous êtes en mode majuscules !")

    def login_callback(ev):  # pylint: disable=invalid-name
        """ login_callback """

        global PREVIOUS_PSEUDO

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

            # extract data from request result
            token_duration_days = req_result['TokenDurationDays']
            access_token = req_result['AccessToken']

            # store data

            # the peudo of player logged in
            storage['PSEUDO'] = pseudo
            # the token itself
            storage['JWT_TOKEN'] = access_token
            # the login time
            time_stamp_now = time.time()
            storage['LOGIN_TIME'] = str(time_stamp_now)
            # token expiration time
            login_expiration_time = time_stamp_now + token_duration_days * 24 * 3600
            storage['LOGIN_EXPIRATION_TIME'] = str(login_expiration_time)

            # inform user
            common.info_dialog(f"Connecté avec succès en tant que {pseudo} - cette information est rappelée en bas de la page", True)
            show_login()

            # request to validate email
            if not email_confirmed(pseudo):
                alert("Merci de penser à vérifier votre adresse courriel. Cela évite que les message du site reviennent en erreur. Pour ce faire : mon_compte/valider mon courriel - 'me renvoyer un nouveau code', recopier le code du courriel que vous avez reçu et 'valider le courriel'\n\nATTENTION : Les comptes avec une adresses courriel en erreur sont susceptibles d'être fermés pour éviter de mettre le site en liste noire")

            # goto directly to page my games
            index.load_option(None, 'Mes parties')

        ev.preventDefault()

        pseudo = input_pseudo.value

        # remember what was entered to propose it if fails
        PREVIOUS_PSEUDO = pseudo

        if not pseudo:
            alert("Il manque le pseudo !")
            render(PANEL_MIDDLE)
            return

        if pseudo.find(' ') != -1:
            alert("Attention, il y a un espace dans le pseudo que vous avez saisi... retirez-le !")
            render(PANEL_MIDDLE)
            return

        if pseudo.find("@") != -1:
            alert("Attention, c'est le pseudo qui est demandé, pas le courriel !")
            render(PANEL_MIDDLE)
            return

        password = input_password.value
        if not password:
            alert("Il manque le mot de passe !")
            render(PANEL_MIDDLE)
            return

        # should have an IP
        ip_value = None
        if 'IPADDRESS' in storage:
            ip_value = storage['IPADDRESS']

        host = config.SERVER_CONFIG['USER']['HOST']
        port = config.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/login"

        json_dict = {
            'user_name': pseudo,
            'password': password,
            'ip_address': ip_value
        }

        # login (getting token) : no need for token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def forgot_callback(ev):  # pylint: disable=invalid-name
        """ forgot_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au sauvetage : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au sauvetage : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but still refresh window
                render(PANEL_MIDDLE)

                return

            alert("Un lien de sauvetage vous a été envoyé par courriel...")
            render(PANEL_MIDDLE)

        ev.preventDefault()

        pseudo = input_pseudo.value

        if not pseudo:
            alert("Il manque le pseudo !")
            render(PANEL_MIDDLE)
            return

        # should have an IP
        ip_value = None
        if 'IPADDRESS' in storage:
            ip_value = storage['IPADDRESS']

        host = config.SERVER_CONFIG['USER']['HOST']
        port = config.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/rescue"

        json_dict = {
            'user_name': pseudo,
            'ip_address': ip_value
        }

        # rescue (getting token) : no need for token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def logout_callback(ev):  # pylint: disable=invalid-name
        """ logout_callback """

        ev.preventDefault()

        effective = logout()

        if not effective:
            alert("Déjà déconnecté !")
        else:
            common.info_dialog("Déconnecté avec succès", True)

        render(PANEL_MIDDLE)

    def create_account_callback(_):
        """ create_account_callback """

        # go to create account page
        index.load_option(None, 'Mon compte')

    # begins here

    sub_panel = html.DIV(id='sub_panel')

    # --
    form = html.FORM()

    # try to make user gain a bit of time
    if PREVIOUS_PSEUDO is not None:
        proposed_pseudo = PREVIOUS_PSEUDO
    elif 'PSEUDO' in storage:
        proposed_pseudo = storage['PSEUDO']
    else:
        proposed_pseudo = ""

    fieldset = html.FIELDSET()
    legend_pseudo = html.LEGEND("Pseudo", title="Attention la casse est importante")
    fieldset <= legend_pseudo
    input_pseudo = html.INPUT(type="text", value=proposed_pseudo)
    fieldset <= input_pseudo
    form <= fieldset
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_password = html.LEGEND("Mot de passe", title="Notez le dans un coin !")
    fieldset <= legend_password
    input_password = html.INPUT(type="password", value="")
    fieldset <= input_password
    form <= fieldset
    form <= html.BR()

    # detect caps lock
    input_password.bind("keypress", detect_caps_lock_callback)

    input_login = html.INPUT(type="submit", value="Connexion")
    input_login.bind("click", login_callback)
    form <= input_login
    form <= html.BR()
    form <= html.BR()

    # --

    input_forgot = html.INPUT(type="submit", value="Mot de passe oublié")
    input_forgot.bind("click", forgot_callback)
    form <= input_forgot
    form <= html.BR()
    form <= html.BR()

    # --

    if 'PSEUDO' in storage:
        input_logout = html.INPUT(type="submit", value="Déconnexion")
        input_logout.bind("click", logout_callback)
        form <= input_logout
        form <= html.BR()
        form <= html.BR()

    # --

    if 'PSEUDO' not in storage:
        # shortcut to create account
        input_create_account = html.INPUT(type="submit", value="Je n'ai pas de compte, je veux le créer !")
        input_create_account.bind("click", create_account_callback)
        form <= input_create_account
        form <= html.BR()
        form <= html.BR()

    sub_panel <= form

    return sub_panel


def logout():
    """ logout """

    global PREVIOUS_PSEUDO

    effective = False

    if 'PSEUDO' in storage:
        del storage['PSEUDO']
        effective = True

    if 'LOGIN_TIME' in storage:
        del storage['LOGIN_TIME']
        effective = True

    PREVIOUS_PSEUDO = None

    show_login()

    if PANEL_MIDDLE is not None:
        render(PANEL_MIDDLE)

    return effective


def check_token():
    """ check_token """

    if 'PSEUDO' not in storage:
        return

    if 'JWT_TOKEN' not in storage:
        # should not happen (or tweak)
        common.info_dialog("Pour des raisons techniques il faut vous loguer à nouveau !")
        return

    if 'LOGIN_EXPIRATION_TIME' not in storage:
        # should not happen (or tweak or transition period)
        common.info_dialog("Pour des raisons techniques il faut vous loguer à nouveau !")
        logout()
        return

    # fast imprecise method
    time_stamp_now = time.time()
    time_stamp_expiration = float(storage['LOGIN_EXPIRATION_TIME'])
    if time_stamp_now > time_stamp_expiration:
        alert("Votre jeton d'authentification a expiré... Vous devez juste vous loguer à nouveau !")
        logout()


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
        date_desc = mydatetime.fromtimestamp(time_stamp)
        date_desc_str = mydatetime.strftime(*date_desc)
        log_message <= f", depuis {date_desc_str}"

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
