""" home """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

import profiler

import json
import time

from browser import html, ajax, alert, document, window  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import user_config
import faq
import whynot
import interface
import mydatetime
import config
import mapping
import memoize
import common
import selection
import scoring
import index  # circular import


OPTIONS = ['Vue d\'ensemble', 'Toutes les parties', 'Déclarer un incident', 'Foire aux questions', 'Pourquoi yapa', 'Coin technique', 'Choix d\'interface', 'Tester un scorage', 'Parties sans arbitres', 'Autres liens', 'Brique sociale']

NOTE_CONTENT_STATED = """Bienvenue dans la première version du site Diplomania.
Information importante : vous visualisez ici une interface au design rustique pour accéder au moteur de jeu.
Merci de nous remonter vos remarques sur le forum ou sur le serveur Discord."""


# for safety
if 'ANNOUNCEMENT' not in storage:
    storage['ANNOUNCEMENT'] = ""
if 'ALREADY_SPAMMED' not in storage:
    storage['ALREADY_SPAMMED'] = 'yes'


def get_all_news_content():
    """ get_all_news_content """

    all_news_content = {}

    def reply_callback(req):
        nonlocal all_news_content
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du contenu des nouvelles (admin+modo) : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du contenu des nouvelles (admin+modo) : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        all_news_content = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/all_news"

    # get news : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return all_news_content


def get_stats_content():
    """ get_stats_content """

    stats_content = {}

    def reply_callback(req):
        nonlocal stats_content
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return stats_content


def get_teaser_content():
    """ get_teaser_content """

    teaser_content = None

    def reply_callback(req):
        nonlocal teaser_content
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return teaser_content


def formatted_news(news_content_loaded, admin):
    """ formatted_news """

    # init
    news_content = html.DIV(Class='news2' if admin else 'news')

    # format
    if news_content_loaded is not None:
        for line in news_content_loaded.split("\n"):
            if line.startswith(".ANNONCE"):
                if admin:
                    _, _, announcement = line.partition(".ANNONCE ")
                    previous_announcement = storage['ANNOUNCEMENT']
                    storage['ANNOUNCEMENT'] = announcement
                    if announcement != previous_announcement:
                        storage['ALREADY_SPAMMED'] = 'no'
            elif line.startswith(".HR"):
                separator = html.HR()
                news_content <= separator
            elif line.startswith(".STRONG"):
                _, _, extracted = line.partition(".STRONG ")
                bold = html.STRONG(extracted)
                news_content <= bold
            elif line.startswith(".KBD"):
                _, _, extracted = line.partition(".KBD ")
                kbd = html.KBD(extracted)
                news_content <= kbd
            elif line.startswith(".LINK"):
                _, _, extracted = line.partition(".LINK ")
                link = html.A(href=extracted, target="_blank")
                link <= extracted
                news_content <= link
            elif line.startswith(".BR"):
                news_content <= html.BR()
            else:
                news_content <= line

    return news_content


def formatted_games(suffering_games):
    """ formatted_games """

    # init
    games_content = html.DIV()

    game_content_table = html.TABLE()
    row = html.TR()
    for game in suffering_games:
        game_content_table <= row
        col = html.TD(game)
        row <= col

    games_content <= game_content_table
    return games_content


def formatted_teaser(teasers):
    """ formatted_teaser """

    # init
    teaser_content = html.DIV(Class='teaser')

    for champion in teasers.split('\n'):
        teaser_content <= champion
        teaser_content <= html.BR()

    return teaser_content


