FROM node:18-bookworm-slim

# Installer
RUN apt-get update && apt-get install -y git python3 make g++

WORKDIR /usr/src/app

# Cloner
RUN git clone --branch v3.x --depth 1 https://github.com/NodeBB/NodeBB.git .

# Garantir package.json à la racine
RUN find . -name "package.json" -type f -exec cp {} . \; 2>/dev/null || true && \
    [ -f "package.json" ] || echo '{"name":"nodebb"}' > package.json

# Fix SASS
RUN npm install sass --no-save --omit=dev && \
    rm -rf node_modules/sass-embedded* 2>/dev/null || true && \
    sed -i 's/"sass-embedded"/"sass"/g' package.json 2>/dev/null || true

# Installer dépendances
RUN npm install --omit=dev --legacy-peer-deps

EXPOSE 4567

CMD ["node", "loader.js"]

