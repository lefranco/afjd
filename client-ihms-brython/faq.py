""" faq """


FAQ_CONTENT_TABLE = {

    "Pourquoi certains messages sont en français, certains en anglais, voire certains dans un mélange des deux ?":
    "Les messages issus de l'interface 'front end' sont en français (sauf omission à corriger rapidement). Les messages issus du serveur 'back end' sont en anglais.",

    "Peut-on jouer plusieurs rôles sur une partie ?":
    "Non, cela n'est pas prévu. Il doit y avoir 8 intervenants distincts sur une partie (arbitre y compris).",

    "Peut-on faire des erreurs d'ordres ?":
    "Eh non. Les ordres sont 100% vérifiés avant d'être enregistrés. Par contre le menu 'taguer' dans une partie permet une communcation par ordres 'ésotériques'. Cela ne presente un intérêt que dans les parties sans communication.",

    "Quand a lieu la résolution ?":
    "Quand le dernier joueur qui a des ordres à rendre coche sur la case 'prêt à résoudre' tout simplement (ou quand l'arbitre le fait à sa place pour éviter que la partie ne s'éternise).",

    "Pourquoi les dates limites changent-elles de couleur ?":
    "Le code de couleur est assez conventionnel. Jaune signifie que la date limite est proche (24h). Orange qu'elle est passée. Rouge que la grâce est aussi passée. Soyez ponctuels !",

    "Il y a des retards indiqués. Dans quel cas un joueur est-il marqué en retard ?":
    "Passer ses ordres signifie réaliser une transition 'pas prêt à résoudre' (ou pas d'information) -> 'prêt à résoudre'. Un retard signifie que cela est réalisé après la date limite (que ce soit par le joueur ou par l'arbitre). Si l'arbitre reporte la date limite, le retard n'est pas effacé (mais il est impossible d'avoir deux retards sur une même saison.) Soyez ponctuels !",

    "Pourquoi les unités ne se déplacent pas dans le bac à sable ?":
    "Le bac à sable n'a pas vocation à déplacer les unités, il cherche à répondre à la question 'que se passerait-il si...'. Il faut bien lire le compte rendu des ordres sous forme de texte sous la carte.",

    "Eh, je pense avoir trouvé un bug dans le moteur de résolution. Que faire ?":
    "Le moteur s'appuie sur le DATC. Il faut utiliser le lien en page d'accueil pour envoyer un courriel et signaler le problème. Reproduisez le soigneusement avec le bac à sable.",

    "Où trouver des explications sur les paramètres des parties ?":
    "Soit en survolant les titres à la création de la partie, soit en consultant le menu 'paramètres' d'une partie existante.",

    "Comment remplacer un joueur ?":
    "C'est le rôle de l'arbitre. Il faut lui retirer le rôle dans la console d'arbitrage et attribuer le rôle à un autre joueur dans la partie, qu'il aura fallu faire venir au préalable. Faire venir ou partir les joueurs de la partie se réalise par contre dans le menu appariement.",

    "Que peut faire l'arbitre ?":
    "L'arbitre connaît l'identité des joueurs de sa partie. Il démarre et arrête la partie. Il peut forcer des ordres de désordre civil pour un pays. Il peut forcer un accord pour résoudre pour un pays. Il peut retirer ou ajouter un joueur dans une partie, et allouer un rôle ou retirer un rôle à un joueur dans une partie. Il peut modifier une date limite (même si celle-ci est gérée par le système). Il gère également les paramètres de la partie.",

    "Que peut faire un modérateur ?":
    "Un modérateur peut voir le courriel et le numéro de téléphone d'un inscrit. Il peut retrouver un pseudo à partir d'une adresse courriel. Il peut voir qui a soumis les ordres sur toutes les parties du site. Il peut voir le résultat complet d'un tournoi (anonyme ou pas). Enfin, dans les parties : il voit les identités des joueurs même si la partie est anonyme, ainsi que les soumissions et les incidents même s'il n'est pas dans la partie.",

    "Que peut faire un administrateur ?":
    "Il peut rectifier la position d'une partie. Il peut modifier les nouvelles. Il peut savoir les dates des dernières connexions et les connexions manquées (erreur de pseudo/mot de passe). Il peut se substituer à un inscrit. Il peut envoyer un courriel de la part du site. Enfin, il gère les modérateurs.",

    "Comment créer une partie dans laquelle je joue ?":
    "Il faut créer la partie, puis se retirer de l'arbitrage et demander à un arbitre de parties du site d'en prendre l'arbitrage.",

    "Qu'est ce qui change pour une partie 'en direct' ?":
    "Une telle partie est destinée à se dérouler comme sur un jeu de plateau. Le calcul des dates limites se fait en minutes et non en heures. Il est possible d'observer la partie (mise à jour régulière du plateau). Il est possible pour l'arbitre d'activer la supervision de la partie, qui forcera des ordres pour les joueurs automtiquement après la grâce. Pas de message de notification pour une telle partie.",

    "C'est quoi ce truc : 'consulter l'oracle sur cette position' ?":
    "Pas encore développé. Fournira une suggestion de jeux d'ordres à partir d'une position...",

    "Est-il prévu de développer des variantes ?":
    "Certainement. Hundred tient la corde pour le moment...",

    "Je veux donner de l'argent pour le site. Que faire ?":
    "Reportez-vous à la page d'accueil/liens du site pour le lien vers le site de recueil des dons.",

    "Comment discuter avec les membres de la communauté":
    "Reportez-vous à la page accueil/liens du site pour le lien vers la brique sociale.",

    "Ce site est-il le site de jeu officiel de l'AFJD ?":
    "Oui. Une autre interface moins rustique est prévue mais plus tard. En principe...",
}
