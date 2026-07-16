from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.routes import auth_router
from auth import config

app = FastAPI(title="CoSMIC Auth API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}