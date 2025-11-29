FROM php:8.3-fpm-alpine

# Installation des dépendances système nécessaires pour Flarum et Composer
RUN apk update && apk add --no-cache \
    mariadb-client \
    git \
    openssh-client \
    icu-dev \
    libxml2-dev \
    libzip-dev \
    libpng-dev \
    libjpeg-turbo-dev \
    freetype-dev \
    gmp-dev \
    # Outils de construction pour les extensions PHP
    g++ \
    make

# INSTALLATION DE COMPOSER
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Installation des extensions PHP requises par Flarum
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
        pdo_mysql \
        mysqli \
        gd \
        exif \
        zip \
        opcache \
        intl \
        gmp \
        bcmath

# Configuration de l'utilisateur www-data (UID 82)
# Cette étape garantit que l'UID est correctement configuré.
RUN deluser www-data 2>/dev/null || true \
    && delgroup www-data 2>/dev/null || true \
    && addgroup -g 82 www-data \
    && adduser -D -u 82 -G www-data www-data

# COPIE DE LA CONFIGURATION PHP :
COPY custom.ini /usr/local/etc/php/conf.d/custom.ini

# Définir le répertoire de travail pour le code Flarum (partagé avec Nginx)
WORKDIR /var/www/html

# TODO ???
# USER www-data

