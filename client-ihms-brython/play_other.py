""" play """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

from json import loads, dumps

from browser import html, ajax, alert, window, document   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import mydialog
import config
import common
import sandbox
import mapping
import index  # circular import

import play  # circular import
import play_low


def date_last_visit_update(game_id, role_id, visit_type):
    """ date_last_visit_update """

    def reply_callback(req):
        req_result = loads(req.text)
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
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


def join_game():
    """ join_game_action : the third way of joining a game (by a link) """

    def reply_callback(req):

        req_result = loads(req.text)
        if req.status != 201:
            if 'message' in req_result:
                alert(f"Erreur à l'inscription à la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à l'inscription à la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        messages = "<br>".join(req_result['msg'].split('\n'))
        common.info_dialog(f"Vous avez rejoint la partie (en utilisant un lien externe) : {messages}<br>Attention, c'est un réel engagement à ne pas prendre à la légère.<br>Un abandon pourrait compromettre votre inscription à de futures parties sur le site...", True)

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
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


def game_incidents2_reload(game_id):
    """ game_incidents2_reload """

    incidents = []

    def reply_callback(req):
        nonlocal incidents
        req_result = loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return incidents


def non_playing_information():
    """ non_playing_information """

    # need to be connected
    if play_low.PSEUDO is None:
        return None

    # is game anonymous
    if not (play_low.ROLE_ID == 0 or not play_low.GAME_PARAMETERS_LOADED['anonymous']):
        return None

    dangling_players = [p for p, d in play_low.GAME_PLAYERS_DICT.items() if d == - 1]
    if not dangling_players:
        return None

    info = "Les pseudos suivants sont alloués à la partie sans rôle : "
    for dangling_player_id_str in dangling_players:
        dangling_player_id = int(dangling_player_id_str)
        dangling_player = play_low.ID2PSEUDO[dangling_player_id]
        info += f"{dangling_player} "

    return html.EM(info)


def show_position(direct_last_moves):
    """ show_position """

    position_data = None
    adv_last_moves = None
    fake_report_loaded = None
    orders_data_txt = ""

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

    def callback_text_orders(_):
        """ callback_text_orders """

        if orders_data_txt:
            alert(orders_data_txt)

    def callback_export_sandbox(_):
        """ callback_export_sandbox """

        # action on importing game
        sandbox.set_arrival("play")

        # action on importing game
        sandbox.import_position(play_low.POSITION_DATA)

        # action of going to sandbox page
        index.load_option(None, 'Bac à sable')

    def callback_export_game_json(_):
        """ callback_export_game_json """

        json_return_dict = None

        def reply_callback(req):
            nonlocal json_return_dict
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de l'export json de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de l'export json de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return
            json_return_dict = req_result['content']
            json_text = dumps(json_return_dict, indent=4, ensure_ascii=False)

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
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return True

    def transition_display_callback(_, advancement_selected):

        nonlocal position_data
        nonlocal fake_report_loaded
        nonlocal orders_data_txt

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

        if advancement_selected < 0:
            alert("Il n'y a rien avant, désolé !")
            return

        if advancement_selected > last_advancement:
            alert("Il n'y a rien après, désolé !")
            return

        if advancement_selected != last_advancement:

            fog_of_war = play_low.GAME_PARAMETERS_LOADED['fog']
            if fog_of_war:
                if play_low.ROLE_ID is None:
                    transition_loaded = None
                else:
                    transition_loaded = play_low.game_transition_fog_of_war_reload(play_low.GAME_ID, advancement_selected, play_low.ROLE_ID)
            else:
                transition_loaded = play_low.game_transition_reload(play_low.GAME_ID, advancement_selected)

            if transition_loaded:

                # retrieve stuff from history
                time_stamp = transition_loaded['time_stamp']
                report_loaded = transition_loaded['report_txt']
                fake_report_loaded = {'time_stamp': time_stamp, 'content': report_loaded}

                # digest the position
                position_loaded = transition_loaded['situation']
                position_data = mapping.Position(position_loaded, play_low.VARIANT_DATA)

                # do we have comm orders ?
                communication_orders_are_present = report_loaded.count('*') > 1

                # digest the orders
                orders_loaded = transition_loaded['orders']
                orders_data = mapping.Orders(orders_loaded, position_data, communication_orders_are_present)

                # make a text version (for fog mainly)
                orders_data_txt = orders_data.display()

            else:

                # to force current map to be displayed
                advancement_selected = last_advancement

                # erase
                orders_data_txt = ""

        else:

            # erase
            orders_data_txt = ""

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

        game_scoring = play_low.GAME_PARAMETERS_LOADED['scoring']
        rating_colours_window = play_low.make_rating_colours_window(play_low.VARIANT_DATA, position_data, play_low.INTERFACE_CHOSEN, game_scoring)

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

        input_refresh = html.INPUT(type="submit", value="Recharger la partie", Class='btn-inside')
        input_refresh.bind("click", callback_refresh)
        buttons_right <= input_refresh
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        # button last moves
        play_low.stack_last_moves_button(buttons_right)

        buttons_right <= html.H3("Historique")

        input_first = html.INPUT(type="submit", value="||<<", Class='btn-inside')
        input_first.bind("click", lambda e, a=0: transition_display_callback(e, a))
        buttons_right <= input_first
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_previous = html.INPUT(type="submit", value="<", Class='btn-inside')
        input_previous.bind("click", lambda e, a=advancement_selected - 1: transition_display_callback(e, a))
        buttons_right <= input_previous
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_next = html.INPUT(type="submit", value=">", Class='btn-inside')
        input_next.bind("click", lambda e, a=advancement_selected + 1: transition_display_callback(e, a))
        buttons_right <= input_next
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_last = html.INPUT(type="submit", value=">>||", Class='btn-inside')
        input_last.bind("click", lambda e, a=last_advancement: transition_display_callback(e, a))
        buttons_right <= input_last
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        for adv_sample in range(4, last_advancement, 5):

            adv_sample_season, adv_sample_year = common.get_short_season(adv_sample, play_low.VARIANT_DATA)
            adv_sample_season_readable = play_low.VARIANT_DATA.season_name_table[adv_sample_season]

            input_last = html.INPUT(type="submit", value=f"{adv_sample_season_readable} {adv_sample_year}", Class='btn-inside')
            input_last.bind("click", lambda e, a=adv_sample: transition_display_callback(e, a))
            buttons_right <= input_last
            if adv_sample + 5 < last_advancement:
                buttons_right <= html.BR()
                buttons_right <= html.BR()

        buttons_right <= html.H3("Divers")

        if orders_data_txt:
            input_show_orders_text = html.INPUT(type="submit", value="Visualiser les ordres en texte", Class='btn-inside')
            input_show_orders_text.bind("click", callback_text_orders)
            buttons_right <= input_show_orders_text
            buttons_right <= html.BR()
            buttons_right <= html.BR()

        input_export_sandbox = html.INPUT(type="submit", value="Exporter la partie vers le bac à sable", Class='btn-inside')
        input_export_sandbox.bind("click", callback_export_sandbox)
        buttons_right <= input_export_sandbox
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_download_game_json = html.INPUT(type="submit", value="Télécharger la partie au format JSON", Class='btn-inside')
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

    # conversion
    game_type_conv = {v: k for k, v in config.GAME_TYPES_CODE_TABLE.items()}

    game_params_table = html.TABLE()

    # table header
    thead = html.THEAD()
    for field_name in "Nom du paramètre", "Type", "Valeur pour la partie", "Explication":
        col = html.TD(field_name)
        thead <= col
    game_params_table <= thead

    for key, value in play_low.GAME_PARAMETERS_LOADED.items():

        if key in ['name', 'description', 'variant', 'deadline', 'current_state', 'current_advancement', 'finished', 'soloed']:
            continue

        row = html.TR()

        parameter_name, parameter_type, parameter_explanation = {
            'fog':                            ("brouillard",                                     "oui ou non", "Si oui, la visibilité des unités est restreinte, Les joueurs ne voient que les unités voisines de leurs centres et leurs unités"),  # noqa: E241
            'archive':                        ("archive",                                        "oui ou non", "Si oui, la partie n'est pas jouée, elle est juste consultable, L'arbitre peut passer des ordres, les dates limites ne sont pas gérées, le système autorise les résolutions sans tenir compte des soumissions des joueurs, le système ne réalise pas l'attribution des roles au démarrage de la partie, pas de courriel de notification aux joueurs"),  # noqa: E241
            'used_for_elo':                   ("utilisée pour le calcul du élo",                 "oui ou non", "Si oui, Le résultat de la partie est pris en compte dans le calcul du élo des joueurs du site"),  # noqa: E241
            'anonymous':                      ("anonyme",                                        "oui ou non", "Si oui, Seul l'arbitre peut savoir qui joue et les joueurs ne savent pas qui a passé les ordres - effacé à la fin de la partie"),  # noqa: E241
            'nomessage_current':              ("blocage des négociations",                       "oui ou non", "Si oui le système empêche l'utilisation des négociations - cette valeur est modifiable pendant la partie et effacée en fin de partie"),  # noqa: E241
            'nopress_current':                ("blocage des déclarations",                       "oui ou non", "Si oui le système empêche l'utilisation des déclarations - cette valeur est modifiable pendant la partie et effacée en fin de partie"),  # noqa: E241
            'fast':                           ("en direct",                                      "oui ou non", "Si oui, La partie est jouée en temps réel comme sur un plateau, Les paramètres de calcul des dates limites sont en minutes et non en heures, pas de courriel de notification aux joueurs"),  # noqa: E241
            'manual':                         ("attribution manuelle des rôles",                 "oui ou non", "L'arbitre doit attribuer lui-même les roles, Le système ne réalise pas l'attribution des roles au démarrage de la partie"),  # noqa: E241
            'scoring':                        ("scorage",                                        "choix sur liste", "Le système de scorage appliqué - Se reporter à Accueil/Technique/Documents pour le détail des scorages implémentés. Note : Le calcul est réalisé dans l'interface"),  # noqa: E241
            'deadline_hour':                  ("heure de la date limite",                        "entier entre 0 et 23", "Heure à laquelle le système placera la date limite dans la journée si la synchronisation est souhaitée"),  # noqa: E241
            'deadline_sync':                  ("synchronisation de la date limite",              "oui ou non", "Si oui, Le système synchronise la date limite à une heure précise dans la journée"),  # noqa: E241
            'grace_duration':                 ("durée de la grâce",                              "entier en heures", "Décoratif : passé un retard d'autant d'heure la date limite change de couleur..."),  # noqa: E241
            'speed_moves':                    ("vitesse pour les mouvements",                    "entier en heures", "Le système ajoute autant d'heures avant une résolution de mouvement pour une date limite"),  # noqa: E241
            'speed_retreats':                 ("vitesse pour les retraites",                     "entier en heures", "Le système ajoute autant d'heures avant une résolution de retraites pour une date limite"),  # noqa: E241
            'speed_adjustments':              ("vitesse pour les ajustements",                   "entier en heures", "Le système ajoute autant d'heures avant une résolution d'ajustements pour une date limite"),  # noqa: E241
            'cd_possible_moves':              ("désordre civil possible pour les mouvements",    "oui ou non", "Si oui, L'arbitre est en mesure d'imposer un désordre civil pour une phase de mouvements"),  # noqa: E241
            'cd_possible_retreats':           ("désordre civil possible pour les retraites",     "oui ou non", "Si oui, L'arbitre est en mesure d'imposer un désordre civil pour une phase de retraites"),  # noqa: E241
            'cd_possible_builds':             ("désordre civil possible pour les constructions", "oui ou non", "Si oui, L'arbitre est en mesure d'imposer un désordre civil pour une phase d'ajustements"),  # noqa: E241
            'play_weekend':                   ("jeu le week-end",                                "oui ou non", "Si oui, on joue le week-end et Le système pourra placer une date limite pendant le week-end"),  # noqa: E241
            'access_restriction_reliability': ("restriction d'accès sur la fiabilité",           "entier", "Un minimum de fiabilité est exigé pour rejoindre la partie"),  # noqa: E241
            'access_restriction_regularity':  ("restriction d'accès sur la régularité",          "entier", "Un minimum de régularité est exigé pour rejoindre la partie"),  # noqa: E241
            'access_restriction_performance': ("restriction d'accès sur la performance",         "entier", "Un minimum de performance est exigé pour rejoindre la partie"),  # noqa: E241
            'nb_max_cycles_to_play':          ("nombre maximum de cycles (années) à jouer",      "entier", "Durée de la partie : Le système déclare la partie terminée si autant de cycles ont été joués"),  # noqa: E241
            'game_type':                      ("type de la partie",                              "choix sur liste", "Type de la partie : Négo : pas de restriction, tout est possible ! Blitz : pas de communication, tout est fermé ! NégoPublique : communication publique uniquement... BlitzOuverte : comme Blitz avec ouverture du canal public (déclarations) pour parler d'autre chose que la partie"),  # noqa: E241

        }[key]

        col = html.TD(html.B(parameter_name))
        row <= col

        col = html.TD(parameter_type)
        row <= col

        if key == 'game_type':
            parameter_value = game_type_conv[value]
        elif value is False:
            parameter_value = "Non"
        elif value is True:
            parameter_value = "Oui"
        else:
            parameter_value = value

        col = html.TD(html.B(parameter_value), Class='important')
        row <= col

        col = html.TD(parameter_explanation)
        row <= col

        game_params_table <= row

    play_low.MY_SUB_PANEL <= game_params_table

    return True


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
            req_result = loads(req.text)
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
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def remove_incident_callback(_, dialog, role_id, advancement):

        def reply_callback(req):
            req_result = loads(req.text)
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
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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

    for role_id, advancement, time_stamp in sorted(game_incidents2, key=lambda i: i[2], reverse=True):

        row = html.TR()

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)

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
        nb_max_cycles_to_play = play_low.GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']
        game_season = common.get_full_season(advancement, play_low.VARIANT_DATA, nb_max_cycles_to_play, False)
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
    game_dropouts = common.game_dropouts_reload(play_low.GAME_ID)
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

    for role_id, player_id, time_stamp in sorted(game_dropouts, key=lambda d: d[2], reverse=True):

        row = html.TR()

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)

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
        pseudo_quitter = play_low.ID2PSEUDO[player_id]
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
            input_remove_dropout = html.INPUT(type="submit", value="Supprimer", Class='btn-inside')
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
    game_incidents = play_low.game_incidents_reload(play_low.GAME_ID)
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

    for role_id, advancement, player_id, duration, time_stamp in sorted(game_incidents, key=lambda i: i[4], reverse=True):

        row = html.TR()

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)

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
            col <= play_low.ID2PSEUDO[player_id]
        row <= col

        # season
        nb_max_cycles_to_play = play_low.GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']
        game_season = common.get_full_season(advancement, play_low.VARIANT_DATA, nb_max_cycles_to_play, False)
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
            input_remove_incident = html.INPUT(type="submit", value="Supprimer", Class='btn-inside')
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
    for field in ['rang', 'role', 'retards', 'nombre']:
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
        role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)
        col = html.TD(role_icon_img)
        row <= col

        # incidents
        incidents_list = count.get(role_id, [])
        col = html.TD(" ".join([f"{i}" for i in incidents_list]))
        row <= col

        # incidents number
        incidents_number = len(count.get(role_id, []))
        col = html.TD(f"{incidents_number}")
        row <= col

        recap_table <= row
        rank += 1

    play_low.MY_SUB_PANEL <= recap_table
    play_low.MY_SUB_PANEL <= html.BR()

    # a bit of humour !
    if game_incidents:

        play_low.MY_SUB_PANEL <= html.DIV("Un retard signifie que le joueur (ou l'arbitre) a réalisé la transition 'pas d'accord pour le résolution' -> 'd'accord pour résoudre' après la date limite", Class='note')
        play_low.MY_SUB_PANEL <= html.BR()

        play_low.MY_SUB_PANEL <= html.DIV("Seuls les pseudos de joueurs en retard qui depuis ont été remplacés apparaissent (ces retards ne sont pas comptés dans le récapitulatif)", Class='note')
        play_low.MY_SUB_PANEL <= html.BR()

        play_low.MY_SUB_PANEL <= html.DIV("Les retards sont en heures entamées", Class='note')
        play_low.MY_SUB_PANEL <= html.BR()

    return True


