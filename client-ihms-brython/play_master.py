""" play """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

from json import loads, dumps
from time import time

from browser import document, window, html, ajax, alert, timer   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import allgames
import mydatetime
import mydialog
import config
import common

import play  # circular import
import play_low
import index


SUPERVISE_REFRESH_TIMER = None


HELP_CONTENT_TABLE = {

    "Comment changer des joueurs ?": "1) retirer le rôle au partant 2) retirer de la partie sélectionnée le partant 3) mettre dans la partie sélectionnée l'arrivant 4) attribuer le role à l'arrivant",
    "Comment bénéficier du bouton permettant de contacter tous les remplaçants ?": "1) et 2) ci-dessus",
    "Comment forcer la fin de la partie (un joueur tarde à entrer une retraite sans importance) ?": "1) Rectifier le paramètre pour mettre la partie en DC autorisé pour cette saison (si besoin) 2) mettre la DL à maintenant 3) forcer un DC pour ce joueur 4) Annuler la première action (car la partie a été jouée sans DC)",
    "Comment annuler toute mauvaise manipulation (dont la mise du vote de fin de la partie) ?": "Contacter l'administrateur",
}


RANDOM = common.Random()


class Logger(list):
    """ Logger """

    def insert(self, message):
        """ insert """

        # insert datation
        time_stamp_now = time()
        date_now_gmt = mydatetime.fromtimestamp(time_stamp_now)
        date_now_gmt_str = mydatetime.strftime(*date_now_gmt)

        # put in stack (limited height)
        log_line = html.DIV(f"{date_now_gmt_str} : {message}", Class='important')
        self.append(log_line)

    def display(self, log_window):
        """ display """

        for log_line in reversed(self):
            log_window <= log_line


def stack_clock(frame, period):
    """ stack_clock """

    clock_icon_img = html.IMG(src="./images/clock.png", title=f"Cette page est rafraichie périodiquement toutes les {period} secondes")
    frame <= clock_icon_img


# how long between two consecutives refresh
SUPERVISE_REFRESH_PERIOD_SEC = 15


def information_about_start_game():
    """ information_about_start_game """

    information = html.DIV(Class='important')
    information <= "Si la partie n'a pas le bon nombre de joueurs, elle ne pourra pas être démarrée !"
    return information


def information_about_distinguish_game1():
    """ information_about_distinguish_game1 """

    information = html.DIV(Class='important')
    information <= "Une partie en attente ne doit être distinguée que si elle doit servir de modèle à une creation de tournoi."
    return information


def information_about_distinguish_game2():
    """ information_about_distinguish_game2 """

    information = html.DIV(Class='important')
    information <= "Une partie terminée ne doit être distinguée que si elle est copie d'une partie jouée ailleurs."
    return information


def get_game_allocated_players(game_id):
    """ get_available_players returns a tuple game_master + players """

    game_master_id = None
    players_allocated_list = None
    players_assigned_list = None

    def reply_callback(req):
        nonlocal game_master_id
        nonlocal players_allocated_list
        nonlocal players_assigned_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des joueurs de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des joueurs de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        game_masters_list = [int(k) for k, v in req_result.items() if v == 0]
        game_master_id = game_masters_list.pop()
        players_allocated_list = [int(k) for k, v in req_result.items() if v == -1]
        players_assigned_list = [int(k) for k, v in req_result.items() if v > 0]

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-allocations/{game_id}"

    # get players allocated to game : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return game_master_id, players_allocated_list, players_assigned_list


