# Utilise Nginx léger
FROM nginx:alpine

# Copie le contenu de ton site dans le dossier servi par Nginx
COPY ./html/ /usr/share/nginx/html/
COPY ./nginx_conf/default.conf /etc/nginx/conf.d/default.conf

# Expose le port 80 dans le container
EXPOSE 80

# Commande par défaut pour démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]
