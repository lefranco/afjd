""" admin """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common


my_panel = html.DIV(id="admin")

OPTIONS = ['changer nouvelles']


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

    # TODO a revoir
    if pseudo != "Palpatine":
        alert("Pas le bon compte (pas admin)")
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
    load_option(None, item_name_selected)
    panel_middle <= my_panel
