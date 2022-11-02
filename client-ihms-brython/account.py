""" account """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog, Dialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import login

OPTIONS = ['Créer un compte', 'Mot de passe', 'Valider mon courriel', 'Mon code forum', 'Editer', 'Supprimer']


MIN_LEN_PSEUDO = 3
MAX_LEN_PSEUDO = 20
MAX_LEN_EMAIL = 100

DEFAULT_COUNTRY_CODE = "FRA"
DEFAULT_TIMEZONE_CODE = "UTC+01:00"


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
    return information


def information_about_emails():
    """ information_about_emails """

    information = html.DIV(Class='important')
    information <= "Vous recevrez un courriel pour confimer votre adresse de courriel, ainsi qu'au démarrage et à l'arrêt de vos parties. Parfois un courriel de rappel de l'arbitre si vous êtes en retard sur les ordres. Un courriel de notification de résolution mais dans ce dernier cas seulement si vous l'avez demandé. A noter : il vous est déconseillé d'utiliser une adresse courriel professionelle."
    information <= html.BR()
    information <= "Rien de plus !"
    return information


def information_about_pseudo():
    """ information_about_emails """

    information = html.DIV(Class='important')
    information <= "Un pseudo inapproprié pourra être refusé sur le site (et le compte supprimé)"
    return information


