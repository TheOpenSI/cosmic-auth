#!/bin/bash
# Entrypoint for the CoSMIC Keycloak image.
#
# The realm export resolves ${...} placeholders from the environment, so the
# baked secrets are exported under the names it expects before handing over to
# `kc.sh`. `tr -d '\r\n'` keeps Windows line endings out of the values.

set -e


# The datastore volume masks anything baked under /opt/keycloak/data, so the
# realm export is staged into the import directory on every start. Keycloak only
# imports it while the datastore has no `cosmic` realm.
mkdir -p /opt/keycloak/data/import
cp -f /opt/keycloak/cosmic-realm.json /opt/keycloak/data/import/cosmic-realm.json


read_secret() {
    tr -d '\r\n' < "/run/secrets/$1.txt"
}


export KEYCLOAK_SMTP_USER="$(read_secret keycloak_smtp_user)"
export KEYCLOAK_SMTP_PWD="$(read_secret keycloak_smtp_pwd)"
export KC_BOOTSTRAP_ADMIN_USERNAME="$(read_secret keycloak_admin_usr)"
export KC_BOOTSTRAP_ADMIN_PASSWORD="$(read_secret keycloak_admin_pwd)"
export KEYCLOAK_CLIENT_SECRET="$(read_secret keycloak_client_secret)"
export KEYCLOAK_TEST_USER_EMAIL="$(read_secret keycloak_test_user_email)"
export KEYCLOAK_TEST_USER_PASSWORD="$(read_secret keycloak_test_user_pwd)"
export KEYCLOAK_GOOGLE_CLIENT_ID="$(read_secret keycloak_google_client_id)"
export KEYCLOAK_GOOGLE_CLIENT_SECRET="$(read_secret keycloak_google_client_secret)"
export KEYCLOAK_MICROSOFT_CLIENT_ID="$(read_secret keycloak_microsoft_client_id)"
export KEYCLOAK_MICROSOFT_CLIENT_SECRET="$(read_secret keycloak_microsoft_client_secret)"
export KEYCLOAK_MICROSOFT_TENANT_ID="$(read_secret keycloak_microsoft_tenant_id)"


exec /opt/keycloak/bin/kc.sh "$@"
