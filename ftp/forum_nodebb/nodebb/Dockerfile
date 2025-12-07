FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# System depedencies
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

# Install node JS
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get install -y nodejs

#  forum user
RUN groupadd -r forum && useradd -r -g forum -m -s /bin/bash forum

# NodeBB folder
RUN mkdir -p /app && chown -R forum:forum /app

USER forum
WORKDIR /app

# Clone NodeBB
RUN git clone -b v4.x https://github.com/NodeBB/NodeBB.git nodebb

WORKDIR /app/nodebb

# Expose NodeBB port
EXPOSE 4567

# keep it alive"
CMD ["tail", "-f", "/dev/null"]

