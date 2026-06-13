
from contextlib import asynccontextmanager
import time

import httpx
from fastapi import FastAPI

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.core.logging import logger

from app.core.redis.repository import RedisRepository
from app.core.redis.keys import RedisKeys

from app.modules.model_vault.model.repository import ModelRepository
from app.modules.model_vault.provider.repository import ProviderRepository


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("===================================")
    logger.info("Starting RouteLM")
    logger.info("===================================")

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )

    app.state.engine = engine

    try:

        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        logger.info("Database connected successfully.")

    except Exception:

        logger.exception("Database connection failed.")

        raise

    http_client = httpx.AsyncClient(
        timeout=settings.REQUEST_TIMEOUT,
        follow_redirects=True,
        http2=True,
    )

    app.state.http_client = http_client

    logger.info("HTTP Client initialized.")

    redis = RedisRepository()

    start = time.perf_counter()

    try:

        async with AsyncSession(engine) as session:

            provider_repo = ProviderRepository(session)
            model_repo = ModelRepository(session)

            providers = await provider_repo.get_all()

            for provider in providers:

                payload = {
                    "id": provider.id,
                    "name": provider.name,
                    "api_key": provider.api_key,
                    "base_url": provider.base_url,
                    "adapter": provider.adapter,
                    "enabled": provider.enabled,
                }

                await redis.set_json(
                    RedisKeys.provider(provider.id),
                    payload,
                )

                await redis.set_json(
                    RedisKeys.provider_by_name(provider.name),
                    payload,
                )

            models = await model_repo.get_all()

            for model in models:

                await redis.set_json(
                    RedisKeys.model(model.model_name),
                    {
                        "id": model.id,
                        "provider_id": model.provider_id,
                        "model_name": model.model_name,
                        "display_name": model.display_name,
                        "context_window": model.context_window,
                        "input_cost": model.input_cost,
                        "output_cost": model.output_cost,
                        "priority": model.priority,
                        "fallback_order": model.fallback_order,
                        "supports_stream": model.supports_stream,
                        "supports_tools": model.supports_tools,
                        "supports_vision": model.supports_vision,
                        "supports_reasoning": model.supports_reasoning,
                        "enabled": model.enabled,
                    },
                )

        elapsed = (time.perf_counter() - start) * 1000

        logger.info(
            "Loaded %d providers into Redis.",
            len(providers),
        )

        logger.info(
            "Loaded %d models into Redis.",
            len(models),
        )

        logger.info(
            "Redis cache warmed successfully in %.2f ms.",
            elapsed,
        )

    except Exception:

        logger.exception(
            "Failed to warm Redis cache."
        )

        raise

    logger.info("RouteLM Ready 🚀")

    yield

    logger.info("Shutting down RouteLM...")

    await http_client.aclose()

    await redis.close()

    await engine.dispose()

    logger.info("Shutdown complete.")
