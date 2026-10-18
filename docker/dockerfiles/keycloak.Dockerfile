FROM quay.io/keycloak/keycloak:26.0 AS base

ENV JAVA_OPTS_APPEND="-Dkeycloak.migration.replace-placeholders=true" \
    KC_HOSTNAME=localhost \
    KC_HOSTNAME_PORT=8080 \
    KC_HOSTNAME_STRICT=false \
    KC_HTTP_ENABLED=true

# NOTE:
# This's for `dev` environment only. The realm export and the values its ${...}
# placeholders resolve to are baked into the image (built from the ./docker
# context) so compose needs neither secret mounts nor an entrypoint override. The
# realm is staged outside `/opt/keycloak/data` because the datastore volume masks
# whatever is baked underneath it. `entrypoint.sh` copies it in.
COPY --chmod=755 ./keycloak/entrypoint.sh /opt/keycloak/entrypoint.sh
COPY --chmod=644 ./keycloak/cosmic-realm.json /opt/keycloak/cosmic-realm.json
COPY --chmod=755 ./secrets/*.txt /run/secrets/

EXPOSE 8080/tcp
ENTRYPOINT [ "/opt/keycloak/entrypoint.sh" ]
CMD [ "start-dev", "--import-realm" ]