def show_news():
    """ show_home """

    profiler.PROFILER.start_mes("home.show_news()...")

    title = html.H3("Accueil")
    MY_SUB_PANEL <= title
    div_homepage = html.DIV(id='grid')

    # ----
    profiler.PROFILER.start_mes("get stats...")
    stats_content = get_stats_content()
    profiler.PROFILER.stop_mes()
    # ----

    # ----
    profiler.PROFILER.start_mes("parties qui recrutent...")
    div_a5 = html.DIV(Class='tooltip')

    title1 = html.H4("Les parties en cours dans lesquelles il manque un joueur")
    div_a5 <= title1

    suffering_games_loaded = stats_content['suffering_games']
    suffering_games = formatted_games(suffering_games_loaded) if suffering_games_loaded else "Aucune pour le moment. On n'aime pas que les parties restent bloquées longtemps ici ;-)"
    div_a5 <= suffering_games

    div_a5_tip = html.SPAN("Plus de détail dans le menu 'rejoindre une partie'", Class='tooltiptext')
    div_a5 <= div_a5_tip
    div_homepage <= div_a5

    profiler.PROFILER.stop_mes()

    # ----
    profiler.PROFILER.start_mes("meilleurs...")
    div_b5 = html.DIV(Class='tooltip')

    title11 = html.H4("Les meilleurs joueurs du site (d'après le classement ELO)")
    div_b5 <= title11

    teaser_loaded = get_teaser_content()
    teaser = formatted_teaser(teaser_loaded) if teaser_loaded else "Aucun pour le moment."
    div_b5 <= teaser

    div_b5_tip = html.SPAN("Plus de détail dans le menu 'classements'", Class='tooltiptext')
    div_b5 <= div_b5_tip
    div_homepage <= div_b5

    profiler.PROFILER.stop_mes()

    # ----
    profiler.PROFILER.start_mes("evenements ...")
    div_a4 = html.DIV(Class='tooltip')

    title2 = html.H4("Les événements qui recrutent")
    div_a4 <= title2

    news_events = html.OBJECT(data="https://diplomania-gen.fr/events/", width="100%", height="400")
    div_a4 <= news_events

    # no tip
    div_homepage <= div_a4

    profiler.PROFILER.stop_mes()

    # ----
    profiler.PROFILER.start_mes("contributions forum...")
    div_b4 = html.DIV(Class='tooltip')

    title3 = html.H4("Dernières contributions sur les forums")
    div_b4 <= title3

    news_forum = html.OBJECT(data="https://diplomania-gen.fr/external_page.php", width="100%", height="400")
    div_b4 <= news_forum

    # no tip
    div_homepage <= div_b4

    profiler.PROFILER.stop_mes()

    # ----
    profiler.PROFILER.start_mes("get all news...")
    all_news_content_loaded = get_all_news_content()
    profiler.PROFILER.stop_mes()
    # ----

    # ----
    profiler.PROFILER.start_mes("news modo...")
    div_a3 = html.DIV(Class='tooltip')

    title4 = html.H4("Dernières nouvelles moderateur", Class='news')
    div_a3 <= title4

    news_content_loaded2 = all_news_content_loaded['modo']
    news_content2 = formatted_news(news_content_loaded2, False)
    div_a3 <= news_content2

    div_a3_tip = html.SPAN("Vous pouvez contacter le modérateur par un MP sur le forum", Class='tooltiptext')
    div_a3 <= div_a3_tip
    div_homepage <= div_a3

    profiler.PROFILER.stop_mes()

    # ----
    profiler.PROFILER.start_mes("news admin...")
    div_b3 = html.DIV(Class='tooltip')

    title5 = html.H4("Dernières nouvelles administrateur", Class='news2')
    div_b3 <= title5

    news_content_loaded = all_news_content_loaded['admin']
    news_content = formatted_news(news_content_loaded, True)
    div_b3 <= news_content

    div_b3_tip = html.SPAN("Vous pouvez contacter l'administrateur par le menu accueil/déclarer un incident'", Class='tooltiptext')
    div_b3 <= div_b3_tip
    div_homepage <= div_b3

    profiler.PROFILER.stop_mes()

    # ----
    profiler.PROFILER.start_mes("stats...")
    div_a2 = html.DIV(Class='tooltip')

    title9 = html.H4("Statistiques")
    div_a2 <= title9

    ongoing_games = stats_content['ongoing_games']
    active_game_masters = stats_content['active_game_masters']
    active_players = stats_content['active_players']
    div_a2 <= f"Il y a {ongoing_games} parties en cours. Il y a {active_game_masters} arbitres en activité. Il y a {active_players} joueurs en activité."

    div_a2_tip = html.SPAN("Plus de détail dans le menu 'classement/joueurs'", Class='tooltiptext')
    div_a2 <= div_a2_tip
    div_homepage <= div_a2

    profiler.PROFILER.stop_mes()

    # ----
    profiler.PROFILER.start_mes("charte...")
    div_b2 = html.DIV(Class='tooltip')

    title6 = html.H4("Charte du bon diplomate")
    div_b2 <= title6

    link2 = html.A(href="./docs/charte.pdf", target="_blank")
    link2 <= "Lien vers la charte du bon diplomate"
    div_b2 <= link2

    div_b2_tip = html.SPAN("Plus de documents intéressants dans le menu 'accueil/coin technique'", Class='tooltiptext')
    div_b2 <= div_b2_tip
    div_homepage <= div_b2

    profiler.PROFILER.stop_mes()

    # ----
    profiler.PROFILER.start_mes("note importante...")
    div_a1 = html.DIV(Class='tooltip')

    title7 = html.H4("Note importante")
    div_a1 <= title7

    note_bene_content = html.DIV()
    for line in NOTE_CONTENT_STATED.split("\n"):
        note_bene_content <= line
        note_bene_content <= html.BR()
    note_content_table = html.TABLE()
    row = html.TR()
    note_content_table <= row
    col = html.TD(note_bene_content)
    row <= col
    div_a1 <= note_content_table

    div_a1_tip = html.SPAN("Plus de détail dans le menu 'accueil/brique sociale'", Class='tooltiptext')
    div_a1 <= div_a1_tip
    div_homepage <= div_a1

    profiler.PROFILER.stop_mes()

    # ----
    profiler.PROFILER.start_mes("divers...")
    div_b1 = html.DIV(Class='tooltip')

    title8 = html.H4("Divers")
    div_b1 <= title8

    div_b1 <= html.DIV("Pour se creer un compte, utiliser le menu 'mon compte/créer un compte'")
    div_b1 <= html.DIV("Il faut toujours cocher 'd\'accord pour résoudre pour que la partie avance")
    div_b1 <= html.DIV("Pour les daltoniens, une carte avec des couleurs spécifiques a été créée, allez dans 'accueil/choix d'interface'")
    div_b1 <= html.DIV("Pour avoir les parties dans des onglets séparés sur votre smartphone : utilisez 'basculer en mode liens externes' depuis la page 'mes parties'")
    div_b1 <= html.DIV("Si vous souhaitez être contacté en cas de besoin de remplaçant : modifiez le paramètre de votre compte")
    div_b1 <= html.DIV("Si vous souhaitez entrer des 'faux' ordres (parties sans communication possible) : jouer la partie sélectionnée / taguer")
    div_b1 <= html.DIV("Si vous souhaitez créer plusieurs parties par batch contactez l'administrateur pour obtenir les droits")

    div_b1_tip = html.SPAN("Plus de détail dans le menu 'accueil/foire aux question'", Class='tooltiptext')
    div_b1 <= div_b1_tip
    div_homepage <= div_b1

    profiler.PROFILER.stop_mes()

    # ----
    profiler.PROFILER.start_mes("spam")
    MY_SUB_PANEL <= div_homepage

    # announce
    if storage['ALREADY_SPAMMED'] == 'no':
        announcement = storage['ANNOUNCEMENT']
        if announcement:
            alert(announcement)
        storage['ALREADY_SPAMMED'] = 'yes'

    profiler.PROFILER.stop_mes()
    profiler.PROFILER.stop_mes()


