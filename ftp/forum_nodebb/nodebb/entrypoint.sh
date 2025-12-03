#!/bin/bash
set -e

# Timezone (optionnel)
if [ -n "$TZ" ]; then
    ln -sf /usr/share/zoneinfo/$TZ /etc/localtime
    echo $TZ > /etc/timezone
fi

# Wait for MongoDB
echo "Waiting for MongoDB..."
while ! nc -z mongo 27017; do
    sleep 2
done
echo "MongoDB is ready!"

# Check if config exists
if [ ! -f "/usr/src/app/config.json" ]; then
    echo "First run: Setting up NodeBB..."
    
    # Generate random secret
    SECRET=$(openssl rand -hex 32)
    
    # Create config.json
    cat > /usr/src/app/config.json << EOF
{
    "url": "${NODEBB_URL:-http://localhost:4567}",
    "secret": "${SECRET}",
    "database": "mongo",
    "port": 4567,
    "mongo": {
        "host": "${MONGO_HOST:-mongo}",
        "port": ${MONGO_PORT:-27017},
        "username": "${MONGO_USERNAME:-}",
        "password": "${MONGO_PASSWORD:-}",
        "database": "${MONGO_DATABASE:-nodebb}",
        "uri": ""
    },
    "upload_path": "/usr/src/app/public/uploads"
}
EOF
    
    echo "Config file created. Starting NodeBB setup..."
    
    # Run setup non-interactively
    ./nodebb setup || echo "Setup may have warnings, continuing..."
    
    echo "NodeBB setup completed!"
else
    echo "Existing config found, skipping setup."
fi

# Ensure proper permissions
chown -R node:node /usr/src/app/public/uploads /usr/src/app/logs

# Start NodeBB
echo "Starting NodeBB..."
exec "$@"
