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
link1.style = {
    'color': 'blue',
}
my_panel <= link1

title11 = html.H2("Parainage")
my_panel <= title11

link11 = html.A(href="https://www.helloasso.com/associations/association-francophone-des-joueurs-de-diplomacy/collectes/diplomania-fr-le-site-open-source", target="_blank")
link11 <= "Participer au financement du développement du site"
my_panel <= link11
link11.style = {
    'color': 'blue',
}

title2 = html.H2("Note importante")
my_panel <= title2

note_table = html.TABLE()
text1 = html.B(html.CODE("""
Bienvenue dans la version Beta du site diplomania.<br>
Information importante : vous visualisez ici une interface au design rustique pour accéder au moteur de jeu. Une version avec un design plus élaboré est espérée pour plus tard.<br>
Merci de nous remonter vos remarques sur le forum de diplomania ou sur le serveur Discord.
"""))
my_panel <= text1
col = html.TD(text1)
col <= text1
row = html.TR(col)
row <= col
note_table <= row
my_panel <= note_table

title3 = html.H2("Dernières nouvelles")
my_panel <= title3

news_content_loaded = common.get_news_content()  # pylint: disable=invalid-name
news_content = html.DIV()
if news_content_loaded is not None:
    for line in news_content_loaded.split("\n"):
        news_content <= html.EM(line)
        news_content <= html.BR()
news_content.style = {
    'color': 'red',
}
my_panel <= news_content

title4 = html.H2("Support")
my_panel <= title4

text21 = html.P("C'est arrivé, le système s'est bloqué ou le résultat n'était pas celui escompté ? Vous ne parvenez pas entrer vos ordres et la DL est ce soir ? ")
my_panel <= text21

text22 = html.P("Vous pouvez utiliser le lien ci-dessous pour envoyer un email :")
my_panel <= text22

email_support = html.A(href=f"mailto:{EMAIL_SUPPORT}")
email_support <= "Contacter le support"
email_support.style = {
    'color': 'red',
}
my_panel <= email_support

text3 = html.P("N'oubliez de bien préciser une procédure pour reproduire le problème, la différence entre le résultat obtenu et le résultat attendu...")
my_panel <= text3

title5 = html.H2("Copinage")
my_panel <= title5

link4 = html.A(href="https://visitercracovie.wordpress.com/", target="_blank")
link4 <= "Si vous savez pas quoi faire pendant vos vacances..."
my_panel <= link4


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
