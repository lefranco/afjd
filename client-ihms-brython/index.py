""" index """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import document, html, alert, timer  # pylint: disable=import-error # noqa: E402
from browser.local_storage import storage  # pylint: disable=import-error # noqa: E402

import common    # noqa: E402
import home    # noqa: E402
import login    # noqa: E402
import account    # noqa: E402
import opportunities    # noqa: E402
import mygames    # noqa: E402
import games    # noqa: E402
import pairing    # noqa: E402
import selection    # noqa: E402
import play    # noqa: E402
import sandbox    # noqa: E402
import tournament    # noqa: E402
import events    # noqa: E402
import players    # noqa: E402
import moderate    # noqa: E402
import create    # noqa: E402
import admin    # noqa: E402
import forum    # noqa: E402

# TITLE is in index.html

# H2
H2 = html.DIV("Diplomania - le site de l'Association Francophone des Joueurs de Diplomatie (brique jeu)")
H2.attrs['style'] = 'text-align: center'
document <= H2

OPTIONS = ['Accueil', 'Connexion', 'Mon compte', 'Rejoindre une partie', 'Mes parties', 'Editer partie', 'Appariement', 'Sélectionner partie', 'Jouer la partie sélectionnée', 'Bac à sable', 'Interface tournois', 'Evénements', 'Classements', 'Création', 'Modération', 'Administration', 'Forum']

# overall_top
OVERALL_TOP = html.DIV()
OVERALL_TOP.attrs['style'] = 'display:table; width:100%'
document <= OVERALL_TOP

# overall
OVERALL = html.DIV()
OVERALL.attrs['style'] = 'display: table-row'
OVERALL_TOP <= OVERALL

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width: 10%; vertical-align: top;'
OVERALL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION


ITEM_NAME_SELECTED = OPTIONS[0]


def check_event(event_name):
    """ check_event """

    events_data = common.get_events_data()
    event_list = [g['name'] for g in events_data.values()]

    if event_name not in event_list:
        alert(f"Erreur chargement événement {event_name}. Cet événement existe ?")
        return False

    return True


def load_game(game_name):
    """ load_game """

    game_data = common.get_game_data(game_name)
    if not game_data:
        alert(f"Erreur chargement données partie {game_name}. Cette partie existe ?")
        return False

    game_id_int = common.get_game_id(game_name)
    if not game_id_int:
        alert(f"Erreur chargement identifiant partie {game_name}. Cette partie existe ?")
        return False
    game_id = str(game_id_int)

    # create a table to pass information about selected game
    game_data_sel = {game_name: (game_id, game_data['variant'])}

    storage['GAME'] = game_name

    game_id = game_data_sel[game_name][0]
    storage['GAME_ID'] = game_id
    game_variant = game_data_sel[game_name][1]
    storage['GAME_VARIANT'] = game_variant

    return True


def set_flag(_, value):
    """ set_flag """
    storage['flag'] = value
    load_option(_, ITEM_NAME_SELECTED)


