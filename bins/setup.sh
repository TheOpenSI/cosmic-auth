#!/usr/bin/env bash

set -euo pipefail


# Navigate to project root (one level up from 'bins/')
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "==> Creating required directories..."

mkdir -p docker/secrets
mkdir -p cores

echo "==> Checking and preparing environment/configuration files..."

# Helper function to conditionally copy files safely
safe_copy() {
    local src="$1"
    local dest="$2"

    if [ -f "$dest" ]; then
        echo "Skipped: [$dest] already exists (left untouched)."
    else
        cp "$src" "$dest"
        echo "Copied: [$src] -> [$dest]"
    fi
}

# Shared database service (.env)
for file in examples/cosmic_cfg*.example.env; do
    [ -f "$file" ] || continue
    new_name=$(basename "$file" | sed 's/\.example//')
    safe_copy "$file" "cores/$new_name"
done

# Auth (.env) → auth/
for file in examples/cosmic_auth.example.env; do
    [ -f "$file" ] || continue
    new_name=$(basename "$file" | sed 's/\.example//')
    safe_copy "$file" "cores/$new_name"
done

# Shared database secrets (.txt)
for file in examples/postgres_*.example.txt; do
    [ -f "$file" ] || continue
    new_name=$(basename "$file" | sed 's/\.example//')
    safe_copy "$file" "docker/secrets/$new_name"
done

# Keycloak secrets (.txt)
for file in examples/keycloak_*.example.txt; do
    [ -f "$file" ] || continue
    new_name=$(basename "$file" | sed 's/\.example//')
    safe_copy "$file" "docker/secrets/$new_name"
done

# Reconcile the shared-database credentials in `cores/cosmic_cfg.env` with the
# secret files the PostgreSQL container reads, so the Auth service can never
# drift from the database it talks to. Edit the secrets, not the env file.
DB_CONFIG="cores/cosmic_cfg.env"
DB_USER_SECRET="docker/secrets/postgres_usr.txt"
DB_PWD_SECRET="docker/secrets/postgres_pwd.txt"
DB_NAME_SECRET="docker/secrets/postgres_db.txt"

if [[ -f "${DB_USER_SECRET}" && -f "${DB_PWD_SECRET}" && -f "${DB_NAME_SECRET}" ]]; then
    DB_USER_VALUE="$(tr -d '\r\n' < "${DB_USER_SECRET}")"
    DB_PWD_VALUE="$(tr -d '\r\n' < "${DB_PWD_SECRET}")"
    DB_NAME_VALUE="$(tr -d '\r\n' < "${DB_NAME_SECRET}")"
    DB_TMP="${DB_CONFIG}.tmp"

    while IFS= read -r line || [ -n "${line}" ]; do
        case "${line}" in
            DB_USER=*)     printf 'DB_USER=%s\n' "${DB_USER_VALUE}" ;;
            DB_PASSWORD=*) printf 'DB_PASSWORD=%s\n' "${DB_PWD_VALUE}" ;;
            DB_NAME=*)     printf 'DB_NAME=%s\n' "${DB_NAME_VALUE}" ;;
            *)             printf '%s\n' "${line}" ;;
        esac
    done < "${DB_CONFIG}" > "${DB_TMP}"
    mv "${DB_TMP}" "${DB_CONFIG}"

    echo "==> Reconciled [DB_USER], [DB_PASSWORD] and [DB_NAME] in [${DB_CONFIG}] with [docker/secrets/postgres_*.txt]."
else
    echo "==> Skipped: shared-database credentials not reconciled (postgres secrets missing)."
fi

# Generates the RS256 key-pair used to sign the CoSMIC session cookie
SECRETS_DIR="docker/secrets"
PRIVATE_KEY="${SECRETS_DIR}/cosmic_private_session.pem"
PUBLIC_KEY="${SECRETS_DIR}/cosmic_public_session.pem"

if [[ -f "${PRIVATE_KEY}" && -f "${PUBLIC_KEY}" ]]; then
    echo "==> Skipped: session key-pair already exists at [${SECRETS_DIR}] (left untouched)."
else
    echo "==> Generating RSA-2048 session key-pair..."
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "${PRIVATE_KEY}"
    openssl rsa -in "${PRIVATE_KEY}" -pubout -out "${PUBLIC_KEY}"

    echo "Generated:"
    echo " 1. [${PRIVATE_KEY}]"
    echo " 2. [${PUBLIC_KEY}]"
    echo "NOTE: Never commit these files. Rotating the keypair invalidates all active sessions."
fi

echo "==> Setup complete!"
echo "IMPORTANT:"
echo " 1. Review all generated files and update credentials/configurations as needed."
echo " 2. Remove insecure default values before running the system."
