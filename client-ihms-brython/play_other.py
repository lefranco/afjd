""" play """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

import json

from browser import html, ajax, alert, window, document   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import mydialog
import config
import common
import sandbox
import mapping
import moderate
import index  # circular import

import play  # circular import
import play_low


class MessageTypeEnum:
    """ MessageTypeEnum """

    TEXT = 1
    SEASON = 2
    DROPOUT = 3


def readable_season(advancement):
    """ readable_season """

    advancement_season, advancement_year = common.get_season(advancement, play_low.VARIANT_DATA)
    advancement_season_readable = play_low.VARIANT_DATA.season_name_table[advancement_season]
    value = f"{advancement_season_readable} {advancement_year}"
    return value


def get_game_master(game_id):
    """ get_game_master """

    # get the link (allocations) of game masters
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return None

    masters_alloc = allocations_data['game_masters_dict']

    # get the game it self
    for master_id, games_id in masters_alloc.items():
        if game_id in games_id:
            for pseudo, identifier in play_low.PLAYERS_DICT.items():
                if str(identifier) == master_id:
                    return pseudo

    return None


def date_last_visit_update(game_id, role_id, visit_type):
    """ date_last_visit_update """

    def reply_callback(req):
        req_result = json.loads(req.text)
        if req.status != 201:
            if 'message' in req_result:
                alert(f"Erreur à la mise à jour de la dernière visite de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la mise à jour de la dernière visite de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

    json_dict = {
        'role_id': role_id,
    }

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-visits/{game_id}/{visit_type}"

    # putting visit in a game : need token
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


def join_game():
    """ join_game_action : the third way of joining a game (by a link) """

    def reply_callback(req):

        req_result = json.loads(req.text)
        if req.status != 201:
            if 'message' in req_result:
                alert(f"Erreur à l'inscription à la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à l'inscription à la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        messages = "<br>".join(req_result['msg'].split('\n'))
        common.info_dialog(f"Vous avez rejoint la partie : {messages}")

    if play_low.PSEUDO is None:
        alert("Il faut se connecter au préalable")
        return

    pseudo = play_low.PSEUDO

    if play_low.GAME_ID is None:
        alert("Problème avec la partie")
        return

    game_id = play_low.GAME_ID

    json_dict = {
        'game_id': game_id,
        'player_pseudo': pseudo,
        'delete': 0
    }

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/allocations"

    # adding allocation : need a token
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


def game_incidents_reload(game_id):
    """ game_incidents_reload """

    incidents = []

    def reply_callback(req):
        nonlocal incidents
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des incidents retards de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des incidents retards de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        incidents = req_result['incidents']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-incidents/{game_id}"

    # extracting incidents from a game : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return incidents


def game_incidents2_reload(game_id):
    """ game_incidents2_reload """

    incidents = []

    def reply_callback(req):
        nonlocal incidents
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des incidents désordres civils  de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des incidents désordres civils de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        incidents = req_result['incidents']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-incidents2/{game_id}"

    # extracting incidents from a game : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return incidents


def game_note_reload(game_id):
    """ game_note_reload """

    content = None

    def reply_callback(req):
        nonlocal content
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des notes de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des notes de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        content = req_result['content']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-notes/{game_id}"

    # extracting vote from a game : need token (or not?)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return content


def non_playing_information():
    """ non_playing_information """

    # need to be connected
    if play_low.PSEUDO is None:
        return None

    # is game anonymous
    if not (moderate.check_modo(play_low.PSEUDO) or play_low.ROLE_ID == 0 or not play_low.GAME_PARAMETERS_LOADED['anonymous']):
        return None

    id2pseudo = {v: k for k, v in play_low.PLAYERS_DICT.items()}

    dangling_players = [p for p, d in play_low.GAME_PLAYERS_DICT.items() if d == - 1]
    if not dangling_players:
        return None

    info = "Les pseudos suivants sont alloués à la partie sans rôle : "
    for dangling_player_id_str in dangling_players:
        dangling_player_id = int(dangling_player_id_str)
        dangling_player = id2pseudo[dangling_player_id]
        info += f"{dangling_player} "

    return html.EM(info)


def show_position(direct_last_moves):
    """ show_position """

    position_data = None
    adv_last_moves = None
    fake_report_loaded = None

    def callback_refresh(_):
        """ callback_refresh """

        game_parameters_loaded = common.game_parameters_reload(play_low.GAME)
        if not game_parameters_loaded:
            alert("Erreur chargement paramètres")
            return

        if game_parameters_loaded['current_advancement'] == play_low.GAME_PARAMETERS_LOADED['current_advancement']:
            # no change it seeems
            common.info_dialog("Rien de nouveau sous le soleil !")
            return

        alert("La position de la partie a changé !")
        play_low.load_dynamic_stuff()
        play_low.MY_SUB_PANEL.clear()
        play.load_option(None, 'Consulter')

    def callback_export_sandbox(_):
        """ callback_export_sandbox """

        # action on importing game
        sandbox.import_position(play_low.POSITION_DATA)

        # action of going to sandbox page
        index.load_option(None, 'Bac à sable')

    def callback_export_game_json(_):
        """ callback_export_game_json """

        json_return_dict = None

        def reply_callback(req):
            nonlocal json_return_dict
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de l'export json de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de l'export json de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return
            json_return_dict = req_result['content']
            json_text = json.dumps(json_return_dict, indent=4, ensure_ascii=False)

            # needed too for some reason
            play_low.MY_SUB_PANEL <= html.A(id='download_link')

            # perform actual exportation
            text_file_as_blob = window.Blob.new([json_text], {'type': 'text/plain'})
            download_link = document['download_link']
            download_link.download = f"diplomania_{play_low.GAME}_{play_low.GAME_ID}_json.txt"
            download_link.href = window.URL.createObjectURL(text_file_as_blob)
            document['download_link'].click()

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-export/{play_low.GAME_ID}"

        # getting game json export : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return True

    def transition_display_callback(_, advancement_selected):

        nonlocal position_data
        nonlocal fake_report_loaded

        def callback_render(_):
            """ callback_render """

            # since orders are part of the data not save/restore context

            # put the background map first
            ctx.drawImage(img, 0, 0)

            # put the centers
            play_low.VARIANT_DATA.render(ctx)

            # put the position
            position_data.render(ctx)

            # put the legends at the end
            play_low.VARIANT_DATA.render_legends(ctx)

            # put the orders (if history)
            if orders_data:
                orders_data.render(ctx)

        # current position is default
        orders_loaded = None
        fake_report_loaded = play_low.REPORT_LOADED
        position_data = play_low.POSITION_DATA
        orders_data = None

        if advancement_selected != last_advancement:

            transition_loaded = play_low.game_transition_reload(play_low.GAME_ID, advancement_selected)

            if transition_loaded:

                # retrieve stuff from history
                time_stamp = transition_loaded['time_stamp']
                report_loaded = transition_loaded['report_txt']
                fake_report_loaded = {'time_stamp': time_stamp, 'content': report_loaded}

                # digest the position
                position_loaded = transition_loaded['situation']
                position_data = mapping.Position(position_loaded, play_low.VARIANT_DATA)

                # digest the orders
                orders_loaded = transition_loaded['orders']
                orders_data = mapping.Orders(orders_loaded, position_data)

            else:

                # to force current map to be displayed
                advancement_selected = last_advancement

        # now we can display
        play_low.MY_SUB_PANEL.clear()
        #  play_low.MY_SUB_PANEL.attrs['style'] = 'display:table-row'

        # title
        play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
        play_low.MY_SUB_PANEL <= html.BR()

        # create left side
        display_left = html.DIV(id='display_left')
        display_left.attrs['style'] = 'display: table-cell; width:500px; vertical-align: top; table-layout: fixed;'

        # put it in
        play_low.MY_SUB_PANEL <= display_left

        # put stuff in left side

        if advancement_selected != last_advancement:
            # display only if from history
            game_status = play_low.get_game_status_histo(play_low.VARIANT_DATA, advancement_selected)
            display_left <= game_status
            display_left <= html.BR()

        # create canvas
        map_size = play_low.VARIANT_DATA.map_size
        canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
        ctx = canvas.getContext("2d")
        if ctx is None:
            alert("Il faudrait utiliser un navigateur plus récent !")
            return

        # put background (this will call the callback that display the whole map)
        img = common.read_image(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN)
        img.bind('load', lambda _: callback_render(True))

        display_left <= canvas
        display_left <= html.BR()

        ratings = position_data.role_ratings()
        units = play_low.POSITION_DATA.role_units()
        colours = position_data.role_colours()
        game_scoring = play_low.GAME_PARAMETERS_LOADED['scoring']
        rating_colours_window = play_low.make_rating_colours_window(play_low.VARIANT_DATA, ratings, units, colours, game_scoring)

        display_left <= rating_colours_window
        display_left <= html.BR()

        report_non_playing = non_playing_information()
        if report_non_playing is not None:
            display_left <= report_non_playing
            display_left <= html.BR()
            display_left <= html.BR()

        report_window = common.make_report_window(fake_report_loaded)
        display_left <= report_window

        # create right part
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # put it in
        play_low.MY_SUB_PANEL <= buttons_right

        # put stuff in right side

        # role flag if applicable
        if play_low.ROLE_ID is not None:
            play_low.stack_role_flag(buttons_right)

        buttons_right <= html.H3("Position")

        input_refresh = html.INPUT(type="submit", value="Recharger la partie")
        input_refresh.bind("click", callback_refresh)
        buttons_right <= input_refresh
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        # button last moves
        play_low.stack_last_moves_button(buttons_right)

        buttons_right <= html.H3("Historique")

        input_first = html.INPUT(type="submit", value="||<<")
        input_first.bind("click", lambda e, a=0: transition_display_callback(e, a))
        buttons_right <= input_first
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_previous = html.INPUT(type="submit", value="<")
        input_previous.bind("click", lambda e, a=advancement_selected - 1: transition_display_callback(e, a))
        buttons_right <= input_previous
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_next = html.INPUT(type="submit", value=">")
        input_next.bind("click", lambda e, a=advancement_selected + 1: transition_display_callback(e, a))
        buttons_right <= input_next
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_last = html.INPUT(type="submit", value=">>||")
        input_last.bind("click", lambda e, a=last_advancement: transition_display_callback(e, a))
        buttons_right <= input_last
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        for adv_sample in range(4, last_advancement, 5):

            adv_sample_season, adv_sample_year = common.get_season(adv_sample, play_low.VARIANT_DATA)
            adv_sample_season_readable = play_low.VARIANT_DATA.season_name_table[adv_sample_season]

            input_last = html.INPUT(type="submit", value=f"{adv_sample_season_readable} {adv_sample_year}")
            input_last.bind("click", lambda e, a=adv_sample: transition_display_callback(e, a))
            buttons_right <= input_last
            if adv_sample + 5 < last_advancement:
                buttons_right <= html.BR()
                buttons_right <= html.BR()

        buttons_right <= html.H3("Divers")

        input_export_sandbox = html.INPUT(type="submit", value="Exporter la partie vers le bac à sable")
        input_export_sandbox.bind("click", callback_export_sandbox)
        buttons_right <= input_export_sandbox
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_download_game_json = html.INPUT(type="submit", value="Télécharger la partie au format JSON")
        input_download_game_json.bind("click", callback_export_game_json)
        buttons_right <= input_download_game_json
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        url = f"https://diplomania-gen.fr?game={play_low.GAME}"
        buttons_right <= f"Pour inviter un joueur à consulter la partie, lui envoyer le lien : '{url}'"
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        url = f"https://diplomania-gen.fr?game={play_low.GAME}&arrival=rejoindre"
        buttons_right <= f"Pour inviter un joueur à rejoindre la partie, lui envoyer le lien : '{url}'"
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-export/{play_low.GAME_ID}"
        buttons_right <= f"Pour une extraction automatique depuis le back-end utiliser : '{url}'"
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    last_advancement = play_low.GAME_PARAMETERS_LOADED['current_advancement']
    adv_last_moves = last_advancement
    while True:
        adv_last_moves -= 1
        if adv_last_moves % 5 in [0, 2]:
            break

    # initiates callback
    if direct_last_moves:
        transition_display_callback(None, adv_last_moves)
    else:
        transition_display_callback(None, last_advancement)

    return True


def show_game_parameters():
    """ show_game_parameters """

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    game_params_table = html.TABLE()

    # table header
    thead = html.THEAD()
    for field_name in "Nom du paramètre", "Valeur pour la partie", "Explication sommaire", "Effet (ce qui change concrètement)", "Implémenté ?":
        col = html.TD(field_name)
        thead <= col
    game_params_table <= thead

    for key, value in play_low.GAME_PARAMETERS_LOADED.items():

        if key in ['name', 'description', 'variant', 'deadline', 'current_state', 'current_advancement']:
            continue

        row = html.TR()

        parameter_name, explanation, effect, implemented = {
            'archive': ("archive", "la partie n'est pas jouée, elle est juste consultable", "L'arbitre peut passer des ordres, les dates limites ne sont pas gérées, le système autorise les résolutions sans tenir compte des soumissions des joueurs, le système ne réalise pas l'attribution des roles au démarrage de la partie, pas de courriel de notification aux joueurs", "OUI"),
            'used_for_elo': ("utilisée pour le calcul du élo", "oui ou non", "Le résultat de la partie est pris en compte dans le calcul du élo des joueurs du site", "OUI"),
            'anonymous': ("anonyme", "on sait pas qui joue quel rôle dans la partie - cette valeur est modifiable pendant la partie", "Seul l'arbitre peut savoir qui joue et les joueurs ne savent pas qui a passé les ordres  - effacé à la fin de la partie", "OUI"),
            'nomessage_game': ("blocage des messages privés (négociation) pour la partie", "si oui on ne peut pas négocier - sauf avec l'arbitre", "Tout message privé joueur vers joueur est impossible", "OUI"),
            'nopress_game': ("blocage des messages publics (déclaration) pour la partie", "si oui on ne peut pas déclarer - sauf l'arbitre", "Tout message public de joueur est impossible", "OUI"),
            'nomessage_current': ("blocage des messages privés (négociation) pour le moment", "si oui on ne peut pas négocier - valeur utilisée pour accorder l'accès ou pas - cette valeur est modifiable pendant la partie", "effacé en fin de partie", "OUI"),
            'nopress_current': ("blocage des messages publics (déclaration) pour le moment", "si oui on ne peut pas déclarer - valeur utilisée pour accorder l'accès ou pas - cette valeur est modifiable pendant la partie", "effacé en fin de partie", "OUI"),
            'fast': ("en direct", "la partie est jouée comme sur un plateau", "Les paramètres de calcul des dates limites sont en minutes et non en heures, pas de courriel de notification aux joueurs", "OUI"),
            'manual': ("attribution manuelle des rôle", "L'arbitre doit attribuer les roles", "Le système ne réalise pas l'attribution des roles au démarrage de la partie", "OUI"),
            'scoring': ("code du scorage", "le système de scorage appliqué", "Se reporter à Accueil/Coin technique pour le détail des scorages implémentés. Note : Le calcul est réalisé dans l'interface", "OUI"),
            'deadline_hour': ("heure de la date limite", "entre 0 et 23", "Heure à laquelle le système placera la date limite dans la journée si la synchronisation est souhaitée", "OUI"),
            'deadline_sync': ("synchronisation de la date limite", "oui ou non", "Le système synchronise la date limite à une heure précise dans la journée", "OUI"),
            'grace_duration': ("durée de la grâce", "en heures", "L'arbitre tolère un retard d'autant d'heures avant de placer des désordres civils", "OUI"),
            'speed_moves': ("vitesse pour les mouvements", "en heures", "Le système ajoute autant d'heures avant une résolution de mouvement pour une date limite", "OUI"),
            'speed_retreats': ("vitesse pour les retraites", "en heures", "Le système ajoute autant d'heures avant une résolution de retraites pour une date limite", "OUI"),
            'speed_adjustments': ("vitesse pour les ajustements", "en heures", "Le système ajoute autant d'heures avant une résolution d'ajustements pour une date limite", "OUI"),
            'cd_possible_moves': ("désordre civil possible pour les mouvements", "oui ou non", "L'arbitre est en mesure d'imposer un désordre civil pour une phase de mouvements", "OUI"),
            'cd_possible_retreats': ("désordre civil possible pour les retraites", "oui ou non", "L'arbitre est en mesure d'imposer un désordre civil pour une phase de retraites", "OUI"),
            'cd_possible_builds': ("désordre civil possible pour les constructions", "oui ou non", "L'arbitre est en mesure d'imposer un désordre civil pour une phase d'ajustements", "OUI"),
            'play_weekend': ("on joue le week-end", "oui ou non", "Le système pourra placer une date limite pendant le week-end", "OUI"),
            'access_restriction_reliability': ("restriction d'accès sur la fiabilité", "(valeur)", "Un seuil de fiabilité est exigé pour rejoindre la partie", "OUI"),
            'access_restriction_regularity': ("restriction d'accès sur la régularité", "(valeur)", "Un seuil de régularité est exigé pour rejoindre la partie", "OUI"),
            'access_restriction_performance': ("restriction d'accès sur la performance", "(valeur)", "Un seuil de performance est exigé pour rejoindre la partie", "OUI"),
            'nb_max_cycles_to_play': ("nombre maximum de cycles (années) à jouer", "(valeur)", "L'arbitre déclare la partie terminée si autant de cycles ont été joués", "-"),
            'victory_centers': ("nombre de centres pour la victoire", "(valeur)", "L'arbitre déclare la partie gagnée si un joueur possède autant de centres", "-")
        }[key]

        col1 = html.TD(html.B(parameter_name))
        row <= col1

        if value is False:
            parameter_value = "Non"
        elif value is True:
            parameter_value = "Oui"
        else:
            parameter_value = value

        col2 = html.TD(html.B(parameter_value), Class='important')
        row <= col2

        # some more info

        col3 = html.TD(explanation)
        row <= col3

        col4 = html.TD(effect)
        row <= col4

        col5 = html.TD(implemented)
        row <= col5

        game_params_table <= row

    play_low.MY_SUB_PANEL <= game_params_table

    return True


def game_dropouts_reload(game_id):
    """ game_dropouts_reload """

    dropouts = []

    def reply_callback(req):
        nonlocal dropouts
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des abandons de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des abandons de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        dropouts = req_result['dropouts']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-dropouts/{game_id}"

    # extracting dropouts from a game : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dropouts


def game_transitions_reload(game_id):
    """ game_transitions_reload : returns empty dict if problem (or no data) """

    transitions_loaded = {}

    def reply_callback(req):
        nonlocal transitions_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des transitions de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des transitions de la partie: {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        transitions_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-transitions/{game_id}"

    # getting transitions : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return transitions_loaded


def show_events_in_game():
    """ show_events_in_game """

    def cancel_remove_dropout_callback(_, dialog):
        """ cancel_remove_dropout_callback """
        dialog.close(None)

    def cancel_remove_incident_callback(_, dialog):
        """ cancel_remove_incident_callback """
        dialog.close(None)

    def remove_dropout_callback(_, dialog, role_id, player_id):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppression de l'abandon : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppression de l'abandon : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"L'abandon a été supprimé : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            show_events_in_game()

        dialog.close(None)

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-dropouts-manage/{play_low.GAME_ID}/{role_id}/{player_id}"

        # deleting dropout : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def remove_incident_callback(_, dialog, role_id, advancement):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppression de l'incident : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppression de l'incident : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"L'incident a été supprimé : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            show_events_in_game()

        dialog.close(None)

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-incidents-manage/{play_low.GAME_ID}/{role_id}/{advancement}"

        # deleting incident : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def remove_dropout_callback_confirm(ev, role_id, player_id, text):  # pylint: disable=invalid-name
        """ remove_dropout_callback_confirm """

        ev.preventDefault()

        dialog = mydialog.Dialog(f"On supprime vraiment cet abandon pour {text} ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog, r=role_id, p=player_id: remove_dropout_callback(e, d, r, p))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_remove_dropout_callback(e, d))

        # back to where we started
        play_low.MY_SUB_PANEL.clear()
        show_events_in_game()

    def remove_incident_callback_confirm(ev, role_id, advancement, text):  # pylint: disable=invalid-name
        """ remove_incident_callback_confirm """

        ev.preventDefault()

        dialog = mydialog.Dialog(f"On supprime vraiment cet incident pour {text} ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog, r=role_id, a=advancement: remove_incident_callback(e, d, r, a))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_remove_incident_callback(e, d))

        # back to where we started
        play_low.MY_SUB_PANEL.clear()
        show_events_in_game()

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    game_master_pseudo = get_game_master(int(play_low.GAME_ID))
    if game_master_pseudo is None:
        play_low.MY_SUB_PANEL <= html.DIV("Pas d'arbitre pour cette partie ou erreur au chargement de l'arbitre de la partie", Class='important')
    else:

        game_master_table = html.TABLE()

        fields = ['flag', 'role', 'player']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'flag': 'drapeau', 'player': 'joueur', 'role': 'rôle'}[field]
            col = html.TD(field_fr)
            thead <= col
        game_master_table <= thead

        role_id = 0

        row = html.TR()

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        # role name
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        col = html.TD(role_name)
        row <= col

        # player
        pseudo_there = game_master_pseudo
        col = html.TD(pseudo_there)
        row <= col

        game_master_table <= row

        play_low.MY_SUB_PANEL <= game_master_table

    # orders
    play_low.MY_SUB_PANEL <= html.H3("Ordres")

    # if user identified ?
    if play_low.PSEUDO is None:
        play_low.MY_SUB_PANEL <= html.DIV("Il faut se connecter au préalable", Class='important')

    # is player in game ?
    elif not (moderate.check_modo(play_low.PSEUDO) or play_low.ROLE_ID is not None):
        play_low.MY_SUB_PANEL <= html.DIV("Seuls les participants à une partie (ou un modérateur du site) peuvent voir le statut des ordres", Class='important')

    # game anonymous
    elif not (moderate.check_modo(play_low.PSEUDO) or play_low.ROLE_ID == 0 or not play_low.GAME_PARAMETERS_LOADED['anonymous']):
        play_low.MY_SUB_PANEL <= html.DIV("Seul l'arbitre (ou un modérateur du site) peut voir le statut des ordres  pour une partie anonyme", Class='important')

    else:

        # you will at least get your own role
        submitted_data = play_low.get_roles_submitted_orders(play_low.GAME_ID)
        if not submitted_data:
            alert("Erreur chargement données de soumission")
            play.load_option(None, 'Consulter')
            return False

        role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

        id2pseudo = {v: k for k, v in play_low.PLAYERS_DICT.items()}

        game_players_table = html.TABLE()

        fields = ['flag', 'role', 'player', 'orders', 'agreement']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'flag': 'drapeau', 'role': 'rôle', 'player': 'joueur', 'orders': 'ordres', 'agreement': 'accord'}[field]
            col = html.TD(field_fr)
            thead <= col
        game_players_table <= thead

        for role_id in play_low.VARIANT_DATA.roles:

            row = html.TR()

            if role_id <= 0:
                continue

            # role flag
            role = play_low.VARIANT_DATA.roles[role_id]
            role_name = play_low.VARIANT_DATA.role_name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)

            if role_icon_img:
                col = html.TD(role_icon_img)
            else:
                col = html.TD()
            row <= col

            role = play_low.VARIANT_DATA.roles[role_id]
            role_name = play_low.VARIANT_DATA.role_name_table[role]

            col = html.TD(role_name)
            row <= col

            # player
            pseudo_there = ""
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id = int(player_id_str)
                pseudo_there = id2pseudo[player_id]
            col = html.TD(pseudo_there)
            row <= col

            # orders are in
            submitted_roles_list = submitted_data['submitted']
            needed_roles_list = submitted_data['needed']
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
                else:
                    flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
            else:
                flag = ""
            col = html.TD(flag)
            row <= col

            # agreed
            col = html.TD()
            flag = ""
            submitted_roles_list = submitted_data['submitted']
            agreed_now_roles_list = submitted_data['agreed_now']
            agreed_after_roles_list = submitted_data['agreed_after']
            needed_roles_list = submitted_data['needed']
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    if role_id in agreed_now_roles_list:
                        flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre maintenant")
                    elif role_id in agreed_after_roles_list:
                        flag = html.IMG(src="./images/agreed_after.jpg", title="D'accord pour résoudre juste après la date limite")
                    else:
                        flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")
            col <= flag
            row <= col

            game_players_table <= row

        play_low.MY_SUB_PANEL <= game_players_table

    # incidents2
    play_low.MY_SUB_PANEL <= html.H3("Désordres civils")

    # get the actual incidents of the game
    game_incidents2 = game_incidents2_reload(play_low.GAME_ID)
    # there can be no incidents (if no incident of failed to load)

    game_incidents2_table = html.TABLE()

    fields = ['flag', 'role', 'season', 'date']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'flag': 'drapeau', 'role': 'rôle', 'season': 'saison', 'date': 'date'}[field]
        col = html.TD(field_fr)
        thead <= col
    game_incidents2_table <= thead

    for role_id, advancement, time_stamp in sorted(game_incidents2, key=lambda i: i[2]):

        row = html.TR()

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        col = html.TD(role_name)
        row <= col

        # season
        advancement_season, advancement_year = common.get_season(advancement, play_low.VARIANT_DATA)
        advancement_season_readable = play_low.VARIANT_DATA.season_name_table[advancement_season]
        game_season = f"{advancement_season_readable} {advancement_year}"
        col = html.TD(game_season)
        row <= col

        # date
        datetime_incident = mydatetime.fromtimestamp(time_stamp)
        datetime_incident_str = mydatetime.strftime2(*datetime_incident)
        col = html.TD(datetime_incident_str)
        row <= col

        game_incidents2_table <= row

    play_low.MY_SUB_PANEL <= game_incidents2_table

    if game_incidents2:
        play_low.MY_SUB_PANEL <= html.BR()
        play_low.MY_SUB_PANEL <= html.DIV("Un désordre civil signifie que l'arbitre a forcé des ordres pour le joueur", Class='note')

    # quitters
    play_low.MY_SUB_PANEL <= html.H3("Abandons")

    # get the actual dropouts of the game
    game_dropouts = game_dropouts_reload(play_low.GAME_ID)
    # there can be no incidents (if no incident of failed to load)

    game_dropouts_table = html.TABLE()

    fields = ['flag', 'role', 'pseudo', 'date']

    if play_low.ROLE_ID == 0:
        fields.extend(['remove'])

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'flag': 'drapeau', 'role': 'rôle', 'pseudo': 'pseudo', 'date': 'date', 'remove': 'supprimer'}[field]
        col = html.TD(field_fr)
        thead <= col
    game_dropouts_table <= thead

    id2pseudo = {v: k for k, v in play_low.PLAYERS_DICT.items()}

    for role_id, player_id, time_stamp in sorted(game_dropouts, key=lambda d: d[2]):

        row = html.TR()

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        col = html.TD(role_name)
        row <= col

        # pseudo
        col = html.TD()
        pseudo_quitter = id2pseudo[player_id]
        col <= pseudo_quitter
        row <= col

        # date
        datetime_incident = mydatetime.fromtimestamp(time_stamp)
        datetime_incident_str = mydatetime.strftime2(*datetime_incident)
        col = html.TD(datetime_incident_str)
        row <= col

        # remove
        if play_low.ROLE_ID == 0:
            form = html.FORM()
            input_remove_dropout = html.INPUT(type="submit", value="Supprimer")
            text = f"Rôle {role_name} et joueur {pseudo_quitter}"
            input_remove_dropout.bind("click", lambda e, r=role_id, p=player_id, t=text: remove_dropout_callback_confirm(e, r, p, t))
            form <= input_remove_dropout
            col = html.TD(form)
            row <= col

        game_dropouts_table <= row

    play_low.MY_SUB_PANEL <= game_dropouts_table
    play_low.MY_SUB_PANEL <= html.BR()

    # incidents
    play_low.MY_SUB_PANEL <= html.H3("Retards")

    # get the actual incidents of the game
    game_incidents = game_incidents_reload(play_low.GAME_ID)
    # there can be no incidents (if no incident of failed to load)

    game_incidents_table = html.TABLE()

    fields = ['flag', 'role', 'pseudo', 'season', 'duration', 'date']

    if play_low.ROLE_ID == 0:
        fields.extend(['remove'])

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'flag': 'drapeau', 'role': 'rôle', 'pseudo': 'pseudo', 'season': 'saison', 'duration': 'durée', 'date': 'date', 'remove': 'supprimer'}[field]
        col = html.TD(field_fr)
        thead <= col
    game_incidents_table <= thead

    id2pseudo = {v: k for k, v in play_low.PLAYERS_DICT.items()}

    for role_id, advancement, player_id, duration, time_stamp in sorted(game_incidents, key=lambda i: i[4]):

        row = html.TR()

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        col = html.TD(role_name)
        row <= col

        # pseudo
        col = html.TD()
        if player_id is not None:
            col <= id2pseudo[player_id]
        row <= col

        # season
        advancement_season, advancement_year = common.get_season(advancement, play_low.VARIANT_DATA)
        advancement_season_readable = play_low.VARIANT_DATA.season_name_table[advancement_season]
        game_season = f"{advancement_season_readable} {advancement_year}"
        col = html.TD(game_season)
        row <= col

        # duration
        col = html.TD(f"{duration}")
        row <= col

        # date
        datetime_incident = mydatetime.fromtimestamp(time_stamp)
        datetime_incident_str = mydatetime.strftime2(*datetime_incident)
        col = html.TD(datetime_incident_str)
        row <= col

        # remove
        if play_low.ROLE_ID == 0:
            form = html.FORM()
            input_remove_incident = html.INPUT(type="submit", value="Supprimer")
            text = f"Rôle {role_name} en saison {game_season}"
            input_remove_incident.bind("click", lambda e, r=role_id, a=advancement, t=text: remove_incident_callback_confirm(e, r, a, t))
            form <= input_remove_incident
            col = html.TD(form)
            row <= col

        game_incidents_table <= row

    play_low.MY_SUB_PANEL <= game_incidents_table
    play_low.MY_SUB_PANEL <= html.BR()

    count = {}

    for role_id, advancement, player_id, duration, _ in game_incidents:
        if player_id is not None:
            continue
        if role_id not in count:
            count[role_id] = []
        count[role_id].append(duration)

    recap_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['rang', 'role', 'retards']:
        col = html.TD(field)
        thead <= col
    recap_table <= thead

    rank = 1
    for role_id in sorted(count.keys(), key=lambda r: len(count[r]), reverse=True):
        row = html.TR()

        # rank
        col = html.TD(rank)
        row <= col

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        # incidents
        incidents_list = count.get(role_id, [])
        col = html.TD(" ".join([f"{i}" for i in incidents_list]))
        row <= col

        recap_table <= row
        rank += 1

    play_low.MY_SUB_PANEL <= recap_table
    play_low.MY_SUB_PANEL <= html.BR()

    # a bit of humour !
    if game_incidents:

        play_low.MY_SUB_PANEL <= html.DIV("Un retard signifie que le joueur (ou l'arbitre) ont réalisé la transition 'pas d'accord -> 'd'accord pour résoudre' après la date limite", Class='note')
        play_low.MY_SUB_PANEL <= html.BR()

        play_low.MY_SUB_PANEL <= html.DIV("Seuls les pseudos de joueurs en retard qui depuis ont été remplacés apparaissent (ces retards ne sont pas comptés dans le récapitulatif)", Class='note')
        play_low.MY_SUB_PANEL <= html.BR()

        play_low.MY_SUB_PANEL <= html.DIV("Les retards sont en heures entamées (sauf pour les parties en direct - en minutes).  Un retard de 1 par exemple signifie un retard entre 1 seconde et 59 minutes, 59 secondes.", Class='note')
        play_low.MY_SUB_PANEL <= html.BR()

    return True