def load_option(_, item_name):
    """ load_option """

    pseudo = None
    if 'PSEUDO' in storage:
        pseudo = storage['PSEUDO']

    PANEL_MIDDLE.clear()
    if item_name == 'Accueil':
        home.render(PANEL_MIDDLE)
    if item_name == 'Connexion':
        login.render(PANEL_MIDDLE)
    if item_name == 'Mon compte':
        account.render(PANEL_MIDDLE)
    if item_name == 'Rejoindre une partie':
        opportunities.render(PANEL_MIDDLE)
    if item_name == 'Mes parties':
        mygames.render(PANEL_MIDDLE)
    if item_name == 'Editer partie':
        games.render(PANEL_MIDDLE)
    if item_name == 'Appariement':
        pairing.render(PANEL_MIDDLE)
    if item_name == 'Sélectionner partie':
        selection.render(PANEL_MIDDLE)
    if item_name == 'Jouer la partie sélectionnée':
        play.render(PANEL_MIDDLE)
    if item_name == 'Bac à sable':
        sandbox.render(PANEL_MIDDLE)
    if item_name == 'Interface tournois':
        tournament.render(PANEL_MIDDLE)
    if item_name == 'Evénements':
        events.render(PANEL_MIDDLE)
    if item_name == 'Classements':
        players.render(PANEL_MIDDLE)
    if item_name == 'Création':
        create.render(PANEL_MIDDLE)
    if item_name == 'Modération':
        moderate.render(PANEL_MIDDLE)
    if item_name == 'Administration':
        admin.render(PANEL_MIDDLE)
    if item_name == 'Forum':
        forum.render(PANEL_MIDDLE)

    global ITEM_NAME_SELECTED
    prev_item_selected = ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    MENU_LEFT.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        # do not display menu create if not creator
        if possible_item_name == 'Création':
            if pseudo is None or not create.check_creator(pseudo):
                continue

        # do not display menu moderate if not moderator
        if possible_item_name == 'Modération':
            if pseudo is None or not moderate.check_modo(pseudo):
                continue

        # do not display menu administrate if not administrator
        if possible_item_name == 'Administration':
            if pseudo is None or not admin.check_admin(pseudo):
                continue

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        MENU_LEFT <= menu_item

    # quitting superviser : clear timer
    if ITEM_NAME_SELECTED != 'jouer la partie sélectionnée':
        if play.SUPERVISE_REFRESH_TIMER is not None:
            timer.clear_interval(play.SUPERVISE_REFRESH_TIMER)
            play.SUPERVISE_REFRESH_TIMER = None
        if play.OBSERVE_REFRESH_TIMER is not None:
            timer.clear_interval(play.OBSERVE_REFRESH_TIMER)
            play.OBSERVE_REFRESH_TIMER = None

    # these cause some problems
    if prev_item_selected in ['jouer la partie sélectionnée', 'bac à sable']:
        document.unbind("keypress")

    if ITEM_NAME_SELECTED == 'Accueil':
        if 'flag' not in storage or storage['flag'] == 'True':
            emotion_img = html.IMG(src="./images/ukraine-flag-animation.gif")
            MENU_LEFT <= html.BR()
            MENU_LEFT <= emotion_img
            MENU_LEFT <= html.BR()
            button = html.BUTTON("-", Class='btn-menu')
            button.bind("click", lambda e: set_flag(e, 'False'))
        else:
            button = html.BUTTON("+", Class='btn-menu')
            button.bind("click", lambda e: set_flag(e, 'True'))
        MENU_LEFT <= html.BR()
        MENU_LEFT <= button


# panel-middle
PANEL_MIDDLE = html.DIV()
OVERALL <= PANEL_MIDDLE

# starts here
if 'game' in document.query:
    QUERY_GAME_NAME = document.query['game']
    if load_game(QUERY_GAME_NAME):
        if 'arrival' in document.query:
            arrival = document.query['arrival']
            # so that will go to proper page and/or do proper action
            play.set_arrival(arrival)
        load_option(None, 'Jouer la partie sélectionnée')
    else:
        load_option(None, ITEM_NAME_SELECTED)
elif 'event' in document.query:
    QUERY_EVENT_NAME = document.query['event']
    if check_event(QUERY_EVENT_NAME):
        storage['EVENT'] = QUERY_EVENT_NAME
        events.set_arrival()
        load_option(None, 'Evénements')
    else:
        load_option(None, ITEM_NAME_SELECTED)
else:
    load_option(None, ITEM_NAME_SELECTED)

document <= html.BR()
document <= html.BR()

login.check_token()
login.show_login()
selection.show_game_selected()

document <= html.B("Contactez le support par courriel en cas de problème (cf. page d'accueil / onglet 'déclarer un incident'). Merci !")
document <= html.BR()
version = storage['VERSION']
document <= html.I(f"Vous utilisez la version du {version}")
document <= html.BR()
ip_address = storage['IPADDRESS']
document <= html.I(f"Votre adresse IP est {ip_address}")
