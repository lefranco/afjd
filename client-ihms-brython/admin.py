""" admin """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import login

my_panel = html.DIV(id="admin")

OPTIONS = ['changer nouvelles', 'usurper', 'envoyer un mail']


def check_admin(pseudo):
    """ check_admin """

    # TODO improve this with real admin account
    # TODO a revoir
    if pseudo != "Palpatine":
        alert("Pas le bon compte (pas admin)")
        return False

    return True


def change_news():
    """ change_news """

    def change_news_callback(_):
        """ change_news_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error changing news: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem changing news: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Les nouvelles ont été changées : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        news_content = input_news_content.value
        if not news_content:
            alert("Contenu nouvelles manquant")
            return

        json_dict = {
            'pseudo': pseudo,
            'content': news_content,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/news"

        # changing news : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    if 'PSEUDO' not in storage:
        alert("Il faut se loguer au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    news_content_loaded = common.get_news_content()
    if news_content_loaded is None:
        return

    form = html.FORM()

    legend_news_content = html.LEGEND("nouveau contenu de nouvelles")
    form <= legend_news_content

    input_news_content = html.TEXTAREA(type="text", rows=5, cols=80)
    input_news_content <= news_content_loaded
    form <= input_news_content
    form <= html.BR()

    form <= html.BR()

    input_change_news_content = html.INPUT(type="submit", value="mettre à jour")
    input_change_news_content.bind("click", change_news_callback)
    form <= input_change_news_content
    form <= html.BR()

    my_sub_panel <= form


def usurp():
    """ usurp """

    def usurp_callback(_):
        """ usurp_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error usurping: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem usurping: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

            storage['PSEUDO'] = usurped_user_name
            storage['JWT_TOKEN'] = req_result['AccessToken']
            time_stamp = time.time()
            storage['LOGIN_TIME'] = str(time_stamp)
            InfoDialog("OK", f"Vous usurpez maintenant : {usurped_user_name}", remove_after=config.REMOVE_AFTER)
            login.show_login()

        usurped_user_name = input_usurped.value
        if not usurped_user_name:
            alert("User name usurpé manquant")
            return

        json_dict = {
            'usurped_user_name': usurped_user_name,
        }

        host = config.SERVER_CONFIG['USER']['HOST']
        port = config.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/usurp"

        # usurping : need token
        # note : since we access directly to the user server, we present the token in a slightly different way
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    if 'PSEUDO' not in storage:
        alert("Il faut se loguer au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    form = html.FORM()

    legend_usurped = html.LEGEND("Usurpé", title="Sélectionner le joueur à usurper")
    form <= legend_usurped

    players_dict = common.get_players()
    if players_dict is None:
        return

    # all players can be usurped
    possible_usurped = set(players_dict.keys())

    input_usurped = html.SELECT(type="select-one", value="")
    for usurped_pseudo in sorted(possible_usurped):
        option = html.OPTION(usurped_pseudo)
        input_usurped <= option

    form <= input_usurped
    form <= html.BR()

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="usurper")
    input_select_player.bind("click", usurp_callback)
    form <= input_select_player

    my_sub_panel <= form


def sendmail():
    """ sendmail """

    def sendmail_callback(_):
        """ sendmail_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error sending email: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem sending email: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

            InfoDialog("OK", f"Message émis vers : {addressed_user_name}", remove_after=config.REMOVE_AFTER)

        addressed_user_name = input_addressed.value
        if not addressed_user_name:
            alert("User name destinataire manquant")
            return

        subject = "Message de la part de l'administrateur du site www.diplomania.fr (AFJD)"
        body = input_message.value

        addressed_id = players_dict[addressed_user_name]
        addressees = [addressed_id]

        json_dict = {
            'pseudo': pseudo,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    if 'PSEUDO' not in storage:
        alert("Il faut se loguer au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    form = html.FORM()

    legend_addressee = html.LEGEND("Destinataire", title="Sélectionner le joueur à contacter")
    form <= legend_addressee

    players_dict = common.get_players()
    if players_dict is None:
        return

    # all players can be usurped
    possible_addressed = set(players_dict.keys())

    input_addressed = html.SELECT(type="select-one", value="")
    for addressee_pseudo in sorted(possible_addressed):
        option = html.OPTION(addressee_pseudo)
        input_addressed <= option

    form <= input_addressed
    form <= html.BR()

    form <= html.BR()

    legend_message = html.LEGEND("Votre message", title="Qu'avez vous à lui dire ?")
    form <= legend_message
    form <= html.BR()

    input_message = html.TEXTAREA(type="text", rows=5, cols=80)
    form <= input_message
    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="contacter")
    input_select_player.bind("click", sendmail_callback)
    form <= input_select_player

    my_sub_panel <= form


my_panel = html.DIV(id="admin")
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="sub")

my_panel <= my_sub_panel


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'changer nouvelles':
        change_news()
    if item_name == 'usurper':
        usurp()
    if item_name == 'envoyer un mail':
        sendmail()

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


def render(panel_middle):
    """ render """

    # always back to top
    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

    load_option(None, item_name_selected)
    panel_middle <= my_panel