# the idea is not to loose the content of a message if not destinee were specified
CONTENT_BACKUP = None


def negotiate(default_dest_set):
    """ negotiate """

    def answer_callback(_, dest_set):
        play_low.MY_SUB_PANEL.clear()
        negotiate(dest_set)

    def add_message_callback(ev):  # pylint: disable=invalid-name
        """ add_message_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de message dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de message dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Le message a été envoyé ! {messages}", True)

            # back to where we started
            global CONTENT_BACKUP
            CONTENT_BACKUP = None
            play_low.MY_SUB_PANEL.clear()
            negotiate({})

        ev.preventDefault()

        dest_role_ids = ' '.join([str(role_num) for (role_num, button) in selected.items() if button.checked])

        content = input_message.value

        # keep a backup
        global CONTENT_BACKUP
        CONTENT_BACKUP = content

        if not content:
            alert("Pas de contenu pour ce message !")
            play_low.MY_SUB_PANEL.clear()
            negotiate({})
            return

        if not dest_role_ids:
            alert("Pas de destinataire pour ce message !")
            play_low.MY_SUB_PANEL.clear()
            negotiate({})
            return

        json_dict = {
            'dest_role_ids': dest_role_ids,
            'role_id': play_low.ROLE_ID,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{play_low.GAME_ID}"

        # adding a message in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def messages_reload(game_id):
        """ messages_reload """

        messages = []

        def reply_callback(req):
            nonlocal messages
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des messages dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des messages dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = req_result['messages_list']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{game_id}"

        # extracting messages from a game : need token (or not?)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return messages

    if play_low.ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # get time stamp of last visit of declarations
    time_stamp_last_visit = common.date_last_visit_load(play_low.GAME_ID, config.MESSAGES_TYPE)

    # put time stamp of last visit of declarations as now
    date_last_visit_update(play_low.GAME_ID, play_low.ROLE_ID, config.MESSAGES_TYPE)

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_declaration = html.LEGEND("Votre message", title="Qu'avez vous à lui/leur dire ?")
    fieldset <= legend_declaration
    input_message = html.TEXTAREA(type="text", rows=8, cols=80)
    if CONTENT_BACKUP is not None:
        input_message <= CONTENT_BACKUP
    fieldset <= input_message
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_destinees = html.LEGEND("Destinataire(s)", title="Et à qui ?")
    fieldset <= legend_destinees

    table = html.TABLE()
    row = html.TR()
    selected = {}
    for role_id_dest in range(play_low.VARIANT_CONTENT_LOADED['roles']['number'] + 1):

        # dest only if allowed
        if play_low.GAME_PARAMETERS_LOADED['nomessage_current']:
            if not (play_low.ROLE_ID == 0 or role_id_dest == 0):
                continue

        role_dest = play_low.VARIANT_DATA.roles[role_id_dest]
        role_name = play_low.VARIANT_DATA.role_name_table[role_dest]
        role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{role_id_dest}.jpg", title=role_name)

        # the alternative
        input_dest = html.INPUT(type="checkbox", id=str(role_id_dest), checked=role_id_dest in default_dest_set)
        col = html.TD()
        col <= input_dest

        # necessary to link flag with button
        label_dest = html.LABEL(role_icon_img, for_=str(role_id_dest))
        col <= label_dest

        row <= col

        selected[role_id_dest] = input_dest

    table <= row
    fieldset <= table
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="Envoyer le message")
    input_declare_in_game.bind("click", add_message_callback)
    form <= input_declare_in_game

    # now we display messages

    messages = messages_reload(play_low.GAME_ID)
    # there can be no message (if no message of failed to load)

    # insert new field 'type'
    messages = [(MessageTypeEnum.TEXT, 0, i, f, t, d, c) for (i, f, t, d, c) in messages]

    # get the transition table
    game_transitions = game_transitions_reload(play_low.GAME_ID)

    # add fake messages (game transitions)
    fake_messages = [(MessageTypeEnum.SEASON, int(k), -1, -1, v, [], readable_season(int(k))) for k, v in game_transitions.items()]
    messages.extend(fake_messages)

    id2pseudo = {v: k for k, v in play_low.PLAYERS_DICT.items()}

    # get the dropouts table
    game_dropouts = game_dropouts_reload(play_low.GAME_ID)

    # add fake messages (game dropouts)
    fake_messages = [(MessageTypeEnum.DROPOUT, 0, -1, r, d, [], f"Le joueur {id2pseudo[p]} avec ce rôle a quitté la partie...") for r, p, d in game_dropouts]
    messages.extend(fake_messages)

    # sort with all that was added
    messages.sort(key=lambda m: (float(m[4]), float(m[1])), reverse=True)

    messages_table = html.TABLE()

    thead = html.THEAD()
    for title in ['id', 'Date', 'Auteur', 'Destinataire(s)', 'Contenu', 'Répondre']:
        col = html.TD(html.B(title))
        thead <= col
    messages_table <= thead

    game_master_pseudo = get_game_master(int(play_low.GAME_ID))
    role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

    for type_, _, id_, from_role_id_msg, time_stamp, dest_role_id_msgs, content in messages:

        if type_ is MessageTypeEnum.TEXT:
            class_ = 'text'
        elif type_ is MessageTypeEnum.SEASON:
            class_ = 'season'
        elif type_ is MessageTypeEnum.DROPOUT:
            class_ = 'dropout'

        row = html.TR()

        id_txt = str(id_) if id_ != -1 else ""
        col = html.TD(id_txt, Class=class_)
        row <= col

        date_desc_gmt = mydatetime.fromtimestamp(time_stamp)
        date_desc_gmt_str = mydatetime.strftime(*date_desc_gmt)

        col = html.TD(f"{date_desc_gmt_str}", Class=class_)
        row <= col

        col = html.TD(Class=class_)

        if from_role_id_msg != -1:

            role = play_low.VARIANT_DATA.roles[from_role_id_msg]
            role_name = play_low.VARIANT_DATA.role_name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{from_role_id_msg}.jpg", title=role_name)
            col <= role_icon_img

            # player
            pseudo_there = ""
            if from_role_id_msg == 0:
                if game_master_pseudo:
                    pseudo_there = game_master_pseudo
            elif from_role_id_msg in role2pseudo:
                player_id_str = role2pseudo[from_role_id_msg]
                player_id = int(player_id_str)
                pseudo_there = id2pseudo[player_id]

            if pseudo_there:
                col <= html.BR()
                col <= pseudo_there

        row <= col

        col = html.TD(Class=class_)

        for dest_role_id_msg in dest_role_id_msgs:

            role = play_low.VARIANT_DATA.roles[dest_role_id_msg]
            role_name = play_low.VARIANT_DATA.role_name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{dest_role_id_msg}.jpg", title=role_name)

            # player
            pseudo_there = ""
            if dest_role_id_msg == 0:
                if game_master_pseudo:
                    pseudo_there = game_master_pseudo
            elif dest_role_id_msg in role2pseudo:
                player_id_str = role2pseudo[dest_role_id_msg]
                player_id = int(player_id_str)
                pseudo_there = id2pseudo[player_id]

            col <= role_icon_img
            if pseudo_there:
                col <= html.BR()
                col <= pseudo_there

            # separator
            col <= html.BR()

        row <= col

        col = html.TD(Class=class_)

        for line in content.split('\n'):
            # new so put in bold
            if from_role_id_msg != play_low.ROLE_ID and time_stamp > time_stamp_last_visit:
                line = html.B(line)
            col <= line
            col <= html.BR()

        row <= col

        col = html.TD()
        if play_low.ROLE_ID in dest_role_id_msgs:
            button = html.BUTTON("Répondre", Class='btn-menu')
            new_dest_role_id_msgs = set(dest_role_id_msgs)
            new_dest_role_id_msgs.add(from_role_id_msg)
            new_dest_role_id_msgs.remove(play_low.ROLE_ID)
            button.bind("click", lambda e, d=new_dest_role_id_msgs: answer_callback(e, d))
            col <= button
        row <= col

        messages_table <= row

    # now we can display

    # header

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    # map and ratings
    play_low.show_board(play_low.MY_SUB_PANEL)

    # role flag
    play_low.stack_role_flag(play_low.MY_SUB_PANEL)

    # button last moves
    play_low.stack_last_moves_button(play_low.MY_SUB_PANEL)

    # form
    play_low.MY_SUB_PANEL <= form
    play_low.MY_SUB_PANEL <= html.BR()
    play_low.MY_SUB_PANEL <= html.BR()

    # advice to report
    label_unsuitable_content = html.DIV(Class="important")
    label_unsuitable_content <= "Attention, les messages sont privés entre émetteur et destinataire(s) mais doivent respecter la charte. L'administrateur peut sur demande les lire pour vérifier. Si cela ne vous convient pas, quittez le site. Contenu inaproprié ? Déclarez un incident ! (reperez le message par son id)"
    play_low.MY_SUB_PANEL <= label_unsuitable_content
    play_low.MY_SUB_PANEL <= html.BR()

    # messages already
    play_low.MY_SUB_PANEL <= messages_table
    play_low.MY_SUB_PANEL <= html.BR()
    play_low.MY_SUB_PANEL <= html.BR()

    information = html.DIV(Class='note')
    information <= "Le pseudo affiché est celui du joueur en cours, pas forcément celui de l'auteur réel du message"
    play_low.MY_SUB_PANEL <= information

    return True


def declare():
    """ declare """

    def add_declaration_callback(ev):  # pylint: disable=invalid-name
        """ add_declaration_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de déclaration dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de déclaration dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La déclaration a été faite ! {messages}", True)

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            declare()

        ev.preventDefault()

        anonymous = input_anonymous.checked

        content = input_declaration.value

        if not content:
            alert("Pas de contenu pour cette déclaration !")
            play_low.MY_SUB_PANEL.clear()
            declare()
            return

        json_dict = {
            'role_id': play_low.ROLE_ID,
            'anonymous': anonymous,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{play_low.GAME_ID}"

        # adding a declaration in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def declarations_reload(game_id):
        """ declarations_reload """

        declarations = []

        def reply_callback(req):
            nonlocal declarations
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de déclarations dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de déclarations dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            declarations = req_result['declarations_list']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{game_id}"

        # extracting declarations from a game : need token (or not?)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return declarations

    if play_low.ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # get time stamp of last visit of declarations
    time_stamp_last_visit = common.date_last_visit_load(play_low.GAME_ID, config.DECLARATIONS_TYPE)

    # put time stamp of last visit of declarations as now
    date_last_visit_update(play_low.GAME_ID, play_low.ROLE_ID, config.DECLARATIONS_TYPE)

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_declaration = html.LEGEND("Votre déclaration", title="Qu'avez vous à déclarer à tout le monde ?")
    fieldset <= legend_declaration
    input_declaration = html.TEXTAREA(type="text", rows=8, cols=80)
    fieldset <= input_declaration
    form <= fieldset

    fieldset = html.FIELDSET()
    label_anonymous = html.LABEL("En restant anonyme ? (pas anonyme auprès de l'arbitre cependant)")
    fieldset <= label_anonymous
    input_anonymous = html.INPUT(type="checkbox")
    fieldset <= input_anonymous
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="Déclarer dans la partie")
    input_declare_in_game.bind("click", add_declaration_callback)
    form <= input_declare_in_game

    # now we display declarations

    declarations = declarations_reload(play_low.GAME_ID)
    # there can be no message (if no declaration of failed to load)

    # insert new field 'type'
    declarations = [(MessageTypeEnum.TEXT, 0, i, a, r, t, c) for (i, a, r, t, c) in declarations]

    # get the transition table
    game_transitions = game_transitions_reload(play_low.GAME_ID)

    # add fake declarations (game transitions) and sort
    fake_declarations = [(MessageTypeEnum.SEASON, int(k), -1, False, -1, v, readable_season(int(k))) for k, v in game_transitions.items()]
    declarations.extend(fake_declarations)

    id2pseudo = {v: k for k, v in play_low.PLAYERS_DICT.items()}

    # get the dropouts table
    game_dropouts = game_dropouts_reload(play_low.GAME_ID)

    # add fake messages (game dropouts)
    fake_declarations = [(MessageTypeEnum.DROPOUT, 0, -1, False, r, d, f"Le joueur {id2pseudo[p]} avec ce rôle a quitté la partie...") for r, p, d in game_dropouts]
    declarations.extend(fake_declarations)

    # sort with all that was added
    declarations.sort(key=lambda d: (float(d[5]), float(d[1])), reverse=True)

    declarations_table = html.TABLE()

    thead = html.THEAD()
    for title in ['id', 'Date', 'Auteur', 'Contenu']:
        col = html.TD(html.B(title))
        thead <= col
    declarations_table <= thead

    game_master_pseudo = get_game_master(int(play_low.GAME_ID))
    role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}
    id2pseudo = {v: k for k, v in play_low.PLAYERS_DICT.items()}

    for type_, _, id_, anonymous, role_id_msg, time_stamp, content in declarations:

        if type_ is MessageTypeEnum.TEXT:
            if anonymous:
                class_ = 'text_anonymous'
            else:
                class_ = 'text'
        elif type_ is MessageTypeEnum.SEASON:
            class_ = 'season'
        elif type_ is MessageTypeEnum.DROPOUT:
            class_ = 'dropout'

        row = html.TR()

        id_txt = str(id_) if id_ != -1 else ""
        col = html.TD(id_txt, Class=class_)
        row <= col

        date_desc_gmt = mydatetime.fromtimestamp(time_stamp)
        date_desc_gmt_str = mydatetime.strftime(*date_desc_gmt)

        col = html.TD(f"{date_desc_gmt_str}", Class=class_)
        row <= col

        role_icon_img = ""
        pseudo_there = ""
        if role_id_msg != -1:

            role = play_low.VARIANT_DATA.roles[role_id_msg]
            role_name = play_low.VARIANT_DATA.role_name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{play_low.VARIANT_NAME_LOADED}/{play_low.INTERFACE_CHOSEN}/roles/{role_id_msg}.jpg", title=role_name)

            # player
            if role_id_msg == 0:
                if game_master_pseudo:
                    pseudo_there = game_master_pseudo
            elif role_id_msg in role2pseudo:
                player_id_str = role2pseudo[role_id_msg]
                player_id = int(player_id_str)
                pseudo_there = id2pseudo[player_id]

        col = html.TD(Class=class_)

        col <= role_icon_img
        if pseudo_there:
            col <= html.BR()
            col <= pseudo_there

        row <= col

        col = html.TD(Class=class_)

        for line in content.split('\n'):
            # new so put in bold
            if role_id_msg != play_low.ROLE_ID and time_stamp > time_stamp_last_visit:
                line = html.B(line)
            col <= line
            col <= html.BR()

        row <= col

        declarations_table <= row

    # now we can display

    # header

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    # map and ratings
    play_low.show_board(play_low.MY_SUB_PANEL)

    # role flag
    play_low.stack_role_flag(play_low.MY_SUB_PANEL)

    # button last moves
    play_low.stack_last_moves_button(play_low.MY_SUB_PANEL)

    # form only if allowed
    if play_low.GAME_PARAMETERS_LOADED['nopress_current'] and play_low.ROLE_ID != 0:
        play_low.MY_SUB_PANEL <= html.P("Cette partie est sans presse des joueurs")
    else:
        # form
        play_low.MY_SUB_PANEL <= form
        play_low.MY_SUB_PANEL <= html.BR()
        play_low.MY_SUB_PANEL <= html.BR()

    # advice to report
    label_unsuitable_content = html.DIV(Class="important")
    label_unsuitable_content <= "Attention, les déclarations sont privées entre joueurs de la partie mais doivent respecter la charte. L'administrateur peut les lire pour vérifier. Si cela ne vous convient pas, quittez le site. Contenu inaproprié ? Déclarez un incident ! (reperez la déclaration par son id)"
    play_low.MY_SUB_PANEL <= label_unsuitable_content
    play_low.MY_SUB_PANEL <= html.BR()

    # declarations already
    play_low.MY_SUB_PANEL <= declarations_table
    play_low.MY_SUB_PANEL <= html.BR()
    play_low.MY_SUB_PANEL <= html.BR()

    information = html.DIV(Class='note')
    information <= "Le pseudo affiché est celui du joueur en cours, pas forcément celui de l'auteur réel du message"
    play_low.MY_SUB_PANEL <= information

    return True


