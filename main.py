# Entry point file so no need to do anything special here
from .cores.apis import cosmic_auth_app


# `fastapi dev` / `fastapi run` look for `app` on the default entrypoint.
app = cosmic_auth_app
