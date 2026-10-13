#!/usr/bin/env bash

set -euo pipefail


# Navigate to project root (one level up from 'bins/')
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Similar concept to the `-DbEnvFile` parameter in the PowerShell script version:
# the `.env` file the shared-database credentials are reconciled from.
DB_ENV_FILE="${1:-../cosmic-db/cores/cosmic_cfg.env}"

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

# Keycloak secrets (.txt)
for file in examples/keycloak_*.example.txt; do
    [ -f "$file" ] || continue
    new_name=$(basename "$file" | sed 's/\.example//')
    safe_copy "$file" "docker/secrets/$new_name"
done

# Reconcile the shared-database credentials in `cores/cosmic_cfg.env` with the
# values declared in another `.env` file (by default the database owner,
# `cosmic-db`). This way, the Auth micro-service can never drift from the
# database it talks to. Point it elsewhere with the positional argument.
DB_CONFIG="cores/cosmic_cfg.env"

read_env_value() {
    sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$2" \
        | tr -d '\r' \
        | tail -n 1 \
        | sed -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'\$/\1/"
}

if [[ ! -f "${DB_ENV_FILE}" ]]; then
    echo "==> Skipped: shared-database credentials not reconciled ([${DB_ENV_FILE}] not found)."
elif [[ ! -f "${DB_CONFIG}" ]]; then
    echo "==> Skipped: shared-database credentials not reconciled ([${DB_CONFIG}] not found)."
else
    DB_USER_VALUE="$(read_env_value DB_USER "${DB_ENV_FILE}")"
    DB_PWD_VALUE="$(read_env_value DB_PASSWORD "${DB_ENV_FILE}")"
    DB_NAME_VALUE="$(read_env_value DB_NAME "${DB_ENV_FILE}")"

    if [[ -z "${DB_USER_VALUE}" || -z "${DB_PWD_VALUE}" || -z "${DB_NAME_VALUE}" ]]; then
        echo "==> Skipped: shared-database credentials not reconciled (missing [DB_USER], [DB_PASSWORD] or [DB_NAME] in [${DB_ENV_FILE}])."
    else
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

        echo "==> Reconciled [DB_USER], [DB_PASSWORD] and [DB_NAME] in [${DB_CONFIG}] with [${DB_ENV_FILE}]."
    fi
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