def all_games(state_name):
    """all_games """

    def select_game_callback(_, game_name, game_data_sel):
        """ select_game_callback """

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        InfoDialog("OK", f"Partie sélectionnée : {game_name} - cette information est rappelée en bas de la page", remove_after=config.REMOVE_AFTER)
        selection.show_game_selected()

        # action of going to game page
        index.load_option(None, 'Jouer la partie sélectionnée')

    def again(state_name):
        """ again """
        MY_SUB_PANEL.clear()
        all_games(state_name)

    def change_button_mode_callback(_):
        if storage['GAME_ACCESS_MODE'] == 'button':
            storage['GAME_ACCESS_MODE'] = 'link'
        else:
            storage['GAME_ACCESS_MODE'] = 'button'
        MY_SUB_PANEL.clear()
        all_games(state_name)

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by != storage['SORT_BY_HOME']:
            storage['SORT_BY_HOME'] = new_sort_by
            storage['REVERSE_NEEDED_HOME'] = str(False)
        else:
            storage['REVERSE_NEEDED_HOME'] = str(not bool(storage['REVERSE_NEEDED_HOME'] == 'True'))

        MY_SUB_PANEL.clear()
        all_games(state_name)

    overall_time_before = time.time()

    # title
    title = html.H3(f"Parties dans l'état: {state_name}")
    MY_SUB_PANEL <= title

    state = config.STATE_CODE_TABLE[state_name]

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # get the players (masters)
    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire des joueurs")
        return

    # get the link (allocations) of game masters
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return
    masters_alloc = allocations_data['game_masters_dict']

    # fill table game -> master
    game_master_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            game_master_dict[game] = master

    time_stamp_now = time.time()

    # button for switching mode
    if 'GAME_ACCESS_MODE' not in storage:
        storage['GAME_ACCESS_MODE'] = 'button'
    if storage['GAME_ACCESS_MODE'] == 'button':
        button = html.BUTTON("Basculer en mode liens externes (plus lent mais conserve cette page)", Class='btn-menu')
    else:
        button = html.BUTTON("Basculer en mode boutons (plus rapide mais remplace cette page)", Class='btn-menu')
    button.bind("click", change_button_mode_callback)
    MY_SUB_PANEL <= button
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    games_table = html.TABLE()

    fields = ['name', 'go_game', 'id', 'master', 'variant', 'used_for_elo', 'nopress_game', 'nomessage_game', 'deadline', 'current_advancement']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'go_game': 'aller dans la partie', 'id': 'id', 'master': 'arbitre', 'variant': 'variante', 'used_for_elo': 'elo', 'nopress_game': 'publics(*)', 'nomessage_game': 'privés(*)', 'deadline': 'date limite', 'current_advancement': 'saison à jouer'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    row = html.TR()
    for field in fields:
        buttons = html.DIV()
        if field in ['name', 'master', 'variant', 'used_for_elo', 'nopress_game', 'nomessage_game', 'deadline', 'current_advancement']:

            if field == 'name':

                # button for sorting by creation date
                button = html.BUTTON("&lt;date de création&gt;", Class='btn-menu')
                button.bind("click", lambda e, f='creation': sort_by_callback(e, f))
                buttons <= button

                # separator
                buttons <= " "

                # button for sorting by name
                button = html.BUTTON("&lt;nom&gt;", Class='btn-menu')
                button.bind("click", lambda e, f='name': sort_by_callback(e, f))
                buttons <= button

            else:

                button = html.BUTTON("<>", Class='btn-menu')
                button.bind("click", lambda e, f=field: sort_by_callback(e, f))
                buttons <= button

        col = html.TD(buttons)
        row <= col
    games_table <= row

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    number_games = 0

    # default
    if 'SORT_BY_HOME' not in storage:
        storage['SORT_BY_HOME'] = 'creation'
    if 'REVERSE_NEEDED_HOME' not in storage:
        storage['REVERSE_NEEDED_HOME'] = str(False)

    sort_by = storage['SORT_BY_HOME']
    reverse_needed = bool(storage['REVERSE_NEEDED_HOME'] == 'True')

    if sort_by == 'creation':
        def key_function(g): return int(g[0])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'name':
        def key_function(g): return g[1]['name'].upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'master':
        def key_function(g): return game_master_dict.get(g[1]['name'], '').upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'variant':
        def key_function(g): return g[1]['variant']  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'used_for_elo':
        def key_function(g): return int(g[1]['used_for_elo'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nopress_game':
        def key_function(g): return (int(g[1]['nopress_game']), int(g[1]['nopress_current']))  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nomessage_game':
        def key_function(g): return (int(g[1]['nomessage_game']), int(g[1]['nomessage_current']))  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    else:
        def key_function(g): return int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

    for game_id_str, data in sorted(games_dict.items(), key=key_function, reverse=reverse_needed):

        if data['current_state'] != state:
            continue

        number_games += 1

        game_id = int(game_id_str)

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content

        if variant_name_loaded in memoize.VARIANT_CONTENT_MEMOIZE_TABLE:
            variant_content_loaded = memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded]
        else:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                return
            memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded] = variant_content_loaded

        # selected interface (user choice)
        interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

        # parameters

        if (variant_name_loaded, interface_chosen) in memoize.PARAMETERS_READ_MEMOIZE_TABLE:
            parameters_read = memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)]
        else:
            parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)
            memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)] = parameters_read

        # build variant data

        variant_name_loaded_str = str(variant_name_loaded)
        if (variant_name_loaded_str, interface_chosen) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
            variant_data = memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)]
        else:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)] = variant_data

        data['go_game'] = None
        data['id'] = None
        data['master'] = None

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None
            game_name = data['name']

            if field == 'name':
                value = game_name

            if field == 'go_game':
                if storage['GAME_ACCESS_MODE'] == 'button':
                    form = html.FORM()
                    input_jump_game = html.INPUT(type="image", src="./images/play.png")
                    input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: select_game_callback(e, gn, gds))
                    form <= input_jump_game
                    value = form
                else:
                    img = html.IMG(src="./images/play.png")
                    link = html.A(href=f"?game={game_name}", target="_blank")
                    link <= img
                    value = link

            if field == 'id':
                value = game_id

            if field == 'used_for_elo':
                value = "Oui" if value else "Non"

            if field == 'master':
                game_name = data['name']
                # some games do not have a game master
                master_name = game_master_dict.get(game_name, '')
                value = master_name

            if field == 'nopress_game':
                value1 = value
                value2 = data['nopress_current']
                if value2 == value1:
                    value = "Non" if value1 else "Oui"
                else:
                    value1 = "Non" if value1 else "Oui"
                    value2 = "Non" if value2 else "Oui"
                    value = f"{value1} ({value2})"

            if field == 'nomessage_game':
                value1 = value
                value2 = data['nomessage_current']
                if value2 == value1:
                    value = "Non" if value1 else "Oui"
                else:
                    value1 = "Non" if value1 else "Oui"
                    value2 = "Non" if value2 else "Oui"
                    value = f"{value1} ({value2})"

            if field == 'deadline':
                deadline_loaded = value
                datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
                datetime_deadline_loaded_str = mydatetime.strftime2(*datetime_deadline_loaded)
                value = datetime_deadline_loaded_str

                time_unit = 60 if data['fast'] else 60 * 60
                approach_duration = 24 * 60 * 60

                # we are after deadline + grace
                if time_stamp_now > deadline_loaded + time_unit * data['grace_duration']:
                    colour = config.PASSED_GRACE_COLOUR
                # we are after deadline
                elif time_stamp_now > deadline_loaded:
                    colour = config.PASSED_DEADLINE_COLOUR
                # deadline is today
                elif time_stamp_now > deadline_loaded - approach_duration:
                    colour = config.APPROACHING_DEADLINE_COLOUR

            if field == 'current_advancement':
                advancement_loaded = value
                advancement_season, advancement_year = common.get_season(advancement_loaded, variant_data)
                advancement_season_readable = variant_data.season_name_table[advancement_season]
                value = f"{advancement_season_readable} {advancement_year}"

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        games_table <= row

    MY_SUB_PANEL <= games_table
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("Les icônes suivants sont cliquables pour aller dans ou agir sur les parties :", Class='note')
    MY_SUB_PANEL <= html.IMG(src="./images/play.png", title="Pour aller dans la partie")
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("(*) Messagerie possible sur la partie, si le paramètre applicable actuellement est différent (partie terminée) il est indiqué entre parenthèses", Class='note')
    MY_SUB_PANEL <= html.BR()

    # get GMT date and time
    time_stamp = time.time()
    date_now_gmt = mydatetime.fromtimestamp(time_stamp)
    date_now_gmt_str = mydatetime.strftime(*date_now_gmt)
    special_info = html.DIV(f"Pour information, date et heure actuellement : {date_now_gmt_str}")
    MY_SUB_PANEL <= special_info
    MY_SUB_PANEL <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed} avec {number_games} partie(s)"
    if number_games:
        stats += f" soit {elapsed/number_games} par partie"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')
    MY_SUB_PANEL <= html.BR()

    for other_state_name in config.STATE_CODE_TABLE:

        if other_state_name != state_name:

            input_change_state = html.INPUT(type="submit", value=other_state_name)
            input_change_state.bind("click", lambda _, s=other_state_name: again(s))

            MY_SUB_PANEL <= input_change_state
            MY_SUB_PANEL <= html.BR()
            MY_SUB_PANEL <= html.BR()


