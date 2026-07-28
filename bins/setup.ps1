# Similar concept to the shebang defined in Bash script version
#Requires -Version 7.0

# Similar concept to the `set -e` flag in Bash script version
$ErrorActionPreference = "Stop"

Write-Host "==> Creating required directories..."
New-Item -ItemType Directory -Force -Path "docker\secrets" | Out-Null
New-Item -ItemType Directory -Force -Path "docker\configs" | Out-Null
New-Item -ItemType Directory -Force -Path "cores" | Out-Null
New-Item -ItemType Directory -Force -Path "auth" | Out-Null

Write-Host "==> Copying and preparing environment/configuration files..."

# Backend service (.env)
foreach ($file in (Get-ChildItem -Path "examples" -Filter "cosmic_cfg*.example.env" -ErrorAction SilentlyContinue))
{
    $newName = $file.Name -replace "\.example", ""
    Copy-Item -Path $file.FullName -Destination "cores\$newName"
    Write-Host "Copied: $($file.FullName) -> cores\$newName"
}

# Auth (.env) → auth/
foreach ($file in (Get-ChildItem -Path "examples" -Filter "cosmic_auth.example.env" -ErrorAction SilentlyContinue))
{
    $newName = $file.Name -replace "\.example", ""
    Copy-Item -Path $file.FullName -Destination "auth\$newName"
    Write-Host "Copied: $($file.FullName) -> auth\$newName"
}



# PostgreSQL (.txt)
foreach ($file in (Get-ChildItem -Path "examples" -Filter "postgres_*.example.txt" -ErrorAction SilentlyContinue))
{
    $newName = $file.Name -replace "\.example", ""
    Copy-Item -Path $file.FullName -Destination "docker\secrets\$newName"
    Write-Host "Copied: $($file.FullName) -> docker\secrets\$newName"
}

# pgAdmin secrets (.txt)
foreach ($file in (Get-ChildItem -Path "examples" -Filter "pgadmin_*.example.txt" -ErrorAction SilentlyContinue))
{
    $newName = $file.Name -replace "\.example", ""
    Copy-Item -Path $file.FullName -Destination "docker\secrets\$newName"
    Write-Host "Copied: $($file.FullName) -> docker\secrets\$newName"
}

# pgAdmin configs (.json)
foreach ($file in (Get-ChildItem -Path "examples" -Filter "pgadmin_*.example.json" -ErrorAction SilentlyContinue))
{
    $newName = $file.Name -replace "\.example", ""
    Copy-Item -Path $file.FullName -Destination "docker\configs\$newName"
    Write-Host "Copied: $($file.FullName) -> docker\configs\$newName"
}

# Keycloak secrets (.txt)
foreach ($file in (Get-ChildItem -Path "examples" -Filter "keycloak_*.example.txt" -ErrorAction SilentlyContinue))
{
    $newName = $file.Name -replace "\.example", ""
    Copy-Item -Path $file.FullName -Destination "docker\secrets\$newName"
    Write-Host "Copied: $($file.FullName) -> docker\secrets\$newName"
}

Write-Host "==> Setup complete!"
Write-Host "IMPORTANT:"
Write-Host " - Review all generated files and update credentials/configurations as needed."
Write-Host " - Remove insecure default values before running the system."
