""" whynot """


WHYNOT_CONTENT_TABLE = {

    "Pourquoi la brique jeu est - elle si lente ?":
    "Par ce que cette brique est décomposée en un front end qui s'execute dans le navigateur et un back end qui est un serveur REST sur l'ordinateur loué pas l'association. Le gros de la lenteur vient du nombre des requêtes entre les deux que certaines pages nécessitent. Ce problème est accru dans les pays loins du serveur (il est en France). Un écart de 20ms à 500ms se multiplie par autant de requêtes. Cet aspect est devenu important que lorsque des personnes à l'étranger ont commené à jouer, et le developpement du site était déjà très avance. Par ailleurs, le développement du front end est en python compilé en javascript, aussi cela explique la lenteur relative de chargement de la page d'accueil.",

    "Pourquoi je peux pas commettre des erreurs volontaires d'ordres ?":
    "Le moteur de jeu a été développé au départ en vérifiant les ordres en détail. Il a été réalisé il y plus de dix ans et il n'a pas été question de le refondre pour faire ce site. Ce componsant est particulièrement sophistiqué. Par ailleurs, cette solution présente l'avantage de ne pas laisser les joueurs débutants faire des erreurs *involontaires* d'ordres. Un sous menu complémentaitre nommé 'taguer' a été ajouté qui permet tout de même d'entrer des ordres de communication. L'option de faire exprès de se tromper dans ses ordres par ruse et d'incriminer le site n'est pas envisageable.",

    "Pourquoi la résolution ne se déclenche pas automatiquement après la date limite, que les joueurs soient d'accord ou pas ? En plus je n'ai pas envie que la partie avance avant la date limite, cela m'inquiète !":
    "Cela nécessite une sorte de macanique infernale qui surveille les parties de anière périodique et déclenche des résolutions. Nous n'avons par encore d'idée précise sur comment la réaliser. Ou bien de donner à un joueur qui arrive sur la partie après la date limite la possibilté de déclencher cette résolution.",

    "Pourquoi il faut un compte séparé entre joueur et arbitre sur une partie ?":
    "Cela a été implémenté ainsi au départ, et tous les développements s'appuient sur le compte (et le jeton prouvant l'identité) pour savoir si la requête vient d'un arbitre ou d'un joueur. Autoriser un même compte aurait beaucoup d'impacts sur toute la couche de vérification des autorisations. Pour une partie amicale, laisser l'arbitrage à un habitué du site, ou créer deux comptes séparés.",

    "Pourquoi il faut un compte sur la brique sociale et un compte sur la brique jeu ?":
    "Nous avons pas encore trouvé ni le temps ni les compétences pour faire en sorte de partager l'identifiant entre les deux",

    "Pourquoi je peux pas mettre un accent dans mon pseudo et dans le nom de la partie ?":
    "Cette contrainte est venue pour des raisons de simplicité, pour que les parties et les pseudo apparaissent simplement dans les liens URL. Le jeu en vaut-il la chandelle ?",

    "Pourquoi quand je passe mes ordres je suis obligé de cliquer sous le label alors que je pourrais plus simplement cliquer n'importe où sur la zone ?":
    "Parce qu'un implémentation plus simple a été réalisée qui détecte la position d'un clic non par rapport à son appartenance à un polygone, mais par sa proximité à un point central, situé juste en dessous de la légende et où se placent les unités.",

    "Pourquoi les unités sont placées parfois bizarrement dans leur zone sur la carte ?":
    "Ce placement est réalisé par un algorithme de centrage automatique sur le polygone de région. Pour améliorer cette position il faudrait modifier la carte elle-même puisque le positionnement manuel est trop fastidieux, surtout quand viendront des variantes avec des cartes ésotériques. Ce point sera remonté au concepteur de la carte.",

    "Pourquoi je peux pas récupérer mon mot de passe à partir de mon adresse courriel ?":
    "C'est assez long à réaliser. C'est prévu dans un avenir assez proche.",

    "Pourquoi il n'y a pas de calcul de ELO des joueurs ?":
    "C'est prévu dans un avenir assez proche. Le principal obstacle sera la compréhension de la formule par le codeur (ainsi que ce mettre d'accord sur cette formule) !",

    "Pourquoi il n'y a pas de fiche joueur ?":
    "C'est prévu dans un avenir très proche. Néanmoins les participations aux parties anonymes resteront invisibles...",

}
