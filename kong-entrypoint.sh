#!/bin/sh

set -eu

# kong.yml is mounted read-only. Render the runtime JWT secret into a
# temporary writable config before starting Kong.
sed "s|__JWT_SECRET__|${JWT_SECRET}|g" \
    /kong/declarative/kong.yml > /tmp/kong.yml

export KONG_DECLARATIVE_CONFIG=/tmp/kong.yml

exec /docker-entrypoint.sh kong docker-start
