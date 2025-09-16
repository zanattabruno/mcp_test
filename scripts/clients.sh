#!/usr/bin/env bash
set -euo pipefail

# Basic curl helpers for the Clients API
# Usage: set BASE_URL or pass as first arg. Default http://localhost:8000
BASE_URL=${1:-${BASE_URL:-http://localhost:8000}}
API="$BASE_URL/api/clients/"

jq_exists() {
  command -v jq >/dev/null 2>&1
}

hr() { printf '\n%s\n' '----------------------------------------'; }

echo "Using base: $BASE_URL"

list_clients() {
  hr; echo "GET list"; curl -sS "$API" | (jq_exists && jq . || cat)
}

create_client() {
  local name="$1" email="$2" phone="${3:-}"
  hr; echo "POST create $name <$email>";
  curl -sS -X POST "$API" \
    -H 'Content-Type: application/json' \
    -d "$(jq -n --arg name "$name" --arg email "$email" --arg phone "$phone" '{name:$name,email:$email,phone:$phone}')" \
    | (jq_exists && jq . || cat)
}

get_client() {
  local id="$1"
  hr; echo "GET detail id=$id"; curl -sS "$API$id/" | (jq_exists && jq . || cat)
}

update_client() {
  local id="$1" name="$2"
  hr; echo "PATCH update id=$id name=$name";
  curl -sS -X PATCH "$API$id/" -H 'Content-Type: application/json' -d "$(jq -n --arg name "$name" '{name:$name}')" | (jq_exists && jq . || cat)
}

delete_client() {
  local id="$1"
  hr; echo "DELETE id=$id"; curl -sS -X DELETE -i "$API$id/" | grep -E 'HTTP/|^$' || true
}

query_examples() {
  hr; echo "Filter by email"; curl -sS "$API?email=alice@example.com" | (jq_exists && jq . || cat)
  hr; echo "Search by name"; curl -sS "$API?search=Bob" | (jq_exists && jq . || cat)
  hr; echo "Order by created_at desc"; curl -sS "$API?ordering=-created_at" | (jq_exists && jq . || cat)
}

run_all() {
  list_clients
  create_client "Test User" "test.user@example.com" "+1-202-555-0199"
  list_clients
  # Grab an ID (last object)
  ID=$(curl -sS "$API" | (jq -r '.[-1].id' 2>/dev/null || sed -n 's/.*"id": \([0-9]*\).*/\1/p' | tail -n1))
  if [[ -n "${ID}" && "${ID}" != "null" ]]; then
    get_client "$ID"
    update_client "$ID" "Updated User"
    get_client "$ID"
    delete_client "$ID"
  else
    echo "Could not parse ID; skipping get/update/delete"
  fi
  query_examples
}

case "${2:-run_all}" in
  list) list_clients ;;
  create) create_client "${3:-Demo User}" "${4:-demo@example.com}" "${5:-}" ;;
  get) get_client "${3:?id required}" ;;
  update) update_client "${3:?id required}" "${4:?name required}" ;;
  delete) delete_client "${3:?id required}" ;;
  query) query_examples ;;
  run_all) run_all ;;
  *) echo "Unknown command"; exit 1 ;;
 esac
