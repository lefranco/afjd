""" account """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import re

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error

import config

OPTIONS = ['create account', 'change password', 'confirm email', 'modify data', 'delete account']

EMAIL_PATTERN = r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$'
MAX_LEN_PSEUDO = 12


def create_account():
    """ create_account """

    def create_account_callback(_) -> None:
        """ create_account_callback """

        def reply_callback(req):
            print("reply_callback")
            print(f"{req=}")
            req_result = json.loads(req.text)
            print(f"{req_result=}")
            if req.status != 200:
                alert(f"Problem : {req_result['msg']}")
                return
            print(f"{req_result=}")
            InfoDialog("OK", f"Account created : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        def noreply_callback(_):
            print("noreply_callback")
            alert("Problem (no answer from server)")

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
        replace = input_ok_replace.value
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

    legend_ok_replace = html.LEGEND("ok to replace")
    form <= legend_ok_replace
    input_ok_replace = html.INPUT(type="checkbox", value="")
    form <= input_ok_replace
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
    dummy = html.P("change password")
    my_sub_panel <= dummy


def confirm_email():
    """ confirm_email """

    dummy = html.P("confirm email")
    my_sub_panel <= dummy


def modify_data():
    """ modify_data """

    dummy = html.P("modify data")
    my_sub_panel <= dummy


def delete_account():
    """ delete_account """

    dummy = html.P("delete account")
    my_sub_panel <= dummy


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
    if item_name == 'create account':
        create_account()
    if item_name == 'change password':
        change_password()
    if item_name == 'confirm email':
        confirm_email()
    if item_name == 'modify data':
        modify_data()
    if item_name == 'delete account':
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
