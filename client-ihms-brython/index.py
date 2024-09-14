""" index """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

from json import loads, dumps
from time import time

START_TIME = time()


from browser import document, html, alert, timer, ajax, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import play_master
import play

import config
import home
import login
import account
import mygames
import allgames
import tournament
import events
import ratings
import sandbox
import training
import technical
import helping
import variants
import wiki
import forum
import messenging


SITE_IMAGE_DISPLAY_SIZE = 100

# TITLE is in index.html

# H1
MAIN_TITLE = html.H1("Diplomania - le site de l'Association Francophone des Joueurs de Diplomacy. (β)")
document <= MAIN_TITLE


OPTIONS = {
    'Accueil': "L'accueil du site et les fonctionnalité élémentaires d'un site web",
    'Aide': "Pour obtenir de l'aide et découvrir simplement le jeu et le site par des vidéos, des tutoriels etc...",
    'Connexion': "Se connecter au site par mot de passe",
    'Mon compte': "Pour éditer les paramètres de son compte sur le site (il faut être connecté)",
    'Les parties': "Se mettrtea dans une partie, créer ujne partie, rectifier une partie, liste des parties...",
    'Mes parties': "La liste des parties dans laquelle vous jouez (il faut être connecté)",
    'Interface tournois': "Les tournois en cours et passés ainsi que leurs resultats",
    'Evénements': "Les évenements  à venir sur lesquels il est possible de s'inscrire",
    'Classements': "Différents classements sur les joueurs du site (obtenir une liste de joueurs) et les scorages disponibles",
    'Bac à sable': "Pour essayer le moteur de résolution hors d'une parte sur un cas concret",
    'Tutoriels et défis': "Pour s'entrainer à passer des ordres et comprendre les règles",
    'Technique': "Différents articles techniques (pour les joueurs chevronnés)",
    'Variantes': "Explications sur les variantes de jeu pratiquées sur le site",
    'Wiki': "Un wiki de partage de contenu sur le jeu en général",
    'Forum': "Un forum de discusion sur beaucoup de sujets",
    'Messages personnels': "Lire mes messages personnels et en envoyer",
    'Création': "Ce menu réservé aux créateurs de tournois",
    'Modération': "Ce menu réservé aux modérateurs du site",
    'Administration': "Ce menu réservé à l'administrateur du site"
}


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


ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

IP_TIMEOUT_SEC = 7


# reading the IP in a non disruptive way
def read_ip():
    """ read_ip """

    def store_ip(req):
        if req.status != 200:
            # Problem getting IP
            return
        ip_value = req.read()
        storage['IPADDRESS'] = ip_value

    def no_ip():
        # Failed to get IP (timeout)
        pass

    url = "https://ident.me"
    ajax.get(url, blocking=False, timeout=IP_TIMEOUT_SEC, oncomplete=store_ip, ontimeout=no_ip)


def check_event(event_name):
    """ check_event """

    events_data = common.get_events_data()
    event_list = [g['name'] for g in events_data.values()]

    if event_name not in event_list:
        alert(f"Erreur chargement événement {event_name}. Cet événement existe ?")
        return False

    return True


SITE_IMAGE_DICT = None


def get_site_image():
    """ get_site_image """

    global SITE_IMAGE_DICT

    SITE_IMAGE_DICT = None

    def reply_callback(req):
        global SITE_IMAGE_DICT
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de l'image du site : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de l'image du site : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        SITE_IMAGE_DICT = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/site_image"

    # get site image : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


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


def set_site_image(_, value):
    """ set_site_image """
    storage['SITE_IMAGE'] = value
    load_option(_, ITEM_NAME_SELECTED)


def show_site_image(_):
    """ show_site_image """
    document.clear()
    image_full = html.IMG(src=f"data:image/jpeg;base64,{SITE_IMAGE_DICT['image']}")
    document <= image_full


