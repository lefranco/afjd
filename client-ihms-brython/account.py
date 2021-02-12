""" account """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import re

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config

OPTIONS = ['create', 'change password', 'validate', 'edit', 'delete']

EMAIL_PATTERN = r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$'
MAX_LEN_PSEUDO = 12


def noreply_callback(_):
    """ noreply_callback """
    alert("Problem (no answer from server)")


def create_account():
    """ create_account """

    def create_account_callback(_) -> None:
        """ create_account_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                alert(f"Problem : {req_result['msg']}")
                return
            InfoDialog("OK", f"Account created : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        pseudo = input_pseudo.value

        if not pseudo:
            alert("Pseudo is missing")
            return
        if len(pseudo) > MAX_LEN_PSEUDO:
            alert("Pseudo is too long")
            return

        password = input_password.value
        if not password:
            alert("Password is missing")
            return

        password_again = input_password_again.value
        if password_again != password:
            alert("Passwords do not match")
            return

        email = input_email.value
        if not re.match(EMAIL_PATTERN, email):
            alert("email is incorrect")
            return

        telephone = input_telephone.value
        replace = input_replace.value
        family_name = input_family_name.value
        first_name = input_first_name.value

        # TODO : implement
        country = "FRA"
        time_zone = "UTC + 1"

        json_dict = {
            'pseudo': pseudo,
            'password': password,
            'email': email,
            'telephone': telephone,
            'replace': replace,
            'family_name': family_name,
            'first_name': first_name,
            'country': country,
            'time_zone': time_zone,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players"

        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    form = html.FORM()
    my_sub_panel <= form

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

    legend_password_again = html.LEGEND("password again")
    form <= legend_password_again
    input_password_again = html.INPUT(type="password", value="")
    form <= input_password_again
    form <= html.BR()

    legend_email = html.LEGEND("email")
    form <= legend_email
    input_email = html.INPUT(type="email", value="")
    form <= input_email
    form <= html.BR()

    legend_telephone = html.LEGEND("telephone")
    form <= legend_telephone
    input_telephone = html.INPUT(type="tel", value="")
    form <= input_telephone
    form <= html.BR()

    legend_replace = html.LEGEND("ok to replace")
    form <= legend_replace
    input_replace = html.INPUT(type="checkbox", value="")
    form <= input_replace
    form <= html.BR()

    legend_family_name = html.LEGEND("family name")
    form <= legend_family_name
    input_family_name = html.INPUT(type="text", value="")
    form <= input_family_name
    form <= html.BR()

    legend_first_name = html.LEGEND("first name")
    form <= legend_first_name
    input_first_name = html.INPUT(type="text", value="")
    form <= input_first_name
    form <= html.BR()

    legend_country = html.LEGEND("country (not implemented)")
    form <= legend_country
    input_country = html.SELECT(type="select-one", value="")
    #  TODO : propose list of countries
    form <= input_country
    form <= html.BR()

    legend_time_zone = html.LEGEND("time zone (not implemented)")
    form <= legend_time_zone
    input_time_zone = html.SELECT(type="select-one", value="")
    #  TODO : propose list of timezones
    form <= input_time_zone
    form <= html.BR()

    input_create_account = html.INPUT(type="submit", value="create account")
    input_create_account.bind("click", create_account_callback)
    form <= input_create_account
    form <= html.BR()


def change_password():
    """ change_password """

    def change_password_callback(_) -> None:
        """ change_password_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                alert(f"Problem : {req_result['msg']}")
                return
            InfoDialog("OK", f"Password changed : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        new_password = input_new_password.value
        if not new_password:
            alert("New password is missing")
            return

        new_password_again = input_new_password_again.value
        if new_password_again != new_password:
            alert("Passwords do not match")
            return

        json_dict = {
            'pseudo': pseudo,
            'password': new_password,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    form = html.FORM()
    my_sub_panel <= form

    legend_new_password = html.LEGEND("new password")
    form <= legend_new_password
    input_new_password = html.INPUT(type="password", value="")
    form <= input_new_password
    form <= html.BR()

    legend_new_password_again = html.LEGEND("new_password again")
    form <= legend_new_password_again
    input_new_password_again = html.INPUT(type="password", value="")
    form <= input_new_password_again
    form <= html.BR()

    input_change_password = html.INPUT(type="submit", value="change password")
    input_change_password.bind("click", change_password_callback)
    form <= input_change_password
    form <= html.BR()


def validate_account():
    """ validate_account """

    def validate_account_callback(_) -> None:
        """ validate_account_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                alert(f"Problem : {req_result['msg']}")
                return
            InfoDialog("OK", f"Congratulations, your account was validated : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        confirmation_code = int(input_confirmation_code.value)

        if not confirmation_code:
            alert("Confirmation code is missing")
            return

        try:
            confirmation_code_int = int(confirmation_code)
        except:  # noqa: E722 pylint: disable=bare-except
            alert("Confirmation code is incorrect")
            return

        if not 1000 <= confirmation_code_int <= 9999:
            alert("Confirmation code should use 4 digits")
            return

        json_dict = {
            'pseudo': pseudo,
            'code': confirmation_code_int,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/emails"

        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    form = html.FORM()
    my_sub_panel <= form

    legend_confirmation_code = html.LEGEND("confirmation code")
    form <= legend_confirmation_code
    input_confirmation_code = html.INPUT(type="number", value="", required=True)
    form <= input_confirmation_code
    form <= html.BR()

    input_validate_account = html.INPUT(type="submit", value="validate account")
    input_validate_account.bind("click", validate_account_callback)
    form <= input_validate_account
    form <= html.BR()


def edit_account():
    """ edit_account """

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    # declare the values
    email_loaded = None
    email_confirmed_loaded = None
    telephone_loaded = None
    replace_loaded = None
    family_name_loaded = None
    first_name_loaded = None
    country_loaded = None
    time_zone_loaded = None

    def edit_account_reload():
        """ edit_account_reload """

        status = True

        def local_noreply_callback(_):
            """ noreply_callback """
            nonlocal status
            alert("Problem (no answer from server)")
            status = False

        def reply_callback(req):
            """ reply_callback """
            nonlocal status
            nonlocal email_loaded
            nonlocal email_confirmed_loaded
            nonlocal telephone_loaded
            nonlocal replace_loaded
            nonlocal family_name_loaded
            nonlocal first_name_loaded
            nonlocal country_loaded
            nonlocal time_zone_loaded

            req_result = json.loads(req.text)
            if req.status != 200:
                alert(f"Problem loading account: {req_result['msg']}")
                status = False
                return

            pseudo_loaded = req_result['pseudo']
            if pseudo_loaded != pseudo:
                alert("Wierd. Pseudo is different !")
                status = False
                return

            email_loaded = req_result['email']
            email_confirmed_loaded = req_result['email_confirmed']
            telephone_loaded = req_result['telephone']
            replace_loaded = req_result['replace']
            family_name_loaded = req_result['family_name']
            first_name_loaded = req_result['first_name']

            # TODO : handle
            country_loaded = req_result['country']
            time_zone_loaded = req_result['time_zone']

        json_dict = dict()

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        # present the authentication token (we are reading content of an account)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_account_callback(_) -> None:
        """ change_account_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                alert(f"Problem : {req_result['msg']}")
                return
            InfoDialog("OK", f"Account changed : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        email = input_email.value
        if not re.match(EMAIL_PATTERN, email):
            alert("email is incorrect")
            return

        telephone = input_telephone.value
        replace = input_replace.value
        family_name = input_family_name.value
        first_name = input_first_name.value

        # TODO : implement
        country = "FRA"
        time_zone = "UTC + 1"

        json_dict = {
            'pseudo': pseudo,
            'email': email,
            'telephone': telephone,
            'replace': int(replace == 'true'),
            'family_name': family_name,
            'first_name': first_name,
            'country': country,
            'time_zone': time_zone,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    status = edit_account_reload()
    if not status:
        return

    form = html.FORM()
    my_sub_panel <= form

    legend_email = html.LEGEND("email")
    form <= legend_email

    input_email = html.INPUT(type="email", value=email_loaded)
    form <= input_email
    form <= html.BR()

    legend_telephone = html.LEGEND("telephone")
    form <= legend_telephone
    input_telephone = html.INPUT(type="tel", value=telephone_loaded)
    form <= input_telephone
    form <= html.BR()

    legend_replace = html.LEGEND("ok to replace")
    form <= legend_replace
    input_replace = html.INPUT(type="checkbox", checked=replace_loaded)
    form <= input_replace
    form <= html.BR()

    legend_family_name = html.LEGEND("family name")
    form <= legend_family_name
    input_family_name = html.INPUT(type="text", value=family_name_loaded)
    form <= input_family_name
    form <= html.BR()

    legend_first_name = html.LEGEND("first name")
    form <= legend_first_name
    input_first_name = html.INPUT(type="text", value=first_name_loaded)
    form <= input_first_name
    form <= html.BR()

    legend_country = html.LEGEND("country (not implemented)")
    form <= legend_country
    input_country = html.SELECT(type="select-one", value="")
    #  TODO : propose list of countries
    form <= input_country
    form <= html.BR()

    legend_time_zone = html.LEGEND("time zone (not implemented)")
    form <= legend_time_zone
    input_time_zone = html.SELECT(type="select-one", value="")
    #  TODO : propose list of timezones
    form <= input_time_zone
    form <= html.BR()

    input_create_account = html.INPUT(type="submit", value="change account")
    input_create_account.bind("click", change_account_callback)
    form <= input_create_account
    form <= html.BR()


def delete_account():
    """ delete_account """

    def delete_account_callback(_) -> None:
        """ delete_account_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                alert(f"Problem : {req_result['msg']}")
                return
            InfoDialog("OK", f"Your account was deleted : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        json_dict = {
            'pseudo': pseudo,
        }

        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    form = html.FORM()
    my_sub_panel <= form

    input_delete_account = html.INPUT(type="submit", value="delete account")
    input_delete_account.bind("click", delete_account_callback)
    form <= input_delete_account
    form <= html.BR()


my_panel = html.DIV(id="account")
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width:10%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="sub")

my_panel <= my_sub_panel


def load_option(_, item_name) -> None:
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'create':
        create_account()
    if item_name == 'change password':
        change_password()
    if item_name == 'validate':
        validate_account()
    if item_name == 'edit':
        edit_account()
    if item_name == 'delete':
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

        button = html.BUTTON(item_name_bold_or_not)
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_left <= menu_item


# starts here
load_option(None, item_name_selected)


def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
