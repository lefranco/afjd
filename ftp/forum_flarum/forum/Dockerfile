FROM php:8.2-fpm

RUN apt-get update && apt-get install -y \
    git unzip zip libzip-dev libpng-dev libonig-dev curl \
    && docker-php-ext-install pdo pdo_mysql

# Installer Composer
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

WORKDIR /flarum/app

# Copier composer.json corrigé
COPY composer.json composer.json

# Installer Flarum + extensions
RUN composer install --no-dev --prefer-dist --optimize-autoloader

RUN composer clear-cache

