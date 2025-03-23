""" home """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

from json import loads, dumps
from time import time

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import user_config
import config
import common
import helping
import training
import ezml_render
import mydatetime
import mydialog
import play
import allgames


THRESHOLD_DRIFT_ALERT_SEC = 59


OPTIONS = {
    'Vue d\'ensemble': "Vue d'ensemble du site",
    'Tester le jeu': "Entrer dans une partie de démonstration pour y passer des ordres et échanger des messages",
    'Discuter en ligne': "Echanger des messages volatiles à court terme",
    'Déclarer un incident': "Déclarer un incident par courriel à l'administrateur",
    'Données personnelles': "Explications sur la manière dont le site gère les données personnelles",
}


# for safety
for num in range(1, 4):
    if f'ANNOUNCEMENT_{num}_ADMIN' not in storage:
        storage[f'ANNOUNCEMENT_{num}_ADMIN'] = ""
    if f'ANNOUNCEMENT_{num}_DISPLAYED_ADMIN' not in storage:
        storage[f'ANNOUNCEMENT_{num}_DISPLAYED_ADMIN'] = 'no'
    if f'ANNOUNCEMENT_{num}_MODO' not in storage:
        storage[f'ANNOUNCEMENT_{num}_MODO'] = ""
    if f'ANNOUNCEMENT_{num}_DISPLAYED_MODO' not in storage:
        storage[f'ANNOUNCEMENT_{num}_DISPLAYED_MODO'] = 'no'


ARRIVAL = None


def set_arrival(arrival):
    """ set_arrival """
    global ARRIVAL
    ARRIVAL = arrival


def get_stats_content():
    """ get_stats_content """

    stats_content = {}

    def reply_callback(req):
        nonlocal stats_content
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du contenu des statistiques : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du contenu des statistiques : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        stats_content = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/statistics"

    # get news : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return stats_content


def get_teaser_content():
    """ get_teaser_content """

    teaser_content = None

    def reply_callback(req):
        nonlocal teaser_content
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du contenu du teaser elo : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du contenu du teaser elo : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        teaser_content = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/elo_rating"

    # get teaser elo : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return teaser_content


def select_game_callback(ev, game_name, game_data_sel):  # pylint: disable=invalid-name
    """ select_game_callback """

    ev.preventDefault()

    # action of selecting game
    storage['GAME'] = game_name
    game_id = game_data_sel[game_name][0]
    storage['GAME_ID'] = game_id
    game_variant = game_data_sel[game_name][1]
    storage['GAME_VARIANT'] = game_variant

    allgames.show_game_selected()

    # action of going to game page
    PANEL_MIDDLE.clear()
    play.render(PANEL_MIDDLE)


def formatted_games(games_dict, game_data_sel, conversion_table, suffering_games):
    """ formatted_games """

    # 4 on PC 3 on smartphone it should be
    max_col = 3

    # init
    games_content = html.DIV()

    games_table = html.TABLE()
    row = html.TR()
    num_col = 0
    for game_name in suffering_games:

        if num_col == max_col:
            # new line
            games_table <= row
            row = html.TR()
            num_col = 0

        col = html.TD()
        content = html.DIV()

        # name of game in a link
        button = html.BUTTON(game_name, title="Cliquer pour aller dans la partie", Class='btn-inside')
        button.style = {'font-size': '10px'}
        button.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=None: select_game_callback(e, gn, gds))
        content <= button

        content <= " "

        # some information to raise interest
        col = html.TD()
        game_id_str = game_data_sel[game_name][0]
        data = games_dict[game_id_str]
        infos = f"{data['variant']} {conversion_table[data['game_type']]}"
        if data['used_for_elo']:
            infos += " elo"
        if data['fog']:
            infos += " brouillard"
        infos += f" {data['current_advancement'] // 5}/{data['nb_max_cycles_to_play']}"
        content <= infos

        col.style = {'font-size': '10px'}
        col <= content
        row <= col

        num_col += 1

    games_table <= row
    games_content <= games_table
    return games_content


