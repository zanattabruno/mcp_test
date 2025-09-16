#!/usr/bin/env bash
set -euo pipefail

# Load sample clients from fixture using Django loaddata
# Usage: ./scripts/load_clients_fixture.sh [manage.py directory]

PROJECT_DIR=${1:-$(dirname "$0")/..}
cd "$PROJECT_DIR"

python manage.py loaddata api/fixtures/clients.json
