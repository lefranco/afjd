""" home """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time
import datetime

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import faq
import whynot
import interface
import config
import mapping
import memoize
import common
import selection
import index  # circular import


OPTIONS = ['dernières nouvelles', 'autres liens', 'toutes les parties', 'déclarer un incident', 'foire aux questions', 'pourquoi yapa', 'coin technique', 'choix d\'interface', 'parties sans arbitres']

NOTE_CONTENT_STATED = """Bienvenue dans la première version du site Diplomania.
Information importante : vous visualisez ici une interface au design rustique pour accéder au moteur de jeu.
Merci de nous remonter vos remarques sur le forum de Diplomania (cf accueil/liens) ou sur le serveur Discord."""


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


def get_needing_replacement_games():
    """ get_needing_replacement_games : returns empty list if error or no game"""

    needing_replacement_games_list = []

    def reply_callback(req):
        nonlocal needing_replacement_games_list
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des parties qui ont besoin de remplaçant : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des parties qui ont besoin de remplaçant : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        needing_replacement_games_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games-needing-replacement"

    # getting needing replacement games list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return needing_replacement_games_list


def formatted_news(news_content_loaded, admin):
    """ formatted_news """

    # init
    news_content = html.DIV(Class='news2' if admin else 'news')

    # format
    if news_content_loaded is not None:
        for line in news_content_loaded.split("\n"):
            if line.startswith(".HR"):
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


