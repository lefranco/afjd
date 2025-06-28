""" account """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydialog
import config
import common
import login
import welcome
import home

OPTIONS = {
    'Editer': "Modifier une information personnelle",
    'Valider mon courriel': "Valider mon adresse courriel",
    'Mot de passe': "Changer mon mot de passe",
    'Mon code forum': "Visualiser mon code de vérification pour le forum",
    'Supprimer': "Supprimer mon compte sur le site",
}


MIN_LEN_PSEUDO = 3
MAX_LEN_PSEUDO = 20
MAX_LEN_EMAIL = 100

DEFAULT_COUNTRY_CODE = "FRA"


RESCUE = False


def date_last_visit_update():
    """ date_last_visit_update """

    def reply_callback(req):
        req_result = loads(req.text)
        if req.status != 201:
            if 'message' in req_result:
                alert(f"Erreur à la mise à jour de la dernière visite des messages prives: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la mise à jour de la dernière visite des messages prives : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

    json_dict = {
    }

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/private-visits"

    # putting visit  : need token
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


def set_rescue():
    """ set_rescue """
    global RESCUE
    RESCUE = True


def information_about_private_data():
    """ information_about_private_data """

    def show_private_data_callback(ev):  # pylint: disable=invalid-name
        """ show_private_data_callback """

        ev.preventDefault()

        arrival = 'RGPD'

        # so that will go to proper page
        home.set_arrival(arrival)

        # action of going to game page
        PANEL_MIDDLE.clear()
        home.render(PANEL_MIDDLE)

    form = html.FORM()
    input_show_private_data = html.INPUT(type="submit", value="Les données personnelles (R.G.P.D.)", Class='btn-inside')
    input_show_private_data.bind("click", show_private_data_callback)
    form <= input_show_private_data
    return form


def information_about_input():
    """ information_about_account """

    information = html.DIV(Class='note')
    information <= "Survolez les titres pour pour plus de détails"
    return information


def information_about_account():
    """ information_about_account """

    information = html.DIV(Class='note')
    information <= html.B("Vous voulez rester discret ?")
    information <= html.BR()
    information <= "La plupart des champs sont privés et ne seront pas montrés sur le site et/ou facultatifs."
    information <= html.BR()
    return information


def information_about_account2():
    """ information_about_account2 """

    information = html.DIV(Class='important')
    information <= f"ATTENTION : Un compte oisif plus de {config.IDLE_DAY_TIMEOUT} jours sera supprimé pour ne pas encombrer le système."
    return information


def information_about_emails():
    """ information_about_emails """

    information = html.DIV(Class='note')
    information <= "Vous recevrez un courriel de rappel de l'arbitre si vous êtes en retard sur les ordres. Un courriel au démarrage et à l'arrêt de vos parties. Un courriel de notification de résolution et/ou de message ou presse dans la partie. Sauf dans le premier cas, seulement si vous l'avez demandé. Un courriel à la suppression du compte. Un courriel à chaque modification d'adresse courriel pour vérifier celle-ci..."
    information <= html.BR()
    information <= "Rien de plus !"
    information <= html.BR()
    information <= "Il vous est déconseillé d'utiliser une adresse courriel professionelle."
    return information


def information_about_pseudo():
    """ information_about_emails """

    information = html.DIV(Class='important')
    information <= "Un pseudo inapproprié pourra être refusé sur le site (et le compte supprimé)"
    return information


def information_about_confirm():
    """ information_about_account """

    information = html.DIV(Class='note')
    information <= html.B("Vous arrivez sur cette page ? Cliquez sur le bouton 'Me renvoyer un nouveau code' et consultez votre boite à lettre. Recopiez le code ici et cliquez 'Valider le courriel'")
    information <= html.BR()
    return information


def create_account(json_dict):
    """ create_account """

    # load previous values if applicable
    pseudo = json_dict['pseudo'] if json_dict and 'pseudo' in json_dict else None
    password = json_dict['password'] if json_dict and 'password' in json_dict else None
    password_again = json_dict['password_again'] if json_dict and 'password_again' in json_dict else None
    email = json_dict['email'] if json_dict and 'email' in json_dict else None
    notify_deadline = json_dict['notify_deadline'] if json_dict and 'notify_deadline' in json_dict else None
    notify_adjudication = json_dict['notify_adjudication'] if json_dict and 'notify_adjudication' in json_dict else None
    notify_message = json_dict['notify_message'] if json_dict and 'notify_message' in json_dict else None
    notify_replace = json_dict['notify_replace'] if json_dict and 'notify_replace' in json_dict else None
    newsletter = json_dict['newsletter'] if json_dict and 'newsletter' in json_dict else None
    family_name = json_dict['family_name'] if json_dict and 'pseudo' in json_dict else None
    first_name = json_dict['first_name'] if json_dict and 'family_name' in json_dict else None
    residence_code = json_dict['residence'] if json_dict and 'residence' in json_dict else DEFAULT_COUNTRY_CODE
    nationality_code = json_dict['nationality'] if json_dict and 'nationality' in json_dict else DEFAULT_COUNTRY_CODE

    # conversion
    residence = {v: k for k, v in config.COUNTRY_CODE_TABLE.items()}[residence_code]
    nationality = {v: k for k, v in config.COUNTRY_CODE_TABLE.items()}[nationality_code]

    def create_account_callback(ev):  # pylint: disable=invalid-name
        """ create_account_callback """

        nonlocal pseudo
        nonlocal password
        nonlocal password_again
        nonlocal email
        nonlocal notify_deadline
        nonlocal notify_adjudication
        nonlocal notify_message
        nonlocal notify_replace
        nonlocal newsletter
        nonlocal family_name
        nonlocal first_name
        nonlocal residence
        nonlocal nationality

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la création du compte : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la création du compte  : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Votre compte a été créé : {messages}")
            alert(f"Félicition, votre compte a été crée.\n\nUn code de vérification vous a été envoyé pour vérifier votre adresse courriel.\n\n Attention : votre compte sera supprimé après {config.IDLE_DAY_TIMEOUT / 30.5} mois d'inactivité")
            alert(welcome.MESSAGE)

        ev.preventDefault()

        # get values from user input

        pseudo = input_pseudo.value
        password = input_password.value
        password_again = input_password_again.value
        email = input_email.value
        notify_deadline = int(input_notify_deadline.checked)
        notify_adjudication = int(input_notify_adjudication.checked)
        notify_message = int(input_notify_message.checked)
        notify_replace = int(input_notify_replace.checked)
        newsletter = int(input_newsletter.checked)
        family_name = input_family_name.value
        first_name = input_first_name.value
        residence = input_residence.value
        nationality = input_nationality.value

        # conversion
        residence_code = config.COUNTRY_CODE_TABLE[residence]
        nationality_code = config.COUNTRY_CODE_TABLE[nationality]

        # make data structure
        json_dict = {
            'pseudo': pseudo,
            'password': password,
            'password_again': password_again,
            'email': email,
            'notify_deadline': notify_deadline,
            'notify_adjudication': notify_adjudication,
            'notify_message': notify_message,
            'notify_replace': notify_replace,
            'newsletter': newsletter,
            'family_name': family_name,
            'first_name': first_name,
            'residence': residence_code,
            'nationality': nationality_code,
        }

        # start checking data

        if not pseudo:
            alert("Pseudo manquant")
            MY_SUB_PANEL.clear()
            create_account(json_dict)
            return

        if len(pseudo) < MIN_LEN_PSEUDO:
            alert("Pseudo trop court")
            MY_SUB_PANEL.clear()
            create_account(json_dict)
            return

        if len(pseudo) > MAX_LEN_PSEUDO:
            alert("Pseudo trop long")
            MY_SUB_PANEL.clear()
            create_account(json_dict)
            return

        if not password:
            alert("Mot de passe manquant")
            MY_SUB_PANEL.clear()
            create_account(json_dict)
            return

        if password_again != password:
            alert("Les mots de passe ne correspondent pas")
            MY_SUB_PANEL.clear()
            create_account(json_dict)
            return

        if not email:
            alert("courriel manquant")
            MY_SUB_PANEL.clear()
            create_account(json_dict)
            return

        if email.find('@') == -1:
            alert("@ dans courriel manquant")
            MY_SUB_PANEL.clear()
            create_account(json_dict)
            return

        del json_dict['password_again']

        # send to server

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players"

        # adding a player : no need for token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # restore password again in case of failure
        json_dict['password_again'] = password_again

        # back to where we started
        MY_SUB_PANEL.clear()
        create_account(json_dict)

    MY_SUB_PANEL <= html.H3("Création du compte")

    MY_SUB_PANEL <= information_about_private_data()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= information_about_account()
    MY_SUB_PANEL <= html.BR()

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    form <= html.DIV("Pas d'accents, d'espaces ni de tirets dans le pseudo", Class='note')
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_pseudo = html.LEGEND("pseudo", title="Votre identifiant sur le site")
    fieldset <= legend_pseudo
    input_pseudo = html.INPUT(type="text", value=pseudo if pseudo is not None else "", Class='btn-inside')
    fieldset <= input_pseudo
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_password = html.LEGEND("mot de passe", title="Pour empêcher les autres de jouer à votre place;-)")
    fieldset <= legend_password
    input_password = html.INPUT(type="password", value=password if password is not None else "", Class='btn-inside')
    fieldset <= input_password
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_password_again = html.LEGEND("confirmation mot de passe", title="Pour éviter une faute de frappe sur le mot de passe")
    fieldset <= legend_password_again
    input_password_again = html.INPUT(type="password", value=password_again if password_again is not None else "", Class='btn-inside')
    fieldset <= input_password_again
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_email = html.LEGEND("courriel (privé) - impérativement un courriel valide !", title="Le site vous notifiera de quelques très rares événements (sauf si vous demandez les notifications)")
    fieldset <= legend_email
    input_email = html.INPUT(type="email", value=email if email is not None else "", size=MAX_LEN_EMAIL, Class='btn-inside')
    fieldset <= input_email
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_notify_deadline = html.LEGEND("notification approche date limite parties", title="Envoyez moi un courriel à l'approche de la date limite de mes parties")
    fieldset <= legend_notify_deadline
    input_notify_deadline = html.INPUT(type="checkbox", checked=bool(notify_deadline) if notify_deadline is not None else True, Class='btn-inside')
    fieldset <= input_notify_deadline
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_notify_adjudication = html.LEGEND("notification avancement parties", title="Envoyez moi un courriel sur chaque résolution de mes parties")
    fieldset <= legend_notify_adjudication
    input_notify_adjudication = html.INPUT(type="checkbox", checked=bool(notify_adjudication) if notify_adjudication is not None else True, Class='btn-inside')
    fieldset <= input_notify_adjudication
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_notify_message = html.LEGEND("notification messages et presses parties", title="Envoyez moi un courriel sur chaque message ou presse de mes parties")
    fieldset <= legend_notify_message
    input_notify_message = html.INPUT(type="checkbox", checked=bool(notify_message) if notify_message is not None else True, Class='btn-inside')
    fieldset <= input_notify_message
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_replace = html.LEGEND("notification remplacement", title="Prévenez moi par courriel en cas de remplacement nécessaire sur une partie")
    fieldset <= legend_replace
    input_notify_replace = html.INPUT(type="checkbox", checked=bool(notify_replace) if notify_replace is not None else False, Class='btn-inside')
    fieldset <= input_notify_replace
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_newsletter = html.LEGEND("abonnement newsletter", title="Envoyez moi la newsletter de l'association A.F.J.D.")
    fieldset <= legend_newsletter
    input_newsletter = html.INPUT(type="checkbox", checked=bool(newsletter) if newsletter is not None else True, Class='btn-inside')
    fieldset <= input_newsletter
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_family_name = html.LEGEND("nom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    fieldset <= legend_family_name
    input_family_name = html.INPUT(type="text", value=family_name if family_name is not None else False, Class='btn-inside')
    fieldset <= input_family_name
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_first_name = html.LEGEND("prénom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    fieldset <= legend_first_name
    input_first_name = html.INPUT(type="text", value=first_name if first_name is not None else False, Class='btn-inside')
    fieldset <= input_first_name
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_residence = html.LEGEND("résidence (public)", title="Mettez votre lieu de résidence")
    fieldset <= legend_residence
    input_residence = html.SELECT(type="select-one", value="", Class='btn-inside')

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if country_name == residence:
            option.selected = True
        input_residence <= option

    fieldset <= input_residence
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_nationality = html.LEGEND("nationalité (public)", title="Mettez votre nationalité")
    fieldset <= legend_nationality
    input_nationality = html.SELECT(type="select-one", value="", Class='btn-inside')

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if country_name == nationality:
            option.selected = True
        input_nationality <= option

    fieldset <= input_nationality
    form <= fieldset

    form <= html.BR()

    input_create_account = html.INPUT(type="submit", value="Créer le compte", Class='btn-inside')
    input_create_account.bind("click", create_account_callback)
    form <= input_create_account

    MY_SUB_PANEL <= form

    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= information_about_account2()
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= information_about_pseudo()
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= information_about_emails()


def edit_account():
    """ edit_account """

    # declare the values
    email_loaded = None
    email_status_loaded = None
    notify_deadline_loaded = None
    notify_adjudication_loaded = None
    notify_message_loaded = None
    notify_replace_loaded = None
    newsletter_loaded = None
    family_name_loaded = None
    first_name_loaded = None
    residence_loaded_code = None
    nationality_loaded_code = None

    def edit_account_reload():
        """ edit_account_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            nonlocal status
            nonlocal email_loaded
            nonlocal email_status_loaded
            nonlocal notify_deadline_loaded
            nonlocal notify_adjudication_loaded
            nonlocal notify_message_loaded
            nonlocal notify_replace_loaded
            nonlocal newsletter_loaded
            nonlocal family_name_loaded
            nonlocal first_name_loaded
            nonlocal residence_loaded_code
            nonlocal nationality_loaded_code
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au chargement des informations du compte : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au chargement des informations du compte : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            pseudo_loaded = req_result['pseudo']
            if pseudo_loaded != pseudo:
                alert("Etrange. Le pseudo est différent !")
                status = False
                return

            email_loaded = req_result['email']
            email_status_loaded = req_result['email_status']
            notify_deadline_loaded = req_result['notify_deadline']
            notify_adjudication_loaded = req_result['notify_adjudication']
            notify_message_loaded = req_result['notify_message']
            notify_replace_loaded = req_result['notify_replace']
            newsletter_loaded = req_result['newsletter']
            family_name_loaded = req_result['family_name']
            first_name_loaded = req_result['first_name']
            residence_loaded_code = req_result['residence']
            nationality_loaded_code = req_result['nationality']

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        # reading data about account : need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_account_callback(ev):  # pylint: disable=invalid-name
        """ change_account_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification des informations du compte : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification des informations du compte : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Votre compte a été changé : {messages}")

        ev.preventDefault()

        email = input_email.value
        if not email:
            alert("email manquant")
            MY_SUB_PANEL.clear()
            edit_account()
            return

        if email.find('@') == -1:
            alert("@ dans email manquant")
            MY_SUB_PANEL.clear()
            edit_account()
            return

        notify_deadline = int(input_notify_deadline.checked)
        notify_adjudication = int(input_notify_adjudication.checked)
        notify_message = int(input_notify_message.checked)
        notify_replace = int(input_notify_replace.checked)
        newsletter = int(input_newsletter.checked)
        family_name = input_family_name.value
        first_name = input_first_name.value
        residence_code = config.COUNTRY_CODE_TABLE[input_residence.value]
        nationality_code = config.COUNTRY_CODE_TABLE[input_nationality.value]

        json_dict = {
            'pseudo': pseudo,
            'email': email,
            'notify_deadline': notify_deadline,
            'notify_adjudication': notify_adjudication,
            'notify_message': notify_message,
            'notify_replace': notify_replace,
            'newsletter': newsletter,
            'family_name': family_name,
            'first_name': first_name,
            'residence': residence_code,
            'nationality': nationality_code,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        # updating data about account : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        edit_account()

    MY_SUB_PANEL <= html.H3("Edition du compte")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    status = edit_account_reload()
    if not status:
        return

    MY_SUB_PANEL <= information_about_private_data()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= information_about_account()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= information_about_input()
    MY_SUB_PANEL <= html.BR()

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_pseudo = html.LEGEND("pseudo", title="(pour rappel)")
    fieldset <= legend_pseudo
    input_pseudo = html.INPUT(type="text", readonly=True, value=pseudo, Class='btn-inside')
    fieldset <= input_pseudo
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_email = html.LEGEND("courriel (privé) - impérativement un courriel valide !", title="Le site vous notifiera de quelques très rares événements (sauf si vous demandez les notifications)")
    fieldset <= legend_email
    input_email = html.INPUT(type="email", value=email_loaded, size=MAX_LEN_EMAIL, Class='btn-inside')
    fieldset <= input_email
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_email_confirmed = html.LEGEND("courriel confirmé", title="(pour information)")
    fieldset <= legend_email_confirmed
    input_email_confirmed = html.INPUT(type="checkbox", disabled=True, checked=email_status_loaded == 1, Class='btn-inside')
    fieldset <= input_email_confirmed
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_email_error = html.LEGEND("courriel en erreur", title="(pour information)")
    fieldset <= legend_email_error
    input_email_error = html.INPUT(type="checkbox", disabled=True, checked=email_status_loaded == 2, Class='btn-inside')
    fieldset <= input_email_error
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_notify_deadline = html.LEGEND("notification approche date limite parties", title="Envoyez moi un courriel à l'approche de la dete limite de mes parties")
    fieldset <= legend_notify_deadline
    input_notify_deadline = html.INPUT(type="checkbox", checked=notify_deadline_loaded, Class='btn-inside')
    fieldset <= input_notify_deadline
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_notify_adjudication = html.LEGEND("notification avancement parties", title="Envoyez moi un courriel sur chaque résolution de mes parties")
    fieldset <= legend_notify_adjudication
    input_notify_adjudication = html.INPUT(type="checkbox", checked=notify_adjudication_loaded, Class='btn-inside')
    fieldset <= input_notify_adjudication
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_notify_message = html.LEGEND("notification messages et presses parties", title="Envoyez moi un courriel sur chaque message ou presse de mes parties")
    fieldset <= legend_notify_message
    input_notify_message = html.INPUT(type="checkbox", checked=notify_message_loaded, Class='btn-inside')
    fieldset <= input_notify_message
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_notify_replace = html.LEGEND("notification remplacement", title="Prévenez moi par courriel en cas de remplacement nécessaire sur une partie")
    fieldset <= legend_notify_replace
    input_notify_replace = html.INPUT(type="checkbox", checked=notify_replace_loaded, Class='btn-inside')
    fieldset <= input_notify_replace
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_newsletter = html.LEGEND("abonnement newsletter", title="Envoyez moi par courriel la newsletter de l'association A.F.J.D.")
    fieldset <= legend_newsletter
    input_newsletter = html.INPUT(type="checkbox", checked=newsletter_loaded, Class='btn-inside')
    fieldset <= input_newsletter
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_family_name = html.LEGEND("nom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    fieldset <= legend_family_name
    input_family_name = html.INPUT(type="text", value=family_name_loaded, Class='btn-inside')
    fieldset <= input_family_name
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_first_name = html.LEGEND("prénom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    fieldset <= legend_first_name
    input_first_name = html.INPUT(type="text", value=first_name_loaded, Class='btn-inside')
    fieldset <= input_first_name
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_residence = html.LEGEND("résidence (public)", title="Mettez votre lieu de résidence")
    fieldset <= legend_residence
    input_residence = html.SELECT(type="select-one", value="", Class='btn-inside')

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if config.COUNTRY_CODE_TABLE[country_name] == residence_loaded_code:
            option.selected = True
        input_residence <= option

    fieldset <= input_residence
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_nationality = html.LEGEND("nationalité (public)", title="Mettez votre nationalité")
    fieldset <= legend_nationality
    input_nationality = html.SELECT(type="select-one", value="", Class='btn-inside')

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if config.COUNTRY_CODE_TABLE[country_name] == nationality_loaded_code:
            option.selected = True
        input_nationality <= option

    fieldset <= input_nationality
    form <= fieldset

    form <= html.BR()

    input_change_account = html.INPUT(type="submit", value="Changer le compte", Class='btn-inside')
    input_change_account.bind("click", change_account_callback)
    form <= input_change_account

    MY_SUB_PANEL <= form


def validate_email():
    """ validate_email """

    def send_new_code_callback(ev):  # pylint: disable=invalid-name
        """ send_new_code_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la demande de renvoi de code de validation : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la demande de renvoi de code de validation : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Nouveau code de vérification de l'adresse couriel envoyé : {messages}")

        ev.preventDefault()

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/resend-code"

        # asking resend of verification code for account : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        validate_email()

    def validate_email_callback(ev):  # pylint: disable=invalid-name
        """ validate_email_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la validation de l'adresse mail : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la validation de l'adresse mail : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Félicitations, votre courriel a été validé : {messages}")

        ev.preventDefault()

        if not input_confirmation_code.value:
            alert("Code de confirmation mal saisi")
            MY_SUB_PANEL.clear()
            validate_email()
            return

        try:
            confirmation_code_int = int(input_confirmation_code.value)
        except:  # noqa: E722 pylint: disable=bare-except
            alert("Code de confirmation incorrect")
            MY_SUB_PANEL.clear()
            validate_email()
            return

        if not 1000 <= confirmation_code_int <= 9999:
            alert("Le code de confirmation doit utiliser 4 chiffres")
            MY_SUB_PANEL.clear()
            validate_email()
            return

        json_dict = {
            'pseudo': pseudo,
            'code': confirmation_code_int,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/check-email"

        # checking a code for email : no need for token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        validate_email()

    MY_SUB_PANEL <= html.H3("Validation du courriel")

    MY_SUB_PANEL <= information_about_confirm()
    MY_SUB_PANEL <= html.BR()

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_confirmation_code = html.LEGEND("code de confirmation", title="Le code reçu par courriel")
    fieldset <= legend_confirmation_code
    input_confirmation_code = html.INPUT(type="number", value="", required=True, Class='btn-inside')
    fieldset <= input_confirmation_code
    form <= fieldset

    form <= html.BR()

    input_validate_email = html.INPUT(type="submit", value="Valider le courriel", Class='btn-inside')
    input_validate_email.bind("click", validate_email_callback)
    form <= input_validate_email
    form <= html.BR()

    MY_SUB_PANEL <= form

    MY_SUB_PANEL <= html.BR()

    form2 = html.FORM()

    input_send_new_code = html.INPUT(type="submit", value="Me renvoyer un nouveau code", Class='btn-inside')
    input_send_new_code.bind("click", send_new_code_callback)
    form2 <= input_send_new_code
    form2 <= html.BR()

    MY_SUB_PANEL <= form2


def change_password():
    """ change_password """

    def change_password_callback(ev):  # pylint: disable=invalid-name
        """ change_password_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de mot de passe : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de mot de passe : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Votre mot de passe a été changé : {messages}")

        ev.preventDefault()

        new_password = input_new_password.value
        if not new_password:
            alert("Nouveau mot de passe manquant")
            MY_SUB_PANEL.clear()
            change_password()
            return

        new_password_again = input_new_password_again.value
        if new_password_again != new_password:
            alert("Les mots de passe ne correspondent pas")
            MY_SUB_PANEL.clear()
            change_password()
            return

        json_dict = {
            'pseudo': pseudo,
            'password': new_password,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        # changing password : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_password()

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    MY_SUB_PANEL <= html.H3("Changement de mot de passe")

    pseudo = storage['PSEUDO']

    form = html.FORM()

    form <= information_about_input()
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_new_password = html.LEGEND("nouveau mot de passe", title="Le nouveau mot de passe")
    fieldset <= legend_new_password
    input_new_password = html.INPUT(type="password", value="", Class='btn-inside')
    fieldset <= input_new_password
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_new_password_again = html.LEGEND("nouveau mot de passe encore", title="Le nouveau mot de passe")
    fieldset <= legend_new_password_again
    input_new_password_again = html.INPUT(type="password", value="", Class='btn-inside')
    fieldset <= input_new_password_again
    form <= fieldset

    form <= html.BR()

    input_change_password = html.INPUT(type="submit", value="Changer le mot de passe", Class='btn-inside')
    input_change_password.bind("click", change_password_callback)
    form <= input_change_password

    MY_SUB_PANEL <= form


def forum_code():
    """ forum_code """

    MY_SUB_PANEL <= html.H3("Code pour le forum")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    legende_code_forum = html.DIV(Class='note')
    legende_code_forum <= "Votre code à utiliser sur le forum est : "
    MY_SUB_PANEL <= legende_code_forum

    MY_SUB_PANEL <= html.BR()

    code_forum = html.DIV(Class='important')
    code_value = common.verification_code(pseudo)
    code_forum <= code_value
    MY_SUB_PANEL <= code_forum


def delete_account():
    """ delete_account """

    def cancel_delete_account_callback(_, dialog):
        """ cancel_delete_account_callback """
        dialog.close(None)

    def delete_account_callback(_, dialog):
        """ delete_account_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppression du compte : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppression du compte : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Votre compte a été supprimé : {messages}")

            # logout
            login.PANEL_MIDDLE = None
            login.logout()

        dialog.close(None)

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        # deleting account : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def delete_account_callback_confirm(ev):  # pylint: disable=invalid-name
        """ delete_account_callback_confirm """

        ev.preventDefault()

        dialog = mydialog.MyDialog(f"On supprime vraiment le compte {pseudo} ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog: delete_account_callback(e, d))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_delete_account_callback(e, d))

        # back to where we started
        MY_SUB_PANEL.clear()
        delete_account()

    MY_SUB_PANEL <= html.H3("Suppression du compte")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    form = html.FORM()

    MY_SUB_PANEL <= form

    input_delete_account = html.INPUT(type="submit", value="Supprimer le compte", Class='btn-inside')
    input_delete_account.bind("click", delete_account_callback_confirm)
    form <= input_delete_account
    form <= html.BR()


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION

ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

MY_SUB_PANEL = html.DIV(id="page")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Editer':
        edit_account()
    if item_name == 'Valider mon courriel':
        validate_email()
    if item_name == 'Mot de passe':
        change_password()
    if item_name == 'Mon code forum':
        forum_code()
    if item_name == 'Supprimer':
        delete_account()

    # special : not in menu
    if item_name == 'Créer un compte':
        create_account(None)

    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    MENU_LEFT.clear()

    # items in menu
    for possible_item_name, legend in OPTIONS.items():

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, title=legend, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        MENU_LEFT <= menu_item


PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    PANEL_MIDDLE = panel_middle

    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

    if 'PSEUDO' not in storage:
        ITEM_NAME_SELECTED = 'Créer un compte'
    else:
        if RESCUE:
            ITEM_NAME_SELECTED = 'Mot de passe'

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
