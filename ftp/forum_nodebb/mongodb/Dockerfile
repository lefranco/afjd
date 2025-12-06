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
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
   gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg \
   --dearmor
RUN echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-8.0.list
RUN apt-get update && apt-get install -y mongodb-org

CMD ["tail", "-f", "/dev/null"]
