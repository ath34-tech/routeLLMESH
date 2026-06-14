import time
from fastapi import HTTPException
from app.core.redis.keys import RedisKeys
from app.core.redis.repository import RedisRepository
from app.modules.chat.schemas import ChatRequest
from app.modules.model_vault.model.repository import ModelRepository
from app.modules.model_vault.provider.repository import ProviderRepository
from app.modules.chat.provider_factory import ProviderFactory
from app.modules.chat.normalizer import ResponseNormalizer
from app.modules.chat.routing import RoutingEngine, RoutingOutcome
import logging
from app.core.circuit_breaker.repository import CircuitBreakerRepository
from app.core.circuit_breaker.service import CircuitBreakerService

logger = logging.getLogger(__name__)
class ChatService:

    def __init__(
        self,
        model_repository: ModelRepository,
        provider_repository: ProviderRepository,
    ):
        self.model_repository = model_repository
        self.provider_repository = provider_repository
        self.redis = RedisRepository()
        self.circuit_breaker=CircuitBreakerService(CircuitBreakerRepository())
    async def chat(self, request: ChatRequest):
        
        start_time = time.time()
        
        # ============================================
        # ROUTING: Get optimal model
        # ============================================
        
        # ============================================
        # ROUTING
        # ============================================

        routing_result = await RoutingEngine.route(request)

        last_exception = None
        for candidate in routing_result.candidate_models:
            if not await self.circuit_breaker.allow_request(candidate.model_name):
                logger.info("Circuit OPEN for %s. Skipping.",candidate.model_name)
                continue

            request.model = candidate.model_name

            try:

                # ============================================
                # Model
                # ============================================

                model = await self.redis.get_json(
                    RedisKeys.model(candidate.model_name)
                )

                if model is None:

                    db_model = (
                        await self.model_repository.get_enabled_by_name(
                            candidate.model_name
                        )
                    )

                    if db_model is None:
                        continue

                    model = {
                        "id": db_model.id,
                        "provider_id": db_model.provider_id,
                        "model_name": db_model.model_name,
                        "display_name": db_model.display_name,
                        "context_window": db_model.context_window,
                        "input_cost": db_model.input_cost,
                        "output_cost": db_model.output_cost,
                        "priority": db_model.priority,
                        "fallback_order": db_model.fallback_order,
                        "supports_stream": db_model.supports_stream,
                        "supports_tools": db_model.supports_tools,
                        "supports_vision": db_model.supports_vision,
                        "supports_reasoning": db_model.supports_reasoning,
                        "enabled": db_model.enabled,
                    }

                    await self.redis.set_json(
                        RedisKeys.model(candidate.model_name),
                        model,
                    )

                # ============================================
                # Provider
                # ============================================

                provider = await self.redis.get_json(
                    RedisKeys.provider(model["provider_id"])
                )

                if provider is None:

                    db_provider = (
                        await self.provider_repository.get_by_id(
                            model["provider_id"]
                        )
                    )

                    if db_provider is None:
                        continue

                    provider = {
                        "id": db_provider.id,
                        "name": db_provider.name,
                        "api_key": db_provider.api_key,
                        "base_url": db_provider.base_url,
                        "adapter": db_provider.adapter,
                        "enabled": db_provider.enabled,
                    }

                    await self.redis.set_json(
                        RedisKeys.provider(db_provider.id),
                        provider,
                    )

                # ============================================
                # Adapter
                # ============================================

                adapter = ProviderFactory.get_adapter(
                    provider["adapter"]
                )

                logger.info(
                    "Trying model=%s score=%.2f",
                    candidate.model_name,
                    candidate.score,
                )

                # ============================================
                # Streaming
                # ============================================

                if request.stream:
                    await self.circuit_breaker.record_success(candidate.model_name)
                    return adapter.stream_chat(
                        provider=provider,
                        model=model,
                        request=request,
                    )

                # ============================================
                # Execute
                # ============================================

                response = await adapter.chat(
                    provider=provider,
                    model=model,
                    request=request,
                )

                normalized = ResponseNormalizer.normalize(
                    response
                )

                logger.info(
                    "Model %s succeeded",
                    candidate.model_name,
                )


                await self.circuit_breaker.record_success(candidate.model_name)
                return normalized

            except Exception as exc:

                logger.warning(
                    "Model %s failed. Trying next candidate.",
                    candidate.model_name,
                )
                await self.circuit_breaker.record_failure(candidate.model_name)
                last_exception = exc

                # Future:
                #
                # await health_manager.mark_unhealthy(
                #     candidate.model_name,
                #     ttl=300,
                # )

                continue

        # ============================================
        # All candidates exhausted
        # ============================================

        raise HTTPException(
            status_code=503,
            detail="No available model could satisfy the request.",
        ) from last_exception

    @staticmethod
    def _estimate_output_tokens(response: dict) -> int:
        """Estimate output tokens from response."""
        try:
            # If response has usage info
            if "usage" in response:
                return response["usage"].get("completion_tokens", 500)
            
            # Fallback: estimate from content length
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return max(100, len(content) // 4)
        except:
            return 500