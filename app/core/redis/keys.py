class RedisKeys:
    """
    Centralized Redis key builder.

    All Redis keys in RouteLM should be generated from this class
    to maintain consistency and avoid hardcoded strings.
    """

    # ------------------------
    # Model Vault
    # ------------------------

    @staticmethod
    def provider(provider_id: int) -> str:
        return f"provider:{provider_id}"

    @staticmethod
    def provider_by_name(name: str) -> str:
        return f"provider:name:{name.lower()}"

    @staticmethod
    def model(model_name: str) -> str:
        return f"model:{model_name}"

    # ------------------------
    # Rate Limiter (Future)
    # ------------------------

    @staticmethod
    def user_rate_limit(api_key: str) -> str:
        return f"ratelimit:user:{api_key}"

    @staticmethod
    def provider_rate_limit(provider: str) -> str:
        return f"ratelimit:provider:{provider}"

    @staticmethod
    def model_rate_limit(model: str) -> str:
        return f"ratelimit:model:{model}"

    # ------------------------
    # Circuit Breaker (Future)
    # ------------------------

    @staticmethod
    def circuit_breaker(provider: str) -> str:
        return f"circuit:{provider}"

    # ------------------------
    # Provider Health (Future)
    # ------------------------

    @staticmethod
    def provider_health(provider: str) -> str:
        return f"health:{provider}"

    # ------------------------
    # Semantic Cache (Future)
    # ------------------------

    @staticmethod
    def semantic_cache(prompt_hash: str) -> str:
        return f"semantic:{prompt_hash}"

    # ------------------------
    # Metrics (Future)
    # ------------------------

    @staticmethod
    def provider_metrics(provider: str) -> str:
        return f"metrics:provider:{provider}"

    @staticmethod
    def model_metrics(model: str) -> str:
        return f"metrics:model:{model}"

    # ------------------------
    # Sessions (Future)
    # ------------------------

    @staticmethod
    def session(session_id: str) -> str:
        return f"session:{session_id}"