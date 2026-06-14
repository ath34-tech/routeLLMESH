
from app.core.redis.repository import RedisRepository
from app.core.circuit_breaker.schemas import CircuitBreakerState
from app.core.circuit_breaker.enums import CircuitState


class CircuitBreakerRepository:
    """
    Redis persistence layer for Circuit Breaker.
    """

    def __init__(self):
        self.redis = RedisRepository()

    def _key(self, model_name: str) -> str:
        return f"circuit_breaker:{model_name}"

    async def get(
        self,
        model_name: str,
    ) -> CircuitBreakerState | None:

        data = await self.redis.get_json(
            self._key(model_name)
        )

        if data is None:
            return None

        return CircuitBreakerState.model_validate(data)

    async def save(
        self,
        model_name: str,
        state: CircuitBreakerState,
    ) -> None:

        await self.redis.set_json(
            self._key(model_name),
            state.model_dump(mode="json"),
        )

    async def delete(
        self,
        model_name: str,
    ) -> None:

        await self.redis.delete(
            self._key(model_name)
        )

    def new_state(
        self,
    ) -> CircuitBreakerState:

        return CircuitBreakerState(
            state=CircuitState.CLOSED,
            failure_count=0,
            opened_at=None,
        )
