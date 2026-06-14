from fastapi import FastAPI
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.logging import setup_logger



# Initialize logger before app startup
setup_logger(settings.LOG_LEVEL)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# Register all API routes
app.include_router(api_router)


@app.get("/", tags=["System"])
async def root():

    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["System"],
)
async def health():

    try:

        async with app.state.engine.begin() as conn:

            await conn.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
            "provider_cache_size": len(app.state.provider_cache),
            "model_cache_size": len(app.state.model_cache),
        }

    except Exception as e:

        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }


@app.get(
    "/db-test",
    tags=["Debug"],
    include_in_schema=False,
)
async def db_test():

    async with app.state.engine.begin() as conn:

        result = await conn.execute(
            text("SELECT current_database()")
        )

        return {
            "database": result.scalar()
        }