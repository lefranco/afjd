""" account """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog, Dialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import login

OPTIONS = ['créer', 'mot de passe', 'valider mon email', 'editer', 'supprimer']

MAX_LEN_PSEUDO = 20

DEFAULT_COUNTRY_CODE = "FRA"
DEFAULT_TIMEZONE_CODE = "UTC+01:00"


def information_about_account():
    """ information_about_account """

    information = html.DIV()
    information <= "La plupart des champs sont privés et ne seront pas montrés sur le site et/ou facultatifs"
    information <= html.BR()
    information <= "Survolez les titres pour plus de détails"
    return information


def information_about_emails():
    """ information_about_emails """

    information = html.DIV()
    information <= "Vous recevrez un email pour confimer votre adresse mail, ainsi qu'au démarrage et à l'arrêt de vos parties."
    information <= html.BR()
    information <= "Rien de plus !"
    return information


def create_account():
    """ create_account """

    def create_account_callback(_):
        """ create_account_callback """

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

        pseudo = input_pseudo.value

        if not pseudo:
            alert("Pseudo manquant")
            my_sub_panel.clear()
            create_account()
            return

        if len(pseudo) > MAX_LEN_PSEUDO:
            alert("Pseudo trop long")
            my_sub_panel.clear()
            create_account()
            return

        password = input_password.value
        if not password:
            alert("Mot de passe manquant")
            return

        password_again = input_password_again.value
        if password_again != password:
            alert("Les mots de passe ne correspondent pas")
            my_sub_panel.clear()
            create_account()
            return

        email = input_email.value
        if not email:
            alert("email manquant")
            my_sub_panel.clear()
            create_account()
            return

        if email.find('@') == -1:
            alert("@ dans email manquant")
            my_sub_panel.clear()
            create_account()
            return

        telephone = input_telephone.value
        replace = input_replace.value
        family_name = input_family_name.value
        first_name = input_first_name.value

        residence_code = config.COUNTRY_CODE_TABLE[input_residence.value]
        nationality_code = config.COUNTRY_CODE_TABLE[input_nationality.value]
        timezone_code = config.TIMEZONE_CODE_TABLE[input_timezone.value]

        json_dict = {
            'pseudo': pseudo,
            'password': password,
            'email': email,
            'telephone': telephone,
            'replace': replace,
            'family_name': family_name,
            'first_name': first_name,
            'residence': residence_code,
            'nationality': nationality_code,
            'time_zone': timezone_code,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players"

        # adding a player : no need for token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        my_sub_panel.clear()
        create_account()

    form = html.FORM()

    form <= information_about_account()
    form <= html.BR()

    legend_pseudo = html.LEGEND("pseudo", title="Votre identifiant sur le site")
    form <= legend_pseudo
    input_pseudo = html.INPUT(type="text", value="")
    form <= input_pseudo
    form <= html.BR()

    legend_password = html.LEGEND("mot de passe", title="Pour empêcher les autres de jouer à votre place;-)")
    form <= legend_password
    input_password = html.INPUT(type="password", value="")
    form <= input_password
    form <= html.BR()

    legend_password_again = html.LEGEND("confirmation mot de passe", title="Pour éviter une faute de frappe sur le mot de passe")
    form <= legend_password_again
    input_password_again = html.INPUT(type="password", value="")
    form <= input_password_again
    form <= html.BR()

    legend_email = html.LEGEND("email (privé)", title="Le site vous notifiera des événements")
    form <= legend_email
    input_email = html.INPUT(type="email", value="", size="80")
    form <= input_email
    form <= html.BR()

    legend_telephone = html.LEGEND("téléphone (privé et facultatif)", title="En cas d'urgence")
    form <= legend_telephone
    input_telephone = html.INPUT(type="tel", value="")
    form <= input_telephone
    form <= html.BR()

    legend_replace = html.LEGEND("D'accord pour remplacer - à effacer après usage !", title="Pouvons-nous vous mettre dans une partie pour remplacer un joueur qui a abandonné ?")
    form <= legend_replace
    input_replace = html.INPUT(type="checkbox", checked=False)
    form <= input_replace
    form <= html.BR()

    legend_family_name = html.LEGEND("nom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    form <= legend_family_name
    input_family_name = html.INPUT(type="text", value="")
    form <= input_family_name
    form <= html.BR()

    legend_first_name = html.LEGEND("prénom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    form <= legend_first_name
    input_first_name = html.INPUT(type="text", value="")
    form <= input_first_name
    form <= html.BR()

    legend_residence = html.LEGEND("résidence", title="Mettez votre lieu de résidence")
    form <= legend_residence
    input_residence = html.SELECT(type="select-one", value="")

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if config.COUNTRY_CODE_TABLE[country_name] == DEFAULT_COUNTRY_CODE:
            option.selected = True
        input_residence <= option

    form <= input_residence
    form <= html.BR()

    legend_nationality = html.LEGEND("nationalité", title="Mettez votre nationalité")
    form <= legend_nationality
    input_nationality = html.SELECT(type="select-one", value="")

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if config.COUNTRY_CODE_TABLE[country_name] == DEFAULT_COUNTRY_CODE:
            option.selected = True
        input_nationality <= option

    form <= input_nationality
    form <= html.BR()

    legend_timezone = html.LEGEND("fuseau horaire", title="Pour mieux comprendre vos heures d'éveil")
    form <= legend_timezone
    input_timezone = html.SELECT(type="select-one", value="")

    for timezone_cities in config.TIMEZONE_CODE_TABLE:
        option = html.OPTION(timezone_cities)
        if config.TIMEZONE_CODE_TABLE[timezone_cities] == DEFAULT_TIMEZONE_CODE:
            option.selected = True
        input_timezone <= option

    form <= input_timezone
    form <= html.BR()

    form <= html.BR()

    input_create_account = html.INPUT(type="submit", value="créer le compte")
    input_create_account.bind("click", create_account_callback)
    form <= input_create_account

    form <= html.BR()
    form <= html.BR()
    form <= information_about_emails()

    my_sub_panel <= form


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
            my_sub_panel.clear()
            change_password()
            return

        new_password_again = input_new_password_again.value
        if new_password_again != new_password:
            alert("Les mots de passe ne correspondent pas")
            my_sub_panel.clear()
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
        my_sub_panel.clear()
        change_password()

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    form = html.FORM()

    legend_new_password = html.LEGEND("nouveau mot de passe")
    form <= legend_new_password
    input_new_password = html.INPUT(type="password", value="")
    form <= input_new_password
    form <= html.BR()

    legend_new_password_again = html.LEGEND("nouveau mot de passe encore")
    form <= legend_new_password_again
    input_new_password_again = html.INPUT(type="password", value="")
    form <= input_new_password_again
    form <= html.BR()

    form <= html.BR()

    input_change_password = html.INPUT(type="submit", value="changer le mot de passe")
    input_change_password.bind("click", change_password_callback)
    form <= input_change_password
    form <= html.BR()

    my_sub_panel <= form


def validate_email():
    """ validate_email """

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
            InfoDialog("OK", f"Félicitations, votre email a été validé : {messages}", remove_after=config.REMOVE_AFTER)

        if not input_confirmation_code.value:
            alert("Code de confirmation mal saisi")
            my_sub_panel.clear()
            validate_email()
            return

        try:
            confirmation_code_int = int(input_confirmation_code.value)
        except:  # noqa: E722 pylint: disable=bare-except
            alert("Code de confirmation incorrect")
            my_sub_panel.clear()
            validate_email()
            return

        if not 1000 <= confirmation_code_int <= 9999:
            alert("Le code de confirmation doit utiliser 4 chiffres")
            my_sub_panel.clear()
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
        my_sub_panel.clear()
        validate_email()

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    form = html.FORM()

    legend_confirmation_code = html.LEGEND("code de confirmation")
    form <= legend_confirmation_code
    input_confirmation_code = html.INPUT(type="number", value="", required=True)
    form <= input_confirmation_code
    form <= html.BR()

    form <= html.BR()

    input_validate_email = html.INPUT(type="submit", value="valider l'email")
    input_validate_email.bind("click", validate_email_callback)
    form <= input_validate_email
    form <= html.BR()

    my_sub_panel <= form


def edit_account():
    """ edit_account """

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    # declare the values
    email_loaded = None
    email_confirmed_loaded = None
    telephone_loaded = None
    replace_loaded = None
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
            nonlocal replace_loaded
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
            replace_loaded = req_result['replace']
            family_name_loaded = req_result['family_name']
            first_name_loaded = req_result['first_name']
            residence_loaded_code = req_result['residence']
            nationality_loaded_code = req_result['nationality']
            timezone_loaded_code = req_result['time_zone']

        json_dict = dict()

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
            my_sub_panel.clear()
            edit_account()
            return

        if email.find('@') == -1:
            alert("@ dans email manquant")
            my_sub_panel.clear()
            edit_account()
            return

        telephone = input_telephone.value
        replace = int(input_replace.checked)
        family_name = input_family_name.value
        first_name = input_first_name.value
        residence_code = config.COUNTRY_CODE_TABLE[input_residence.value]
        nationality_code = config.COUNTRY_CODE_TABLE[input_nationality.value]
        timezone_code = config.TIMEZONE_CODE_TABLE[input_timezone.value]

        json_dict = {
            'pseudo': pseudo,
            'email': email,
            'telephone': telephone,
            'replace': replace,
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
        my_sub_panel.clear()
        edit_account()

    status = edit_account_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_account()
    form <= html.BR()

    legend_pseudo = html.LEGEND("pseudo", title="(pour rappel)")
    form <= legend_pseudo
    input_pseudo = html.INPUT(type="text", readonly=True, value=pseudo)
    form <= input_pseudo
    form <= html.BR()

    legend_email = html.LEGEND("email", title="Le site vous notifiera des événements")
    form <= legend_email
    input_email = html.INPUT(type="email", value=email_loaded, size="40")
    form <= input_email
    form <= html.BR()

    legend_email_confirmed = html.LEGEND("email confirmé", title="(pour information)")
    form <= legend_email_confirmed
    input_email_confirmed = html.INPUT(type="checkbox", readonly=True, checked=email_confirmed_loaded)
    form <= input_email_confirmed
    form <= html.BR()

    legend_telephone = html.LEGEND("téléphone (privé et facultatif)", title="En cas d'urgence")
    form <= legend_telephone
    input_telephone = html.INPUT(type="tel", value=telephone_loaded)
    form <= input_telephone
    form <= html.BR()

    legend_replace = html.LEGEND("D'accord pour remplacer - à effacer après usage !", title="Pouvons-nous vous mettre dans une partie pour remplacer un joueur qui a abandoné ?")
    form <= legend_replace
    input_replace = html.INPUT(type="checkbox", checked=replace_loaded)
    form <= input_replace
    form <= html.BR()

    legend_family_name = html.LEGEND("nom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    form <= legend_family_name
    input_family_name = html.INPUT(type="text", value=family_name_loaded)
    form <= input_family_name
    form <= html.BR()

    legend_first_name = html.LEGEND("prénom (facultatif et public)", title="Pour vous connaître dans la vraie vie - attention les accents seront supprimés")
    form <= legend_first_name
    input_first_name = html.INPUT(type="text", value=first_name_loaded)
    form <= input_first_name
    form <= html.BR()

    legend_residence = html.LEGEND("résidence", title="Mettez votre lieu de résidence")
    form <= legend_residence
    input_residence = html.SELECT(type="select-one", value="")

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if config.COUNTRY_CODE_TABLE[country_name] == residence_loaded_code:
            option.selected = True
        input_residence <= option

    form <= input_residence
    form <= html.BR()

    legend_nationality = html.LEGEND("nationalité", title="Mettez votre nationalité")
    form <= legend_nationality
    input_nationality = html.SELECT(type="select-one", value="")

    for country_name in config.COUNTRY_CODE_TABLE:
        option = html.OPTION(country_name)
        if config.COUNTRY_CODE_TABLE[country_name] == nationality_loaded_code:
            option.selected = True
        input_nationality <= option

    form <= input_nationality
    form <= html.BR()
    legend_timezone = html.LEGEND("fuseau horaire", title="Pour mieux comprendre vos heures d'éveil")
    form <= legend_timezone
    input_timezone = html.SELECT(type="select-one", value="")

    for timezone_cities in config.TIMEZONE_CODE_TABLE:
        option = html.OPTION(timezone_cities)
        if config.TIMEZONE_CODE_TABLE[timezone_cities] == timezone_loaded_code:
            option.selected = True
        input_timezone <= option

    form <= input_timezone
    form <= html.BR()

    form <= html.BR()

    input_change_account = html.INPUT(type="submit", value="changer le compte")
    input_change_account.bind("click", change_account_callback)
    form <= input_change_account

    my_sub_panel <= form


def delete_account():
    """ delete_account """

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']


    def cancel_delete_account_callback(_, dialog):

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
            login.logout()

            # back to the top
            my_sub_panel.clear()
            create_account()

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

        dialog = Dialog(f"On supprime vraiment le compte {pseudo} ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog: delete_account_callback(e, d))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_delete_account_callback(e, d))

        # back to where we started
        my_sub_panel.clear()
        delete_account()

    form = html.FORM()
    my_sub_panel <= form

    input_delete_account = html.INPUT(type="submit", value="supprimer le compte")
    input_delete_account.bind("click", delete_account_callback_confirm)
    form <= input_delete_account
    form <= html.BR()


my_panel = html.DIV()
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="account")
my_panel <= my_sub_panel


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'créer':
        create_account()
    if item_name == 'mot de passe':
        change_password()
    if item_name == 'valider mon email':
        validate_email()
    if item_name == 'editer':
        edit_account()
    if item_name == 'supprimer':
        delete_account()

    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == item_name_selected:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_left <= menu_item


def render(panel_middle):
    """ render """

    # always back to top
    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

    load_option(None, item_name_selected)
    panel_middle <= my_panel