def formatted_teaser(teasers):
    """ formatted_teaser """

    # collect data
    data = {}
    done = False
    datation = ''
    for line in teasers.split('\n'):
        if line:
            if done:
                datation = line
            else:
                champion_data = line.split()
                c_pseudo = champion_data[0]
                c_score = int(champion_data[1])
                c_role = champion_data[2]
                c_mode = champion_data[3]
                data[(c_role, c_mode)] = (c_pseudo, c_score)
        else:
            done = True

    roles = sorted({d[0] for d in data})
    modes = sorted({d[1] for d in data})

    # init
    teaser_content = html.DIV()

    # data in table
    teaser_content_table = html.TABLE()
    title = html.TR()
    for header in [' '] + modes:
        title <= html.TD(html.B(header))
    teaser_content_table <= title
    for role in sorted(roles):
        row = html.TR()
        row <= html.TD(html.B(role))
        for mode in modes:
            pseud, score = data[(role, mode)]
            elem = html.DIV()
            elem <= pseud
            elem <= " "
            elem <= score
            row <= html.TD(elem)
        teaser_content_table <= row

    teaser_content <= teaser_content_table
    teaser_content <= html.BR()
    teaser_content <= html.EM(f"En date de {datation}")

    return teaser_content


def new_private_messages_received():
    """ new_private_messages_received """

    new_messages_loaded = 0

    def reply_callback(req):
        nonlocal new_messages_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement si des messages personnels : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement si des messages personnels : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        new_messages_loaded = req_result['new_messages']
        return

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/new-private-messages-received"

    # reading new private messages received : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return new_messages_loaded


def email_address_is_confirmed():
    """ email_address_is_confirmed """

    email_confirmed = False

    def reply_callback(req):
        nonlocal email_confirmed
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement confirmation email : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement confirmation email : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        email_confirmed = req_result['email_confirmed']
        return

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/email-confirmed"

    # reading new private messages received : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return email_confirmed


