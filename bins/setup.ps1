# Similar concept to the shebang defined in Bash script version
#Requires -Version 7.0

# Similar concept to the `set -e` flag in Bash script version
$ErrorActionPreference = "Stop"


# Navigate to project root (one level up from 'bins/')
$scriptRoot = $PSScriptRoot
$projectRoot = Split-Path -Parent $scriptRoot
Set-Location $projectRoot

# Similar concept to the positional <db-env-file> argument in the Bash version:
# the `.env` file the shared-database credentials are reconciled from.
param(
    [string] $DbEnvFile = "..\cosmic-db\cores\cosmic_cfg.env"
)

Write-Host "==> Creating required directories..."

New-Item -ItemType Directory -Force -Path "docker\secrets" | Out-Null
New-Item -ItemType Directory -Force -Path "cores" | Out-Null

Write-Host "==> Checking and preparing environment/configuration files..."

# Helper function to conditionally copy files safely
function Invoke-SafeCopy {
    param(
		$Source,
		$Destination
	)

    if (Test-Path $Destination) {
        Write-Host "Skipped: [$Destination] already exists (left untouched)."
    } else {
        Copy-Item -Path $Source -Destination $Destination
        Write-Host "Copied: [$Source] -> [$Destination]"
    }
}

# Shared database service (.env)
foreach ($file in (Get-ChildItem -Path "examples" -Filter "cosmic_cfg*.example.env" -ErrorAction SilentlyContinue))
{
    $newName = $file.Name -replace "\.example", ""
    Invoke-SafeCopy -Source $file.FullName -Destination "cores\$newName"
}

# Auth (.env) → cores/
foreach ($file in (Get-ChildItem -Path "examples" -Filter "cosmic_auth.example.env" -ErrorAction SilentlyContinue))
{
    $newName = $file.Name -replace "\.example", ""
    Invoke-SafeCopy -Source $file.FullName -Destination "cores\$newName"
}

# Keycloak secrets (.txt)
foreach ($file in (Get-ChildItem -Path "examples" -Filter "keycloak_*.example.txt" -ErrorAction SilentlyContinue))
{
    $newName = $file.Name -replace "\.example", ""
    Invoke-SafeCopy -Source $file.FullName -Destination "docker\secrets\$newName"
}

# Reconcile the shared-database credentials in `cores/cosmic_cfg.env` with the
# values declared in another `.env` file (by default the database owner,
# `cosmic-db`). This way, the Auth micro-service can never drift from the
# database it talks to. Point it elsewhere with the `-DbEnvFile` parameter.
$dbConfigPath = "cores\cosmic_cfg.env"
$dbEnvKeys = @(
	"DB_USER",
	"DB_PASSWORD",
	"DB_NAME"
)

$dbEnvValues = @{}
$missingKeys = @()

if (-not (Test-Path -LiteralPath $DbEnvFile)) {
    Write-Host "==> Skipped: shared-database credentials not reconciled ([$DbEnvFile] not found)."
}
elseif (-not (Test-Path -LiteralPath $dbConfigPath)) {
    Write-Host "==> Skipped: shared-database credentials not reconciled ([$dbConfigPath] not found)."
}
else {
    $sourceEnv = @{}
    foreach ($line in (Get-Content -Path $DbEnvFile)) {
        if ($line -match "^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$") {
            $sourceEnv[$Matches[1]] = $Matches[2].Trim().Trim('"').Trim("'")
        }
    }

    foreach ($key in $dbEnvKeys) {
        if ($sourceEnv.ContainsKey($key) -and $sourceEnv[$key]) {
            $dbEnvValues[$key] = $sourceEnv[$key]
        } else {
            $missingKeys += $key
        }
    }

    if ($missingKeys.Count -gt 0) {
        Write-Host "==> Skipped: shared-database credentials not reconciled (missing in [$DbEnvFile]: $($missingKeys -join ', '))."
    }
    else {
        $reconciled = foreach ($line in (Get-Content -Path $dbConfigPath)) {
            if     ($line -like "DB_USER=*")     { "DB_USER=$($dbEnvValues['DB_USER'])" }
            elseif ($line -like "DB_PASSWORD=*") { "DB_PASSWORD=$($dbEnvValues['DB_PASSWORD'])" }
            elseif ($line -like "DB_NAME=*")     { "DB_NAME=$($dbEnvValues['DB_NAME'])" }
            else                                 { $line }
        }

        Set-Content -Path $dbConfigPath -Value $reconciled
        Write-Host "==> Reconciled [DB_USER], [DB_PASSWORD] and [DB_NAME] in [$dbConfigPath] with [$DbEnvFile]."
    }
}

# Generates the RS256 key-pair used to sign the CoSMIC session cookie
$secretsDir = Join-Path $projectRoot "docker\secrets"
$privateKey = Join-Path $secretsDir "cosmic_private_session.pem"
$publicKey = Join-Path $secretsDir "cosmic_public_session.pem"

if ((Test-Path $privateKey) -and (Test-Path $publicKey))
{
    Write-Host "==> Skipped: session key-pair already exists at [$secretsDir] (left untouched)."
}
else
{
    Write-Host "==> Generating RSA-2048 session keypair..."
    $rsa = [System.Security.Cryptography.RSA]::Create(2048)
    try
    {
        [System.IO.File]::WriteAllText($privateKey, $rsa.ExportPkcs8PrivateKeyPem())
        [System.IO.File]::WriteAllText($publicKey, $rsa.ExportSubjectPublicKeyInfoPem())
    }
    finally
    {
        $rsa.Dispose()
    }

    Write-Host "Generated:"
    Write-Host " 1. [$privateKey]"
    Write-Host " 2. [$publicKey]"
    Write-Host "NOTE: Never commit these files. Rotating the keypair invalidates all active sessions."
}

Write-Host "==> Setup complete!"
Write-Host "IMPORTANT:"
Write-Host " 1. Review all generated files and update credentials/configurations as needed."
Write-Host " 2. Remove insecure default values before running the system."
