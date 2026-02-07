#!/bin/bash

KEYCLOAK_DIR=$1

if [ -z "$KEYCLOAK_DIR" ]; then
  echo "Usage: ./setup_keycloak.sh /path/to/keycloak"
  exit 1
fi

echo "Importing realm..."

$KEYCLOAK_DIR/bin/kc.sh import \
  --file "$(pwd)/keycloak/hackathon-realm.json"

echo "Starting Keycloak..."

$KEYCLOAK_DIR/bin/kc.sh start-dev
