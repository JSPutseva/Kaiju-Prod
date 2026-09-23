import os
from pathlib import Path

from dotenv import load_dotenv

# load Back/.env before any module below reads env vars at import time
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
# import every model so Base.metadata has all tables registered
from app.models import (  # noqa: F401
    quarter,
    quarter_connection,
    quarter_resource,
    reservation,
    resource_type,
    request,
    transfer,
    user,
    user_quarter,
)
from app.routers import quarters, transfers, users, requests, reservations, websocket

app = FastAPI(title="KAIJU Crisis Manager API")

# allowed frontend origins, from env
_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(quarters.router)
app.include_router(transfers.router)
app.include_router(users.router)
app.include_router(requests.router)
app.include_router(reservations.router)
app.include_router(websocket.router)


@app.get("/")
def root():
    return {
        "message": "KAIJU Crisis Manager API",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
