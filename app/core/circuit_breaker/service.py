
from datetime import datetime, timedelta

from app.core.circuit_breaker.enums import CircuitState
from app.core.circuit_breaker.constants import (
    FAILURE_THRESHOLD,
    OPEN_TIMEOUT_SECONDS,
)
from app.core.circuit_breaker.repository import (
    CircuitBreakerRepository,
)


class CircuitBreakerService:
    """
    Production-grade Circuit Breaker.

    CLOSED
        ↓ failures
    OPEN
        ↓ timeout
    HALF_OPEN
        ↓ success/failure
    CLOSED / OPEN
    """

    def __init__(
        self,
        repository: CircuitBreakerRepository,
    ):
        self.repository = repository

    async def allow_request(
        self,
        model_name: str,
    ) -> bool:

        state = await self.repository.get(model_name)

        # First request ever
        if state is None:
            return True

        # CLOSED
        if state.state == CircuitState.CLOSED:
            return True

        # OPEN

        if state.state == CircuitState.OPEN:

            if state.opened_at is None:
                return False

            recover_at = (
                state.opened_at
                + timedelta(
                    seconds=OPEN_TIMEOUT_SECONDS
                )
            )

            if datetime.utcnow() >= recover_at:

                state.state = CircuitState.HALF_OPEN

                await self.repository.save(
                    model_name,
                    state,
                )

                return True

            return False

        # HALF_OPEN

        if state.state == CircuitState.HALF_OPEN:

            return True

        return True

    async def record_success(
        self,
        model_name: str,
    ) -> None:

        state = await self.repository.get(
            model_name
        )

        if state is None:
            return

        state.state = CircuitState.CLOSED

        state.failure_count = 0

        state.opened_at = None

        await self.repository.save(
            model_name,
            state,
        )

    async def record_failure(
        self,
        model_name: str,
    ) -> None:

        state = await self.repository.get(
            model_name
        )

        if state is None:

            state = self.repository.new_state()

        state.failure_count += 1

        if (
            state.failure_count
            >= FAILURE_THRESHOLD
        ):

            state.state = CircuitState.OPEN

            state.opened_at = datetime.utcnow()

        await self.repository.save(
            model_name,
            state,
        )

    async def get_state(
        self,
        model_name: str,
    ):

        return await self.repository.get(
            model_name
        )

    async def reset(
        self,
        model_name: str,
    ) -> None:

        await self.repository.delete(
            model_name
        )
