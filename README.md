<h1 align="center">Directory Hierarchy</h1>

```md
cosmic-auth/
├── cores/                  # Application core
│   ├── apis.py             # FastAPI application factory (CORS, session middleware, routers)
│   ├── configs.py          # Loads `cores/cosmic_cfg.env` and `cores/cosmic_auth.env`
│   ├── db.py               # Shared PostgreSQL engine and session dependency
│   └── tags.py             # OpenAPI tag used by the auth endpoints
├── models/                 # Multiple Model patterns trimmed to the auth footprint.
│   ├── bases/              # SQLModel Base Models (inherited by other models)
│   ├── datas/              # SQLModel Data Models (in charge of endpoint validations thanks to Pydantic)
│   ├── tables/             # SQLModel Table Models (define db schemas for Auth BFF to talk natively with CoSMIC actual schemas)
│   ├── responses/          # SQLModel Response Models (define the custom response messages for each endpoint)
│   └── filters/            # SQL Filter Models (define query filters for some special endpoints)
├── interfaces/             # IAM and IdP seams
│   ├── abstracts/iam.py    # IAM provider contract the Auth micro-service depends on
│   ├── abstracts/idp.py    # IdP contract for a single IdP
│   ├── iams/keycloak.py    # Keycloak adapter (backed by Authlib) supplied through FastAPI DI
│   ├── iams/authentik.py   # Authentik adapter (backed by Authlib) supplied through FastAPI DI
│   └── idps/               # IdP implementations (brokered within Keycloak except certain circumstances)
├── routers/                # HTTP surface
│   ├── apis/auth.py        # Auth endpoints (`/api/v1/auth/*`)
│   ├── apis/users.py       # IAM user API (`/api/v1/users/*`)
│   ├── apis/roles.py       # IAM role API (`/api/v1/roles/*`)
│   └── regulars/           # Regular endpoints (`/health`, `/jwks.json`)
├── utils/                  # Helper functions and shared utility scripts
├── bins/                   # Helper scripts, 3rd vendor binaries, etc
├── docker/                 # Containerization resources and orchestration files
│   ├── dockerfiles/        # Dockerfile for each services defined in Docker Compose file
│   ├── keycloak/           # Keycloak realm export (baked into the Keycloak image, imported on first start)
│   └── secrets/            # Secure storage for the Keycloak credentials + the RS256 session key-pair
├── examples/               # Template files and default values for rapid environment setup
├── .dockerignore           # Files excluded from Docker builds
├── .gitattributes          # Git configuration for path attributes
├── .gitignore              # Files excluded from version control
├── .python-version         # Pinned Python version for the project (beneficial to `uv` only)
├── CONTRIBUTING            # Guidelines for project contributors
├── LICENSE                 # Project licensing information (MIT)
├── README.md               # This's what you're seeing right now
├── __init__.py             # Package initialisation (mainly for relative import usages)
├── compose.yaml            # Docker Compose specification for the Auth + Keycloak services
├── main.py                 # Primary entry point re-exporting the Auth BFF application
├── pyproject.toml          # Project metadata and dependency definitions
└── uv.lock                 # Pinned dependency lockfile via `uv`
```

---
# `cosmic-db` relationship

> [!IMPORTANT]
> This repository runs with **no** PostgreSQL of its own. `bins/setup.ps1` (Windows) or
> `bins/setup.sh` (Linux/MacOS) reconciles `DB_USER`, `DB_PASSWORD` and `DB_NAME`
> in `cores/cosmic_cfg.env` directly from a `.env` file it is told to read -
> `../cosmic-db/cores/cosmic_cfg.env` by default (the database owner), or the path
> you pass in (`.\bins\setup.ps1 -DbEnvFile <path>` / `./bins/setup.sh <path>`).
> Keep it identical to the one `cosmic-db` runs; if they differ, logins fail with
> `FATAL: password authentication failed for user ...`.

This repository is **not** the owner of the CoSMIC PostgreSQL schema *(it should be, but not at the time this README get written)*. It connects to the same database under `cosmic-db` repo and carries a copy of the three tables the **Auth BFF** reads/writes (`users`, `roles`, `user_identities`). This way, it can be deployed and reasoned about on its own:

1. Both repositories attach to the same `cosmic_net` Docker network. Therefore, we must start `cosmic-db` Docker containers (`docker compose up -d database`) first before starting this one.

2. This micro-service listens on port `8081` and publishes the JWKS info at `http://localhost:8081/jwks.json` for other micro-services to discover. It also answers a liveness probe at `http://localhost:8081/health`.

---
# IAM management API

`cosmic-db` keeps the public `PATCH /api/v1/users/{id}`, `DELETE /api/v1/users/{id}`
and the Roles API, but the IAM is always updated first. The database calls these
endpoints before writing its fallback row:

| Method   | Endpoint                          | Purpose                           |
| -------- | --------------------------------- | --------------------------------- |
| `PATCH`  | `/api/v1/users/{user_id}`         | Update email/name/role in the IAM |
| `DELETE` | `/api/v1/users/{user_id}`         | Delete the IAM-backed user        |
| `POST`   | `/api/v1/roles`                   | Create/ensure an IAM role         |
| `PATCH`  | `/api/v1/roles/{role_name}`       | Rename/update an IAM role         |
| `DELETE` | `/api/v1/roles/{role_name}`       | Delete an IAM role                |

> [!NOTE]
> These endpoints are currently unauthenticated so they can be exercised from the
> FastAPI docs page during development. AuthN/AuthZ will be added in a dedicated
> ticket; until then the shared Docker network is the only boundary.

## Keycloak service account

The Admin REST calls do **not** use the Keycloak master admin account. A dedicated
confidential client, `cosmic-auth-service`, is defined in
`docker/keycloak/cosmic-realm.json` with a service account carrying the
`realm-management` roles `manage-users`, `view-users`, `query-users`,
`manage-realm` and `view-realm`.

- Client id: `KEYCLOAK_SERVICE_ACCOUNT_CLIENT_ID` (default `cosmic-auth-service`)
- Client secret: `KEYCLOAK_SERVICE_ACCOUNT_CLIENT_SECRET`, or the baked file
  `docker/secrets/keycloak_service_account_client_secret.txt`

> [!IMPORTANT]
> The realm export only runs when the `cosmic` realm is first imported. On an
> existing Keycloak volume, remove the `cosmic-keycloak-data` volume (or add the
> client/roles manually in the admin console) so the new service account is
> created. Losing the volume also removes the existing Keycloak users, so take a
> backup first if they matter.

A custom DB role is pushed into Keycloak before it is stored locally. Assigning a
custom role to a user also ensures the realm role exists, so the IAM stays the
source of truth for every role the platform exposes.

---
# Quick Start

Before setting up, decide which one is the correct purpose when you get to this modular repository:

> [!NOTE]
> The rest of this guide covers **Purpose 1**. For **Purpose 2**, refer to the
> setup instructions in [cosmic-docker repository](https://github.com/TheOpenSI/cosmic-docker)

1. **Module-only**: you are working on this part of the project in isolation (e.g., only Auth + Keycloak).
2. **Full-stack**: you need an end-to-end test run across all services (**Front-end** &rarr; **Back-end** &rarr; **Auth** &rarr; **CoSMIC**).

Next, ensure you have the appropriate tools installed depending on your chosen execution method. This guide supports:

- **Native setup** (running **CoSMIC Auth** directly on your machine)
- **Docker setup** (running **CoSMIC Auth** in isolated containers)


| **Tool** | **Docker Setup**                       | **Native Setup**                               |
| -------- | -------------------------------------- | ---------------------------------------------- |
| Docker   | $\textcolor{green}{\text{Mandatory}}$  | $\textcolor{red}{\text{Not required}}$         |
| Python   | $\textcolor{red}{\text{Not required}}$ | $\textcolor{green}{\text{Mandatory (v3.14+)}}$ |
| uv       | $\textcolor{red}{\text{Not required}}$ | $\textcolor{green}{\text{Mandatory (latest)}}$ |


Then, start by cloning the repository using your preferred method:

```bash
# Linux/MacOS
git clone https://github.com/TheOpenSI/cosmic-auth.git    # Using HTTPS (recommended for most users)
git clone git@github.com:TheOpenSI/cosmic-auth.git        # Using SSH (recommended if you've SSH keys configured)
```
```ps1
# Windows
git clone https://github.com/TheOpenSI/cosmic-auth.git    # Using HTTPS (recommended for most users)
git clone git@github.com:TheOpenSI/cosmic-auth.git        # Using SSH (recommended if you've SSH keys configured)
```

Once cloned, navigate to the project root directory:

```bash
# Linux/MacOS
cd cosmic-auth/
```
```ps1
# Windows
Set-Location cosmic-auth\
```

---
# Understanding Configuration Setup

The Auth micro-service expects configuration files to be organised in specific locations depending on your chosen setup method. Understanding this structure will help you prepare the environment correctly.

> [!TIP]
> You can follow the instructions below to understand what these 2 scripts will
> do, or simply run it to automatically configure your environment for running
> the Auth micro-service as a Docker container.

```bash
# Linux/MacOS
./bins/setup.sh
```
```ps1
# Windows
.\bins\setup.ps1
```

## Docker Configuration

Create the necessary directories first:

```bash
# Linux/MacOS
mkdir -p docker/{secrets}
```
```ps1
# Windows
New-Item -Type Directory -Name secrets -Path .\docker\
```

Then, copy the following files from the `examples/` directory to the following location:

> [!IMPORTANT]
> Remove `.example` suffix from each filename.

1. **Shared database service**:
- `examples/cosmic_cfg.example.env` &rarr; `cores/cosmic_cfg.env` (PostgreSQL connection settings. This must point at the `cosmic-db` repo database - `DB_USER`/`DB_PASSWORD`/`DB_NAME` are then reconciled from its `.env` by `bins/setup.*`).

2. **Auth service**:
- `examples/cosmic_auth.example.env` &rarr; `cores/cosmic_auth.env` (contains Keycloak, Authlib session, RS256 session-key settings and the `IAM_PROVIDER` selection. See [Configure Authentication Credentials](#configure-authentication-credentials) for more details).
- Generate the RS256 session keypair used to sign the CoSMIC session cookie using either `.\bins\setup.ps1` (Windows) or `./bins/setup.sh` (Linux/macOS).

3. **Keycloak service**:
- `examples/keycloak_*.example.txt` &rarr; `docker/secrets/keycloak_*.txt` (contains Keycloak admin credentials, the confidential client secret, the service-account client secret, the seeded test user, and the Google/Microsoft client credentials brokered by Keycloak).

> [!TIP]
> Before finalising these files, review and adjust default values (Keep default setting if you're unsure about whether or not to modify it):
> - Password
> - Username
> - Port
> - Etc

## Native Configuration

> [!TIP]
> The `.env` file approach is recommended as it keeps your configuration
> organised and prevents accidentally committing secrets to version control.
> Make sure to add `.env` to your `.gitignore` file.

Copy the example environment files to their runtime locations:

```bash
# Linux/MacOS
cp ./examples/cosmic_cfg.example.env ./cores/cosmic_cfg.env
cp ./examples/cosmic_auth.example.env ./cores/cosmic_auth.env
```
```ps1
# Windows
Copy-Item -Path .\examples\cosmic_cfg.example.env -Destination .\cores\cosmic_cfg.env
Copy-Item -Path .\examples\cosmic_auth.example.env -Destination .\cores\cosmic_auth.env
```

Then, edit the `cores/cosmic_cfg.env` file to point at your local PostgreSQL instance (the `## Native setup` block in that file lists the usual values) and generate the RS256 session key-pair with `bins/setup.ps1` (Windows) or `bins/setup.sh` (Linux/MacOS).

---
# Setup & Execution

> [!TIP]
> Docker provides an isolated environment where all services run in containers.
> This approach is recommended if you want to avoid installing PostgreSQL and
> other dependencies directly on your machine.

## Docker Setup

> [!NOTE]
> It's possible to run Docker in rootless mode on Linux. However, the way to set
> it up is different on each Linux distros. Please refer to [this](https://docs.docker.com/engine/install) and [this](https://docs.docker.com/engine/security/rootless/)
> (all sourced from Docker documentation) to choose the one that fits for your
> current Linux distro.

Before you begin, ensure you have **Docker** & **Docker Compose** installed on your system. These are required to run the platform:

1. [**Docker**](https://docs.docker.com/get-docker/)
2. [**Docker Compose**](https://docs.docker.com/compose/install/)

### **1. Starting the shared database**

This repository attaches to the `cosmic_net` network owned by `cosmic-db`. Start its database at least once so the network and the shared schema exist:

```bash
# Linux/MacOS
cd ../cosmic-db && docker compose up -d database
```
```ps1
# Windows
Set-Location ..\cosmic-db; docker compose up -d database
```

### **2. Starting Docker Services**

From the project root directory, ensure you've completed the steps in the [Docker Configuration](#docker-configuration) section above (including [Configuring Authentication Credentials](#configure-authentication-credentials)). Set the Keycloak client secret, the Google/Microsoft broker credentials, and session values **before** the first `docker compose up` so Keycloak imports a matching client secret. Then start all the service using the Docker Compose file:

```bash
# Linux/MacOS
docker compose up --build -d # Refer to NOTE if running on rootless mode
```
```ps1
# Windows
docker compose up --build -d # Docker run through lightweight Linux VM on Windows so it's rootless by default
```

### **3. Verifying Docker Services**

Once the containers are running, you can verify that all services are working correctly by these way:

1. **Auth (FastAPI)**: [localhost:8081/docs](http://localhost:8081/docs)
2. **Keycloak**: [localhost:8080](http://localhost:8080) **(use credentials from `docker/secrets/keycloak_admin_*.txt`)**
3. **Shared PostgreSQL**:
- We disabled direct access by default as this's totally viewable from **pgAdmin** in `cosmic-db`. However, you can still do it by typing this in your terminal:

```bash
# Linux/MacOS
docker exec cosmic-postgres psql -U <DB_USER> # Refer to NOTE if running on rootless mode
```
```ps1
# Windows
docker exec cosmic-postgres psql -U <DB_USER> # Docker run through lightweight Linux VM on Windows so it's rootless by default
```

or go to **Docker Desktop**, search for `cosmic-postgres` service under `opensi-cosmic` top-level service, click on it then click on **Terminal** icon on the near top right corner.

## Native Setup

> [!IMPORTANT]
> The service is imported as the `app` package (`app.cores.apis:app`), which is how the container resolves it: the repository is mounted at `/app` and `PYTHONPATH` points at `/`. To run natively, expose the checkout under a package named `app` and start the server from inside it:

```bash
# Linux/MacOS (run from the directory CONTAINING this repository)
ln -s cosmic-auth app
cd app
uv run fastapi dev
```
```ps1
# Windows (run from the directory CONTAINING this repository)
New-Item -ItemType Junction -Path .\app -Target .\cosmic-auth
Set-Location app
uv run fastapi dev
```

> [!NOTE]
> Only the package name has to be `app`; the checkout directory itself can be called anything.

### **1. Installing Dependencies**

Our service uses **Python (v3.14+)** with the `uv` package manager for dependency management. Once the configuration files are in place and you're in the project root directory (`cosmic-auth/`), install the project's dependencies:

```bash
# Linux/MacOS
uv sync --frozen --no-cache
```
```ps1
# Windows
uv sync --frozen --no-cache
```

### **2. Starting Auth Server**

After dependencies are installed, ensure you've completed the steps from the [Native Configuration](#native-configuration) section above. Then, start the FastAPI development server as shown in the note above.

### **3. Verifying Native Setup**

You can now verify that the auth service is running correctly by these way:

1. **Auth (FastAPI)**: [localhost:8081/docs](http://localhost:8081/docs)
2. **Keycloak**: [localhost:8080](http://localhost:8080) (it still has to run somewhere reachable by the browser *and* by this service - see `KEYCLOAK_PUBLIC_URL` & `KEYCLOAK_INTERNAL_URL` in `cores/cosmic_auth.env`)

# **Configure Authentication Credentials**

> [!CAUTION]
> DO **NOT** COMMIT REAL CREDENTIALS.

After running `.\bins\setup.ps1` (Windows) or `./bins/setup.sh` (Linux/MacOS), the setup script copies example files into:

- `cores/cosmic_auth.env` (Keycloak, Authlib session, RS256 session-key settings and the `IAM_PROVIDER` selection used by the auth service)
- `cores/cosmic_cfg.env` (connection settings for the shared PostgreSQL database — `DB_USER`/`DB_PASSWORD`/`DB_NAME` are reconciled from the database owner's `.env` on every run)
- `docker/secrets/keycloak_*.txt` (Keycloak admin credentials, the confidential client secret, the service-account client secret, the seeded test user and the Google/Microsoft broker credentials)
- `docker/secrets/cosmic_private_session.pem` & `docker/secrets/cosmic_public_session.pem` (the RS256 key-pair that signs the CoSMIC session cookie)

Open `cores/cosmic_auth.env` and replace the defaults below:

> [!IMPORTANT]
> `KEYCLOAK_CLIENT_SECRET` environment variable value **must be identical** to
> `docker/secrets/keycloak_client_secret.txt` value. If they differ, Keycloak
> login will fail because the auth service and Keycloak will not share the same
> client secret.

## **Google & Microsoft (brokered by Keycloak)**

> [!TIP]
> `docker/dockerfiles/keycloak.Dockerfile` bakes the realm export and the secrets
> its `${...}` placeholders resolve to into the Keycloak image, and the realm is
> imported on first boot. Set them **before** the first `docker compose up`; to
> change them later, rebuild the image (`docker compose build keycloak`) and
> recreate the container, update the IdPs in the Keycloak admin console, or
> remove the `cosmic-keycloak-data` volume and start again so the realm is
> re-imported.

The platform itself only talks to Keycloak as Google & Microsoft are configured as its **identity providers (IdPs)**. Because of that, Keycloak login page shows a very clean typical username/password form + Google & Microsoft login icons by default.

Register each provider in its own console and use **Keycloak's broker callback** as the redirect URI (not the CoSMIC BFF Framework):


| Provider  | Redirect URI                                                      |
| --------- | ----------------------------------------------------------------- |
| Google    | `http://localhost:8080/realms/cosmic/broker/google/endpoint`      |
| Microsoft | `http://localhost:8080/realms/cosmic/broker/microsoft/endpoint`   |


1. **Google**: [Google Cloud Console](https://console.developers.google.com/) &rarr; **APIs & Services** &rarr; **Credentials** &rarr; **Create credentials** &rarr; **OAuth client ID** (type **Web application**). Add the Google redirect URI above, then put the client ID/secret in `docker/secrets/keycloak_google_client_id.txt` & `docker/secrets/keycloak_google_client_secret.txt` respectively.

2. **Microsoft**: [Azure Portal](https://portal.azure.com/) &rarr; **App registrations** &rarr; **New registration**. Add the Microsoft redirect URI above, then put the application (client) ID/secret in `docker/secrets/keycloak_microsoft_client_id.txt` & `docker/secrets/keycloak_microsoft_client_secret.txt` respectively, and the directory (tenant) ID (or `common` for multi-tenant) in `docker/secrets/keycloak_microsoft_tenant_id.txt`.

## **Keycloak client secret**

> [!TIP]
> Set this **before** the first Keycloak start. The Keycloak image bakes
> `docker/keycloak/cosmic-realm.json` and substitutes `${KEYCLOAK_CLIENT_SECRET}`
> from `docker/secrets/keycloak_client_secret.txt` on first boot; rebuild it
> (`docker compose build keycloak`) after changing a secret. If you change the
> secret after the realm exists, also update the client secret in the Keycloak
> admin console (**Clients** &rarr; `cosmic-keycloak-fastapi` &rarr; **Credentials**),
> or remove the Keycloak volume and start again so the realm is re-imported.

The default `KEYCLOAK_CLIENT_SECRET` is only a local example. You may keep it for a first run, but we recommend replacing it with a unique value.

Generate a unique secret:

```bash
# Linux/MacOS
uuidgen
```
```ps1
# Windows
[guid]::NewGuid().ToString()
```

Put **the same value** in both places:

1. `cores/cosmic_auth.env`:

```txt
KEYCLOAK_CLIENT_SECRET=<your-unique-secret>
```

2. `docker/secrets/keycloak_client_secret.txt`:

```txt
<your-unique-secret>
```

You can leave `KEYCLOAK_CLIENT_ID=cosmic-keycloak-fastapi` and the Keycloak URLs/realm defaults unless you have changed those in the realm export.

## **Session keys (RS256) and `SESSION_SECRET`**

> [!CAUTION]
> Rotating the RS256 key-pair invalidates every active session (users must log in
> again) and invalidates cached JWKS in the other services. Rotating
> `SESSION_SECRET` only interrupts logins that are in flight.

The CoSMIC session cookie is a JWT signed with **RS256** encryption algorithm using a static RSA key-pair. This way, other micro-services can verify it with the public key only.

- Generate the key-pair with `.\bins\setup.ps1` (Windows) or `./bins/setup.sh` (Linux/MacOS). It writes `docker/secrets/cosmic_private_session.pem` & `docker/secrets/cosmic_public_session.pem`, both of which are gitignored.
- The public half is published at `http://localhost:8081/jwks.json` for the other services to discover.
- `cosmic_session` is the **only** application cookie. Because of that, Keycloak refresh token travels inside it as a claim, so `/refresh` & `/logout` endpoints need no separate token cookie.
- `SESSION_SECRET` is now only used to sign the temporary Authlib OAuth state/nonce cookie for [Starlette SessionMiddleWare](https://starlette.dev/middleware/#sessionmiddleware), separate from the RS256 key-pair.

```txt
SESSION_SECRET=<your-unique-session-secret>
SESSION_COOKIE_NAME=cosmic_session
SESSION_MAX_AGE=900
SESSION_REFRESH_TOKEN_MAX_AGE=86400
SESSION_OAUTH_COOKIE=cosmic_oauth_session
```

## **Keycloak service account**

```txt
KEYCLOAK_SERVICE_ACCOUNT_CLIENT_ID=cosmic-auth-service
KEYCLOAK_SERVICE_ACCOUNT_CLIENT_SECRET=<optional; defaults to the baked secret file>
```

The matching database value lives in `cosmic-db/cores/cosmic_cfg.env`:

```txt
COSMIC_AUTH_URL=http://cosmic-keycloak-fastapi:8081
```