MAX_LEN_GAME_NAME = 50
MAX_LEN_EMAIL = 100


def declare_incident():
    """ declare_incident """

    email_loaded = ""

    def reply_callback(req):
        nonlocal email_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement courriel du compte : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement courriel compte : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        email_loaded = req_result['email']

    def submit_incident_callback(_):
        """ submit_incident_callback """

        def submit_incident_reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

        subject = "Déclaration d'incident de la part du site https://diplomania-gen.fr (AFJD)"
        body = ""
        body += f"pseudo : {input_pseudo.value}"
        body += "\n\n"
        body += f"courriel : {input_email.value}"
        body += "\n\n"
        body += f"partie : {input_game.value}"
        body += "\n\n"
        body += f"description : {input_description.value}"
        body += "\n\n"
        version = storage['VERSION']
        body += f"version : {version}"
        body += "\n\n"
        body += f"config : {user_config.CONFIG}"
        body += "\n\n"

        json_dict = {
            'subject': subject,
            'body': body,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-support"

        # sending email to support : do not need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=submit_incident_reply_callback, ontimeout=common.noreply_callback)

        alert("Votre incident va être examiné dans les plus brefs délais")

        # back to where we started
        MY_SUB_PANEL.clear()
        declare_incident()

    # get game if possible
    game = ""
    if 'GAME' in storage:
        game = storage['GAME']

    # get email if possible
    pseudo = ""
    if 'PSEUDO' in storage:

        pseudo = storage['PSEUDO']

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"

        # reading data about account : need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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

    text22 = html.P("S'il s'agit d'un bug, il est peut-être déjà corrigé, essayez de recharger le cache de votre navigateur au préalable (par exemple en utilisant CTRL+F5 - selon les navigateurs)")
    MY_SUB_PANEL <= text22

    text23 = html.P("Vous pouvez utiliser le formulaire ci-dessous pour déclarer un incident :")
    MY_SUB_PANEL <= text23

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_pseudo = html.LEGEND("pseudo (facultatif)", title="Votre pseudo (si applicable)")
    fieldset <= legend_pseudo
    input_pseudo = html.INPUT(type="text", value=pseudo)
    fieldset <= input_pseudo
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_email = html.LEGEND("courriel (facultatif mais bienvenu pour répondre facilement)", title="Votre courriel (si pas de pseudo)")
    fieldset <= legend_email
    input_email = html.INPUT(type="text", value=email_loaded, size=MAX_LEN_EMAIL)
    fieldset <= input_email
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_game = html.LEGEND("partie (facultatif)", title="La partie (si applicable)")
    fieldset <= legend_game
    input_game = html.INPUT(type="text", value=game, size=MAX_LEN_GAME_NAME)
    fieldset <= input_game
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_description = html.LEGEND("description", title="Description du problème")
    fieldset <= legend_description
    input_description = html.TEXTAREA(type="text", rows=8, cols=80)
    fieldset <= input_description
    form <= fieldset

    fieldset = html.FIELDSET()
    fieldset <= "Il est toujours bienvenu de fournir une procédure pour reproduire le problème ainsi que la différence entre le résultat obtenu et le résultat attendu..."
    form <= fieldset

    input_submit_incident = html.INPUT(type="submit", value="soumettre l'incident")
    input_submit_incident.bind("click", submit_incident_callback)
    form <= input_submit_incident

    MY_SUB_PANEL <= form


FAQ_DISPLAYED_TABLE = {k: False for k in faq.FAQ_CONTENT_TABLE}
FAQ_CONTENT = html.DIV("faq")


def show_faq():
    """ show_faq """

    def reveal_callback(_, question):
        """ reveal_callback """

        FAQ_DISPLAYED_TABLE[question] = not FAQ_DISPLAYED_TABLE[question]
        MY_SUB_PANEL.clear()
        show_faq()

    title1 = html.H3("Foire aux questions")
    MY_SUB_PANEL <= title1

    FAQ_CONTENT.clear()

    for question_txt, answer_txt in faq.FAQ_CONTENT_TABLE.items():

        reveal_button = html.INPUT(type="submit", value=question_txt)
        reveal_button.bind("click", lambda e, q=question_txt: reveal_callback(e, q))
        FAQ_CONTENT <= reveal_button

        if FAQ_DISPLAYED_TABLE[question_txt]:

            faq_elt = html.DIV(answer_txt)
            FAQ_CONTENT <= faq_elt

        FAQ_CONTENT <= html.P()

    MY_SUB_PANEL <= FAQ_CONTENT


WHYNOT_DISPLAYED_TABLE = {k: False for k in whynot.WHYNOT_CONTENT_TABLE}
WHYNOT_CONTENT = html.DIV("faq")


def show_whynot():
    """ show_whynot """

    def reveal_callback(_, question):
        """ reveal_callback """

        WHYNOT_DISPLAYED_TABLE[question] = not WHYNOT_DISPLAYED_TABLE[question]
        MY_SUB_PANEL.clear()
        show_whynot()

    title1 = html.H3("Pourquoi c'est pas comme ça ?")
    MY_SUB_PANEL <= title1

    WHYNOT_CONTENT.clear()

    for question_txt, answer_txt in whynot.WHYNOT_CONTENT_TABLE.items():

        reveal_button = html.INPUT(type="submit", value=question_txt)
        reveal_button.bind("click", lambda e, q=question_txt: reveal_callback(e, q))
        WHYNOT_CONTENT <= reveal_button

        if WHYNOT_DISPLAYED_TABLE[question_txt]:

            whynot_elt = html.DIV(answer_txt)
            WHYNOT_CONTENT <= whynot_elt

        WHYNOT_CONTENT <= html.P()

    MY_SUB_PANEL <= WHYNOT_CONTENT


def show_technical():
    """ show_technical """

    title = html.H3("Coin technique")
    MY_SUB_PANEL <= title

    title1 = html.H4("Règles du jeu officielles")
    MY_SUB_PANEL <= title1

    link1 = html.A(href="https://media.wizards.com/2015/rules/diplomacy_rules.pdf", target="_blank")
    MY_SUB_PANEL <= link1
    link1 <= "Lien vers les règles officielles du jeu"

    # --

    title2 = html.H4("Algorithme de résolution (D.A.T.C.)")
    MY_SUB_PANEL <= title2

    link2 = html.A(href="http://web.inter.nl.net/users/L.B.Kruijswijk/", target="_blank")
    link2 <= "Lien vers une description technique de l'algorithme de résolution utilisé"
    MY_SUB_PANEL <= link2

    # --

    title3 = html.H4("Choix d'implémentation")
    MY_SUB_PANEL <= title3

    link3 = html.A(href="./docs/Compl_en.pdf", target="_blank")
    link3 <= "Lien vers les choix de comportement pour le moteur de résolution"
    MY_SUB_PANEL <= link3

    # --

    title4 = html.H4("Le scorage (la marque sur un tournoi)")
    MY_SUB_PANEL <= title4

    link4 = html.A(href="./docs/Scorings.pdf", target="_blank")
    link4 <= "Lien vers les spécifications des systèmes de scorage sur le site"
    MY_SUB_PANEL <= link4

    # --

    title5 = html.H4("Le calcul du ELO")
    MY_SUB_PANEL <= title5

    link5 = html.A(href="./docs/calcul_elo.pdf", target="_blank")
    link5 <= "Lien vers les spécifications du calcul du ELO sur le site"
    MY_SUB_PANEL <= link5
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    link6 = html.A(href="https://towardsdatascience.com/developing-a-generalized-elo-rating-system-for-multiplayer-games-b9b495e87802", target="_blank")
    link6 <= "Lien vers la source d'inspiration pour le calcul du ELO sur le site"
    MY_SUB_PANEL <= link6

    # --

    title6 = html.H4("Règles simplifiées")
    MY_SUB_PANEL <= title6

    link7 = html.A(href="./docs/Summary_rules_fr.pdf", target="_blank")
    link7 <= "Lien vers une version simplifiée des règles du jeu par Edi Birsan"
    MY_SUB_PANEL <= link7

    # --

    title7 = html.H4("Création de fichier de tournoi")
    MY_SUB_PANEL <= title7

    link8 = html.A(href="./docs/Fichier_tournoi.pdf", target="_blank")
    link8 <= "Comment allouer les joueurs dans les parties d'un tournoi (i.e. créer un CSV acceptable sur le site)"
    MY_SUB_PANEL <= link8
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    link8 = html.A(href="./scripts/allocate.py", target="_blank")
    link8 <= "Le script à utiliser pour réaliser cette allocation (lire le document au préalable)"
    MY_SUB_PANEL <= link8

    # --

    title7 = html.H4("Remerciements")
    MY_SUB_PANEL <= title7

    link9 = html.A(href="https://brython.info/", target="_blank")
    link9 <= "Outil utilisé pour ce site web"
    MY_SUB_PANEL <= link9

    MY_SUB_PANEL <= html.P()

    link10 = html.A(href="https://www.flaticon.com/", target="_blank")
    link10 <= "Icônes utilisées pour ce site web"
    MY_SUB_PANEL <= link10


def select_interface():
    """ select_interface """

    variant_name_loaded = None

    def select_interface_callback(_, user_interface):
        """ select_interface_callback """

        interface.set_interface(variant_name_loaded, user_interface)
        InfoDialog("OK", f"Interface sélectionnée pour la variante {variant_name_loaded} : {user_interface}", remove_after=config.REMOVE_AFTER)

        # we do not go back to where we started
        # this is intended otherwise the new maps are not active

    title1 = html.H3("Choix d'interface")
    MY_SUB_PANEL <= title1

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable (pour la variante)")
        return

    if 'GAME_VARIANT' not in storage:
        alert("ERREUR : variante introuvable")
        return

    variant_name_loaded = storage['GAME_VARIANT']

    information = html.DIV(Class='important')
    information <= "Une 'interface' vous permet d'avoir une carte et des trigrammes de désignation des régions spécifiques c'est-à-dire différents de ceux pratiqués sur le site"
    MY_SUB_PANEL <= information
    MY_SUB_PANEL <= html.BR()

    select_table = html.TABLE()

    for user_interface in interface.INTERFACE_TABLE[variant_name_loaded]:

        # get description
        with open(f"./variants/{variant_name_loaded}/{user_interface}/README", "r", encoding="utf-8") as file_ptr:
            lines = file_ptr.readlines()
        description = html.DIV(Class='note')
        for line in lines:
            description <= line
            description <= html.BR()

        form = html.FORM()
        fieldset = html.FIELDSET()
        legend_display = html.LEGEND(user_interface, title=description)
        fieldset <= legend_display
        form <= fieldset

        fieldset = html.FIELDSET()
        fieldset <= description
        form <= fieldset

        form <= html.BR()

        input_select_interface = html.INPUT(type="submit", value="sélectionner cette interface")
        input_select_interface.bind("click", lambda e, i=user_interface: select_interface_callback(e, i))
        form <= input_select_interface

        col = html.TD()
        col <= form
        col <= html.BR()

        row = html.TR()
        row <= col

        select_table <= row

    MY_SUB_PANEL <= select_table


RATING_TABLE = {}


def test_scoring():
    """ test_scoring """

    def test_scoring_callback(_, game_scoring, ratings_input):
        """ test_scoring_callback """

        for name, element in ratings_input.items():
            val = 0
            try:
                val = int(element.value)
            except:  # noqa: E722 pylint: disable=bare-except
                pass
            RATING_TABLE[name] = val

        # scoring
        solo_threshold = variant_data.number_centers() // 2
        score_table = scoring.scoring(game_scoring, solo_threshold, RATING_TABLE)

        score_desc = "\n".join([f"{k} : {v} points" for k, v in score_table.items()])
        alert(f"Dans cette configuration la marque est :\n{score_desc}")

        # back to where we started
        MY_SUB_PANEL.clear()
        test_scoring()

    # title
    title = html.H3("Test de scorage")
    MY_SUB_PANEL <= title

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    game_parameters_loaded = common.game_parameters_reload(game)

    variant_name_loaded = storage['GAME_VARIANT']

    # from variant name get variant content
    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)

    # selected interface (user choice)
    interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

    # from display chose get display parameters
    interface_parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, interface_parameters_read)

    # this comes from game
    game_scoring = game_parameters_loaded['scoring']

    form = html.FORM()

    title_enter_centers = html.H4("Entrer les nombre de centres")
    form <= title_enter_centers

    ratings_input = {}
    for num, role in variant_data.roles.items():

        if num == 0:
            continue

        role_name = variant_data.role_name_table[role]

        fieldset = html.FIELDSET()
        legend_centers = html.LEGEND(role_name, title="nombre de centres")
        fieldset <= legend_centers
        input_centers = html.INPUT(type="number", value=str(RATING_TABLE[role_name]) if role_name in RATING_TABLE else "")
        fieldset <= input_centers
        form <= fieldset

        ratings_input[role_name] = input_centers

    # get scoring name
    name2code = {v: k for k, v in config.SCORING_CODE_TABLE.items()}
    scoring_name = name2code[game_scoring]

    form <= html.DIV(f"Pour cette partie le scorage est {scoring_name}", Class='note')
    form <= html.BR()

    input_test_scoring = html.INPUT(type="submit", value="calculer le scorage")
    input_test_scoring.bind("click", lambda e, gs=game_scoring, ri=ratings_input: test_scoring_callback(e, gs, ri))
    form <= input_test_scoring

    MY_SUB_PANEL <= form


