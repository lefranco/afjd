""" home """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

import common

my_panel = html.DIV(id="home")

title1 = html.H2("Lien utile : Diplomania")
my_panel <= title1

link1 = html.A(href="http://www.diplomania.fr")
link1 <= "Diplomania : Le site officiel pour jouer de l'Association Française des Joueurs de Diplomatie (brique sociale)"
my_panel <= link1

title2 = html.H2("Note importante")
my_panel <= title2

note_table = html.TABLE()
note_table.style = {
    "border": "solid",
}
text1 = html.B(html.CODE("Cette interface de jeu n'a reçu aucun financement de la parte de l'Association Française des Joueurs de Diplomatie"))
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
my_panel <= news_content

title4 = html.H2("Support")
my_panel <= title4

text2 = html.P("C'est arrivé, le système s'est bloqué ou le résultat n'était pas celui escompté ? Vous ne parvenez pas entrer vos ordres et la DL est ce soir ? Vous pouvez envoyer un mél à l'adresse ci-dessous.")
my_panel <= text2

emails_support_img = html.IMG(src="./data/email_support.png")
my_panel <= emails_support_img

text3 = html.P("N'oubliez de bien préciser une procédure pour reproduire le problème, la différence entre le résultat obtenu et le résultat attendu...")
my_panel <= text3

title5 = html.H2("Une version simplifiée des règles du Jeu")
my_panel <= title5

my_panel <= html.BR()

iframe = html.IFRAME(src="./docs/Summary_rules_fr.html", width='100%', height=500)
my_panel <= iframe


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
