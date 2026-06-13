from fastapi import FastAPI

from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.logging import setup_logger


setup_logger(settings.LOG_LEVEL)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


@app.get("/", tags=["System"])
async def root():

    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
    }


from sqlalchemy import text


@app.get("/db-test")
async def db_test():

    async with app.state.engine.begin() as conn:

        result = await conn.execute(text("SELECT current_database()"))

        return {
            "database": result.scalar()
        }

@app.get("/health", tags=["System"])
async def health():

    return {
        "status": "healthy",
        "provider_cache_size": len(app.state.provider_cache),
        "model_cache_size": len(app.state.model_cache),
    }