def show_no_game_masters_data():
    """ show_no_game_masters_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # get the players (masters)
    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    masters_alloc = allocations_data['game_masters_dict']
    games_with_master = []
    for load in masters_alloc.values():
        games_with_master += load

    no_game_masters_table = html.TABLE()

    fields = ['game']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'game': 'partie'}[field]
        col = html.TD(field_fr)
        thead <= col
    no_game_masters_table <= thead

    for identifier, data in sorted(games_dict.items(), key=lambda g: g[1]['name'].upper()):

        if int(identifier) in games_with_master:
            continue

        row = html.TR()
        value = data['name']
        col = html.TD(value)
        row <= col
        no_game_masters_table <= row

    MY_SUB_PANEL <= html.H3("Les parties sans arbitre")
    MY_SUB_PANEL <= no_game_masters_table


def show_links():
    """ show_links """

    title = html.H3("Autres liens")
    MY_SUB_PANEL <= title

    # ----

    title2 = html.H4("Parrainage")
    MY_SUB_PANEL <= title2

    link2 = html.A(href="https://www.helloasso.com/associations/association-francophone-des-joueurs-de-diplomacy/collectes/diplomania-fr-le-site-open-source", target="_blank")
    link2 <= "Participer au financement du développement du site"
    MY_SUB_PANEL <= link2

    # ----

    title3 = html.H4("Tutoriel youtube")
    MY_SUB_PANEL <= title3

    link3 = html.A(href="https://youtu.be/luOiAz9i7Ls", target="_blank")
    link3 <= "Si vous comprenez rien à ce site, ce tutoriel va vous éclairer sur les points essentiels..."
    MY_SUB_PANEL <= link3

    # ----

    title4 = html.H4("Document d'interface de l'API")
    MY_SUB_PANEL <= title4

    link4 = html.A(href="https://afjdserveurressources.wordpress.com/", target="_blank")
    link4 <= "Si vous voulez vous aussi développer votre front end..."
    MY_SUB_PANEL <= link4


def social():
    """ social """

    # load social directly

    # use button
    button = html.BUTTON("Lancement du la brique sociale", id='social_link')
    MY_SUB_PANEL <= button
    button.bind("click", lambda e: window.open("https://www.diplomania.fr/"))
    document['social_link'].click()


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

MY_SUB_PANEL = html.DIV(id="lists")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    profiler.PROFILER.start_mes("home.load_option()...")

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Vue d\'ensemble':
        show_news()
    if item_name == 'Toutes les parties':
        all_games('en cours')
    if item_name == 'Déclarer un incident':
        declare_incident()
    if item_name == 'Foire aux questions':
        show_faq()
    if item_name == 'Pourquoi yapa':
        show_whynot()
    if item_name == 'Coin technique':
        show_technical()
    if item_name == 'Choix d\'interface':
        select_interface()
    if item_name == 'Tester un scorage':
        test_scoring()
    if item_name == 'Parties sans arbitres':
        show_no_game_masters_data()
    if item_name == 'Autres liens':
        show_links()
    if item_name == 'Brique sociale':
        social()

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

    profiler.PROFILER.stop_mes()


def render(panel_middle):
    """ render """

    profiler.PROFILER.start_mes("home.render()...")

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL

    profiler.PROFILER.stop_mes()
