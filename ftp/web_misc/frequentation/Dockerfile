# Utilise Nginx léger
FROM nginx:alpine

# Copie le contenu de ton site dans le dossier servi par Nginx
COPY . /usr/share/nginx/html

# Expose le port 80 dans le container
EXPOSE 80

# Commande par défaut pour démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]
