FROM node:18-slim
RUN apt-get update && apt-get install -y git
WORKDIR /app
RUN git clone https://github.com/NodeBB/NodeBB.git .
RUN find . -name "package.json" -exec cp {} . \; 2>/dev/null || true
RUN [ -f "package.json" ] || echo '{"name":"nodebb"}' > package.json
RUN npm install
EXPOSE 4567
CMD ["node", "loader.js"]