def show_news():
    """ show_home """

    title = html.H3("Accueil")
    MY_SUB_PANEL <= title

    # ----

    title1 = html.H4("Les parties en souffrance")
    MY_SUB_PANEL <= title1

    suffering_games_loaded = get_needing_replacement_games()
    suffering_games = formatted_games(suffering_games_loaded)
    MY_SUB_PANEL <= suffering_games

    # ----

    title2 = html.H4("Dernières contributions sur les formus", Class='news')
    MY_SUB_PANEL <= title2

    news_forum = html.OBJECT(data="https://diplomania-gen.fr/external_page.php", width="100%", height="300")

    MY_SUB_PANEL <= news_forum

    # ----

    title3 = html.H4("Dernières nouvelles moderateur", Class='news')
    MY_SUB_PANEL <= title3

    news_content_loaded2 = common.get_news_content2()
    news_content2 = formatted_news(news_content_loaded2, False)
    MY_SUB_PANEL <= news_content2

    # ----

    title4 = html.H4("Dernières nouvelles administrateur", Class='news2')
    MY_SUB_PANEL <= title4

    news_content_loaded = common.get_news_content()
    news_content = formatted_news(news_content_loaded, True)
    MY_SUB_PANEL <= news_content

    # ----

    title5 = html.H4("Charte du bon diplomate")
    MY_SUB_PANEL <= title5

    link2 = html.A(href="./docs/charte.pdf", target="_blank")
    link2 <= "Lien vers la charte du bon diplomate"
    MY_SUB_PANEL <= link2

    # ----

    title6 = html.H4("Note importante")
    MY_SUB_PANEL <= title6

    note_bene_content = html.DIV()
    for line in NOTE_CONTENT_STATED.split("\n"):
        note_bene_content <= line
        note_bene_content <= html.BR()
    note_content_table = html.TABLE()
    row = html.TR()
    note_content_table <= row
    col = html.TD(note_bene_content)
    row <= col
    MY_SUB_PANEL <= note_content_table

    # ----

    title8 = html.H4("Divers")
    MY_SUB_PANEL <= title8

    MY_SUB_PANEL <= html.DIV("Pour se creer un compte, utiliser le menu 'mon compte/créer un compte'")
    MY_SUB_PANEL <= html.DIV("Pour les daltoniens, une carte avec des couleurs spécifiques a été créée, allez dans 'accueil/choix d'interface'")
    MY_SUB_PANEL <= html.DIV("Pour avoir les parties dans des onglets séparés sur votre smartphone : utilisez 'basculer en mode liens externes' depuis la page 'mes parties'")
    MY_SUB_PANEL <= html.DIV("Si vous souhaitez être contacté en cas de besoin de remplaçant : modifiez le paramètre de votre compte")
    MY_SUB_PANEL <= html.DIV("Si vous souhaitez entrer des 'faux' ordres (parties sans communication possible) : jouer la partie sélectionnée / taguer")

    # ----
    title9 = html.H4("Statistiques")
    MY_SUB_PANEL <= title9

    stats_content = get_stats_content()
    MY_SUB_PANEL <= f"Il y a {stats_content['ongoing_games']} parties en cours. Il y a {stats_content['active_game_masters']} arbitres en activité. Il y a {stats_content['active_players']} joueurs en activité."


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
        index.load_option(None, 'jouer la partie sélectionnée')

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
        button = html.BUTTON("Basculer en mode liens externes (plus lent mais conserve cette page)")
    else:
        button = html.BUTTON("Basculer en mode boutons (plus rapide mais remplace cette page)")
    button.bind("click", change_button_mode_callback)
    MY_SUB_PANEL <= button
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    games_table = html.TABLE()

    fields = ['name', 'go_game', 'id', 'master', 'variant', 'nopress_game', 'nomessage_game', 'deadline', 'current_advancement']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'go_game': 'aller dans la partie', 'id': 'id', 'master': 'arbitre', 'variant': 'variante', 'nopress_game': 'publics(*)', 'nomessage_game': 'privés(*)', 'deadline': 'date limite', 'current_advancement': 'saison à jouer'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    row = html.TR()
    for field in fields:
        buttons = html.DIV()
        if field in ['name', 'master', 'variant', 'nopress_game', 'nomessage_game', 'deadline', 'current_advancement']:

            if field == 'name':

                # button for sorting by creation date
                button = html.BUTTON("&lt;date de création&gt;")
                button.bind("click", lambda e, f='creation': sort_by_callback(e, f))
                buttons <= button

                # separator
                buttons <= " "

                # button for sorting by name
                button = html.BUTTON("&lt;nom&gt;")
                button.bind("click", lambda e, f='name': sort_by_callback(e, f))
                buttons <= button

            else:

                button = html.BUTTON("<>")
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
    elif sort_by == 'nopress_game':
        def key_function(g): return (g[1]['nopress_game'], g[1]['nopress_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nomessage_game':
        def key_function(g): return (g[1]['nomessage_game'], g[1]['nomessage_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
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
                datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
                deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
                deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"
                deadline_loaded_str = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"
                value = deadline_loaded_str

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
                advancement_season_readable = variant_data.name_table[advancement_season]
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
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
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

    game = ""
    email_loaded = ""
    pseudo = ""

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
    if 'GAME' in storage:
        game = storage['GAME']

    # get email if possible
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

    title5 = html.H4("Règles simplifiées")
    MY_SUB_PANEL <= title5

    link5 = html.A(href="./docs/Summary_rules_fr.pdf", target="_blank")
    link5 <= "Lien vers une version simplifiée des règles du jeu par Edi Birsan"
    MY_SUB_PANEL <= link5

    # --

    title6 = html.H4("Création de fichier de tournoi")
    MY_SUB_PANEL <= title6

    link6 = html.A(href="./docs/Fichier_tournoi.pdf", target="_blank")
    link6 <= "Comment allouer les joueurs dans les parties d'un tournoi (i.e. créer un CSV acceptable sur le site)"
    MY_SUB_PANEL <= link6
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    link7 = html.A(href="./scripts/allocate.py", target="_blank")
    link7 <= "Le script à utiliser pour réaliser cette allocation (lire le document au préalable)"
    MY_SUB_PANEL <= link7

    # --

    title7 = html.H4("Remerciements")
    MY_SUB_PANEL <= title7

    link8 = html.A(href="https://brython.info/", target="_blank")
    link8 <= "Outil utilisé pour ce site web"
    MY_SUB_PANEL <= link8

    MY_SUB_PANEL <= html.P()

    link9 = html.A(href="https://www.flaticon.com/", target="_blank")
    link9 <= "Icônes utilisées pour ce site web"
    MY_SUB_PANEL <= link9


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

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'dernières nouvelles':
        show_news()
    if item_name == 'toutes les parties':
        all_games('en cours')
    if item_name == 'autres liens':
        show_links()
    if item_name == 'déclarer un incident':
        declare_incident()
    if item_name == 'foire aux questions':
        show_faq()
    if item_name == 'pourquoi yapa':
        show_whynot()
    if item_name == 'coin technique':
        show_technical()
    if item_name == 'choix d\'interface':
        select_interface()
    if item_name == 'parties sans arbitres':
        show_no_game_masters_data()

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


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
