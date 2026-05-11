#!/bin/bash
# One-command re-deploy: pull latest code, rebuild, restart
set -e

echo "==> Pulling latest code..."
git pull origin main

echo "==> Rebuilding images..."
docker compose -f docker-compose.prod.yml build --no-cache

echo "==> Restarting services..."
docker compose -f docker-compose.prod.yml up -d

echo "==> Cleaning up old images..."
docker image prune -f

echo "==> Done. App live at https://nimbleleads.co"
docker compose -f docker-compose.prod.yml ps
