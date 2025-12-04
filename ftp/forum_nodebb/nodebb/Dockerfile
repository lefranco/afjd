FROM node:18-bookworm-slim

RUN apt-get update && apt-get install -y git python3 make g++

WORKDIR /app

# Clone et préparation
RUN git clone --branch v3.x --depth 1 https://github.com/NodeBB/NodeBB.git . && \
    # Garantir package.json à la racine
    find . -name "package.json" -type f -exec cp {} . \; 2>/dev/null || true && \
    [ -f "package.json" ] || echo '{"name":"nodebb"}' > package.json

# Fix SASS
RUN npm install sass --no-save --omit=dev && \
    sed -i 's/sass-embedded/sass/g' package.json 2>/dev/null || true

RUN npm install --omit=dev

EXPOSE 4567

CMD ["sh", "-c", "export NODEBB_SKIP_SASS=1 && node loader.js"]
