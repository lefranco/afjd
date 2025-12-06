FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    iputils-ping \
    net-tools \
    gnupg \
    ca-certificates \
    git \
    python3 \
    coreutils \
    build-essential \
    nano \
    && apt-get clean

# From NodeBB website installation

# node js installation
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get install -y nodejs

# Clone NodeBB
RUN mkdir -p /app \
    && cd /opt \
    && git clone -b v4.x https://github.com/NodeBB/NodeBB.git /app/nodebb

# Créer l'utilisateur forum
RUN groupadd -r forum && useradd -r -g forum -m -s /bin/bash forum

# Changer les permissions APRÈS l'installation
RUN chown -R forum:forum /app

# Définir le répertoire de travail
WORKDIR /app/nodebb

# Exposer le port de NodeBB
EXPOSE 4567

USER forum

# keep it alive"
CMD ["tail", "-f", "/dev/null"]
