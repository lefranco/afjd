""" home """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

import json
import time

from browser import html, ajax, alert, document, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import user_config
import config
import common
import faq
import tips
import mydatetime


THRESHOLD_DRIFT_ALERT_SEC = 59


OPTIONS = ['Vue d\'ensemble', 'Chatter en direct', 'Déclarer un incident', 'Foire aux questions', 'Les petits tuyaux', 'Evolution de la fréquentation', 'Brique sociale']


# for safety
if 'ANNOUNCEMENT' not in storage:
    storage['ANNOUNCEMENT'] = ""
if 'ALREADY_SPAMMED' not in storage:
    storage['ALREADY_SPAMMED'] = 'yes'


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


def get_chat_messages():
    """ get_chat_messages """

    chat_messages = {}

    def reply_callback(req):
        nonlocal chat_messages
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des messages chat : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des messages chat : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        chat_messages = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/chats"

    # get chats : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return chat_messages


def formatted_news(news_content_loaded, admin, class_):
    """ formatted_news """

    # init
    news_content = html.DIV(Class=class_)

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

    # collect data
    data = {}
    done = False
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


def show_news():
    """ show_home """

    title = html.H3("Accueil")
    MY_SUB_PANEL <= title
    div_homepage = html.DIV(id='grid')

    # ----
    stats_content = get_stats_content()
    news_content_table_loaded = common.get_news_content()
    # ----

    # ----
    div_a5 = html.DIV(Class='tooltip')

    title1 = html.H4("Remplacements urgents et dernier chats")
    div_a5 <= title1

    div_a5 <= "Remplacements :"
    div_a5 <= html.BR()
    suffering_games_loaded = stats_content['suffering_games']
    if suffering_games_loaded:
        div_a5 <= "Les parties suivantes sont en cours et ont besoin de remplaçant(s)"
        div_a5 <= html.BR()
        div_a5 <= formatted_games(suffering_games_loaded)
    else:
        div_a5 <= "Aucune partie en cours n'a besoin de remplaçant(s)."

    chat_content_loaded = news_content_table_loaded['chats']
    if chat_content_loaded:
        last_chat = chat_content_loaded[-1]
        last_chat_author = last_chat[1]
        last_chat_message = last_chat[2]
        div_a5 <= html.BR()
        div_a5 <= html.BR()
        div_a5 <= "Dernier chat :"
        div_a5 <= html.BR()
        div_a5 <= html.DIV(f"{last_chat_author} : {last_chat_message}", Class='chat_sample')

    div_a5_tip = html.SPAN("Plus de détail dans le menu “Rejoindre une partie“ et dans le menu “Chatter en direct“", Class='tooltiptext')
    div_a5 <= div_a5_tip
    div_homepage <= div_a5

    # ----
    div_b5 = html.DIV(Class='tooltip')

    title2 = html.H4("Les meilleurs joueurs du site (d'après le classement ELO)")
    div_b5 <= title2
    teaser_loaded = get_teaser_content()
    teaser = formatted_teaser(teaser_loaded) if teaser_loaded else "Aucun pour le moment."
    div_b5 <= teaser

    div_b5_tip = html.SPAN("Plus de détail dans le menu “Classements“ sous menu “Classement performance“", Class='tooltiptext')
    div_b5 <= div_b5_tip
    div_homepage <= div_b5

    # ----
    div_a4 = html.DIV(Class='tooltip')

    title3 = html.H4("Les événements qui recrutent")
    div_a4 <= title3
    news_events = html.OBJECT(data="https://diplomania-gen.fr/events/", width="100%", height="400", title="Evénements", alt="Evénements")
    div_a4 <= news_events

    # no tip
    div_homepage <= div_a4

    # ----
    div_b4 = html.DIV(Class='tooltip')

    title4 = html.H4("Dernières contributions sur les forums")
    div_b4 <= title4
    news_forum = html.OBJECT(data="https://diplomania-gen.fr/external_page.php", width="100%", height="400", title="Forums", alt="Forums")
    div_b4 <= news_forum

    # no tip
    div_homepage <= div_b4

    # ----
    div_a3 = html.DIV(Class='tooltip')

    title5 = html.H4("Dernières nouvelles moderateur", Class='modo_news')
    div_a3 <= title5
    news_content_loaded2 = news_content_table_loaded['modo']
    news_content2 = formatted_news(news_content_loaded2, False, 'modo_news')
    div_a3 <= news_content2
    div_a3_tip = html.SPAN("Vous pouvez contacter le modérateur par un MP sur le forum", Class='tooltiptext')
    div_a3 <= div_a3_tip
    div_homepage <= div_a3

    # ----
    div_b3 = html.DIV(Class='tooltip')

    title6 = html.H4("Dernières nouvelles administrateur", Class='admin_news')
    div_b3 <= title6
    news_content_loaded = news_content_table_loaded['admin']
    news_content = formatted_news(news_content_loaded, True, 'admin_news')
    div_b3 <= news_content
    div_b3_tip = html.SPAN("Vous pouvez contacter l'administrateur par le menu “Accueil“ sous menu “Déclarer un incident“", Class='tooltiptext')
    div_b3 <= div_b3_tip
    div_homepage <= div_b3

    # ----
    div_a1 = html.DIV(Class='tooltip')

    title7 = html.H4("Les glorieux", Class='news3')
    div_a1 <= title7
    hall_content_loaded = news_content_table_loaded['glory']
    hall_content = formatted_news(hall_content_loaded, False, 'glory_news')
    div_a1 <= hall_content
    div_a1_tip = html.SPAN("Plus de détail sur la page wikipedia https://fr.wikipedia.org/wiki/Palmar%C3%A8s_internationaux_de_Diplomatie", Class='tooltiptext')
    div_a1 <= div_a1_tip
    div_homepage <= div_a1

    # ----
    div_b1 = html.DIV(Class='tooltip')

    title9 = html.H4("Liens très importants")
    div_b1 <= title9
    note_bene_content = html.DIV(Class='note')

    note_bene_content_table = html.TABLE()

    # ======================

    row = html.TR()
    note_bene_content_table <= row

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/explain.png")
    col <= img
    row <= col

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/pay.png")
    col <= img
    row <= col

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/chat.png")
    col <= img
    row <= col

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/chart.png")
    col <= img
    row <= col

    # ----------------------

    row = html.TR()
    note_bene_content_table <= row

    col = html.TD()
    link3 = html.A(href="https://youtu.be/luOiAz9i7Ls", target="_blank")
    link3 <= "Je comprend rien à ce site, je veux des explications claires avec un tutorial Youtube !"
    col <= link3
    row <= col

    col = html.TD()
    link4 = html.A(href="https://www.helloasso.com/associations/association-francophone-des-joueurs-de-diplomacy", target="_blank")
    link4 <= "Je souhaite contribuer au financement du site !"
    col <= link4
    row <= col

    col = html.TD()
    link5 = html.A(href="https://discord.gg/mUWes7yEqR", target="_blank")
    link5 <= "Je veux aller causer sur Discord avec d'autres joueurs !"
    col <= link5
    row <= col

    col = html.TD()
    link5 = html.A(href="./docs/charte.pdf", target="_blank")
    link5 <= "La charte du bon diplomate - à lire absolument !"
    col <= link5
    row <= col

    # ======================

    row = html.TR()
    note_bene_content_table <= row

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/facebook.png")
    col <= img
    row <= col

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/twitter.png")
    col <= img
    row <= col

    col = html.TD()
    col.attrs['style'] = 'text-align:center;'
    img = html.IMG(src="./images/abydos.jpeg")
    col <= img
    row <= col

    # ----------------------

    row = html.TR()
    note_bene_content_table <= row

    col = html.TD()
    link5 = html.A(href="https://www.facebook.com/groups/104700706277433", target="_blank")
    link5 <= "La page Facebook de l'association"
    col <= link5
    row <= col

    col = html.TD()
    link5 = html.A(href="https://twitter.com/asso_diplo", target="_blank")
    link5 <= "La page Twitter de l'association"
    col <= link5
    row <= col

    col = html.TD()
    link5 = html.A(href="https://sites.google.com/view/abydosfr/accueil", target="_blank")
    link5 <= "Le site dédié à Diplomacy de notre ami Abydos !"
    col <= link5
    row <= col

    # ======================

    note_bene_content <= note_bene_content_table
    div_b1 <= note_bene_content
    div_b1_tip = html.SPAN("Plus de détail dans le menu “Accueil“ sous menu “Brique sociale“", Class='tooltiptext')
    div_b1 <= div_b1_tip
    div_homepage <= div_b1

    # ----
    div_a0 = html.DIV(Class='tooltip')

    title10 = html.H4("Statistiques")
    div_a0 <= title10
    ongoing_games = stats_content['ongoing_games']
    active_game_masters = stats_content['active_game_masters']
    active_players = stats_content['active_players']
    div_a0 <= f"Il y a {ongoing_games} parties en cours. Il y a {active_game_masters} arbitres en activité. Il y a {active_players} joueurs en activité. (Un joueur ou un arbitre est en activité s'il participe à une partie en cours)"
    div_a0_tip = html.SPAN("Plus de détail dans le menu “Classement“ sous menu “Joueurs“", Class='tooltiptext')
    div_a0 <= div_a0_tip
    div_homepage <= div_a0

    # ----
    div_b0 = html.DIV(Class='tooltip')

    title8 = html.H4("Divers")
    div_b0 <= title8

    # time shift

    server_time = news_content_table_loaded['server_time']
    local_time = time.time()
    delta_time = round(local_time - server_time)
    if delta_time > 0:
        status = "en avance"
    else:
        status = "en retard"
    abs_delta_time = abs(delta_time)
    if abs_delta_time > 60:
        abs_delta_time //= 60
        unit = "minutes"
    else:
        unit = "secondes"

    # do not always display
    if abs(delta_time) > THRESHOLD_DRIFT_ALERT_SEC:
        div_b0 <= html.DIV(f"Votre horloge locale est {status} de {abs_delta_time} {unit} sur celle du serveur", Class='note')
        div_b0 <= html.BR()

    div_b0_tip = html.SPAN("Plus de détail dans le menu “Accueil” sous menu “Foire aux question”", Class='tooltiptext')
    div_b0 <= div_b0_tip
    div_homepage <= div_b0

    # ----

    MY_SUB_PANEL <= div_homepage

    # announce
    if storage['ALREADY_SPAMMED'] == 'no':
        announcement = storage['ANNOUNCEMENT']
        if announcement:
            alert(announcement)
        storage['ALREADY_SPAMMED'] = 'yes'