def show_news():
    """ show_home """

    def show_chart_callback(ev):  # pylint: disable=invalid-name
        """ show_chart_callback """

        ev.preventDefault()

        arrival = 'charte'

        # so that will go to proper page
        helping.set_arrival(arrival)

        # action of going to game page
        PANEL_MIDDLE.clear()
        helping.render(PANEL_MIDDLE)

    def show_tutorial_callback(ev):  # pylint: disable=invalid-name
        """ show_chart_callback """

        ev.preventDefault()

        # action of going to game page
        PANEL_MIDDLE.clear()
        training.render(PANEL_MIDDLE)

    games_dict = common.get_games_data(0, 1)  # awaiting or ongoing
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    # No need for a title
    div_homepage = html.DIV(id='grid')

    stats_content = get_stats_content()
    news_content_table_loaded = common.get_news_content()
    players_dict = common.get_players()

    # ==A5==============================

    div_a5 = html.DIV(Class='tooltip')
    title1 = html.H4("Actions urgentes, dernière discussion en ligne et jauge de financement")
    div_a5 <= title1

    # ----

    # game_type identifier -> description
    conversion_table = {v: k for k, v in config.GAME_TYPES_CODE_TABLE.items()}

    dying_games_loaded = stats_content['dying_games']
    if dying_games_loaded:
        div_a5 <= html.H5("Grands retards :")
        div_a5 <= "Les parties ci-dessous sont en grand retard."
        div_a5 <= html.BR()
        div_a5 <= formatted_games(games_dict, game_data_sel, conversion_table, dying_games_loaded)

    suffering_games_loaded = stats_content['suffering_games']
    if suffering_games_loaded:
        div_a5 <= html.H5("Remplacements urgents :")
        div_a5 <= "Les parties ci-dessous sont en cours et ont besoin de remplaçant(s) - arbitre ou joueur."
        div_a5 <= html.BR()
        div_a5 <= formatted_games(games_dict, game_data_sel, conversion_table, suffering_games_loaded)

    stalled_games_loaded = stats_content['stalled_games']
    if stalled_games_loaded:
        div_a5 <= html.H5("Démarrages difficiles :")
        div_a5 <= "Les parties ci-dessous sont en en attente d'être complète pour démarrer depuis trop longtemps."
        div_a5 <= html.BR()
        div_a5 <= formatted_games(games_dict, game_data_sel, conversion_table, stalled_games_loaded)

    chat_content_loaded = news_content_table_loaded['chats']
    if chat_content_loaded:
        last_chat = chat_content_loaded[-1]
        last_chat_author = last_chat[1]
        last_chat_message = last_chat[2]
        div_a5 <= html.BR()
        div_a5 <= html.H5("Dernier message :")
        div_a5 <= html.DIV(f"{last_chat_author} : {last_chat_message}", Class='chat_sample')

    div_a5 <= html.H5("Jauge de financement :")
    div_a5 <= html.DIV("TODO ;-)")

    # ----

    div_a5_tip = html.SPAN("Plus de détail dans le menu “Les parties“ sous menu 'Rejoindre une partie' et dans le menu 'Discuter en ligne'", Class='tooltiptext')
    div_a5 <= div_a5_tip
    div_homepage <= div_a5

    # ==B5==============================

    div_b5 = html.DIV(Class='tooltip')
    title2 = html.H4("Les meilleurs joueurs du site (d'après le classement ELO sur les parties 'standard')")
    div_b5 <= title2

    # ----

    teaser_loaded = get_teaser_content()
    teaser = formatted_teaser(teaser_loaded) if teaser_loaded else "Aucun pour le moment."
    div_b5 <= teaser

    # ----

    div_b5_tip = html.SPAN("Plus de détail dans le menu 'Classements' sous menu 'Classement performance'", Class='tooltiptext')
    div_b5 <= div_b5_tip
    div_homepage <= div_b5

    # ==A4==============================

    div_a4 = html.DIV(Class='tooltip')
    title3 = html.H4("Les événements qui recrutent")
    div_a4 <= title3

    # ----

    news_events = html.OBJECT(data=f"{config.SITE_ADDRESS}/events/", width="100%", height="350", title="Evénements", alt="Evénements")
    div_a4 <= news_events

    # ----

    # tip
    div_a4_tip = html.SPAN("Vous pouvez accéder aux événements par le bouton du menu tout à gauche", Class='tooltiptext')
    div_a4 <= html.BR()
    div_a4 <= div_a4_tip
    div_homepage <= div_a4

    # =B4==============================

    div_b4 = html.DIV(Class='tooltip')
    # need special positioning !
    div_b4.style = {
        'grid-column': '2/3',
        'grid-row': '2/4'
    }
    title4 = html.H4("Dernières contributions sur les forums")
    div_b4 <= title4

    # ----

    news_forum = html.OBJECT(data=f"{config.SITE_ADDRESS}/external_page.php", width="100%", height="700", title="Forums", alt="Forums")
    div_b4 <= news_forum

    # ----

    # tip
    div_b4_tip = html.SPAN("Vous pouvez accéder aux forums par le bouton du menu tout à gauche", Class='tooltiptext')
    div_b4 <= html.BR()
    div_b4 <= div_b4_tip
    div_homepage <= div_b4

    # ==A3==============================

    div_a3 = html.DIV(Class='tooltip')
    title5 = html.H4("Dernières nouvelles !")
    div_a3 <= title5

    # ----

    title51 = html.H5("Administrateur")
    div_a3 <= title51
    news_content_loaded = news_content_table_loaded['admin']
    news_content = common.formatted_news(news_content_loaded, 'ADMIN', 'admin_news')
    div_a3 <= news_content

    title52 = html.H5("Moderateur")
    div_a3 <= title52
    news_content_loaded = news_content_table_loaded['modo']
    news_content = common.formatted_news(news_content_loaded, 'MODO', 'modo_news')
    div_a3 <= news_content

    # ----

    div_a3_tip = html.SPAN("Vous pouvez contacter l'administrateur par le menu “Accueil“ sous menu “Déclarer un incident“ et le modérateur par un MP sur le forum", Class='tooltiptext')
    div_a3 <= div_a3_tip
    div_homepage <= div_a3

    # ==B3==============================

    # Merged with B4

    # ==A2==============================

    div_a2 = html.DIV(Class='tooltip')
    title9 = html.H4("Liens très importants")
    div_a2 <= title9

    # ----

    note_bene_content = html.DIV(Class='note')
    note_bene_content_table = html.TABLE()

    # -------------

    row = html.TR()
    note_bene_content_table <= row

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/pay.png")
    col <= img
    row <= col

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/support.png")
    col <= img
    row <= col

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/tuto.jpg")
    col <= img
    row <= col

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/chart.png")
    col <= img
    row <= col

    # ............

    row = html.TR()
    note_bene_content_table <= row

    col = html.TD()
    link4 = html.A(href="https://www.helloasso.com/associations/association-francophone-des-joueurs-de-diplomacy/formulaires/3", target="_blank")
    link4 <= "Je souhaite contribuer au financement de l'association qui gère le site !"
    col <= link4
    row <= col

    col = html.TD()
    link5 = html.A(href="https://discord.com/invite/wAHgMWQG4Z", target="_blank")
    link5 <= "Feedback et support du site diplomania sur Discord !"
    col <= link5
    row <= col

    col = html.TD()
    form = html.FORM()
    input_show_tutorial = html.INPUT(type="submit", value="Le tutoriel", Class='btn-inside')
    input_show_tutorial.attrs['style'] = 'font-size: 10px'
    input_show_tutorial.bind("click", show_tutorial_callback)
    form <= input_show_tutorial
    col <= form
    col <= "Tutoriel intertactif pour les règles et le site !"
    row <= col

    col = html.TD()
    form = html.FORM()
    input_show_chart = html.INPUT(type="submit", value="La charte", Class='btn-inside')
    input_show_chart.attrs['style'] = 'font-size: 10px'
    input_show_chart.bind("click", show_chart_callback)
    form <= input_show_chart
    col <= form
    col <= "La charte du bon diplomate - à lire absolument !"
    row <= col

    # -------------

    row = html.TR()
    note_bene_content_table <= row

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/facebook.png")
    col <= img
    row <= col

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/abydos.jpeg")
    col <= img
    row <= col

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/chat.png")
    col <= img
    row <= col

    col = html.TD()
    row <= col

    # ............

    row = html.TR()
    note_bene_content_table <= row

    col = html.TD()
    link5 = html.A(href="https://www.facebook.com/groups/104700706277433", target="_blank")
    link5 <= "La page Facebook de l'association"
    col <= link5
    row <= col

    col = html.TD()
    link5 = html.A(href="https://sites.google.com/view/abydosfr/accueil", target="_blank")
    link5 <= "Le site dédié à Diplomacy de notre ami Abydos !"
    col <= link5
    row <= col

    col = html.TD()
    link51 = html.A(href="https://discord.gg/mUWes7yEqR", target="_blank")
    link51 <= "Causer sur le Discord de l'Association avec d'autres joueurs !"
    col <= link51
    row <= col

    note_bene_content <= note_bene_content_table
    div_a2 <= note_bene_content
    div_homepage <= div_a2

    col = html.TD()
    row <= col

    # ----

    div_a2_tip = html.SPAN("Plus de détail sur le site http://www.diplomania.fr", Class='tooltiptext')
    div_a2 <= div_a2_tip
    div_homepage <= div_a2

    # ==B2==============================

    div_b2 = html.DIV(Class='tooltip')
    # need special positioning !
    div_b2.style = {
        'grid-column': '2/3',
        'grid-row': '4/6'
    }

    title7 = html.H4("Du nouveau sur le wiki (pour l'ouvrir dans une nouvelle fenêtre utiliser le menu 'Wiki')")
    div_b2 <= title7

    # ----

    news_wiki = html.IFRAME(src=f"{config.SITE_ADDRESS}/dokuwiki/doku.php?id=start&do=export_xhtml", width="100%", height="350", title="Wiki", alt="Wiki", allow="fullscreen")
    div_b2 <= news_wiki

    # ----

    # no tip
    div_b2_tip = html.SPAN("Vous pouvez accéder au Wiki par le bouton du menu tout à gauche", Class='tooltiptext')
    div_b2 <= html.BR()
    div_b2 <= div_b2_tip
    div_homepage <= div_b2

    # ==A1==============================

    div_a1 = html.DIV(Class='tooltip')

    id2pseudo = {v: k for k, v in players_dict.items()}

    title11 = html.H4("Statistiques")
    div_a1 <= title11
    ongoing_games = stats_content['ongoing_games']
    active_game_masters = stats_content['active_game_masters']
    active_players = stats_content['active_players']
    most_active_master_id = stats_content['most_active_master']
    most_active_master = id2pseudo[most_active_master_id]
    most_active_player_id = stats_content['most_active_player']
    most_active_player = id2pseudo[most_active_player_id]
    information = f"Il y a {ongoing_games} parties en cours. Il y a {active_game_masters} arbitres en activité. Il y a {active_players} joueurs en activité. L'arbitre le plus actif est {most_active_master}. Le joueur le plus actif est {most_active_player}. (Un joueur ou un arbitre est en activité s'il participe à une partie en cours)"
    div_a1 <= information

    # ----

    div_b1_tip = html.SPAN("Plus de détail dans le menu 'Classement' sous menu 'Joueurs'", Class='tooltiptext')
    div_a1 <= div_b1_tip
    div_homepage <= div_a1

    # ==B1==============================

    # Merged with B2

    # ================================

    # calculate and store time shift with server

    # time on server
    server_time = news_content_table_loaded['server_time']

    # time locally
    local_time = time()

    # difference
    delta_time_sec = round(local_time - server_time)

    # store to be used later on
    storage['DELTA_TIME_SEC'] = str(delta_time_sec)

    # ----

    MY_SUB_PANEL <= div_homepage

    # announce
    for origin in ('ADMIN', 'MODO'):
        for number in range(1, 4):
            if storage[f'ANNOUNCEMENT_{number}_DISPLAYED_{origin}'] == 'no':
                if storage[f'ANNOUNCEMENT_{number}_{origin}']:
                    alert(storage[f'ANNOUNCEMENT_{number}_{origin}'])
                    storage[f'ANNOUNCEMENT_{number}_DISPLAYED_{origin}'] = 'yes'

    if 'PSEUDO' in storage:

        # get the day
        day_now = int(time()) // (3600 * 24)

        # we check new private messages once a day
        day_notified = 0
        if 'DATE_NEW_MESSAGES_NOTIFIED' in storage:
            day_notified = int(storage['DATE_NEW_MESSAGES_NOTIFIED'])
        if day_now > day_notified:
            new_messages = new_private_messages_received()
            if new_messages:
                alert(f"Vous avez {new_messages} nouveau(x) message(s) personnel(s) ! Pour le(s) lire : Menu Messages personnels.")
                storage['DATE_NEW_MESSAGES_NOTIFIED'] = str(day_now)

        # we check email not confirmed once a day
        day_notified = 0
        if 'DATE_CONFIRMATION_MISSING_NOTIFIED' in storage:
            day_notified = int(storage['DATE_CONFIRMATION_MISSING_NOTIFIED'])
        if day_now > day_notified:
            is_confirmed = email_address_is_confirmed()
            if not is_confirmed:
                alert("Votre adresse courriel n'est pas confirmée. Soit elle est en rebond, soit vous ne l'avez pas encore confirmée ! Pour le faire : Menu 'Mon compte' / Sous menu 'Valider mon courriel' / Bouton 'Me renvoyer un nouveau code'.\nCela ne vous empêche pas de rejoindre et jouer des parties sur le site !")
                storage['DATE_CONFIRMATION_MISSING_NOTIFIED'] = str(day_now)

    # RGPD
    if 'RGPD_ACCEPTED' not in storage:
        mydialog.InfoDialog("Information", "Règlement général sur la protection des données :<br>Vous êtes d'accord avec la manière dont le site utilise et conserve vos données personnelles. Si vous ne l'êtes pas, n'utilisez pas le site ! Plus de détail dans la page 'Données personnelles' accessible depuis le menu Accueil.", True)
        storage['RGPD_ACCEPTED'] = 'yes'


