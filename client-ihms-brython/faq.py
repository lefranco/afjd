""" faq """


FAQ_CONTENT_TABLE = {

    "Pourquoi certains messages sont en français, certains en anglais, voire certains dans un mélange des deux ?":
    "Les messages issus de l'interface 'front end' sont en français (sauf omission à corriger rapidement). Les messages issus du serveur 'back end' sont en anglais.",

    "Peut-on jouer plusieurs rôles sur une partie ?":
    "Non, cela n'est pas possible. Il doit y avoir 8 intervenants distincts sur une partie (arbitre y compris). Le système se base sur l'identité pour trouver le rôle, et ainsi présenter l'interface idoine",

    "Peut-on faire des erreurs d'ordres ?":
    "Non. Les ordres sont 100% vérifiés avant d'être enregistrés. L'option de bienveillance vis à vis des débutants a été privilégiée. Par contre le menu “Taguer“ dans une partie permet une communcation par ordres 'ésotériques'. Cela ne presente un intérêt que dans les parties sans communication.",

    "Que signifient toutes les couleurs de remplissage des regions sur la carte ?":
    "Une région prend la couleur du pays qui possède le centre qui s'y trouve. Sinon, elle prend la couleur du pays qui possède l'unité qui l'occupe. Sinon, elle prend la couleur géographique (ce critère restant subjectif) du pays.",

    "Quand a lieu la résolution ?":
    "Quand le dernier joueur qui a des ordres à rendre coche sur la case 'd'accord pour résoudre maintenant' tout simplement. Lire la question suivante...",

    "C'est tout ?":
    "Non. Premièrement : un arbitre peut le faire à sa place pour éviter que la partie ne s'éternise, avec les mêmes conséquences. Deuxièmement un 'accord pour résoudre à la date limite' exprimé après la date limite devient un 'accord pour résoudre maintenant' avec les mêmes conséquences. Troisièmement : un petit automate vient regarder les parties dont la date limite est passée toutes les demies heures. Il se charge de soigeusement transformer tout 'accord pour résoudre après la date limite' en 'accord pour résoudre maintenant' toujours avec les mêmes conséquences.",

    "Comment est calculée la nouvelle date limite ?":
    "On part de la date courante. On arrondit à l'heure précédente (si on est après la date limite) ou à l'heure suivante (si on est avant la date limite). On ajoute les heures correspondant à la prochaine saison à jouer. On passe le week-end si besoin. On ajoute ce qu'il faut pour être sur l'heure de la synchronisation si besoin (quitte à passer au jour suivant dans ce dernier cas). Pour les parties en direct on se contente d'incrémenter en minutes.",

    "Pourquoi les dates limites changent-elles de couleur ?":
    "Le code de couleur est assez conventionnel. Jaune signifie que la date limite est proche (24h). Or qu'elle est passée de moins de 5 secondes (délai de prise en compte de l'automate). Orange qu'elle est passée de plus de 5 secondes. Rouge que la grâce est aussi passée (en général 24 heures). Rouge foncé qu'elle est passée d'une semaine (partie que l'on qualifiera pudiquemment d'être \"en mauvaise santé\"). Argent que la partie est finie. La grace n'a aucune incidence sur le jeu (mais entraine des plus grandes pénalités dans certains tournois). Pour les parties en direct on utilise les minutes au lieu des heures, la grace à une incidence puisque passée elle entraîne des désordre civils en mode supervisé",

    "Il y a des retards indiqués. Dans quel cas un joueur est-il marqué en retard ?":
    "Passer ses ordres signifie réaliser une transition 'pas d'accord pour la résolution' (ou pas d'information) -> 'd'accord pour la résolution (maintenant ou à la date limite, peu importe)'. Un retard signifie que cela est réalisé après la date limite (que ce soit par le joueur ou par l'arbitre). Si l'arbitre reporte la date limite, le retard n'est pas effacé (mais il est impossible d'avoir deux retards sur une même saison.) Soyez ponctuels (on l'a déjà dit ?) !",

    "Comment sont comptés les retards ?":
    " Toute heure de retard entamée est due. Cela signifie qu'un retard indiqué '2' (2 heures)est un retard de plus d'une heure et d'au plus deux heures (par rapport à la date limite au moment de la soumission)",

    "Est ce que je peux écrire n'importe quoi dans les messages et les presses ?":
    "Non ! Les messages sont privés entre émetteur et destinataire(s). Les presses sont privées dans la partie et modérateur du site (qui peut les lire et en écrire). Dans les deux cas le contenu doit respecter la charte. L'administrateur peut sur demande lire un message pour vérifier. Contenu inaproprié ? Déclarez un incident ! (reperez le message par son id)",

    "C'est quoi cette petite pastille rose en haut à gauche dans la carte ?":
    "Celà attire l'attention sur la présence d'ordres de communications.",

    "C'est quoi le 'focus' dans l'interface messagerie de la partie ?":
    "Cela permet de se limiter aux échanges avec un seul des protagonistes présents (qui s'affiche alors en gras)",

    "Pourquoi les unités ne se déplacent pas dans le bac à sable ?":
    "Le bac à sable n'a pas vocation à déplacer les unités, il cherche à répondre à la question 'que se passerait-il si...'. Il faut bien lire le compte rendu des ordres sous forme de texte sous la carte.",

    "Il me restait une dernière unité, je pouvais retraiter, mais le système m'a carrément supprimé mon unité. C'est quoi ce bug ?":
    "Non, c'est normal. Le système, pour une retraite d'hiver, supprime les unités d'un joueur qui n'a plus de centre et ne peut retraiter sur un centre, ni avoir une retraite en conflit avec un autre joueur. Cela anticipe sa disparition et évite d'avoir à attendre son ordre de suppression de ses dernières unités par la suite. Une euthanasie en quelque sorte !",

    "Eh, je pense avoir trouvé un bug dans le moteur de résolution. Que faire ?":
    "Le moteur s'appuie sur le DATC. Il faut utiliser le lien en page d'accueil pour envoyer un courriel et signaler le problème. Reproduisez le soigneusement avec le bac à sable.",

    "Où trouver des explications sur les paramètres des parties ?":
    "Soit en survolant les titres à la création de la partie, soit en consultant le menu “Paramètres“ d'une partie existante.",

    "Dans les paramètres des parties, la notion de messages publics et privés est dupliquée. Pourquoi  ?":
    "Ces deux paramètres ont une version 'partie' et une version 'en cours' La première est celle entrée par le créateur de la partie. La deuxième est celle qui va s'appliquer, elle est initialisée à la valeur de la première. A la fin de la partie, la deuxième est effacée. L'arbitre peut également jouer avec l'autorisation des messages publics et privés pendant la partie. Les exportations de partie (pour savoir comment elle a été jouée) se baseront sur la première.",

    "Comment remplacer un joueur ?":
    "C'est le rôle de l'arbitre. Il faut lui retirer le rôle dans la console d'arbitrage et attribuer le rôle à un autre joueur dans la partie, qu'il aura fallu faire venir au préalable cf. question suivante.",

    "Comment mettre un joueur dans une partie ?":
    "Faire venir ou partir les joueurs de la partie se réalise par contre dans le editer parties / déplacer des joueurs. Un joueur peut se mettre ou se retire d'une partie, un arbitre peut mettre un joueur ou le retirer d'une partie. Pour un joueur, il y a trois manière de rejoindre une partie : par le menu “Parties“ sous menu “Appariement“ (qui gère tous les cas), par le menu opportunités (qui liste les parties qui recrutent), par un hyper lien que quelqu'un vous aura envoyé s(pour vous inviter).",

    "Comment ameuter les remplaçants pour un remplacement ?":
    "Il faut enlever le rôle au joueur et le retirer de la partie (cf les deux questions précédentes). Un bouton est alors disponible dans la console d'arbitrage.",

    "Sur ma partie il y a un joueur bizarre. Depuis qu'un autre l'a stabbé, il passe son temps à lui donner du \"l'autre abruti\" et j'en passe et des meilleures. L'arbitre ne fait rien. Que dois-je faire  ?":
    "C'est à l'arbitre de le rappeler à l'ordre en principe. Si sa manière de traiter la chose ne vous plait pas, il faut déclarer un incident. Nous voulons une atmosphère cordiale sur le site.",

    "Que peut faire l'arbitre ?":
    "L'arbitre connaît l'identité des joueurs de sa partie. Il démarre et arrête la partie. Il peut distinguer la partie. Il peut forcer des ordres de désordre civil pour un pays (si les paramètres de la partie le permettent). Il peut forcer un accord pour résoudre pour un pays (seulement après la date limite). Il peut retirer ou ajouter un joueur dans une partie, et allouer un rôle ou retirer un rôle à un joueur dans une partie. Il peut modifier une date limite (même si celle-ci est gérée par le système). Il gère également les paramètres de la partie.",

    "Que peut faire un créateur ?":
    "Un créateur peut créer plusieurs parties en une seul fois grace à un petit fichier csv contenant les joueurs dans les parties. Pour obtenir le statut de créateur et pouvoir réaliser cette opération consulter l'administrateur (en déclarant un incident par exemple)",

    "Que peut faire un modérateur ?":
    "Un modérateur peut modifier ses nouvelles. Il peut lister toutes les adresses courriel du site pour préparer un publipostage. Il peut envoyer un courriel à un inscrit. Il peut voir le résultat complet d'un tournoi (que les parties soient anonymes ou pas). Il peut réaliser une annonce en envoyant une déclarations dans certaines parties de sorte à atteindre tous les joueurs de toutes les parties en cours. Il peut lire et écrire dans les presses de toute les parties. Il peut lire les informations personnelles d'un inscrit. Il peut voir tous les retards dans toutes les parties. Il peut voir toutes les parties dans laquelle intervient d'un joueur donné. Il peut consulter les dates de dernière activite pour tous les comptes (soumission d'ordres) . Il peut vérifier les adresses IP. Il peut vérifier les adresses courriel. Il peut consulter la liste des comptes dont l'adresse courriel n'est pas confirmée. Il peut consulter les codes de vérification pour le forum. Il peut destituer un arbitre. Il peut changer le responsable d'un tournoi. Il peut changer le responsable d'un événement. Enfin, dans les parties : il voit les identités des joueurs même si la partie est anonyme, ainsi que les soumissions et les incidents même s'il n'est pas dans la partie. Il peut en faire, des coses !",

    "Que peut faire un administrateur ?":
    "Un administrateur peut modifier ses nouvelles. Il peut se substituer à un inscrit (donc cela implique qu'il puisse, s'il le souhaite, lire tous les messages privés et publics de toutes les parties). Il peut rectifier les paramètres fixes (en théorie) et la position d'une partie. Il peut savoir les dates des dernières connexions réussies et manquées (erreur de pseudo/mot de passe). Il gère la liste des créateurs et des modérateurs. Il peut (provisoirement) mettre à jour le elo, la fiabilité et la régularité. Il peut voir les comptes oisifs et les comptes qui n'ont pas confirmé leur adresse courriel.",

    "Comment créer une partie dans laquelle je joue ?":
    "Il faut créer la partie, puis se retirer de l'arbitrage. Un arbitre de parties du site se chargera d'en prendre l'arbitrage.",

    "J'ai oublié mon mot de passe. Au secours !":
    "Entrer son pseudo et cliquer 'Mot de passe oublié'. Un courriel est envoyé avec un lien. Cliquer sur le mien amène sur le site avec une authentification valable un temps limité. Se dépêcher de modifier sont mot de passe.",

    "Comment créer un gros tournoi ?":
    """
      Super facile ! <br>
     <br>
     1- créer une partie modèle correspondant à ce que l'on veut pour le tournoi <br>
     2- sélectionner cette partie <br>
     3- mettre des joueurs quelconques dans cette partie pour pouvoir la démarrer (one, two, three, four, five, six, seven par exemple) <br>
     4- démarrer cette partie <br>
     5- terminer cette partie <br>
     6- distinguer cette partie (pas obligatoire mais pratique) <br>
     7- retirer les joueurs de la partie (pas obligatoire mais plus propre) <br>
     8- ATTENTION : modifier l'anonymat sur cette partie si besoin (il a pu changer lorsque la partie a été terminée) <br>
     9- remplir un document CSV (avec EXCEL par exemple) décrivant les parties cf. la page tournoi/créer plusieurs parties <br>
    10- si plusieurs arbitres, fournir à chaque arbitre le fichier avec les lignes correspondant à ses parties <br>
    11- chaque arbitre créé ses parties : <br>
             - sélectionne la partie modèle <br>
             - utilise la page tournoi/créer plusieurs parties <br>
    12- chaque arbitre démarre ses parties au moment opportun : <br>
             - sélectionne la page mes parties <br>
             - sélectionne les parties en attente <br>
             - clique sur démarrer pour chaque partie
    """,

    "Qu'est ce qui change pour une partie 'en direct' ?":
    "Une telle partie est destinée à se dérouler comme sur un jeu de plateau. Le calcul des dates limites se fait en minutes et non en heures. Les retards sont comptés en minutes et non en heures entamées. Il est possible d'observer la partie (mise à jour régulière du plateau). Il est possible pour l'arbitre d'activer la supervision de la partie, qui forcera des ordres de désordre civil pour les joueurs automatiquement après la grâce. Pas de message de notification pour une telle partie. Pas d'accord pour résoudre après la date limite",

    "Qu'est ce qui change pour une partie 'archive' ?":
    "Une telle partie n'est pas jouée sur le site. Elle est saisie par son arbitre à partir de feuilles d'ordres mais cette partie à eu lieu ailleurs (par exemple une table finale de championnat du monde. Avec juste un intérêt de consultation",

    "Pourquoi des parties sont distinguées ?":
    "Ce sont soit des parties modèles de tournoi que l'on veut retrouver plus rapidement, soit des parties archives sur lesquelles on veut attirer l'attention du badaud.",

    "Ce site est-il le site de jeu officiel de l'Association Francophone des Joueurs de Diplomatie ?":
    "Oui.",

    "(Pour les modérateurs) Quels sont les codes pour écrire sur le mur ?":
    """
    .ANNONCE pour une annonce spéciale (sur la même ligne) - admin seulement <br>
    .HR pour un trait horizontal <br>
    .STRONG pour écrire en gras <br>
    .KBD pour écrire ce que l'on doit taper au clavier <br>
    .LINK pour mettre un lien <br>
    .BR pour aller à la ligne
    """

}
