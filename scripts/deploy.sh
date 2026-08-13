#!/usr/bin/env bash
# Deploys idilio-chat end to end: pulls the latest commit on whatever branch
# is already checked out, rebuilds the Docker image from source (never
# reuses a stale pulled tag), recreates the container, waits for it to
# report healthy, then re-applies the idilio-script-intelligence
# skill/tools/knowledge/settings via seed.py.
#
# Meant to run ON the deploy host, from the repo root, on the branch
# already checked out -- this only pulls --ff-only on the CURRENT branch.
# Point CI/an operator at the right branch before invoking this; it doesn't
# switch branches itself.
#
# Usage:
#   DEPLOY_ADMIN_EMAIL=you@idilio.tv DEPLOY_ADMIN_PASSWORD='...' \
#       ./scripts/deploy.sh
#
# Optional env vars (defaults match the current chat.idilio.tv setup):
#   DEPLOY_BASE_URL   (default http://localhost:3003)
#   DEPLOY_MODELS     (default gpt-5.6-luna,gpt-5.6-terra,gpt-5.6-sol)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

: "${DEPLOY_ADMIN_EMAIL:?set DEPLOY_ADMIN_EMAIL -- the admin account seed.py signs in as}"
: "${DEPLOY_ADMIN_PASSWORD:?set DEPLOY_ADMIN_PASSWORD}"
DEPLOY_BASE_URL="${DEPLOY_BASE_URL:-http://localhost:3003}"
DEPLOY_MODELS="${DEPLOY_MODELS:-gpt-5.6-luna,gpt-5.6-terra,gpt-5.6-sol}"

echo "==> Pulling latest ($(git branch --show-current))..."
git pull --ff-only

echo "==> Building the image from source (this is what actually bakes in"
echo "    the app's own code/branding -- docker compose up alone would just"
echo "    reuse whatever's already pulled/cached under this tag)..."
docker compose build open-webui

echo "==> Recreating the container..."
docker compose up -d

echo "==> Waiting for it to report healthy (Dockerfile HEALTHCHECK, up to 5min)..."
healthy=false
for i in $(seq 1 30); do
  status="$(docker inspect --format='{{.State.Health.Status}}' open-webui 2>/dev/null || echo starting)"
  if [ "$status" = "healthy" ]; then
    echo "    healthy after $((i * 10))s"
    healthy=true
    break
  fi
  sleep 10
done
if [ "$healthy" != "true" ]; then
  echo "    still not healthy after 300s (status: $status) -- check: docker logs open-webui" >&2
  exit 1
fi

echo "==> Seeding skill/tools/knowledge/settings on: $DEPLOY_MODELS..."
(
  cd idilio-script-intelligence/openwebui
  python3 seed.py --base-url "$DEPLOY_BASE_URL" \
    --email "$DEPLOY_ADMIN_EMAIL" --password "$DEPLOY_ADMIN_PASSWORD" \
    --base-model-id "$DEPLOY_MODELS"
)

echo "==> Deploy complete."