def pairing():
    """ pairing """

    def join_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'inscription à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Erreur à l'inscription à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                play_low.MY_SUB_PANEL.clear()
                pairing()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Vous avez rejoint la partie : {messages}<br>Attention, c'est un réel engagement à ne pas prendre à la légère.<br>Un abandon pourrait compromettre votre inscription à de futures parties sur le site...", True)

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            pairing()

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'player_pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # adding allocation : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def quit_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la désinscription de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Erreur à la désinscription de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                play_low.MY_SUB_PANEL.clear()
                pairing()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Vous avez quitté la partie : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            pairing()

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'player_pseudo': pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # should be a delete but body in delete requests is more or less forbidden
        # quitting a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def take_mastering_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):

            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la prise de l'arbitrage de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la prise de l'arbitrage de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                play_low.MY_SUB_PANEL.clear()
                pairing()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Vous avez pris l'arbitrage de la partie : {messages}")

            # action of going to game page
            play_low.PANEL_MIDDLE.clear()
            play.render(play_low.PANEL_MIDDLE)

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'role_id': 0,
            'player_pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # taking game mastering : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def quit_mastering_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la démission de l'arbitrage de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la démission de l'arbitrage de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                play_low.MY_SUB_PANEL.clear()
                pairing()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Vous avez quitté l'arbitrage de la partie : {messages}")

            # action of going to game page
            play_low.PANEL_MIDDLE.clear()
            play.render(play_low.PANEL_MIDDLE)

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'role_id': 0,
            'player_pseudo': pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # giving up game mastering : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        play.load_option(None, 'Consulter')
        return False

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return False

    if 'GAME_ID' not in storage:
        alert("ERREUR : identifiant de partie introuvable")
        return False

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    pseudo = storage['PSEUDO']
    game_id = storage['GAME_ID']

    # role flag if applicable
    if play_low.ROLE_ID is not None:
        play_low.stack_role_flag(play_low.MY_SUB_PANEL)

    play_low.MY_SUB_PANEL <= html.H3("Se mettre dans la partie (à condition de ne pas déjà y être, charge à l'arbitre d'attribuer ensuite un rôle)")

    # join game

    form = html.FORM()
    input_join_game = html.INPUT(type="submit", value="Je rejoins la partie", Class='btn-inside')
    input_join_game.bind("click", join_game_callback)
    form <= input_join_game
    play_low.MY_SUB_PANEL <= form

    # quit game

    play_low.MY_SUB_PANEL <= html.H3("Se retirer de la partie (à condition d'y être déjà et de ne pas y avoir un rôle attribué)")

    form = html.FORM()
    input_quit_game = html.INPUT(type="submit", value="Je quitte la partie !", Class='btn-inside')
    input_quit_game.bind("click", quit_game_callback)
    form <= input_quit_game
    play_low.MY_SUB_PANEL <= form

    # take mastering

    play_low.MY_SUB_PANEL <= html.H3("Prendre l'arbitrage de la partie (à condition qu'il n'y ait pas déjà un arbitre)")

    form = html.FORM()
    input_join_game = html.INPUT(type="submit", value="Je prends l'arbitrage !", Class='btn-inside')
    input_join_game.bind("click", take_mastering_game_callback)
    form <= input_join_game
    play_low.MY_SUB_PANEL <= form

    # quit mastering

    play_low.MY_SUB_PANEL <= html.H3("Quitter l'arbitrage de cette partie (à condition d'en être l'arbitre)")

    form = html.FORM()
    input_join_game = html.INPUT(type="submit", value="Je démissionne de l'arbitrage !", Class='btn-inside')
    input_join_game.bind("click", quit_mastering_game_callback)
    form <= input_join_game
    play_low.MY_SUB_PANEL <= form

    return True