RANDOM = common.Random()
MAX_CHAT_NUMBER = 999
CHAT_NUMBER = RANDOM.choice(list(range(1, MAX_CHAT_NUMBER + 1)))


def live_chat():
    """ live_chat """

    def add_chat_callback(ev):  # pylint: disable=invalid-name
        """ add_chat_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de message chat : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de message chat : {req_result['msg']}")
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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def chats_reload_callback(ev):  # pylint: disable=invalid-name
        """ chats_reload_callback """

        if ev is not None:
            ev.preventDefault()

        chat_messages = []

        def reply_callback(req):
            nonlocal chat_messages
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des messages chats : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des messages chats : {req_result['msg']}")
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
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return chat_messages

    title4 = html.H3("Chatter en direct")
    MY_SUB_PANEL <= title4

    chats = chats_reload_callback(None)
    # there can be no message (if no declaration of failed to load)

    chats_table = html.TABLE()

    thead = html.THEAD()
    for title in ['Date', 'Auteur', 'Contenu']:
        col = html.TD(html.B(title))
        thead <= col
    chats_table <= thead

    for time_stamp, author, content in chats:

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
    input_reload_all = html.INPUT(type="submit", value="Recharger les messages")
    input_reload_all.bind("click", chats_reload_callback)
    form1 <= input_reload_all

    # say

    form2 = html.FORM()

    fieldset = html.FIELDSET()
    legend_message = html.LEGEND("Votre message", title="Qu'avez vous à dire ?")
    fieldset <= legend_message
    input_message = html.TEXTAREA(type="text", rows=4, cols=80)
    fieldset <= input_message
    form2 <= fieldset

    input_say_message = html.INPUT(type="submit", value="Envoyer")
    input_say_message.bind("click", add_chat_callback)
    form2 <= input_say_message

    information1 = html.DIV(Class='important')
    information1 <= "La première vocation du chat est de fournir une aide rapide aux nouveaux arrivants sur le site."

    information2 = html.DIV(Class='note')
    information2 <= "Les messages persistent au moins 24 heures. L'auteur des messages n'est pas garanti par le système. Ce chat rustique n'a pas destination à remplacer le salon Discord"

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
        req_result = json.loads(req.text)
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
            req_result = json.loads(req.text)
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

        subject = "Déclaration d'incident de la part du site https://diplomania-gen.fr (AFJD)"
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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=submit_incident_reply_callback, ontimeout=common.noreply_callback)

        alert("Votre incident va être examiné dans les plus brefs délais")

        # back to where we started
        MY_SUB_PANEL.clear()
        declare_incident(json_dict_params)

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
                ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=get_email_reply_callback, ontimeout=common.noreply_callback)

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

    text24 = html.P("Vous pouvez utiliser le formulaire ci-dessous pour déclarer un incident :")
    MY_SUB_PANEL <= text24

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_pseudo = html.LEGEND("pseudo (facultatif)", title="Votre pseudo (si applicable)")
    fieldset <= legend_pseudo
    input_pseudo = html.INPUT(type="text", value=pseudo if pseudo is not None else "")
    fieldset <= input_pseudo
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_email = html.LEGEND("courriel (obligatoire)", title="Votre courriel")
    fieldset <= legend_email
    input_email = html.INPUT(type="text", value=email if email is not None else "", size=MAX_LEN_EMAIL)
    fieldset <= input_email
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_game = html.LEGEND("partie (facultatif)", title="La partie (si applicable)")
    fieldset <= legend_game
    input_game = html.INPUT(type="text", value=game if game is not None else "", size=MAX_LEN_GAME_NAME)
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

    input_submit_incident = html.INPUT(type="submit", value="Soumettre l'incident")
    input_submit_incident.bind("click", submit_incident_callback)
    form <= input_submit_incident

    MY_SUB_PANEL <= form


FAQ_DISPLAYED_TABLE = {k: False for k in faq.FAQ_CONTENT_TABLE}
FAQ_CONTENT = html.DIV("faq")

TIPS_DISPLAYED_TABLE = {k: False for k in tips.TIPS_CONTENT_TABLE}
TIPS_CONTENT = html.DIV("tips")


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

            faq_elt = html.DIV(answer_txt, Class='faq-info')
            FAQ_CONTENT <= faq_elt

        FAQ_CONTENT <= html.P()

    MY_SUB_PANEL <= FAQ_CONTENT


def show_tips():
    """ show_tips """

    def reveal_callback(_, question):
        """ reveal_callback """

        TIPS_DISPLAYED_TABLE[question] = not TIPS_DISPLAYED_TABLE[question]
        MY_SUB_PANEL.clear()
        show_tips()

    title1 = html.H3("Les petits tuyaux")
    MY_SUB_PANEL <= title1

    TIPS_CONTENT.clear()

    for question_txt, answer_txt in tips.TIPS_CONTENT_TABLE.items():

        reveal_button = html.INPUT(type="submit", value=question_txt)
        reveal_button.bind("click", lambda e, q=question_txt: reveal_callback(e, q))
        TIPS_CONTENT <= reveal_button

        if TIPS_DISPLAYED_TABLE[question_txt]:

            tip_elt = html.DIV(answer_txt, Class='faq-info')
            TIPS_CONTENT <= tip_elt

        TIPS_CONTENT <= html.P()

    MY_SUB_PANEL <= TIPS_CONTENT


def frequentation_evolution():
    """ frequentation_evolution """

    # load frequentation directly

    # use button
    button = html.BUTTON("Lancement du calcul de fréquentation", id='frequentation_link')
    MY_SUB_PANEL <= button
    button.bind("click", lambda e: window.open("https://diplomania-gen.fr/frequentation"))
    document['frequentation_link'].click()


def social():
    """ social """

    # load social directly

    # use button
    button = html.BUTTON("Lancement de la brique sociale", id='social_link')
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

MY_SUB_PANEL = html.DIV(id="home")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Vue d\'ensemble':
        show_news()
    if item_name == 'Chatter en direct':
        live_chat()
    if item_name == 'Déclarer un incident':
        declare_incident(None)
    if item_name == 'Foire aux questions':
        show_faq()
    if item_name == 'Les petits tuyaux':
        show_tips()
    if item_name == 'Evolution de la fréquentation':
        frequentation_evolution()
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


PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    PANEL_MIDDLE = panel_middle

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
