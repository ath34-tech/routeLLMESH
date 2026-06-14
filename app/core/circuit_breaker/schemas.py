from datetime import datetime

from pydantic import BaseModel

from app.core.circuit_breaker.enums import CircuitState


class CircuitBreakerState(BaseModel):

    state: CircuitState

    failure_count: int = 0

    opened_at: datetime | None = None