def create_account(json_dict):
    """ create_account """

    # load previous values if applicable
    pseudo = json_dict['pseudo'] if json_dict and 'pseudo' in json_dict else None
    password = json_dict['password'] if json_dict and 'password' in json_dict else None
    password_again = json_dict['password_again'] if json_dict and 'password_again' in json_dict else None
    email = json_dict['email'] if json_dict and 'email' in json_dict else None
    telephone = json_dict['telephone'] if json_dict and 'telephone' in json_dict else None
    notify = json_dict['notify'] if json_dict and 'notify' in json_dict else None
    replace = json_dict['replace'] if json_dict and 'replace' in json_dict else None
    newsletter = json_dict['newsletter'] if json_dict and 'newsletter' in json_dict else None
    family_name = json_dict['family_name'] if json_dict and 'pseudo' in json_dict else None
    first_name = json_dict['first_name'] if json_dict and 'family_name' in json_dict else None
    residence_code = json_dict['residence_code'] if json_dict and 'residence_code' in json_dict else None
    nationality_code = json_dict['nationality_code'] if json_dict and 'nationality_code' in json_dict else None
    timezone_code = json_dict['timezone_code'] if json_dict and 'timezone_code' in json_dict else None

    def create_account_callback(_):
        """ create_account_callback """

        nonlocal pseudo
        nonlocal password
        nonlocal password_again
        nonlocal email
        nonlocal telephone
        nonlocal notify
        nonlocal replace
        nonlocal newsletter
        nonlocal family_name
        nonlocal first_name
        nonlocal residence_code
        nonlocal nationality_code
        nonlocal timezone_code

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la création du compte : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la création du compte  : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Votre compte a été créé : {messages}", remove_after=config.REMOVE_AFTER)
            alert("Maintenant vous devez vous identifier par le menu 'Connexion'")

        # get values from user input

        pseudo = input_pseudo.value
        password = input_password.value
        password_again = input_password_again.value
        email = input_email.value
        telephone = input_telephone.value
        notify = int(input_notify.checked)
        replace = int(input_replace.checked)
        newsletter = int(input_newsletter.checked)
        family_name = input_family_name.value
        first_name = input_first_name.value
        residence_code = config.COUNTRY_CODE_TABLE[input_residence.value]
        nationality_code = config.COUNTRY_CODE_TABLE[input_nationality.value]
        timezone_code = config.TIMEZONE_CODE_TABLE[input_timezone.value]

        # make data structure
        json_dict = {
            'pseudo': pseudo,
            'password': password,
            'password_again': password_again,
            'email': email,
            'telephone': telephone,
            'notify': notify,
            'replace': replace,
            'newsletter': newsletter,
            'family_name': family_name,
            'first_name': first_name,
            'residence': residence_code,
            'nationality': nationality_code,
            'time_zone': timezone_code,
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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # restore password again in case of failure
        json_dict['password_again'] = password_again

        # back to where we started
        MY_SUB_PANEL.clear()
        create_account(json_dict)

    MY_SUB_PANEL <= html.H3("Création du compte")

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
    input_pseudo = html.INPUT(type="text", value=pseudo if pseudo is not None else "")
    fieldset <= input_pseudo
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_password = html.LEGEND("mot de passe", title="Pour empêcher les autres de jouer à votre place;-)")
    fieldset <= legend_password
    input_password = html.INPUT(type="password", value=password if password is not None else "")
    fieldset <= input_password
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_password_again = html.LEGEND("confirmation mot de passe", title="Pour éviter une faute de frappe sur le mot de passe")
    fieldset <= legend_password_again
    input_password_again = html.INPUT(type="password", value=password_again if password_again is not None else "")
    fieldset <= input_password_again
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_email = html.LEGEND("courriel (privé)", title="Le site vous notifiera de quelques très rares événements (sauf si vous demandez les notifications)")
    fieldset <= legend_email
    input_email = html.INPUT(type="email", value=email if email is not None else "", size=MAX_LEN_EMAIL)
    fieldset <= input_email
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_telephone = html.LEGEND("téléphone (privé et facultatif)", title="En cas d'urgence")
    fieldset <= legend_telephone
    input_telephone = html.INPUT(type="tel", value=telephone if telephone is not None else "")
    fieldset <= input_telephone
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_notify = html.LEGEND("Notifiez-moi sur les partie !", title="Devons nous vous envoyer un courriel sur chaque résolution de vos parties ?")
    fieldset <= legend_notify
    input_notify = html.INPUT(type="checkbox", checked=bool(notify) if notify is not None else True)
    fieldset <= input_notify
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_replace = html.LEGEND("Je veux remplacer !", title="Prévenez moi par courriel en cas de remplacement nécessaire sur une partie")
    fieldset <= legend_replace
    input_replace = html.INPUT(type="checkbox", checked=bool(replace) if replace is not None else False)
    fieldset <= input_replace
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_newsletter = html.LEGEND("Je veux recevoir la newsletter !", title="Envoyez moi la newsletter de l'association A.F.J.D.")
    fieldset <= legend_newsletter
    input_newsletter = html.INPUT(type="checkbox", checked=bool(newsletter) if newsletter is not None else True)
    fieldset <= input_newsletter
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_family_name = html.LEGEND("nom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    fieldset <= legend_family_name
    input_family_name = html.INPUT(type="text", value=family_name if family_name is not None else False)
    fieldset <= input_family_name
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_first_name = html.LEGEND("prénom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    fieldset <= legend_first_name
    input_first_name = html.INPUT(type="text", value=first_name if first_name is not None else False)
    fieldset <= input_first_name
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_residence = html.LEGEND("résidence", title="Mettez votre lieu de résidence")
    fieldset <= legend_residence
    input_residence = html.SELECT(type="select-one", value="")

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if config.COUNTRY_CODE_TABLE[country_name] == (residence_code if residence_code is not None else DEFAULT_COUNTRY_CODE):
            option.selected = True
        input_residence <= option

    fieldset <= input_residence
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_nationality = html.LEGEND("nationalité", title="Mettez votre nationalité")
    fieldset <= legend_nationality
    input_nationality = html.SELECT(type="select-one", value="")

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if config.COUNTRY_CODE_TABLE[country_name] == (nationality_code if nationality_code is not None else DEFAULT_COUNTRY_CODE):
            option.selected = True
        input_nationality <= option

    fieldset <= input_nationality
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_timezone = html.LEGEND("fuseau horaire", title="Pour mieux comprendre vos heures d'éveil")
    fieldset <= legend_timezone
    input_timezone = html.SELECT(type="select-one", value="")

    for timezone_cities in config.TIMEZONE_CODE_TABLE:
        option = html.OPTION(timezone_cities)
        if config.TIMEZONE_CODE_TABLE[timezone_cities] == (timezone_code if timezone_code is not None else DEFAULT_TIMEZONE_CODE):
            option.selected = True
        input_timezone <= option

    fieldset <= input_timezone
    form <= fieldset

    form <= html.BR()

    input_create_account = html.INPUT(type="submit", value="créer le compte")
    input_create_account.bind("click", create_account_callback)
    form <= input_create_account

    MY_SUB_PANEL <= form

    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= information_about_pseudo()
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= information_about_emails()


def change_password():
    """ change_password """

    def change_password_callback(_):
        """ change_password_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de mot de passe : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de mot de passe : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Votre mot de passe a été changé : {messages}", remove_after=config.REMOVE_AFTER)

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
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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
    input_new_password = html.INPUT(type="password", value="")
    fieldset <= input_new_password
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_new_password_again = html.LEGEND("nouveau mot de passe encore", title="Le nouveau mot de passe")
    fieldset <= legend_new_password_again
    input_new_password_again = html.INPUT(type="password", value="")
    fieldset <= input_new_password_again
    form <= fieldset

    form <= html.BR()

    input_change_password = html.INPUT(type="submit", value="changer le mot de passe")
    input_change_password.bind("click", change_password_callback)
    form <= input_change_password

    MY_SUB_PANEL <= form


def validate_email():
    """ validate_email """

    def send_new_code_callback(_):
        """ send_new_code_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la demande de renvoi de code de validation : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la demande de renvoi de code de validation : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Nouveau code de vérification de l'adresse couriel envoyé : {messages}", remove_after=config.REMOVE_AFTER)

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/resend-code/{pseudo}"

        # asking resend of verification code for account : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        validate_email()

    def validate_email_callback(_):
        """ validate_email_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la validation de l'adresse mail : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la validation de l'adresse mail : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Félicitations, votre courriel a été validé : {messages}", remove_after=config.REMOVE_AFTER)

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
        url = f"{host}:{port}/emails"

        # adding an email : no need for token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        validate_email()

    MY_SUB_PANEL <= html.H3("Validation du courriel")

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
    input_confirmation_code = html.INPUT(type="number", value="", required=True)
    fieldset <= input_confirmation_code
    form <= fieldset

    form <= html.BR()

    input_validate_email = html.INPUT(type="submit", value="valider le courriel")
    input_validate_email.bind("click", validate_email_callback)
    form <= input_validate_email
    form <= html.BR()

    MY_SUB_PANEL <= form

    MY_SUB_PANEL <= html.BR()

    form2 = html.FORM()

    input_send_new_code = html.INPUT(type="submit", value="me renvoyer un nouveau code")
    input_send_new_code.bind("click", send_new_code_callback)
    form2 <= input_send_new_code
    form2 <= html.BR()

    MY_SUB_PANEL <= form2


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


def edit_account():
    """ edit_account """

    # declare the values
    email_loaded = None
    email_confirmed_loaded = None
    telephone_loaded = None
    notify_loaded = None
    replace_loaded = None
    newsletter_loaded = None
    family_name_loaded = None
    first_name_loaded = None
    residence_loaded_code = None
    nationality_loaded_code = None
    timezone_loaded_code = None

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
            nonlocal email_confirmed_loaded
            nonlocal telephone_loaded
            nonlocal notify_loaded
            nonlocal replace_loaded
            nonlocal newsletter_loaded
            nonlocal family_name_loaded
            nonlocal first_name_loaded
            nonlocal residence_loaded_code
            nonlocal nationality_loaded_code
            nonlocal timezone_loaded_code
            req_result = json.loads(req.text)
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
            email_confirmed_loaded = req_result['email_confirmed']
            telephone_loaded = req_result['telephone']
            notify_loaded = req_result['notify']
            replace_loaded = req_result['replace']
            newsletter_loaded = req_result['newsletter']
            family_name_loaded = req_result['family_name']
            first_name_loaded = req_result['first_name']
            residence_loaded_code = req_result['residence']
            nationality_loaded_code = req_result['nationality']
            timezone_loaded_code = req_result['time_zone']

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        # reading data about account : need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_account_callback(_):
        """ change_account_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification des informations du compte : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification des informations du compte : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Votre compte a été changé : {messages}", remove_after=config.REMOVE_AFTER)

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

        telephone = input_telephone.value
        notify = int(input_notify.checked)
        replace = int(input_replace.checked)
        newsletter = int(input_newsletter.checked)
        family_name = input_family_name.value
        first_name = input_first_name.value
        residence_code = config.COUNTRY_CODE_TABLE[input_residence.value]
        nationality_code = config.COUNTRY_CODE_TABLE[input_nationality.value]
        timezone_code = config.TIMEZONE_CODE_TABLE[input_timezone.value]

        json_dict = {
            'pseudo': pseudo,
            'email': email,
            'telephone': telephone,
            'notify': notify,
            'replace': replace,
            'newsletter': newsletter,
            'family_name': family_name,
            'first_name': first_name,
            'residence': residence_code,
            'nationality': nationality_code,
            'time_zone': timezone_code,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        # updating data about account : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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

    MY_SUB_PANEL <= information_about_account()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= information_about_input()
    MY_SUB_PANEL <= html.BR()

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_pseudo = html.LEGEND("pseudo", title="(pour rappel)")
    fieldset <= legend_pseudo
    input_pseudo = html.INPUT(type="text", readonly=True, value=pseudo)
    fieldset <= input_pseudo
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_email = html.LEGEND("courriel (privé)", title="Le site vous notifiera de quelques très rares événements (sauf si vous demandez les notifications)")
    fieldset <= legend_email
    input_email = html.INPUT(type="email", value=email_loaded, size=MAX_LEN_EMAIL)
    fieldset <= input_email
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_email_confirmed = html.LEGEND("courriel confirmé", title="(pour information)")
    fieldset <= legend_email_confirmed
    input_email_confirmed = html.INPUT(type="checkbox", disabled=True, checked=email_confirmed_loaded)
    fieldset <= input_email_confirmed
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_telephone = html.LEGEND("téléphone (privé et facultatif)", title="En cas d'urgence")
    fieldset <= legend_telephone
    input_telephone = html.INPUT(type="tel", value=telephone_loaded)
    fieldset <= input_telephone
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_notify = html.LEGEND("Notifiez-moi sur les parties !", title="Devons nous vous envoyer un courriel sur chaque résolution de vos parties ?")
    fieldset <= legend_notify
    input_notify = html.INPUT(type="checkbox", checked=notify_loaded)
    fieldset <= input_notify
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_replace = html.LEGEND("Je veux remplacer !", title="Prévenez moi par courriel en cas de remplacement nécessaire sur une partie")
    fieldset <= legend_replace
    input_replace = html.INPUT(type="checkbox", checked=replace_loaded)
    fieldset <= input_replace
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_newsletter = html.LEGEND("Je veux recevoir la newsletter !", title="Envoyez moi par courriel la newsletter de l'A.F.J.D.")
    fieldset <= legend_newsletter
    input_newsletter = html.INPUT(type="checkbox", checked=newsletter_loaded)
    fieldset <= input_newsletter
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_family_name = html.LEGEND("nom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    fieldset <= legend_family_name
    input_family_name = html.INPUT(type="text", value=family_name_loaded)
    fieldset <= input_family_name
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_first_name = html.LEGEND("prénom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    fieldset <= legend_first_name
    input_first_name = html.INPUT(type="text", value=first_name_loaded)
    fieldset <= input_first_name
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_residence = html.LEGEND("résidence", title="Mettez votre lieu de résidence")
    fieldset <= legend_residence
    input_residence = html.SELECT(type="select-one", value="")

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if config.COUNTRY_CODE_TABLE[country_name] == residence_loaded_code:
            option.selected = True
        input_residence <= option

    fieldset <= input_residence
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_nationality = html.LEGEND("nationalité", title="Mettez votre nationalité")
    fieldset <= legend_nationality
    input_nationality = html.SELECT(type="select-one", value="")

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if config.COUNTRY_CODE_TABLE[country_name] == nationality_loaded_code:
            option.selected = True
        input_nationality <= option

    fieldset <= input_nationality
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_timezone = html.LEGEND("fuseau horaire", title="Pour mieux comprendre vos heures d'éveil")
    fieldset <= legend_timezone
    input_timezone = html.SELECT(type="select-one", value="")

    for timezone_cities in config.TIMEZONE_CODE_TABLE:
        option = html.OPTION(timezone_cities)
        if config.TIMEZONE_CODE_TABLE[timezone_cities] == timezone_loaded_code:
            option.selected = True
        input_timezone <= option

    fieldset <= input_timezone
    form <= fieldset

    form <= html.BR()

    input_change_account = html.INPUT(type="submit", value="changer le compte")
    input_change_account.bind("click", change_account_callback)
    form <= input_change_account

    MY_SUB_PANEL <= form


def delete_account():
    """ delete_account """

    def cancel_delete_account_callback(_, dialog):
        """ cancel_delete_account_callback """
        dialog.close()

    def delete_account_callback(_, dialog):
        """ delete_account_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppression du compte : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppression du compte : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Votre compte a été supprimé : {messages}", remove_after=config.REMOVE_AFTER)

            # logout
            login.PANEL_MIDDLE = None
            login.logout()

        dialog.close()

        json_dict = {
            'pseudo': pseudo,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        # deleting account : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def delete_account_callback_confirm(_):
        """ delete_account_callback_confirm """

        dialog = Dialog(f"On supprime vraiment le compte {pseudo} ?", ok_cancel=True)
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

    input_delete_account = html.INPUT(type="submit", value="supprimer le compte")
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

ITEM_NAME_SELECTED = OPTIONS[0]

MY_SUB_PANEL = html.DIV(id="account")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Créer un compte':
        create_account(None)
    if item_name == 'Mot de passe':
        change_password()
    if item_name == 'Valider mon courriel':
        validate_email()
    if item_name == 'Mon code forum':
        forum_code()
    if item_name == 'Editer':
        edit_account()
    if item_name == 'Supprimer':
        delete_account()

    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    MENU_LEFT.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        MENU_LEFT <= menu_item


def render(panel_middle):
    """ render """

    global ITEM_NAME_SELECTED

    if 'PSEUDO' in storage:
        ITEM_NAME_SELECTED = 'Editer'
    else:
        ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
