""" whynot """


WHYNOT_CONTENT_TABLE = {

    "Pourquoi la brique jeu est - elle si lente ?":
    "Par ce que cette brique est décomposée en un front end qui s'execute dans le navigateur et un back end qui est un serveur REST sur l'ordinateur loué par l'association. Le gros de la lenteur vient du nombre des requêtes entre les deux briques que certaines pages nécessitent. Ce problème est accru dans les pays loins du serveur (il est en France). Un écart de 20ms à 500ms se multiplie par autant de requêtes. Cet aspect n'est devenu important que lorsque des personnes à l'étranger ont commené à jouer, et le developpement du site était déjà très avancé. Par ailleurs, le développement du front end est en python compilé en javascript, aussi cela explique la lenteur relative de chargement de la page d'accueil.",

    "Pourquoi je peux pas commettre des erreurs volontaires d'ordres ?":
    "Le moteur de jeu a été développé au départ en vérifiant les ordres en détail. Il a été réalisé il y plus de dix ans et il n'a pas été question de le refondre pour faire ce site. Ce componsant est particulièrement sophistiqué. Par ailleurs, cette solution présente l'avantage de ne pas laisser les joueurs débutants faire des erreurs *involontaires* d'ordres. Un sous menu complémentaitre nommé 'Ordonner_2' a été ajouté qui permet tout de même d'entrer des ordres de communication. L'option de faire exprès de se tromper dans ses ordres par ruse et d'incriminer le site n'est pas envisageable.",

    "Pourquoi il faut un compte séparé entre joueur et arbitre sur une partie ?":
    "Cela a été implémenté ainsi au départ, et tous les développements s'appuient sur le compte (et le jeton prouvant l'identité) pour savoir si la requête vient d'un arbitre ou d'un joueur. Autoriser un même compte aurait beaucoup d'impacts sur toute la couche de vérification des autorisations. Pour une partie amicale, laisser l'arbitrage à un habitué du site, ou créer deux comptes séparés.",

    "Pourquoi je peux pas mettre un accent dans mon pseudo et dans le nom de la partie ?":
    "Cette contrainte est venue pour des raisons de simplicité, pour que les parties et les pseudo apparaissent simplement dans les liens URL. Le jeu en vaut-il la chandelle ?",

    "Pourquoi il n'y a pas de fiche joueur ?":
    "C'est prévu dans un avenir assez proche. Néanmoins les participations aux parties anonymes resteront invisibles...",

}
