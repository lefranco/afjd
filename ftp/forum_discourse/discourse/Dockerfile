# ---- Base ----
FROM ruby:3.3

# ---- Installer dépendances système ----
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    nodejs \
    imagemagick \
    git \
    curl \
    gnupg \
    libyaml-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- Activer Corepack pour gérer Bundler ----
RUN corepack enable

# ---- Créer l’utilisateur Discourse ----
RUN useradd -ms /bin/bash discourse

# ---- Définir le répertoire de travail ----
WORKDIR /home/discourse/app

# ---- Donner les droits à discourse ----
RUN chown -R discourse:discourse /home/discourse/app

# ---- Passer à l’utilisateur discourse ----
USER discourse

# ---- Cloner Discourse ----
RUN git clone https://github.com/discourse/discourse.git .

# ---- Installer Bundler compatible avec Gemfile.lock ----
RUN gem install bundler -v 2.6.4

# ---- Configurer Bundler et installer les gems ----
RUN bundle config set deployment 'true' \
    && bundle config set without 'test' \
    && bundle install -j$(nproc)

# ---- Exposer le port interne de Discourse ----
EXPOSE 3000

# ---- Commande de démarrage ----
CMD ["bin/rails", "server", "-b", "0.0.0.0"]