RANDOM = common.Random()
PSEUDOS_DEMO = ['one', 'two', 'three', 'four', 'five', 'six', 'seven']
GAME_DEMO = 'partie_demo'


def play_test():
    """ play_test """

    title = html.H3("Tester le jeu dans une partie")
    MY_SUB_PANEL <= title

    if 'PSEUDO' not in storage:
        pseudo = RANDOM.choice(PSEUDOS_DEMO)
        password = pseudo
        MY_SUB_PANEL <= html.DIV(f"Vous n'êtes pas connecté. Connectez-vous (page 'Connexion') par exemple avec le compte '{pseudo}' mot de passe '{password}'", Class='important')
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.DIV("Vous arriverez automatiquement sur la  page 'Mes parties', cliquez alors sur le bouton avec le nom de la partie", Class='important')
        MY_SUB_PANEL <= html.BR()
        return

    pseudo = storage['PSEUDO']
    if pseudo not in PSEUDOS_DEMO:
        alert(f"Vous êtes connecté en tant que '{pseudo}'. Déconnectez-vous (page 'Connexion') et revenez sur cette page")
        return

    MY_SUB_PANEL <= html.DIV(f"Vous êtes connecté '{pseudo}', ce qui est très bien !", Class='important')
    MY_SUB_PANEL <= html.DIV("Allez sur la page 'Mes parties', cliquez alors sur le bouton avec le nom de la partie", Class='important')
    MY_SUB_PANEL <= html.BR()