def load_option(_, item_name):
    """ load_option """

    pseudo = None
    game = None
    if 'PSEUDO' in storage:
        pseudo = storage['PSEUDO']
    if 'GAME' in storage:
        game = storage['GAME']

    PANEL_MIDDLE.clear()
    if item_name == 'Accueil':
        home.render(PANEL_MIDDLE)
    if item_name == 'Aide':
        helping.render(PANEL_MIDDLE)
    if item_name == 'Connexion':
        login.render(PANEL_MIDDLE)
    if item_name == 'Mon compte':
        account.render(PANEL_MIDDLE)
    if item_name == 'Les parties':
        allgames.render(PANEL_MIDDLE)
    if item_name == 'Mes parties':
        mygames.render(PANEL_MIDDLE)
    if item_name == 'Interface tournois':
        tournament.render(PANEL_MIDDLE)
    if item_name == 'Evénements':
        events.render(PANEL_MIDDLE)
    if item_name == 'Classements':
        ratings.render(PANEL_MIDDLE)
    if item_name == 'Bac à sable':
        sandbox.render(PANEL_MIDDLE)
    if item_name == 'Tutoriels et défis':
        training.render(PANEL_MIDDLE)
    if item_name == 'Technique':
        technical.render(PANEL_MIDDLE)
    if item_name == 'Variantes':
        variants.render(PANEL_MIDDLE)
    if item_name == 'Wiki':
        wiki.render(PANEL_MIDDLE)
    if item_name == 'Forum':
        forum.render(PANEL_MIDDLE)
    if item_name == 'Messages personnels':
        messenging.render(PANEL_MIDDLE)
    if item_name == 'Création':
        if common.check_creator():
            import create  # pylint: disable=import-outside-toplevel
            create.render(PANEL_MIDDLE)
    if item_name == 'Modération':
        if common.check_modo():
            import moderate  # pylint: disable=import-outside-toplevel
            moderate.render(PANEL_MIDDLE)
    if item_name == 'Administration':
        if common.check_admin():
            import admin  # pylint: disable=import-outside-toplevel
            admin.render(PANEL_MIDDLE)

    priviledged = common.PRIVILEDGED
    creator_list = priviledged['creators']
    moderators_list = priviledged['moderators']

    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    MENU_LEFT.clear()

    # items in menu
    for possible_item_name, legend in OPTIONS.items():

        # do not display some options

        # not connected
        if possible_item_name in ['Mon compte', 'Mes parties', 'Editer partie']:
            if pseudo is None:
                continue
            # should check account exist (but slower for rare case)
        # game not selected
        if possible_item_name in ['Retourner dans la partie']:
            if game is None:
                continue
            # should check game exist (but slower for rare case)

        # do not display menu create if not creator
        if possible_item_name == 'Création':
            if pseudo is None or pseudo not in creator_list:
                continue

        # do not display menu moderate if not moderator
        if possible_item_name == 'Modération':
            if pseudo is None or pseudo not in moderators_list:
                continue

        # do not display menu administrate if not administrator
        if possible_item_name == 'Administration':
            if not common.check_admin():
                continue

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, title=legend, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        MENU_LEFT <= menu_item

    # quitting superviser : clear timer
    if play_master.SUPERVISE_REFRESH_TIMER is not None:
        timer.clear_interval(play_master.SUPERVISE_REFRESH_TIMER)
        play_master.SUPERVISE_REFRESH_TIMER = None

    # these cause some problems
    document.unbind("keypress")

    if ITEM_NAME_SELECTED == 'Accueil':
        if ('SITE_IMAGE' not in storage or storage['SITE_IMAGE'] == 'True') and SITE_IMAGE_DICT:

            # build site image and legend
            figure = html.FIGURE()
            image = html.IMG(src=f"data:image/jpeg;base64,{SITE_IMAGE_DICT['image']}", width=SITE_IMAGE_DISPLAY_SIZE, height=SITE_IMAGE_DISPLAY_SIZE, alt="Image du site", title="Cliquer sur l'image pour l'agrandir et bien la visualiser")
            figure <= image
            legend = html.FIGCAPTION(SITE_IMAGE_DICT['legend'])
            figure <= legend
            figure.bind("click", show_site_image)

            MENU_LEFT <= figure

            button = html.BUTTON("-", title="Cacher l'image", Class='btn-menu')
            button.bind("click", lambda e: set_site_image(e, 'False'))

        else:

            button = html.BUTTON("+", title="Remettre l'image", Class='btn-menu')
            button.bind("click", lambda e: set_site_image(e, 'True'))

        MENU_LEFT <= html.BR()
        MENU_LEFT <= button

    else:
        figure = html.FIGURE()
        image = html.IMG(src="images/logo_AFJD.jpg", alt="AFJD", title="Association Frarcophone des Joueurs de Diplomacy")
        figure <= image
        MENU_LEFT <= figure

    MENU_LEFT <= html.BR()
    MENU_LEFT <= html.BR()
    MENU_LEFT <= html.SMALL("Testé avec Firefox.")


