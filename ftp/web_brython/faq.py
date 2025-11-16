""" faq """


FAQ_CONTENT_TABLE = {

    "Pourquoi certains messages sont en français, certains en anglais, voire certains dans un mélange des deux ?":
    "Les messages issus de l'interface “front end“ sont en français (sauf omission à corriger rapidement). Les messages issus du serveur “back end“ sont en anglais. Certains message sont issus des deux mondes donc on trouve un mélange des deux...",

    "Peut-on jouer plusieurs rôles sur une partie ?":
    "Non, cela n'est pas possible. Il doit y avoir des intervenants distincts sur une partie (arbitre y compris). Le système se base sur l'identité pour trouver le rôle, et ainsi présenter l'interface idoine.",

    "Peut-on faire des erreurs d'ordres ?":
    "Non. Les ordres sont 100% vérifiés avant d'être enregistrés. L'option de bienveillance vis à vis des débutants a été privilégiée. Par contre le menu “Ordres de com'“ dans une partie permet une communcation par ordres “ésotériques“. Cela ne presente un intérêt que dans les parties sans communication.",

    "Que signifient toutes les couleurs de remplissage des regions sur la carte ?":
    "Une région prend la couleur du pays qui possède le centre qui s'y trouve. Sinon, elle prend la couleur du pays qui possède l'unité qui l'occupe. Sinon, elle prend la couleur 'géographique' (ce critère restant subjectif - par exemple la Gascogne est géographiquement en France) du pays.",

    "Quand a lieu la résolution ?":
    "Quand le dernier joueur qui a des ordres à rendre coche sur la case “d'accord pour résoudre maintenant“ tout simplement. Bon, oui, c'est un poil plus compliqué, lire la question suivante...",

    "C'est tout ?":
    "Non. Si au moins un joueur a coché “d'accord pour résoudre à la date limite“ il faudra attendre l'automate. Ce dernier vient, toutes les heures,  regarder les parties dont la date limite est passée. Il se charge de soigneusement transformer tout “d'accord pour résoudre à la date limite“ en “d'accord pour résoudre maintenant“ toujours avec les mêmes conséquences.",

    "Et les parties 'Désordre Civil' ?":
    "Pour de telles partie l'arbitre peut forcer les choses après la résolution. L'automate le fera automatiquement après la grâce.",

    "Pour les parties 'Désordre Civil', celui-ci est-il toujours possible ?":
    "Non. Pas de DC si aucun joueur n'a mis d'ordre. Pas de DC au premier tour de jeu (printemps 1901 typiquement)",

    "A qui sert la grâce ?":
    "Cf. paragraphe précédent. Pour les parties en direct, un autre mécanisme force les choses après la grâce (typiquement une minute) petit à petit et aléatoirement.",

    "La D.L. est passée, je suis arbitre, je vois que tous les ordres sont là, mais la partie n'a pas avancé, au secours !":
    "C'est parce qu'un joueur a coché “d'accord pour résoudre à la date limite“. Il faut attendre le passage de l'automate (toutes les heures)",

    "Comment est calculée la nouvelle date limite ?":
    "On part de la date courante. On arrondit à l'heure précédente (si on est après la date limite) ou à l'heure suivante (si on est avant la date limite). On ajoute les heures correspondant à la prochaine saison à jouer. On passe le week-end si besoin. On ajoute ce qu'il faut pour être sur l'heure de la synchronisation si besoin (quitte à passer au jour suivant dans ce dernier cas). Pour les parties en direct on se contente d'incrémenter en minutes.",

    "Pourquoi les dates limites changent-elles de couleur ?":
    """
    Le code de couleur est assez conventionnel.<br>
      - Jaune signifie que la date limite est proche (24h).<br>
      - Orange qu'elle est passée.<br>
      - Rouge que la grâce est aussi passée (en général 24 heures) (se reporter au paragraphe sur les grâces).<br>
      - Marron qu'elle est passée d'une semaine (partie que l'on qualifiera pudiquemment d'être en “mauvaise santé“).<br>
      - Argent que la partie est finie sur échéance.<br>
      - Bleu clair que la partie est finie sur solo.<br>
      - Blanc que la partie est finie sur vote unanime d'arrêt.<br>
    """,

    "Pourquoi certaines dates limites sont elles précédées du signe = ?":
    """
    Cela signifie que l'arbitre a forcé le bouton d'accord pour la résolution à 'à la date limite' pour la partie. Cela se justifie surtout pour les parties en avance dans les tournois dont on souhaite la synchronisation.
    """,

    "Pourquoi certaines dates limites sont elles précédées du signe < ?":
    """
    Cela signifie que l'arbitre a forcé le bouton d'accord pour la résolution à 'maintenant' pour la partie. Cela se justifie surtout pour les parties en retard dans les tournois dont on souhaite la synchronisation.
    """,

    "Il y a des retards indiqués. Dans quel cas un joueur est-il marqué en retard ?":
    "Passer ses ordres signifie réaliser une transition “pas d'accord pour résoudre“ (ou pas d'information) -> “d'accord pour résoudre“ (maintenant ou à la date limite, peu importe). Un retard signifie que cela est réalisé après la date limite. Si l'arbitre reporte la date limite, le retard n'est pas effacé (mais il est impossible d'avoir deux retards sur une même saison.) Soyez ponctuels (on l'a déjà dit ?) !",

    "Comment sont comptés les retards ?":
    "Toute heure de retard entamée est due. Cela signifie qu'un retard indiqué “2“ (2 heures) est un retard d'au moins une heure et d'au plus deux heures (par rapport à la date limite au moment de la soumission)",

    "Est ce que je peux écrire n'importe quoi dans les messages et les presses ?":
    "Non ! Les messages sont certes privés entre émetteur et destinataire(s). Les presses sont certes privées dans la partie et avec le modérateur du site (qui peut les lire et en écrire). Dans les deux cas le contenu doit respecter la charte. L'administrateur peut sur demande lire un message de presse ou de messagerie pour vérifier. Contenu inaproprié ? Déclarez un incident ! (repérez le message par son id)",

    "C'est quoi cette petite pastille rose en haut à gauche dans la carte ?":
    "Celà attire l'attention sur la présence d'ordres de com'.",

    "Je vois effectivement des témoins indiquant l'état de mes ordres. Le pouce, la main et le montre. Pourquoi changent-ils de sens ?":
    "Ils changent de sens à chaque nouvelle soumission, pour voir facilement qu'elle a bien été prise en compte.",

    "C'est quoi le “focus“ dans l'interface messagerie de la partie ?":
    "Cela permet de se limiter aux échanges avec un seul des protagonistes présents (qui s'affiche alors en gras).",

    "Pourquoi les unités ne se déplacent pas dans le bac à sable ?":
    "Le bac à sable n'a pas vocation à déplacer les unités, il cherche à répondre à la question “que se passerait-il si...“. Il faut bien lire le compte-rendu des ordres sous forme de texte sous la carte.",

    "Il me restait une dernière unité, je pouvais retraiter, mais le système m'a carrément supprimé mon unité. C'est quoi ce bug ?":
    "Non, c'est normal. Le système, pour une retraite d'hiver, supprime les unités d'un joueur qui n'a plus de centre et ne peut retraiter sur un centre, ni avoir une retraite en conflit avec un autre joueur. Cela anticipe sa disparition et évite d'avoir à attendre son ordre de suppression de ses dernières unités par la suite. Une euthanasie en quelque sorte !",

    "Eh, je pense avoir trouvé un bug dans le moteur de résolution. Que faire ?":
    "Le moteur s'appuie sur le D.A.T.C.. Il faut utiliser le lien en page d'accueil pour envoyer un courriel et signaler le problème. Reproduisez le soigneusement avec le bac à sable.",

    "Où trouver des explications sur les paramètres des parties ?":
    "Soit en survolant les titres à la création de la partie, soit en consultant le menu “Paramètres“ d'une partie existante.",

    "Comment démarrer/archiver une partie dont je suis l'arbitre ?":
    "Se connecter, sélectionner la partie comme d'habitude et se placer dans la console arbitrage (il faut être arbitre). Utiliser le bouton “Démarrer la partie“ (ou “Archiver la partie“) puis confirmer. Il est également possible de passer par le menu “Mes parties“ en se mettant en mode “avec colonnes d'action“",

    "Comment remplacer un joueur ?":
    "Accéder à la console arbitrage (cf. question précédente). Chapitre “Gestion“. Utiliser les boutons des colonnes “retirer le rôle“ et “attribuer le rôle“. Pour attribuer le rôle à un autre joueur il faut le faire venir au préalable cf. question suivante.",

    "Comment mettre un joueur dans une partie ?":
    "Accéder à la console arbitrage (cf. question précédente). Chapitre “Déplacement de joueurs“. Le mettre dans la partie.",

    "Comment rejoindre une partie ?":
    """
    Pour un joueur, il y a trois manière de rejoindre une partie :<br>
    - par le sous menu “Appariement“ de la partie elle-même (qui gère tous les cas),<br>
    - par le menu “Parties“ sous menu “Rejoindre une partie“ (qui liste les parties qui recrutent),<br>
    - par un hyper lien que quelqu'un vous aura envoyé (pour vous inviter).
    """,

    "Comment ameuter les remplaçants pour un remplacement ?":
    "Enlever le rôle au joueur et le retirer de la partie (cf les deux questions précédentes). Un bouton est alors disponible (chapitre “Gestion“) dans la console d'arbitrage.",

    "Sur ma partie il y a un joueur qui insulte un autre depuis un stab. L'arbitre ne fait rien. Que dois-je faire  ?":
    "C'est à l'arbitre de le rappeler à l'ordre en principe. Si sa manière de traiter la chose ne vous plait pas, il faut contacter un modérateur via la messagerie personnelle. Nous voulons une atmosphère cordiale sur le site.",

    "Que peut faire l'arbitre ?":
    "L'arbitre connaît l'identité des joueurs de sa partie. Il démarre, arrête et archive la partie. Il peut distinguer la partie. Il peut forcer des ordres de désordre civil pour un pays (si les paramètres de la partie le permettent). Il peut retirer ou ajouter un joueur dans une partie, et allouer un rôle ou retirer un rôle à un joueur dans une partie. Il peut modifier (sans mettre dans le passé) une date limite (même si celle-ci est gérée par le système). Il gère également les paramètres de la partie.",

    "Que peut faire un créateur ?":
    "Un créateur peut créer plusieurs parties en une seul fois grace à un petit fichier CSV contenant les joueurs dans les parties. Il peut voir le résultat complet d'un tournoi (à condition qu'aucune des parties ne soit anonyme). Il peut consulter le mur de la honte, c'est à dire la liste des joueurs qui ont abandonné une partie. Pour obtenir le statut de créateur et pouvoir réaliser cette opération consulter l'administrateur (en déclarant un incident par exemple)",

    "Que peut faire un modérateur ?":
    "Un modérateur peut modifier ses nouvelles. Il effacer les discussions en ligne. Il peut lister toutes les adresses courriel du site pour préparer un publipostage. Il peut envoyer un courriel à un inscrit. Il peut réaliser une annonce en envoyant une presse dans certaines parties de sorte à atteindre tous les joueurs de toutes les parties en cours. Il peut lire et écrire dans les presses de toute les parties. Il peut lire les informations personnelles d'un inscrit. Il peut voir tous les retards dans toutes les parties. Il peut voir toutes les parties dans laquelle intervient d'un joueur donné. Il peut consulter les dates de dernière activite pour tous les comptes (soumission d'ordres) . Il peut vérifier les adresses IP. Il peut vérifier les adresses courriel. Il peut consulter la liste des comptes dont l'adresse courriel n'est pas confirmée. Il peut consulter les codes de vérification pour le forum. Il peut destituer un arbitre. Il peut changer le responsable d'un tournoi. Il peut changer le responsable d'un événement. Enfin, dans les parties : il voit les identités des joueurs même si la partie est anonyme, ainsi que les soumissions et les incidents même s'il n'est pas dans la partie.  Il peut voir les comptes oisifs et les comptes qui n'ont pas confirmé leur adresse courriel. Il peut en faire, des choses !",

    "Que peut faire un administrateur ?":
    "Un administrateur peut modifier ses nouvelles. Il peut se substituer à un inscrit. Il peut rectifier certains paramètres fixes (en théorie) et la position d'une partie. Il peut savoir les dates des dernières connexions réussies et manquées (erreur de pseudo/mot de passe). Il gère la liste des créateurs et des modérateurs.",

    "Comment créer une partie dans laquelle je joue ?":
    "Il se connecter, puis créer la partie (“éditer partie“ puis “créer“) sans oublier de cocher “Je veux juste jouer la partie“ tout en bas (sinon vous êtes arbitre de cette nouvelle partie, dans ce cas il faut démissioner de l'arbitrage). Un arbitre chevronné du site se chargera de prendre l'arbitrage.",

    "J'ai oublié mon mot de passe. Au secours !":
    "Entrer son pseudo et cliquer “Mot de passe oublié“. Un courriel est envoyé avec un lien. Cliquer sur le mien amène sur le site avec une authentification valable un temps limité. Se dépêcher de modifier son mot de passe.",

    "Comment créer un gros tournoi ?":
    """
          Super facile ! <br>
         <br>
    1- créer ou utiliser une partie modèle<br>
    2- remplir un document CSV (avec EXCEL par exemple) décrivant les parties cf. la page tournoi/créer plusieurs parties <br>
    3- si plusieurs arbitres, fournir à chaque arbitre le fichier avec juste les lignes correspondant à ses parties <br>
    4- chaque arbitre créé ses parties : <br>
             - sélectionne la partie modèle <br>
             - utilise la page tournoi/créer plusieurs parties <br>
    5- chaque arbitre démarre ses parties au moment opportun : <br>
             - sélectionne la page mes parties <br>
             - sélectionne les parties en attente <br>
             - clique sur démarrer pour chaque partie
    """,

    "Comment créer une partie modèle ?":
        """
         1- créer la partie<br>
         2- aller dans la console d'arbitrage<br>
         3- mettre les paramètres voulus à la partie <br>
         4- distinguer cette partie (pas obligatoire mais pratique) <br>
        """,

    "Qu'est ce qui change pour une partie “en direct“ ?":
    "Une telle partie est destinée à se dérouler comme sur un jeu de plateau. Le calcul des dates limites se fait en minutes et non en heures. Les retards sont comptés en minutes et non en heures entamées. Il est possible pour l'arbitre d'activer la supervision de la partie, qui forcera des ordres de désordre civil pour les joueurs automatiquement après la grâce. Pas de message de notification pour une telle partie. Pas d'accord pour résoudre après la date limite",

    "Qu'est ce qui change pour une partie “exposition“ ?":
    "Une telle partie n'est pas jouée sur le site. Elle est saisie par son arbitre à partir de feuilles d'ordres mais cette partie à eu lieu ailleurs (par exemple une table finale de championnat du monde). Avec juste un intérêt de consultation",

    "Pourquoi des parties sont “distinguées“ ?":
    "Ce sont soit des parties modèles de tournoi que l'on veut retrouver plus rapidement, soit des parties exposition sur lesquelles on veut attirer l'attention du badaud.",

    "Ce site est-il le site de jeu officiel de l'Association Francophone des Joueurs de Diplomacy ?":
    "Oui.",

    "(Pour les modérateurs) Quels sont les codes pour écrire sur le mur ?":
    """
    .ANNONCE_1 pour une popup (sur la même ligne) - admin et modo seulement  !<br>
    .ANNONCE_2 idem ANNONCE_1<br>
    .ANNONCE_3 idem ANNONCE_1<br>
    .HR pour un trait horizontal <br>
    .STRONG pour écrire en gras <br>
    .KBD pour écrire ce que l'on doit taper au clavier <br>
    .LINK pour mettre un lien <br>
    .BR pour aller à la ligne
    """

}
