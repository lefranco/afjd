""" home """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

import common

EMAIL_SUPPORT = "jeremie.lefrancois@gmail.com"

my_panel = html.DIV(id="home")
my_panel.attrs['style'] = 'display: table'

title1 = html.H2("Lien utile : Diplomania")
my_panel <= title1

link1 = html.A(href="http://www.diplomania.fr", target="_blank")
link1 <= "Diplomania : Le site officiel de l'Association Francophone des Joueurs de Diplomacy (brique sociale)"
my_panel <= link1

title11 = html.H2("Parainage")
my_panel <= title11

link11 = html.A(href="https://www.helloasso.com/associations/association-francophone-des-joueurs-de-diplomacy/collectes/diplomania-fr-le-site-open-source", target="_blank")
link11 <= "Participer au financement du développement du site"
my_panel <= link11


title2 = html.H2("Note importante", Class='important')
my_panel <= title2

# pylint: disable=invalid-name
note_content_stated = """
Bienvenue dans la version Beta du site diplomania.
Information importante : vous visualisez ici une interface au design rustique pour accéder au moteur de jeu. Une version avec un design plus élaboré est espérée pour plus tard.
Merci de nous remonter vos remarques sur le forum de diplomania ou sur le serveur Discord.
"""

note_bene_content = html.DIV(Class='important')
for line in note_content_stated.split("\n"):
    note_bene_content <= line
    note_bene_content <= html.BR()
note_content_table = html.TABLE()
row = html.TR()
note_content_table <= row
col = html.TD(note_bene_content)
row <= col
my_panel <= note_content_table

title3 = html.H2("Dernières nouvelles", Class='news')
my_panel <= title3

news_content_loaded = common.get_news_content()  # pylint: disable=invalid-name
news_content = html.DIV(Class='news')
if news_content_loaded is not None:
    for line in news_content_loaded.split("\n"):
        news_content <= line
        news_content <= html.BR()
my_panel <= news_content

title4 = html.H2("Support")
my_panel <= title4

text21 = html.P("C'est arrivé, le système s'est bloqué ou le résultat n'était pas celui escompté ? Vous ne parvenez pas entrer vos ordres et la DL est ce soir ? Votre partie n'avance pas depuis des jours et il semble que votre arbitre se soit endormi ?")
my_panel <= text21

text22 = html.P("S'il s'agit d'un bug, il est peut-être déjà corrigé, essayez de recharger le cache de votre navigateur au préalable (par exemple en utilisant CTRL+F5 - selon les navigateurs) et n'oubliez pas de bien préciser une procédure pour reproduire le problème ainsi que la différence entre le résultat obtenu et le résultat attendu ...")
my_panel <= text22

text23 = html.P("Vous pouvez utiliser le lien ci-dessous pour envoyer un e-mail :")
my_panel <= text23

email_support = html.A(href=f"mailto:{EMAIL_SUPPORT}")
email_support <= "Contacter le support"
my_panel <= email_support

text3 = html.P("S'il s'agit d'une partie, précisez bien la partie et le rôle que vous y jouez.")
my_panel <= text3

title5 = html.H2("Copinage")
my_panel <= title5

link4 = html.A(href="https://visitercracovie.wordpress.com/", target="_blank")
link4 <= "Si vous savez pas quoi faire pendant vos vacances..."
my_panel <= link4


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
