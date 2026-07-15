#!/usr/bin/env bash

set -e

echo "==> Creating required directories..."
mkdir -p docker/secrets
mkdir -p docker/configs
mkdir -p cores

echo "==> Copying and preparing environment/configuration files..."

# Backend service (.env)
for file in examples/cosmic_*.example.env; do
    [ -f "$file" ] || continue
    new_name=$(basename "$file" | sed 's/\.example//')
    cp "$file" "cores/$new_name"
    echo "Copied: $file -> cores/$new_name"
done

# PostgreSQL (.txt)
for file in examples/postgres_*.example.txt; do
    [ -f "$file" ] || continue
    new_name=$(basename "$file" | sed 's/\.example//')
    cp "$file" "docker/secrets/$new_name"
    echo "Copied: $file -> docker/secrets/$new_name"
done

# pgAdmin secrets (.txt)
for file in examples/pgadmin_*.example.txt; do
    [ -f "$file" ] || continue
    new_name=$(basename "$file" | sed 's/\.example//')
    cp "$file" "docker/secrets/$new_name"
    echo "Copied: $file -> docker/secrets/$new_name"
done

# pgAdmin configs (.json)
for file in examples/pgadmin_*.example.json; do
    [ -f "$file" ] || continue
    new_name=$(basename "$file" | sed 's/\.example//')
    cp "$file" "docker/configs/$new_name"
    echo "Copied: $file -> docker/configs/$new_name"
done

echo "==> Setup complete!"
echo "IMPORTANT:"
echo " - Review all generated files and update credentials/configurations as needed."
echo " - Remove insecure default values before running the system."