MIN_CHAT_NUMBER = 100
MAX_CHAT_NUMBER = 999
CHAT_NUMBER = RANDOM.choice(list(range(MIN_CHAT_NUMBER, MAX_CHAT_NUMBER + 1)))


def live_chat():
    """ live_chat """

    def add_chat_callback(ev):  # pylint: disable=invalid-name
        """ add_chat_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de message en ligne : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de message en ligne : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            # back to where we started
            MY_SUB_PANEL.clear()
            live_chat()

        ev.preventDefault()

        content = input_message.value

        if not content:
            alert("Pas de contenu pour ce message !")
            MY_SUB_PANEL.clear()
            live_chat()
            return

        if 'PSEUDO' in storage:
            author = storage['PSEUDO']
        else:
            author = f"anonyme#{CHAT_NUMBER}"

        json_dict = {
            'author': author,
            'content': content,
        }

        host = config.SERVER_CONFIG['EMAIL']['HOST']
        port = config.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/chat-messages"

        # adding a chat : do not need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def chats_reload_callback(ev):  # pylint: disable=invalid-name
        """ chats_reload_callback """

        if ev is not None:
            ev.preventDefault()

        chat_messages = []

        def reply_callback(req):
            nonlocal chat_messages
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des messages en ligne : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des messages en ligne : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            chat_messages = req_result

        json_dict = {}

        host = config.SERVER_CONFIG['EMAIL']['HOST']
        port = config.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/chat-messages"

        # extracting chats : do not need token
        chat_messages = []
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return chat_messages

    title4 = html.H3("Discuter en direct avec des messsages en ligne")
    MY_SUB_PANEL <= title4

    chats = chats_reload_callback(None)
    # there can be no message (if no declaration of failed to load)

    chats_table = html.TABLE()

    thead = html.THEAD()
    for title in ['Date', 'Auteur', 'Contenu']:
        col = html.TD(html.B(title))
        thead <= col
    chats_table <= thead

    for time_stamp, author, content in sorted(chats, key=lambda t: t[0], reverse=True):

        row = html.TR()

        date_desc_gmt = mydatetime.fromtimestamp(time_stamp)
        date_desc_gmt_str = mydatetime.strftime(*date_desc_gmt)
        col = html.TD(f"{date_desc_gmt_str}", Class='text')
        row <= col

        col = html.TD(author, Class='text')
        row <= col

        col = html.TD(Class='text')
        for line in content.split('\n'):
            # new so put in bold
            col <= line
            col <= html.BR()
        row <= col

        chats_table <= row

    # reload

    form1 = html.FORM()
    input_reload_all = html.INPUT(type="submit", value="Recharger les messages", Class='btn-inside')
    input_reload_all.bind("click", chats_reload_callback)
    form1 <= input_reload_all

    # say

    form2 = html.FORM()

    fieldset = html.FIELDSET()
    legend_message = html.LEGEND("Votre message", title="Qu'avez-vous à dire ?")
    fieldset <= legend_message
    input_message = html.TEXTAREA(type="text", rows=4, cols=80)
    fieldset <= input_message
    form2 <= fieldset

    input_say_message = html.INPUT(type="submit", value="Envoyer", Class='btn-inside')
    input_say_message.bind("click", add_chat_callback)
    form2 <= input_say_message

    information1 = html.DIV(Class='important')
    information1 <= "La première vocation de cette petite messagerie est de fournir une aide rapide aux nouveaux arrivants sur le site."

    information2 = html.DIV(Class='note')
    information2 <= "Les messages persistent au moins 24 heures. Cet outil n'a pas destination à remplacer le salon Discord"

    # display items

    MY_SUB_PANEL <= information1
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= information2
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= form1
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= chats_table
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= form2


MAX_LEN_GAME_NAME = 50
MAX_LEN_EMAIL = 100


def declare_incident(json_dict_params):
    """ declare_incident """

    # load previous values if applicable
    pseudo = json_dict_params['pseudo'] if json_dict_params and 'pseudo' in json_dict_params else None
    email = json_dict_params['email'] if json_dict_params and 'email' in json_dict_params else None
    game = json_dict_params['game'] if json_dict_params and 'game' in json_dict_params else None
    description = json_dict_params['description'] if json_dict_params and 'description' in json_dict_params else None

    def get_email_reply_callback(req):
        nonlocal email
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement courriel du compte : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement courriel compte : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        email = req_result['email']

    def submit_incident_callback(ev):  # pylint: disable=invalid-name
        """ submit_incident_callback """

        def submit_incident_reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

        ev.preventDefault()

        # get values from user input
        pseudo = input_pseudo.value
        email = input_email.value
        game = input_game.value
        description = input_description.value

        # make data structure
        json_dict_params = {
            'pseudo': pseudo,
            'email': email,
            'game': game,
            'description': description,
        }

        # start checking data

        if not email:
            alert("Il faut obligatoirement un courriel (pour répondre)")

            # back to where we started
            MY_SUB_PANEL.clear()
            declare_incident(json_dict_params)
            return

        if email.find('@') == -1:
            alert("@ dans courriel manquant")

            # back to where we started
            MY_SUB_PANEL.clear()
            declare_incident(json_dict_params)
            return

        if not description:
            alert("Déclaration vide")

            # back to where we started
            MY_SUB_PANEL.clear()
            declare_incident(json_dict_params)
            return

        subject = f"Déclaration d'incident de la part du site {config.SITE_ADDRESS} (AFJD)"
        body = ""
        body += f"pseudo : {pseudo}"
        body += "\n\n"
        body += f"courriel : {email}"
        body += "\n\n"
        body += f"partie : {game}"
        body += "\n\n"
        body += f"description : {description}"
        body += "\n\n"
        version = storage['VERSION']
        body += f"version : {version}"
        body += "\n\n"
        body += f"config : {user_config.CONFIG}"
        body += "\n\n"

        json_dict = {
            'subject': subject,
            'body': body,
            'reply_to': email,
        }

        host = config.SERVER_CONFIG['EMAIL']['HOST']
        port = config.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/send-email-support"

        # sending email to support : do not need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=submit_incident_reply_callback, ontimeout=common.noreply_callback)

        alert("Votre incident va être examiné dans les plus brefs délais")

        # back to home
        MY_SUB_PANEL.clear()
        show_news()

    # get game if possible
    if not game:
        if 'GAME' in storage:
            game = storage['GAME']

    # get email if possible
    if not pseudo:
        if 'PSEUDO' in storage:

            pseudo = storage['PSEUDO']

            if not email:
                json_dict = {}

                host = config.SERVER_CONFIG['PLAYER']['HOST']
                port = config.SERVER_CONFIG['PLAYER']['PORT']
                url = f"{host}:{port}/players/{pseudo}"

                # reading data about account : need token
                ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=get_email_reply_callback, ontimeout=common.noreply_callback)

    title4 = html.H3("Déclarer un incident")
    MY_SUB_PANEL <= title4

    text21 = html.P("C'est arrivé, le système s'est bloqué ou le résultat n'était pas celui escompté...")
    MY_SUB_PANEL <= text21

    possible_situations = html.UL()
    possible_situations <= html.LI("Vous ne parvenez pas entrer vos ordres et la date limite est ce soir ?")
    possible_situations <= html.LI("Votre partie n'avance pas depuis des jours et il semble que votre arbitre se soit endormi ?")
    possible_situations <= html.LI("Vous n'êtes pas convaincu par les explications de l'arbitre sur la résolution dans la partie ?")
    possible_situations <= html.LI("Vous soupçonnez un joueur d'utiliser plusieurs fois le même compte sur la partie ?")
    possible_situations <= html.LI("Un joueur sur la partie a un comportement antisocial et l'arbitre ne fait rien ?")
    possible_situations <= html.LI("Vous êtes arbitre et un joueur commence sérieusement à vous agacer ?")
    possible_situations <= html.LI("Vous êtes persuadé qu'il y a de la triche quelque part ?")
    MY_SUB_PANEL <= possible_situations

    text22 = html.P(html.EM("Si votre déclaration concerne un retard, il faut vous adresser à l'arbitre de la partie."))
    MY_SUB_PANEL <= text22

    text23 = html.P(html.B("S'il s'agit d'un bug, il est peut-être déjà corrigé, essayez de recharger le cache de votre navigateur au préalable (par exemple en utilisant CTRL+F5 - selon les navigateurs)"))
    MY_SUB_PANEL <= text23

    text23 = html.P(html.B("Si vous préférez une approche plus interactive, vous pouvez utiliser le serveur discord dont le lien est en page d'accueil 'Feedback est support'"))
    MY_SUB_PANEL <= text23

    text25 = html.P("Formulaire de déclaration d'incident :")
    MY_SUB_PANEL <= text25

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_pseudo = html.LEGEND("pseudo (facultatif)", title="Votre pseudo (si applicable)")
    fieldset <= legend_pseudo
    input_pseudo = html.INPUT(type="text", value=pseudo if pseudo is not None else "", Class='btn-inside')
    fieldset <= input_pseudo
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_email = html.LEGEND("courriel (obligatoire)", title="Votre courriel")
    fieldset <= legend_email
    input_email = html.INPUT(type="text", value=email if email is not None else "", size=MAX_LEN_EMAIL, Class='btn-inside')
    fieldset <= input_email
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_game = html.LEGEND("partie (facultatif)", title="La partie (si applicable)")
    fieldset <= legend_game
    input_game = html.INPUT(type="text", value=game if game is not None else "", size=MAX_LEN_GAME_NAME, Class='btn-inside')
    fieldset <= input_game
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_description = html.LEGEND("description", title="Description du problème")
    fieldset <= legend_description
    input_description = html.TEXTAREA(type="text", rows=8, cols=80)
    if description is not None:
        input_description <= description
    fieldset <= input_description
    form <= fieldset

    fieldset = html.FIELDSET()
    fieldset <= "Ne pas utiliser les emoticons et autres caractères ésotériques"
    fieldset <= html.BR()
    fieldset <= "Il est toujours bienvenu de fournir une procédure pour reproduire le problème ainsi que la différence entre le résultat obtenu et le résultat attendu..."
    form <= fieldset

    input_submit_incident = html.INPUT(type="submit", value="Soumettre cet incident", Class='btn-inside')
    input_submit_incident.bind("click", submit_incident_callback)
    form <= input_submit_incident

    MY_SUB_PANEL <= form


def show_personal_data():
    """ show_personal_data """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = "./docs/rgpd.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def show_load_time_version(load_time):
    """ show_load_time_version """

    MY_SUB_PANEL <= html.BR()
    version_value = storage['VERSION']
    MY_SUB_PANEL <= html.I(f"Vous utilisez la version du {version_value}")

    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.I(f"Temps de chargement de la page d'accueil : {load_time:.2f} secs")


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

MY_SUB_PANEL = html.DIV(id="home")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Vue d\'ensemble':
        show_news()
    if item_name == 'Tester le jeu':
        play_test()
    if item_name == 'Discuter en ligne':
        live_chat()
    if item_name == 'Déclarer un incident':
        declare_incident(None)
    if item_name == 'Données personnelles':
        show_personal_data()

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

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

    # this means user wants to join game
    if ARRIVAL == 'RGPD':
        ITEM_NAME_SELECTED = 'Données personnelles'

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
