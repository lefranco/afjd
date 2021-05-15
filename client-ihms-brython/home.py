""" home """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

import common

my_panel = html.DIV(id="home")

title1 = html.H2("Lien utile : Diplomania")
my_panel <= title1

link1 = html.A(href="http://www.diplomania.fr", target="_blank")
link1 <= "Diplomania : Le site officiel de l'Association Française des Joueurs de Diplomatie (brique sociale)"
my_panel <= link1

title2 = html.H2("Note importante")
my_panel <= title2

note_table = html.TABLE()
note_table.style = {
    "border": "solid",
}
text1 = html.B(html.CODE("""
Bienvenue dans la version Beta du site diplomania.
Information importante : vous ne visualisez ici que le moteur de jeu sans le design. Ce dernier est en cours dans les mains de notre graphiste Wenz partiellement financé par les dons du crowfunding.
Le moteur que vous allez tester est le fruit du très gros travail de Jérémie (Palpatine) membre du CA et bénévole.
On compte sur vous sur ces premiers tests et on vous promet très prochainement la version « habillée » par les soins de wenz.
Et tout cela en open source bien sûr !
merci de nous remonter vos remarque sur le forum de diplomania.
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

text2 = html.P("C'est arrivé, le système s'est bloqué ou le résultat n'était pas celui escompté ? Vous ne parvenez pas entrer vos ordres et la DL est ce soir ? Vous pouvez envoyer un mél à l'adresse ci-dessous.")
my_panel <= text2

emails_support_img = html.IMG(src="./data/email_support.png")
my_panel <= emails_support_img

text3 = html.P("N'oubliez de bien préciser une procédure pour reproduire le problème, la différence entre le résultat obtenu et le résultat attendu...")
my_panel <= text3


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