def note():
    """ note """

    def add_note_callback(ev):  # pylint: disable=invalid-name
        """ add_note_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de la note dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de la note dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La note a été enregistrée ! {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            note()

        ev.preventDefault()

        content = input_note.value

        json_dict = {
            'role_id': play_low.ROLE_ID,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-notes/{play_low.GAME_ID}"

        # adding a vote in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        play_low.MY_SUB_PANEL.clear()
        note()

    # from game id and token get role_id of player

    if play_low.ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    content_loaded = game_note_reload(play_low.GAME_ID)
    if content_loaded is None:
        alert("Erreur chargement note")
        play.load_option(None, 'Consulter')
        return False

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_note = html.LEGEND("Prendre des notes", title="Notez ce dont vous avez besoin de vous souvenir au sujet de cette partie")
    fieldset <= legend_note
    form <= fieldset
    input_note = html.TEXTAREA(type="text", rows=20, cols=80)
    input_note <= content_loaded
    fieldset <= input_note
    form <= fieldset

    form <= html.BR()

    input_vote_in_game = html.INPUT(type="submit", value="Enregistrer dans la partie")
    input_vote_in_game.bind("click", add_note_callback)
    form <= input_vote_in_game

    # now we can display

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    # map and ratings
    play_low.show_board(play_low.MY_SUB_PANEL)

    # role flag
    play_low.stack_role_flag(play_low.MY_SUB_PANEL)

    # button last moves
    play_low.stack_last_moves_button(play_low.MY_SUB_PANEL)

    # form
    play_low.MY_SUB_PANEL <= form

    return True