def game_master():
    """ game_master """

    players_dict = {}
    allocated = []

    def edit_game_callback(ev):  # pylint: disable=invalid-name
        """ edit_game_callback """

        ev.preventDefault()

        # action of going to edit game page
        play_low.PANEL_MIDDLE.clear()
        allgames.set_arrival()
        allgames.render(play_low.PANEL_MIDDLE)

    def end_game_vote_callback(ev):  # pylint: disable=invalid-name
        """ edit_game_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la mise en l'état 'fin votée' de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la mise en l'état 'fin votée' de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # fail but refresh
                play_low.MY_SUB_PANEL.clear()
                game_master()
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"La partie a été mise dans l'état 'fin votée' : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        ev.preventDefault()

        json_dict = {
            'name': play_low.GAME,
            'end_voted': 1,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game state : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def cancel_change_state_game_callback(_, dialog):
        """ cancel_delete_account_callback """
        dialog.close(None)

    def change_state_game_callback(ev, dialog, expected_state):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de l'état de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de l'état de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # fail but refresh
                play_low.MY_SUB_PANEL.clear()
                game_master()
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"L'état de la partie a été modifié : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            play_low.load_special_stuff()
            game_master()

        ev.preventDefault()

        if dialog is not None:
            dialog.close(None)

        json_dict = {
            'name': play_low.GAME,
            'current_state': expected_state,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game state : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def change_state_game_callback_confirm(ev, expected_state):  # pylint: disable=invalid-name

        ev.preventDefault()

        dialog = mydialog.Dialog(f"On arrête vraiment la partie {play_low.GAME} ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog, es=expected_state: change_state_game_callback(e, d, es))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_change_state_game_callback(e, d))

        # back to where we started
        play_low.MY_SUB_PANEL.clear()
        game_master()

    def cancel_delete_game_callback(_, dialog):
        """ cancel_delete_game_callback """
        dialog.close(None)

    def delete_game_callback(ev, dialog):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppression de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppression de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"La partie a été supprimée : {messages}", True)
            allgames.unselect_game()

            # go to select another game
            index.load_option(None, 'Accueil')

        ev.preventDefault()

        dialog.close(None)

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # deleting game : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def delete_game_callback_confirm(ev):  # pylint: disable=invalid-name
        """ delete_game_callback_confirm """

        ev.preventDefault()

        dialog = mydialog.Dialog(f"On supprime vraiment la partie {play_low.GAME} ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog: delete_game_callback(e, d))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_delete_game_callback(e, d))

        # back to where we started
        play_low.MY_SUB_PANEL.clear()
        game_master()

    def callback_download_game_csv(ev):  # pylint: disable=invalid-name
        """ callback_download_game_csv """
        ev.preventDefault()

        # needed too for some reason
        play_low.MY_SUB_PANEL <= html.A(id='download_link')

        role_name2_centers = play_low.POSITION_DATA.role_ratings()

        result_list = []
        for role_id in play_low.VARIANT_DATA.roles:

            if role_id == 0:
                continue

            pseudo_there = ""
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id = int(player_id_str)
                pseudo_there = play_low.ID2PSEUDO[player_id]

            role = play_low.VARIANT_DATA.roles[role_id]
            role_name = play_low.VARIANT_DATA.role_name_table[role]
            n_centers = role_name2_centers[role_name]

            result = ','.join([role_name, pseudo_there, str(n_centers)])
            result_list.append(result)

        result_csv = '\n'.join(result_list)

        # perform actual exportation
        text_file_as_blob = window.Blob.new([result_csv], {'type': 'text/plain'})
        download_link = document['download_link']
        download_link.download = f"diplomania_{play_low.GAME}_{play_low.GAME_ID}_result.csv"
        download_link.href = window.URL.createObjectURL(text_file_as_blob)
        document['download_link'].click()

    def put_in_game_callback(ev):  # pylint: disable=invalid-name
        """ put_in_game_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la mise d'un joueur dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la mise d'un joueur dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                play_low.MY_SUB_PANEL.clear()
                game_master()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le joueur a été mis dans la partie: {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_special_stuff()
            game_master()

        ev.preventDefault()

        player_pseudo = input_incomer.value

        json_dict = {
            'game_id': play_low.GAME_ID,
            'player_pseudo': player_pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # putting a player in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def remove_from_game_callback(ev):  # pylint: disable=invalid-name
        """remove_from_game_callback"""

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au retrait d'un joueur de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au retrait d'un joueur de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                play_low.MY_SUB_PANEL.clear()
                game_master()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le joueur a été retiré de la partie: {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_special_stuff()
            game_master()

        ev.preventDefault()

        player_pseudo = input_outcomer.value

        json_dict = {
            'game_id': play_low.GAME_ID,
            'player_pseudo': player_pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # removing a player from a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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
            mydialog.InfoDialog("Information", f"L'abandon a été supprimé : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            game_master()

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
            mydialog.InfoDialog("Information", f"L'incident a été supprimé : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            game_master()

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
        game_master()

    def remove_incident_callback_confirm(ev, role_id, advancement, text):  # pylint: disable=invalid-name
        """ remove_incident_callback_confirm """

        ev.preventDefault()

        dialog = mydialog.Dialog(f"On supprime vraiment cet incident pour {text} ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog, r=role_id, a=advancement: remove_incident_callback(e, d, r, a))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_remove_incident_callback(e, d))

        # back to where we started
        play_low.MY_SUB_PANEL.clear()
        game_master()

    def clear_vote_callback(ev, role_id):  # pylint: disable=invalid-name
        """ clear_vote_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'effacement de vote d'arrêt dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'effacement de vote d'arrêt dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le vote a été effacé ! {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            game_master()

        ev.preventDefault()

        json_dict = {
            'role_id': role_id,
            'value': False
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-votes/{play_low.GAME_ID}"

        # adding a vote in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        play_low.MY_SUB_PANEL.clear()
        game_master()

    def debrief_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au debrief de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au debrief de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"La partie a été modifiée pour le debrief : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        ev.preventDefault()

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/debrief-game/{play_low.GAME}"

        # debrief : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def change_deadline_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de la date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"La date limite a été modifiée : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        ev.preventDefault()

        # convert this human entered deadline to the deadline the server understands
        deadline_day_part = input_deadline_day.value
        deadline_hour_part = input_deadline_hour.value

        dt_year, dt_month, dt_day = map(int, deadline_day_part.split('-'))
        dt_hour, dt_min, dt_sec = map(int, deadline_hour_part.split(':'))

        deadline_timestamp = mydatetime.totimestamp(dt_year, dt_month, dt_day, dt_hour, dt_min, dt_sec)

        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
        if deadline_timestamp < deadline_loaded:
            alert("Attention, vous êtes en train de reculer la date limite !")

        time_stamp_now = time()
        if deadline_timestamp < time_stamp_now:
            alert("Désolé, il est interdit de positionner une date limite dans le passé")
            # back to where we were
            play_low.MY_SUB_PANEL.clear()
            game_master()
            return

        json_dict = {
            'name': play_low.GAME,
            'deadline': deadline_timestamp,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def push_deadline_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au poussage de date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au poussage de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"La date limite a été reportée : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        ev.preventDefault()

        # get deadline
        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']

        # add one day - if fast game change to one minute
        time_unit = 60 if play_low.GAME_PARAMETERS_LOADED['fast'] else 24 * 60 * 60
        deadline_forced = deadline_loaded + time_unit

        # push on server
        json_dict = {
            'name': play_low.GAME,
            'deadline': deadline_forced,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def sync_deadline_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la synchro de date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la synchro de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"La date limite a été synchronisée : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        ev.preventDefault()

        # push on server
        json_dict = {
            'name': play_low.GAME,
            'deadline': 0,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def force_wait_game_callback(ev, force):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au forçage attente date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au forçage attente de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            desc = {-1: 'Maintenant (au plus tôt)', 0: 'Pas de forçage', 1: 'A la date limite (au plus tard)'}[force]
            mydialog.InfoDialog("Information", f"Le forçage d'attente à été mis à  {desc} : {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            game_master()

        ev.preventDefault()

        # push on server
        json_dict = {
            'name': play_low.GAME,
            'force_wait': force,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{play_low.GAME}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_recall_orders_email_callback(ev, role_id):  # pylint: disable=invalid-name
        """ send_recall_orders_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de rappel (ordres manquants) : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de rappel (ordres manquants) : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            mydialog.InfoDialog("Information", f"Message de rappel (manque ordres) émis vers : {pseudo_there}")

        ev.preventDefault()

        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
        time_stamp_now = time()
        if not time_stamp_now > deadline_loaded:
            alert("Attendez que la date limite soit passée pour réclamer les ordres, sinon le joueur va crier à l'injustice :-)")
            return

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site {config.SITE_ADDRESS} (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !\n"
        body += "\n"
        body += "Il manque vos ordres et la date limite est passée. Merci d'aviser rapidement !"
        body += "\n"
        body += f"Pour rappel votre rôle est {role_name}."
        body += "\n"
        body += "Attention, au bout d'un certain nombre de jours de retards (variable selon les règles du tournoi ou la patience de l'arbitre), les arbitres remplacent un retardataire pour que la partie avance."
        body += "\n"
        body += "Lors de la première saison, cela peut être immédiat car on considère que le nouveau joueur n'a pas/plus l'intention de jouer."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"{config.SITE_ADDRESS}?game={play_low.GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = play_low.ID2PSEUDO[player_id]

        addressed_id = play_low.PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'type': 'reminder',
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_recall_agreed_email_callback(ev, role_id):  # pylint: disable=invalid-name
        """ send_recall_agreed_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de rappel (manque accord pour résoudre) : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de rappel (manque accord pour résoudre) : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            mydialog.InfoDialog("Information", f"Message de rappel (manque d'accord pour résoudre) émis vers : {pseudo_there}")

        ev.preventDefault()

        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
        time_stamp_now = time()
        if not time_stamp_now > deadline_loaded:
            alert("Attendez que la date limite soit passée pour réclamer l'accord, sinon le joueur va crier à l'injustice :-)")
            return

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site {config.SITE_ADDRESS} (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !\n"
        body += "\n"
        body += "Il manque votre confirmation d'être d'accord pour résoudre et la date limite est passée. Merci d'aviser rapidement !"
        body += "\n"
        body += f"Pour rappel votre rôle est {role_name}."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"{config.SITE_ADDRESS}?game={play_low.GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = play_low.ID2PSEUDO[player_id]

        addressed_id = play_low.PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'type': 'reminder',
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_welcome_email_callback(ev, role_id):  # pylint: disable=invalid-name
        """ send_welcome_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de bienvenue : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de bienvenue: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            mydialog.InfoDialog("Information", f"Message de bienvenue émis vers : {pseudo_there}")

        ev.preventDefault()

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site {config.SITE_ADDRESS} (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !\n"
        body += "\n"
        body += "Nous avons l'immense honneur de vous informer que vous avez été mis dans la partie et pouvez donc commencer à jouer !"
        body += "\n"
        body += f"Le rôle qui vous a été attribué est {role_name}."
        body += "\n"
        body += "Conseil : ne tardez pas trop à entrer vos ordres. En effet, certains arbitres remplacent immédiatement un joueur en retard au premier tour."
        body += "\n"
        body += "Ce serait dommage de, par une petite négligence, perdre cette magnifique oppotunité de jouer une partie de Diplomacy !"
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"{config.SITE_ADDRESS}?game={play_low.GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = play_low.ID2PSEUDO[player_id]

        addressed_id = play_low.PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'type': 'reminder',
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_need_replacement_callback(ev, role_id):  # pylint: disable=invalid-name
        """ send_need_replacement_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de demande de remplacement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de demande de remplacement: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            mydialog.InfoDialog("Information", "Message de demande de remplacement émis vers les remplaçants potentiels")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            game_master()

        ev.preventDefault()

        subject = f"Message de la part de l'arbitre de la partie {play_low.GAME} sur le site {config.SITE_ADDRESS} (AFJD)"

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        body = "Bonjour !\n"
        body += "\n"
        body += "Cette partie a besoin d'un remplaçant. Vous aves demandé à être notifié dans un tel cas. Son arbitre vous sollicite !"
        body += "\n"
        body += f"Le rôle qui est libre est {role_name}."
        body += "\n"
        body += "Comment s'y prendre ? Aller sur le site, onglet 'Rejoindre une partie' et cliquez sur le bouton dans la colonne 'rejoindre' de la ligne de la partie en rose (Il peut être judicieux d'aller tâter un peu la partie au préalable)"
        body += "\n"
        body += "Note : Vous pouvez désactiver cette notification en modifiant un paramètre de votre compte sur le site.\n"
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"{config.SITE_ADDRESS}?game={play_low.GAME}"

        # need to filter here otherwise there would be too many
        players_dict = common.get_players_data()
        if not players_dict:
            alert("Erreur chargement dictionnaire joueurs")
            return
        addressees = [p for p in players_dict if players_dict[str(p)]['notify_replace']]

        json_dict = {
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'type': 'replacement',
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def civil_disorder_callback(ev, role_id):  # pylint: disable=invalid-name
        """ civil_disorder_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de désordre civil dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de désordre civil dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le joueur s'est vu infligé des ordres de désordre civil: {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            game_master()

        ev.preventDefault()

        names_dict = play_low.VARIANT_DATA.extract_names()
        names_dict_json = dumps(names_dict)

        json_dict = {
            'role_id': role_id,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-no-orders/{play_low.GAME_ID}"

        # submitting civil disorder : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def force_agreement_callback(ev, role_id):  # pylint: disable=invalid-name
        """ force_agreement_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'accord forcé pour résoudre dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'accord forcé pour résoudre dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le joueur s'est vu imposé un accord pour résoudre: {messages}")

            adjudicated = req_result['adjudicated']
            if adjudicated:
                alert("La position de la partie a changé !")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_dynamic_stuff()
            play_low.load_special_stuff()
            game_master()

        ev.preventDefault()

        inforced_names_dict = play_low.INFORCED_VARIANT_DATA.extract_names()
        inforced_names_dict_json = dumps(inforced_names_dict)

        json_dict = {
            'role_id': role_id,
            'adjudication_names': inforced_names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-agree-solve/{play_low.GAME_ID}"

        # submitting force agreement : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def unallocate_role_callback(ev, pseudo_removed, role_id):  # pylint: disable=invalid-name
        """ unallocate_role_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la désallocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème Erreur à la désallocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le joueur s'est vu retirer le rôle dans la partie: {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_special_stuff()
            game_master()

        ev.preventDefault()

        json_dict = {
            'game_id': play_low.GAME_ID,
            'role_id': role_id,
            'player_pseudo': pseudo_removed,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def allocate_role_callback(ev, input_for_role, role_id):  # pylint: disable=invalid-name
        """ allocate_role_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'allocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'allocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le joueur s'est vu attribuer le rôle dans la partie: {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            play_low.load_special_stuff()
            game_master()

        ev.preventDefault()

        player_pseudo = input_for_role.value

        json_dict = {
            'game_id': play_low.GAME_ID,
            'role_id': role_id,
            'player_pseudo': player_pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def get_list_pseudo_allocatable_game():
        """ get_list_pseudo_allocatable_game """

        pseudo_list = None

        def reply_callback(req):
            nonlocal pseudo_list
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de la liste des joueurs allouables dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de la liste des joueurs allouables dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return None

            pseudo_list = [play_low.ID2PSEUDO[int(k)] for k, v in req_result.items() if v == -1]
            return pseudo_list

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-allocations/{play_low.GAME_ID}"

        # get roles that are allocated to game : do not need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return pseudo_list

    # need to be connected
    if play_low.PSEUDO is None:
        alert("Il faut se connecter au préalable")
        play.load_option(None, 'Consulter')
        return False

    # need to be game master
    if play_low.ROLE_ID != 0:
        alert("Vous ne semblez pas être l'arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # check game soloed
    if play_low.GAME_PARAMETERS_LOADED['soloed']:
        alert("La partie est terminée parce qu'un solo a été réalisé !")

    # check game end voted
    elif play_low.GAME_PARAMETERS_LOADED['end_voted']:
        alert("La partie est terminée sur un vote de fin unanime !")

    # check game finished (if not soloed nor end voted)
    elif play_low.GAME_PARAMETERS_LOADED['finished']:
        alert("La partie est terminée parce qu'arrivée à échéance")

    # warning if game not waiting or ongoing
    if play_low.GAME_PARAMETERS_LOADED['current_state'] not in [0, 1]:
        mydialog.InfoDialog("Information", "Cette partie est terminée !")

    advancement_loaded = play_low.GAME_PARAMETERS_LOADED['current_advancement']

    players_dict = common.get_players()
    if not players_dict:
        alert("Erreur chargement joueurs")
        return False
    id2pseudo = {v: k for k, v in players_dict.items()}

    allocated = get_game_allocated_players(play_low.GAME_ID)
    if allocated is None:
        alert("Erreur chargement allocations joueurs")
        return False

    # now we can display

    # header

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    # role flag
    play_low.stack_role_flag(play_low.MY_SUB_PANEL)

    # get the incidents of the game
    game_incidents = play_low.game_master_incidents_reload(play_low.GAME_ID)
    game_incidents2 = play_low.game_incidents2_reload(play_low.GAME_ID)

    # get the actual dropouts of the game
    game_dropouts = common.game_dropouts_reload(play_low.GAME_ID)
    # there can be no dropouts (if no incident of failed to load)

    ############################################
    if play_low.GAME_PARAMETERS_LOADED['current_state'] == 1:

        play_low.MY_SUB_PANEL <= html.H3("Gestion")

        role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

        submitted_data = play_low.get_roles_submitted_orders(play_low.GAME_ID)
        if not submitted_data:
            alert("Erreur chargement données de soumission")
            play.load_option(None, 'Consulter')
            return False

        # who can I put in this role
        possible_given_role = get_list_pseudo_allocatable_game()

        # votes

        votes = play_low.game_votes_reload(play_low.GAME_ID)
        if votes is None:
            alert("Erreur chargement votes")
            play.load_option(None, 'Consulter')
            return False

        votes = list(votes)

        vote_values_table = {}
        for _, role, vote_val in votes:
            vote_values_table[role] = bool(vote_val)

        submitted_roles_list = submitted_data['submitted']
        agreed_now_roles_list = submitted_data['agreed_now']
        agreed_after_roles_list = submitted_data['agreed_after']
        needed_roles_list = submitted_data['needed']

        game_admin_table = html.TABLE()

        thead = html.THEAD()
        for field in ['drapeau', 'rôle', 'joueur', '', 'retards', 'désordres', '', 'communiquer la bienvenue', '', 'ordres du joueur', 'demander les ordres', 'mettre en désordre civil', '', 'accord du joueur', 'demander l\'accord', 'forcer l\'accord', '', 'vote du joueur', '', 'retirer le rôle', 'attribuer le rôle']:
            col = html.TD(field)
            thead <= col
        game_admin_table <= thead

        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
        time_stamp_now = time()

        for role_id in play_low.VARIANT_DATA.roles:

            # discard game master
            if role_id == 0:
                continue

            row = html.TR()

            role = play_low.VARIANT_DATA.roles[role_id]
            role_name = play_low.VARIANT_DATA.role_name_table[role]

            # flag
            col = html.TD()
            role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)
            col <= role_icon_img
            row <= col

            # role name
            col = html.TD()
            col <= role_name
            row <= col

            # player
            col = html.TD()
            pseudo_there = ""
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id = int(player_id_str)
                pseudo_there = play_low.ID2PSEUDO[player_id]
            col <= pseudo_there
            row <= col

            # separator
            col = html.TD()
            row <= col

            # delays
            col = html.TD()
            num_delays = ""
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id = int(player_id_str)
                num_delays = len([_ for role_id2, _, player_id2, _, _ in game_incidents if role_id2 == role_id and player_id2 is None])
            col <= num_delays
            row <= col

            # cds
            col = html.TD()
            num_disorders = ""
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id = int(player_id_str)
                num_disorders = len([_ for role_id2, _, _ in game_incidents2 if role_id2 == role_id])
            col <= num_disorders
            row <= col

            # separator
            col = html.TD()
            row <= col

            col = html.TD()
            input_send_welcome_email = ""
            if str(role_id) not in play_low.VARIANT_CONTENT_LOADED['disorder']:
                if pseudo_there:
                    input_send_welcome_email = html.INPUT(type="submit", value="Courriel bienvenue", title="Ceci enverra un courriel de bienvenue au joueur. A utiliser pour un nouveau joueur ou au démarrage de la partie", Class='btn-inside')
                    input_send_welcome_email.bind("click", lambda e, r=role_id: send_welcome_email_callback(e, r))
            col <= input_send_welcome_email
            row <= col

            # separator
            col = html.TD()
            row <= col

            col = html.TD()
            flag = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
                else:
                    flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
            col <= flag
            row <= col

            col = html.TD()
            input_send_recall_email = ""
            if role_id in needed_roles_list:
                if role_id not in submitted_roles_list:
                    if pseudo_there:
                        if time_stamp_now > deadline_loaded:
                            input_send_recall_email = html.INPUT(type="submit", value="Courriel rappel ordres", title="Ceci enverra un courriel pour rappeler au joueur d'entrer des ordres dans le système", Class='btn-inside')
                            input_send_recall_email.bind("click", lambda e, r=role_id: send_recall_orders_email_callback(e, r))
            col <= input_send_recall_email
            row <= col

            col = html.TD()
            input_civil_disorder = ""
            if role_id in needed_roles_list:
                if role_id not in submitted_roles_list:
                    if pseudo_there:
                        if time_stamp_now > deadline_loaded:

                            allowed = play_low.civil_disorder_allowed(advancement_loaded)

                            if allowed:
                                input_civil_disorder = html.INPUT(type="submit", value="Désordre civil", title="Ceci forcera des ordres de désordre civil pour le joueur dans le système", Class='btn-inside')
                                input_civil_disorder.bind("click", lambda e, r=role_id: civil_disorder_callback(e, r))

            col <= input_civil_disorder
            row <= col

            # separator
            col = html.TD()
            row <= col

            col = html.TD()
            flag = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    if role_id in agreed_now_roles_list:
                        flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre maintenant")
                    elif role_id in agreed_after_roles_list:
                        flag = html.IMG(src="./images/agreed_after.jpg", title="D'accord pour résoudre à la date limite")
                    else:
                        flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")
            col <= flag
            row <= col

            col = html.TD()
            input_send_recall_email = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    if role_id not in agreed_now_roles_list and role_id not in agreed_after_roles_list:
                        if pseudo_there:
                            if time_stamp_now > deadline_loaded:
                                input_send_recall_email = html.INPUT(type="submit", value="Courriel rappel accord", title="Ceci enverra un courriel demandant au joueur de manifester son accord pour résoudre la partie", Class='btn-inside')
                                input_send_recall_email.bind("click", lambda e, r=role_id: send_recall_agreed_email_callback(e, r))
            col <= input_send_recall_email
            row <= col

            col = html.TD()
            input_force_agreement = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    if role_id not in agreed_now_roles_list and role_id not in agreed_after_roles_list:
                        if pseudo_there:
                            if time_stamp_now > deadline_loaded:

                                allowed = play_low.civil_disorder_allowed(advancement_loaded)

                                if allowed:
                                    input_force_agreement = html.INPUT(type="submit", value="Forcer accord", title="Ceci forcera l'accord pour résoudre du joueur, déclenchant éventuellement la résolution", Class='btn-inside')
                                    input_force_agreement.bind("click", lambda e, r=role_id: force_agreement_callback(e, r))

            col <= input_force_agreement
            row <= col

            # separator
            col = html.TD()
            row <= col
            col = html.TD()

            tab2 = html.TABLE()
            row2 = html.TR()
            if role_id in vote_values_table:

                # must show gm vote value
                col2 = html.TD()
                if vote_values_table[role_id]:
                    flag = html.IMG(src="./images/stop.png", title="Le joueur a voté pour arrêter la partie")
                else:
                    flag = html.IMG(src="./images/continue.jpg", title="Le joueur a voté pour continuer la partie")
                col2 <= flag
                row2 <= col2

                # gm must be able to clear vote
                col2 = html.TD()
                form = html.FORM()
                clear_vote = html.INPUT(type="submit", value="X", Class='btn-inside')
                clear_vote.bind("click", lambda ev, r=role_id: clear_vote_callback(ev, r))
                form <= clear_vote
                col2 <= form
                row2 <= col2

            tab2 <= row2
            col <= tab2
            row <= col

            # separator
            col = html.TD()
            row <= col

            col = html.TD()
            input_unallocate_role = ""
            if str(role_id) not in play_low.VARIANT_CONTENT_LOADED['disorder']:
                if pseudo_there:
                    input_unallocate_role = html.INPUT(type="submit", value="Retirer le rôle", title="Ceci enlèvera le rôle au joueur", Class='btn-inside')
                    input_unallocate_role.bind("click", lambda e, p=pseudo_there, r=role_id: unallocate_role_callback(e, p, r))
            col <= input_unallocate_role
            row <= col

            col = html.TD()
            form = ""
            if not pseudo_there:

                if not possible_given_role and play_low.GAME_PARAMETERS_LOADED['current_state'] == 1:

                    form = html.FORM()
                    input_contact_replacers = html.INPUT(type="submit", value="Contacter les remplaçants", title="Ceci contactera tous les remplaçants déclarés volontaires du site", display='inline', Class='btn-inside')
                    input_contact_replacers.bind("click", lambda e, r=role_id: send_need_replacement_callback(e, r))
                    form <= input_contact_replacers

                elif not (play_low.GAME_PARAMETERS_LOADED['current_state'] == 0 and not play_low.GAME_PARAMETERS_LOADED['manual']):

                    form = html.FORM()
                    input_for_role = html.SELECT(type="select-one", value="", display='inline', Class='btn-inside')
                    for play_role_pseudo in sorted(possible_given_role, key=lambda p: p.upper()):
                        option = html.OPTION(play_role_pseudo)
                        input_for_role <= option
                    form <= input_for_role
                    form <= " "
                    input_put_in_role = html.INPUT(type="submit", value="Attribuer le rôle", title="Ceci attribuera le rôle au joueur", display='inline', Class='btn-inside')
                    input_put_in_role.bind("click", lambda e, i=input_for_role, r=role_id: allocate_role_callback(e, i, r))
                    form <= input_put_in_role

            col <= form
            row <= col

            game_admin_table <= row

        play_low.MY_SUB_PANEL <= game_admin_table

    ############################################
    if play_low.GAME_PARAMETERS_LOADED['current_state'] in [0, 1]:

        play_low.MY_SUB_PANEL <= html.H3("Date limite")

        # form for deadlines
        play_low.MY_SUB_PANEL <= html.DIV("Pour la DL applicable pour le reste de la partie, aller dans les paramètres.", Class='note')
        play_low.MY_SUB_PANEL <= html.BR()

        table = html.TABLE()
        row = html.TR()

        deadline_form = html.FORM()

        dl_gmt = html.DIV("ATTENTION : vous devez entrer une valeur en temps GMT.", Class='important')
        special_legend = html.LEGEND(dl_gmt)
        deadline_form <= special_legend
        deadline_form <= html.BR()

        # get GMT date and time
        time_stamp_now = time()
        date_now_gmt = mydatetime.fromtimestamp(time_stamp_now)
        date_now_gmt_str = mydatetime.strftime(*date_now_gmt)

        # convert 'deadline_loaded' to human editable format
        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']

        datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
        datetime_deadline_loaded_str = mydatetime.strftime(*datetime_deadline_loaded, year_first=True)
        deadline_loaded_day, deadline_loaded_hour, _ = datetime_deadline_loaded_str.split(' ')

        fieldset = html.FIELDSET()
        legend_deadline_day = html.LEGEND("Jour de la prochaine D.L. (DD/MM/YYYY - ou selon les réglages du navigateur)", title="La date limite. Dernier jour pour soumettre les ordres. Après le joueur est en retard.")
        fieldset <= legend_deadline_day
        input_deadline_day = html.INPUT(type="date", value=deadline_loaded_day, Class='btn-inside')
        fieldset <= input_deadline_day
        deadline_form <= fieldset

        fieldset = html.FIELDSET()
        legend_deadline_hour = html.LEGEND("Heure de la prochaine D.L. (hh:mm ou selon les réglages du navigateur)", title="La date limite. Dernière heure du jour pour soumettre les ordres. Après le joueur est en retard.")
        fieldset <= legend_deadline_hour
        input_deadline_hour = html.INPUT(type="time", value=deadline_loaded_hour, step=1, Class='btn-inside')
        fieldset <= input_deadline_hour
        deadline_form <= fieldset

        input_change_deadline_game = html.INPUT(type="submit", value="Changer la prochaine D.L. de la partie à cette valeur", Class='btn-inside')
        input_change_deadline_game.bind("click", change_deadline_game_callback)
        deadline_form <= input_change_deadline_game

        col = html.TD()
        col <= deadline_form
        row <= col

        if play_low.GAME_PARAMETERS_LOADED['current_state'] == 1:

            deadline_form2 = html.FORM()
            input_push_deadline_game = html.INPUT(type="submit", value="Reporter la prochaine D.L. de 24 heures", Class='btn-inside')
            input_push_deadline_game.bind("click", push_deadline_game_callback)
            deadline_form2 <= input_push_deadline_game

            col = html.TD()
            col <= deadline_form2
            row <= col

            deadline_form3 = html.FORM()
            input_push_deadline_game = html.INPUT(type="submit", value="Mettre la prochaine D.L. à maintenant", Class='btn-inside')
            input_push_deadline_game.bind("click", sync_deadline_game_callback)
            deadline_form3 <= input_push_deadline_game

            col = html.TD()
            col <= deadline_form3
            row <= col

            deadline_form4 = html.FORM()

            if play_low.GAME_PARAMETERS_LOADED['force_wait'] != -1:
                input_force_wait_game = html.INPUT(type="submit", value="Forcer les résolutions à maintenant (au plus tôt)", Class='btn-inside')
                input_force_wait_game.bind("click", lambda e, f=-1: force_wait_game_callback(e, f))
                deadline_form4 <= input_force_wait_game
                deadline_form4 <= html.BR()
                deadline_form4 <= html.BR()
            if play_low.GAME_PARAMETERS_LOADED['force_wait'] != 0:
                input_force_wait_game = html.INPUT(type="submit", value="Ne rien forcer", Class='btn-inside')
                input_force_wait_game.bind("click", lambda e, f=0: force_wait_game_callback(e, f))
                deadline_form4 <= input_force_wait_game
                deadline_form4 <= html.BR()
                deadline_form4 <= html.BR()
            if play_low.GAME_PARAMETERS_LOADED['force_wait'] != 1:
                input_force_wait_game = html.INPUT(type="submit", value="Forcer les résolutions à la D.L. (au plus tard)", Class='btn-inside')
                input_force_wait_game.bind("click", lambda e, f=1: force_wait_game_callback(e, f))
                deadline_form4 <= input_force_wait_game
                deadline_form4 <= html.BR()
                deadline_form4 <= html.BR()

            col = html.TD()
            col <= deadline_form4
            row <= col

        table <= row
        play_low.MY_SUB_PANEL <= table

        play_low.MY_SUB_PANEL <= html.BR()
        play_low.MY_SUB_PANEL <= html.DIV(f"Pour information, date et heure actuellement sur votre horloge locale : {date_now_gmt_str}")

    ############################################
    if play_low.GAME_PARAMETERS_LOADED['current_state'] == 1 and (play_low.GAME_PARAMETERS_LOADED['soloed'] or play_low.GAME_PARAMETERS_LOADED['end_voted'] or play_low.GAME_PARAMETERS_LOADED['finished']):

        play_low.MY_SUB_PANEL <= html.H3("Debrief de la partie")

        # form for debrief

        debrief_form = html.FORM()

        debrief_action = html.DIV("Lève l'anonymat et ouvre les canaux de communication (réversible)", Class='None')
        special_legend = html.LEGEND(debrief_action)
        debrief_form <= special_legend

        debrief_form <= html.BR()
        input_debrief_game = html.INPUT(type="submit", value="Debrief !", Class='btn-inside')
        input_debrief_game.bind("click", debrief_game_callback)
        debrief_form <= input_debrief_game

        play_low.MY_SUB_PANEL <= html.BR()
        play_low.MY_SUB_PANEL <= debrief_form

    ############################################
    play_low.MY_SUB_PANEL <= html.H3("Déplacement de joueurs")

    row = html.TR()

    game_master_id, players_allocated_ids_list, players_assigned_ids_list = allocated

    players_allocated_list = [id2pseudo[i] for i in list(players_allocated_ids_list)]
    players_assigned_list = [id2pseudo[i] for i in list(players_assigned_ids_list)]

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_incomer = html.LEGEND("Entrant", title="Sélectionner le joueur à mettre dans la partie")
    fieldset <= legend_incomer

    # all players can come in
    possible_incomers = set(players_dict.keys())

    # not those already in
    possible_incomers -= set(players_allocated_list)
    possible_incomers -= set(players_assigned_list)

    # not the operator
    possible_incomers -= set([play_low.PSEUDO])

    # not the gm of the game
    possible_incomers -= set([game_master_id])

    input_incomer = html.SELECT(type="select-one", value="", Class='btn-inside')
    for play_pseudo in sorted(possible_incomers, key=lambda pi: pi.upper()):
        option = html.OPTION(play_pseudo)
        input_incomer <= option

    fieldset <= input_incomer
    form <= fieldset

    form <= html.BR()

    input_put_in_game = html.INPUT(type="submit", value="Mettre dans la partie sélectionnée", Class='btn-inside')
    input_put_in_game.bind("click", put_in_game_callback)
    form <= input_put_in_game

    form <= html.BR()
    form <= html.BR()

    fieldset = html.FIELDSET()
    fieldset <= html.LEGEND("Ont un rôle : ")
    fieldset <= html.DIV(" ".join(sorted(list(set(players_assigned_list)), key=lambda p: p.upper())), Class='note')
    form <= fieldset

    form <= html.BR()

    fieldset = html.FIELDSET()
    fieldset <= html.LEGEND("Sont en attente : ")
    fieldset <= html.DIV(" ".join(sorted(list(set(players_allocated_list)), key=lambda p: p.upper())), Class='note')
    form <= fieldset

    col = html.TD()
    col <= form
    row <= col

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_outcomer = html.LEGEND("Sortant", title="Sélectionner le joueur à retirer de la partie")
    fieldset <= legend_outcomer

    # players can come out are the ones not assigned
    possible_outcomers = players_allocated_list

    input_outcomer = html.SELECT(type="select-one", value="", Class='btn-inside')
    for play_pseudo in sorted(possible_outcomers):
        option = html.OPTION(play_pseudo)
        input_outcomer <= option

    fieldset <= input_outcomer
    form <= fieldset

    form <= html.BR()

    input_remove_from_game = html.INPUT(type="submit", value="Retirer de la partie sélectionnée", Class='btn-inside')
    input_remove_from_game.bind("click", remove_from_game_callback)
    form <= input_remove_from_game

    col = html.TD()
    col <= form
    row <= col

    table = html.TABLE()
    table <= row
    play_low.MY_SUB_PANEL <= table

    ############################################
    if play_low.GAME_PARAMETERS_LOADED['current_state'] in [1, 2]:

        play_low.MY_SUB_PANEL <= html.H3("Suppression des incidents")

        play_low.MY_SUB_PANEL <= html.H4("Suppression d'abandons")

        game_dropouts_table = html.TABLE()

        fields = ['flag', 'role', 'pseudo', 'date', 'remove']

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
            datetime_incident_str = mydatetime.strftime(*datetime_incident, year_first=True)
            col = html.TD(datetime_incident_str)
            row <= col

            # remove
            form = html.FORM()
            input_remove_dropout = html.INPUT(type="submit", value="Supprimer", Class='btn-inside')
            text = f"Rôle {role_name} et joueur {pseudo_quitter}"
            input_remove_dropout.bind("click", lambda e, r=role_id, p=player_id, t=text: remove_dropout_callback_confirm(e, r, p, t))
            form <= input_remove_dropout
            col = html.TD(form)
            row <= col

            game_dropouts_table <= row

        play_low.MY_SUB_PANEL <= game_dropouts_table

        # incidents
        play_low.MY_SUB_PANEL <= html.H4("Suppression de retards")

        game_incidents_table = html.TABLE()

        fields = ['flag', 'role', 'pseudo', 'season', 'duration', 'date', 'remove']

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
            datetime_incident_str = mydatetime.strftime(*datetime_incident, year_first=True)
            col = html.TD(datetime_incident_str)
            row <= col

            # remove
            form = html.FORM()
            input_remove_incident = html.INPUT(type="submit", value="Supprimer", Class='btn-inside')
            text = f"Rôle {role_name} en saison {game_season}"
            input_remove_incident.bind("click", lambda e, r=role_id, a=advancement, t=text: remove_incident_callback_confirm(e, r, a, t))
            form <= input_remove_incident
            col = html.TD(form)
            row <= col

            game_incidents_table <= row

        play_low.MY_SUB_PANEL <= game_incidents_table

    ############################################
    if play_low.GAME_PARAMETERS_LOADED['current_state'] == 1:

        play_low.MY_SUB_PANEL <= html.H3("Vote de fin de partie")

        if play_low.GAME_PARAMETERS_LOADED['end_voted']:
            play_low.MY_SUB_PANEL <= html.DIV("La fin de partie est déjà votée dans cette partie", Class='note')
        else:
            form = html.FORM()
            input_end_vote_game = html.INPUT(type="submit", value="Déclarer la partie finie par vote unanime", Class='btn-inside')
            input_end_vote_game.bind("click", end_game_vote_callback)
            form <= input_end_vote_game
            play_low.MY_SUB_PANEL <= form

    ############################################
    play_low.MY_SUB_PANEL <= html.H3("Paramètres de la partie")

    form = html.FORM()

    input_rectify_game = html.INPUT(type="submit", value="Rectifier les paramètres", Class='btn-inside')
    input_rectify_game.bind("click", edit_game_callback)
    form <= input_rectify_game
    play_low.MY_SUB_PANEL <= form

    ############################################
    play_low.MY_SUB_PANEL <= html.H3("Etat de la partie")

    state_loaded = play_low.GAME_PARAMETERS_LOADED['current_state']

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_state = html.LEGEND("état", title="Etat de la partie : en attente, en cours, terminée ou distinguée.")
    fieldset <= legend_state

    if state_loaded == 0:
        form <= information_about_start_game()
        form <= html.BR()
        input_start_game = html.INPUT(type="submit", value="Démarrer la partie", Class='btn-inside')
        input_start_game.bind("click", lambda e, s=1: change_state_game_callback(e, None, s))
        form <= input_start_game
        form <= html.BR()
        form <= html.BR()
        form <= information_about_distinguish_game1()
        form <= html.BR()
        input_distinguish_game = html.INPUT(type="submit", value="Distinguer la partie", Class='btn-inside')
        input_distinguish_game.bind("click", lambda e, s=3: change_state_game_callback(e, None, s))
        form <= input_distinguish_game

    if state_loaded == 1:
        input_stop_game = html.INPUT(type="submit", value="Arrêter la partie", Class='btn-inside')
        input_stop_game.bind("click", lambda e, s=2: change_state_game_callback_confirm(e, s))
        form <= input_stop_game

    if state_loaded == 2:
        form <= information_about_distinguish_game2()
        form <= html.BR()
        input_distinguish_game = html.INPUT(type="submit", value="Distinguer la partie", Class='btn-inside')
        input_distinguish_game.bind("click", lambda e, s=3: change_state_game_callback(e, None, s))
        form <= input_distinguish_game

    if state_loaded == 3:
        input_undistinguish_game = html.INPUT(type="submit", value="Ne plus distinguer la partie", Class='btn-inside')
        input_undistinguish_game.bind("click", lambda e, s=2: change_state_game_callback_confirm(e, s))
        form <= input_undistinguish_game

    play_low.MY_SUB_PANEL <= form

    ############################################
    play_low.MY_SUB_PANEL <= html.H3("Existence de la partie")

    form = html.FORM()

    input_delete_game = html.INPUT(type="submit", value="Supprimer la partie", Class='btn-inside')
    input_delete_game.bind("click", delete_game_callback_confirm)
    form <= input_delete_game

    play_low.MY_SUB_PANEL <= form

    play_low.MY_SUB_PANEL <= html.H3("Exportation")

    input_download_game_csv = html.INPUT(type="submit", value="Télécharger le résultat de la partie au format CSV", Class='btn-inside')
    input_download_game_csv.bind("click", callback_download_game_csv)
    play_low.MY_SUB_PANEL <= input_download_game_csv

    play_low.MY_SUB_PANEL <= html.H3("Aide mémoire")

    help_table = html.TABLE()
    for question_txt, answer_txt in HELP_CONTENT_TABLE.items():

        row = html.TR()

        col = html.TD()
        col <= html.B(question_txt)
        row <= col

        col = html.TD()
        col <= answer_txt
        row <= col

        help_table <= row

    play_low.MY_SUB_PANEL <= help_table

    return True


def supervise():
    """ supervise """

    role2pseudo = {}
    log_stack = None

    def civil_disorder_callback(ev, role_id):  # pylint: disable=invalid-name
        """ civil_disorder_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de désordre civil dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de désordre civil dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

        if ev is not None:
            ev.preventDefault()

        names_dict = play_low.VARIANT_DATA.extract_names()
        names_dict_json = dumps(names_dict)

        json_dict = {
            'role_id': role_id,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-no-orders/{play_low.GAME_ID}"

        # submitting civil disorder : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def force_agreement_callback(ev, role_id):  # pylint: disable=invalid-name
        """ force_agreement_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'accord forcé pour résoudre dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'accord forcé pour résoudre dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            adjudicated = req_result['adjudicated']
            if adjudicated:
                mydialog.InfoDialog("Information", "La résolution a été forcée.")
                message = "Résolution forcée par la console suite forçage accord"
                log_stack.insert(message)

        if ev is not None:
            ev.preventDefault()

        inforced_names_dict = play_low.INFORCED_VARIANT_DATA.extract_names()
        inforced_names_dict_json = dumps(inforced_names_dict)

        json_dict = {
            'role_id': role_id,
            'adjudication_names': inforced_names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-agree-solve/{play_low.GAME_ID}"

        # submitting force agreement : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def reload_game_admin_table(submitted_data, votes):
        """ reload_game_admin_table """

        vote_values_table = {}
        for _, role, vote_val in votes:
            vote_values_table[role] = bool(vote_val)

        submitted_roles_list = submitted_data['submitted']
        agreed_now_roles_list = submitted_data['agreed_now']
        agreed_after_roles_list = submitted_data['agreed_after']
        needed_roles_list = submitted_data['needed']

        game_admin_table = html.TABLE()

        for role_id in play_low.VARIANT_DATA.roles:

            # discard game master
            if role_id == 0:
                continue

            row = html.TR()

            role = play_low.VARIANT_DATA.roles[role_id]
            role_name = play_low.VARIANT_DATA.role_name_table[role]

            # flag
            col = html.TD()
            role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)
            col <= role_icon_img
            row <= col

            # role name
            col = html.TD()
            col <= role_name
            row <= col

            # player
            col = html.TD()
            pseudo_there = ""
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id = int(player_id_str)
                pseudo_there = play_low.ID2PSEUDO[player_id]
            col <= pseudo_there
            row <= col

            col = html.TD()
            flag = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
                else:
                    flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
            col <= flag
            row <= col

            col = html.TD()
            flag = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    if role_id in agreed_now_roles_list:
                        flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre maintenant")
                    elif role_id in agreed_after_roles_list:
                        flag = html.IMG(src="./images/agreed_after.jpg", title="D'accord pour résoudre à la date limite")
                    else:
                        flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")
            col <= flag
            row <= col

            col = html.TD()
            flag = ""
            if role_id in vote_values_table:
                if vote_values_table[role_id]:
                    flag = html.IMG(src="./images/stop.png", title="Arrêter la partie")
                else:
                    flag = html.IMG(src="./images/continue.jpg", title="Continuer la partie")
            col <= flag
            row <= col

            game_admin_table <= row

        return game_admin_table

    def refresh():
        """ refresh """

        submitted_data = {}
        votes = None

        def refresh_subroutine():

            # reload from server to see what changed from outside
            play_low.load_dynamic_stuff()
            nonlocal submitted_data
            submitted_data = play_low.get_roles_submitted_orders(play_low.GAME_ID)
            if not submitted_data:
                alert("Erreur chargement données de soumission")
                return

            # votes
            nonlocal votes
            votes = play_low.game_votes_reload(play_low.GAME_ID)
            if votes is None:
                alert("Erreur chargement votes")
                return
            votes = list(votes)

            play_low.MY_SUB_PANEL.clear()

            # clock
            stack_clock(play_low.MY_SUB_PANEL, SUPERVISE_REFRESH_PERIOD_SEC)
            play_low.MY_SUB_PANEL <= html.BR()

            # game status
            play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
            play_low.MY_SUB_PANEL <= html.BR()

            # role flag
            play_low.stack_role_flag(play_low.MY_SUB_PANEL)

        # changed from outside
        refresh_subroutine()

        # calculate deadline + grace
        time_unit = 60 if play_low.GAME_PARAMETERS_LOADED['fast'] else 24 * 60 * 60
        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
        grace_duration_loaded = play_low.GAME_PARAMETERS_LOADED['grace_duration']
        force_point = deadline_loaded + time_unit * grace_duration_loaded
        time_stamp_now = time()

        # are we past ?
        if time_stamp_now > force_point:

            submitted_roles_list = submitted_data['submitted']
            agreed_now_roles_list = submitted_data['agreed_now']
            needed_roles_list = submitted_data['needed']

            missing_orders = []
            for role_id in play_low.VARIANT_DATA.roles:
                if role_id in needed_roles_list and role_id not in submitted_roles_list:
                    missing_orders.append(role_id)

            alterated = False
            if missing_orders:
                role_id = RANDOM.choice(missing_orders)
                civil_disorder_callback(None, role_id)
                role = play_low.VARIANT_DATA.roles[role_id]
                role_name = play_low.VARIANT_DATA.role_name_table[role]
                message = f"Désordre civil pour {role_name}"
                alterated = True
            else:
                missing_agreements = []
                for role_id in play_low.VARIANT_DATA.roles:
                    if role_id in submitted_roles_list and role_id not in agreed_now_roles_list:
                        missing_agreements.append(role_id)
                if missing_agreements:
                    role_id = RANDOM.choice(missing_agreements)
                    force_agreement_callback(None, role_id)
                    role = play_low.VARIANT_DATA.roles[role_id]
                    role_name = play_low.VARIANT_DATA.role_name_table[role]
                    message = f"Forçage accord pour {role_name}"
                    alterated = True

            if alterated:

                log_stack.insert(message)

                # changed from myself
                refresh_subroutine()

        game_admin_table = reload_game_admin_table(submitted_data, votes)
        play_low.MY_SUB_PANEL <= game_admin_table
        play_low.MY_SUB_PANEL <= html.BR()

        # put stack in log window
        log_window = html.DIV(id="log")
        log_stack.display(log_window)

        # display
        play_low.MY_SUB_PANEL <= log_window

    def cancel_supervise_callback(_, dialog):
        """ cancel_supervise_callback """

        dialog.close(None)

        play.load_option(None, 'Consulter')

    def supervise_callback(_, dialog):
        """ supervise_callback """

        dialog.close(None)

        nonlocal role2pseudo
        role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

        nonlocal log_stack
        log_stack = Logger()

        # initiates refresh
        refresh()

        # repeat
        global SUPERVISE_REFRESH_TIMER
        if SUPERVISE_REFRESH_TIMER is None:
            SUPERVISE_REFRESH_TIMER = timer.set_interval(refresh, SUPERVISE_REFRESH_PERIOD_SEC * 1000)  # refresh every x seconds

    # need to be connected
    if play_low.PSEUDO is None:
        alert("Il faut se connecter au préalable")
        play.load_option(None, 'Consulter')
        return False

    # need to be game master
    if play_low.ROLE_ID != 0:
        alert("Vous ne semblez pas être l'arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not waiting
    if play_low.GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not finished
    if play_low.GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà terminée")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be fast
    if not play_low.GAME_PARAMETERS_LOADED['fast']:
        alert("Cette partie n'est pas une partie rapide")
        play.load_option(None, 'Consulter')
        return False

    # since touchy, this requires a confirmation
    dialog = mydialog.Dialog("On supervise vraiment la partie (cela peut entrainer des désordres civils) ?", ok_cancel=True)
    dialog.ok_button.bind("click", lambda e, d=dialog: supervise_callback(e, d))
    dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_supervise_callback(e, d))

    return True