# the idea is not to loose the content of a message if not destinee were specified
CONTENT_BACKUP = None


def negotiate(default_dest_set, def_focus_role_id):
    """ negotiate """

    def focus_callback(ev, role_id):  # pylint: disable=invalid-name
        """ focus_callback """
        nonlocal focus_role_id
        ev.preventDefault()
        if role_id == focus_role_id:
            focus_role_id = None
        else:
            focus_role_id = role_id
        play_low.MY_SUB_PANEL.clear()
        negotiate({}, focus_role_id)

    def answer_callback(ev, dest_set):  # pylint: disable=invalid-name
        """ answer_callback """
        ev.preventDefault()
        play_low.MY_SUB_PANEL.clear()
        negotiate(dest_set, focus_role_id)

    def add_message_callback(ev):  # pylint: disable=invalid-name
        """ add_message_callback """

        def reply_callback(req):
            req_result = loads(req.text)
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
            negotiate({}, focus_role_id)

        ev.preventDefault()

        dest_role_ids = ' '.join([str(role_num) for (role_num, button) in selected.items() if button.checked])

        content = input_message.value

        # keep a backup
        global CONTENT_BACKUP
        CONTENT_BACKUP = content

        if not content:
            alert("Pas de contenu pour ce message !")
            play_low.MY_SUB_PANEL.clear()
            negotiate({}, focus_role_id)
            return

        if not dest_role_ids:
            alert("Pas de destinataire pour ce message !")
            play_low.MY_SUB_PANEL.clear()
            negotiate({}, focus_role_id)
            return

        role_id = play_low.ROLE_ID
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        json_dict = {
            'role_id': play_low.ROLE_ID,
            'dest_role_ids': dest_role_ids,
            'role_name': role_name,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{play_low.GAME_ID}"

        # adding a message in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def messages_reload(game_id):
        """ messages_reload """

        messages = []

        def reply_callback(req):
            nonlocal messages
            req_result = loads(req.text)
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
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return messages

    if play_low.ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # get time stamp of last visit of declarations
    time_stamp_last_visit = common.date_last_visit_load(play_low.GAME_ID, config.MESSAGES_TYPE)

    # copy
    focus_role_id = def_focus_role_id

    # put time stamp of last visit of declarations as now
    date_last_visit_update(play_low.GAME_ID, play_low.ROLE_ID, config.MESSAGES_TYPE)

    role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

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
        role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id_dest, role_name)

        # to restrict
        action = "Focus" if role_id_dest != focus_role_id else "Défocus"
        button_focus = html.BUTTON(action, Class='btn-menu')
        button_focus.bind("click", lambda e, r=role_id_dest: focus_callback(e, r))

        # necessary to link flag with button
        label_dest = html.LABEL(role_icon_img, for_=str(role_id_dest))

        # player
        pseudo_there = ""
        if role_id_dest == 0:
            if play_low.GAME_MASTER:
                pseudo_there = play_low.GAME_MASTER
        elif role_id_dest in role2pseudo:
            player_id_str = role2pseudo[role_id_dest]
            player_id = int(player_id_str)
            pseudo_there = play_low.ID2PSEUDO[player_id]

        # the alternative
        input_dest = html.INPUT(type="checkbox", id=str(role_id_dest), checked=role_id_dest in default_dest_set, Class='btn-inside')

        # create col
        col = html.TD()
        col.style = {
            'width': '70px'
        }

        # now put stuff
        col <= html.CENTER(button_focus)
        col <= html.BR()
        col <= html.CENTER(label_dest)
        col <= html.CENTER(html.B(role_name))
        if pseudo_there:
            col <= html.CENTER(pseudo_there)
        col <= html.CENTER(input_dest)

        row <= col

        selected[role_id_dest] = input_dest

    table <= row
    fieldset <= table
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="Envoyer le message", Class='btn-inside')
    input_declare_in_game.bind("click", add_message_callback)
    form <= input_declare_in_game

    # now we display messages

    messages = messages_reload(play_low.GAME_ID)
    # there can be no message (if no message of failed to load)

    # insert new field 'type'
    messages = [(common.MessageTypeEnum.TEXT, 0, i, f, t, d, c) for (i, f, t, d, c) in messages]

    # get the transition table
    game_transitions = common.game_transitions_reload(play_low.GAME_ID)

    # add fake messages (game transitions)
    fake_messages = [(common.MessageTypeEnum.SEASON, int(k), -1, -1, v, [], common.readable_season(int(k), play_low.VARIANT_DATA)) for k, v in game_transitions.items()]
    messages.extend(fake_messages)

    # get the dropouts table
    game_dropouts = common.game_dropouts_reload(play_low.GAME_ID)

    # add fake messages (game dropouts)
    fake_messages = [(common.MessageTypeEnum.DROPOUT, 0, -1, r, d, [], f"Le joueur {play_low.ID2PSEUDO[p]} avec ce rôle a quitté la partie...") for r, p, d in game_dropouts]
    messages.extend(fake_messages)

    # sort with all that was added
    messages.sort(key=lambda m: (float(m[4]), float(m[1])), reverse=True)

    messages_table = html.TABLE()

    thead = html.THEAD()
    for title in ['id', 'Date', 'Auteur', 'Destinataire(s)', 'Contenu', 'Répondre']:
        col = html.TD(html.B(title))
        thead <= col
    messages_table <= thead

    for type_, _, id_, from_role_id_msg, time_stamp, dest_role_id_msgs, content in messages:

        if type_ is common.MessageTypeEnum.TEXT:
            # if focusing ignore other messages
            if focus_role_id is not None:
                if focus_role_id not in [from_role_id_msg] + dest_role_id_msgs:
                    continue
            class_ = 'text'
        elif type_ is common.MessageTypeEnum.SEASON:
            class_ = 'season'
        elif type_ is common.MessageTypeEnum.DROPOUT:
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
            role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, from_role_id_msg, role_name)
            col <= role_icon_img

            # player
            pseudo_there = ""
            if from_role_id_msg == 0:
                if play_low.GAME_MASTER:
                    pseudo_there = play_low.GAME_MASTER
            elif from_role_id_msg in role2pseudo:
                player_id_str = role2pseudo[from_role_id_msg]
                player_id = int(player_id_str)
                pseudo_there = play_low.ID2PSEUDO[player_id]

            if pseudo_there:
                col <= html.BR()
                if focus_role_id is not None and from_role_id_msg == focus_role_id:
                    pseudo_there = html.B(pseudo_there)
                col <= pseudo_there

        row <= col

        col = html.TD(Class=class_)

        for dest_role_id_msg in dest_role_id_msgs:

            role = play_low.VARIANT_DATA.roles[dest_role_id_msg]
            role_name = play_low.VARIANT_DATA.role_name_table[role]
            role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, dest_role_id_msg, role_name)

            # player
            pseudo_there = ""
            if dest_role_id_msg == 0:
                if play_low.GAME_MASTER:
                    pseudo_there = play_low.GAME_MASTER
            elif dest_role_id_msg in role2pseudo:
                player_id_str = role2pseudo[dest_role_id_msg]
                player_id = int(player_id_str)
                pseudo_there = play_low.ID2PSEUDO[player_id]

            col <= role_icon_img
            if pseudo_there:
                col <= html.BR()
                if focus_role_id is not None and dest_role_id_msg == focus_role_id:
                    pseudo_there = html.B(pseudo_there)
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
            button = html.BUTTON("Répondre", Class='btn-inside')
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
            req_result = loads(req.text)
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
        announce = False

        content = input_declaration.value

        if not content:
            alert("Pas de contenu pour cette déclaration !")
            play_low.MY_SUB_PANEL.clear()
            declare()
            return

        role_id = play_low.ROLE_ID
        if anonymous:
            role_name = ""
        else:
            role = play_low.VARIANT_DATA.roles[role_id]
            role_name = play_low.VARIANT_DATA.role_name_table[role]

        json_dict = {
            'role_id': role_id,
            'anonymous': anonymous,
            'announce': announce,
            'role_name': role_name,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{play_low.GAME_ID}"

        # adding a declaration in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def declarations_reload(game_id):
        """ declarations_reload """

        declarations = []

        def reply_callback(req):
            nonlocal declarations
            req_result = loads(req.text)
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
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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
    input_anonymous = html.INPUT(type="checkbox", Class='btn-inside')
    fieldset <= input_anonymous
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="Déclarer dans la partie", Class='btn-inside')
    input_declare_in_game.bind("click", add_declaration_callback)
    form <= input_declare_in_game

    # now we display declarations

    declarations = declarations_reload(play_low.GAME_ID)
    # there can be no message (if no declaration of failed to load)

    # insert new field 'type'
    declarations = [(common.MessageTypeEnum.TEXT, 0, i, ann, ano, r, t, c) for (i, ann, ano, r, t, c) in declarations]

    # get the transition table
    game_transitions = common.game_transitions_reload(play_low.GAME_ID)

    # add fake declarations (game transitions) and sort
    fake_declarations = [(common.MessageTypeEnum.SEASON, int(k), -1, False, False, -1, v, common.readable_season(int(k), play_low.VARIANT_DATA)) for k, v in game_transitions.items()]
    declarations.extend(fake_declarations)

    # get the dropouts table
    game_dropouts = common.game_dropouts_reload(play_low.GAME_ID)

    # add fake messages (game dropouts)
    fake_declarations = [(common.MessageTypeEnum.DROPOUT, 0, -1, False, False, r, d, f"Le joueur {play_low.ID2PSEUDO[p]} avec ce rôle a quitté la partie...") for r, p, d in game_dropouts]
    declarations.extend(fake_declarations)

    # sort with all that was added
    declarations.sort(key=lambda d: (float(d[6]), float(int(d[2] != -1)), float(d[1])), reverse=True)

    declarations_table = html.TABLE()

    thead = html.THEAD()
    for title in ['id', 'Date', 'Auteur', 'Contenu']:
        col = html.TD(html.B(title))
        thead <= col
    declarations_table <= thead

    role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

    for type_, _, id_, announce, anonymous, role_id_msg, time_stamp, content in declarations:

        if type_ is common.MessageTypeEnum.TEXT:
            if announce:
                class_ = 'text_announce'
            elif anonymous:
                class_ = 'text_anonymous'
            else:
                class_ = 'text'
        elif type_ is common.MessageTypeEnum.SEASON:
            class_ = 'season'
        elif type_ is common.MessageTypeEnum.DROPOUT:
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
        if announce:
            player_id = role_id_msg
            if player_id in play_low.ID2PSEUDO:
                pseudo_there = play_low.ID2PSEUDO[player_id]
        else:
            if role_id_msg != -1:

                role = play_low.VARIANT_DATA.roles[role_id_msg]
                role_name = play_low.VARIANT_DATA.role_name_table[role]
                role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id_msg, role_name)

                # player
                if role_id_msg == 0:
                    if play_low.GAME_MASTER:
                        pseudo_there = play_low.GAME_MASTER
                elif role_id_msg in role2pseudo:
                    player_id_str = role2pseudo[role_id_msg]
                    player_id = int(player_id_str)
                    pseudo_there = play_low.ID2PSEUDO[player_id]

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
            req_result = loads(req.text)
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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        play_low.MY_SUB_PANEL.clear()
        note()

    # from game id and token get role_id of player

    if play_low.ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    content_loaded = common.game_note_reload(play_low.GAME_ID)
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

    input_vote_in_game = html.INPUT(type="submit", value="Enregistrer dans la partie", Class='btn-inside')
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
