FROM node:18-alpine

# 1. Installer outils
RUN apk add --no-cache wget python3 make g++ tar

# 2. Préparer répertoire
WORKDIR /app

# 3. Télécharger
RUN wget -q -O nodebb.tar.gz https://github.com/NodeBB/NodeBB/archive/refs/heads/v3.x.tar.gz

# 4. Extraire et chercher package.json
RUN tar -xzf nodebb.tar.gz --strip-components=1 && \
    rm nodebb.tar.gz

# 5. RECHERCHER package.json
RUN echo "=== RECHERCHE package.json ===" && \
    find /app -name "package.json" -type f && \
    echo "=== Contenu total ===" && \
    find /app -type f -name "*.json" | head -20

# 6. Vérifier s'il existe quelque part
RUN if find /app -name "package.json" -type f | grep -q package.json; then \
        echo "✅ package.json trouvé quelque part"; \
        # Le copier à la racine si nécessaire
        find /app -name "package.json" -type f -exec cp {} /app/ \; 2>/dev/null || true; \
    else \
        echo "❌ AUCUN package.json trouvé"; \
        exit 1; \
    fi

# 7. Installation
RUN [ -f "package.json" ] && npm install --omit=dev || \
    (echo "Installation sans package.json..." && npm init -y && npm install nodebb --omit=dev)

EXPOSE 4567

CMD ["node", "loader.js"]
