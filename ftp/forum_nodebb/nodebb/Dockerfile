FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    nano \
    iputils-ping \
    net-tools \
    curl \
    gnupg \
    ca-certificates \
    && apt-get clean


# From NodeBB website installation
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get install -y nodejs

CMD ["tail", "-f", "/dev/null"]