# we read ip now if necessary
if 'IPADDRESS' not in storage:
    read_ip()


# panel-middle
PANEL_MIDDLE = html.DIV()
OVERALL <= PANEL_MIDDLE

get_site_image()

# starts here
if 'game' in document.query:
    QUERY_GAME_NAME = document.query['game']
    if load_game(QUERY_GAME_NAME):
        if 'arrival' in document.query:
            arrival = document.query['arrival']
            # so that will go to proper page and/or do proper action
            play.set_arrival(arrival)
        # stick to game name
        window.history.pushState({}, document.title, f"?game={QUERY_GAME_NAME}")
        load_option(None, 'Accueil')
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)
    else:
        alert("Partie inconnue !")
        load_option(None, ITEM_NAME_SELECTED)
elif 'edit_game' in document.query:
    QUERY_GAME_NAME = document.query['edit_game']
    if load_game(QUERY_GAME_NAME):
        # stick to game name
        window.history.pushState({}, document.title, f"?edit_game={QUERY_GAME_NAME}")
        PANEL_MIDDLE.clear()
        allgames.set_arrival()
        allgames.render(PANEL_MIDDLE)
    else:
        alert("Partie inconnue !")
        load_option(None, ITEM_NAME_SELECTED)
elif 'event' in document.query:
    QUERY_EVENT_NAME = document.query['event']
    if check_event(QUERY_EVENT_NAME):
        storage['EVENT'] = QUERY_EVENT_NAME
        events.set_arrival()
        window.history.pushState({}, document.title, "/")
        load_option(None, 'Evénements')
    else:
        alert("Evénement inconnu !")
        window.history.pushState({}, document.title, "/")
        load_option(None, ITEM_NAME_SELECTED)
elif 'tournament' in document.query:
    query_tournament_name = document.query['tournament']
    tournament.set_arrival(query_tournament_name)
    window.history.pushState({}, document.title, "/")
    load_option(None, 'Accueil')
    PANEL_MIDDLE.clear()
    tournament.render(PANEL_MIDDLE)
elif 'variant' in document.query:
    query_variant_name = document.query['variant']
    variants.set_arrival('variant', query_variant_name)
    window.history.pushState({}, document.title, "/")
    load_option(None, 'Accueil')
    PANEL_MIDDLE.clear()
    variants.render(PANEL_MIDDLE)
elif 'sequence' in document.query:
    query_sequence_name = document.query['sequence']
    training.set_arrival(query_sequence_name)
    window.history.pushState({}, document.title, "/")
    load_option(None, 'Accueil')
    PANEL_MIDDLE.clear()
    training.render(PANEL_MIDDLE)
elif 'rescue' in document.query:
    if 'pseudo' in document.query:
        passed_pseudo = document.query['pseudo']
        storage['PSEUDO'] = passed_pseudo
    if 'token' in document.query:
        passed_token = document.query['token']
        storage['JWT_TOKEN'] = passed_token
    alert("Changez votre mot de passe rapidement !")
    account.set_rescue()
    window.history.pushState({}, document.title, "/")
    load_option(None, 'Mon compte')
else:
    window.history.pushState({}, document.title, "/")
    load_option(None, ITEM_NAME_SELECTED)

document <= html.BR()
document <= html.BR()

login.check_token()
login.show_login()
allgames.show_game_selected()

document <= html.B("Contactez le support par courriel en cas de problème (cf. page d'accueil / onglet 'déclarer un incident'). Merci !")
document <= html.BR()

# home page loading time
END_TIME = time()
ELAPSED = END_TIME - START_TIME
home.show_load_time_version(ELAPSED)

# spinner dies
spinner = document['spinner']
spinner.className = 'pycorpse'

# spinner dissipates
spinner.parentElement.removeChild(spinner)
