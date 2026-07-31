from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import logger
from app.db.session import init_db
from app.services.cache_service import cache_service
from app.routers import auth, upload, jobs, stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await cache_service.connect()
    logger.info("app_started", name=settings.APP_NAME)
    yield
    await cache_service.disconnect()
    logger.info("app_stopped")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(jobs.router)
app.include_router(stream.router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/api/health", include_in_schema=False)
async def api_health():
    return {"status": "ok", "app": settings.APP_NAME}


STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
