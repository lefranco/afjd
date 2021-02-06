""" account """

from browser import document, html

OPTIONS = ['create account', 'change password', 'confirm email', 'modify data', 'delete account']



def create_account():
    dummy = html.P("create account")
    my_sub_panel <= dummy

def change_password():
    dummy = html.P("change password")
    my_sub_panel <= dummy

def confirm_email():
    dummy = html.P("confirm email")
    my_sub_panel <= dummy

def modify_data():
    dummy = html.P("modify data")
    my_sub_panel <= dummy

def delete_account():
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

item_name_selected = OPTIONS[0]

my_sub_panel = html.DIV(id="sub")

my_panel <= my_sub_panel

def load_option(ev, item_name) -> None:
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
    global item_name_selected
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for item_name in OPTIONS:

        if item_name == item_name_selected:
            item_name_bold_or_not = html.B(item_name)
        else:
            item_name_bold_or_not = item_name

        button = html.BUTTON(item_name_bold_or_not)
        button.bind("click", lambda ev, item_name=item_name: load_option(ev, item_name))
        menu_item = html.LI(button)
        menu_left <= menu_item


# starts here
load_option(None, item_name_selected)


def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
