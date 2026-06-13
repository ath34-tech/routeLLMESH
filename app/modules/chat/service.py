from app.modules.chat.schemas import (
    ChatRequest,
)

from app.modules.model_vault.model.repository import (
    ModelRepository,
)

from app.modules.model_vault.provider.repository import (
    ProviderRepository,
)

from app.modules.chat.provider_factory import (
    ProviderFactory,
)

from app.modules.chat.normalizer import (
    ResponseNormalizer,
)

class ChatService:

    def __init__(
        self,
        model_repository: ModelRepository,
        provider_repository: ProviderRepository,
    ):

        self.model_repository = model_repository

        self.provider_repository = provider_repository

    async def chat(
        self,
        request: ChatRequest,
    ):

        # Step 1: Find model
        model = await self.model_repository.get_by_name(
            request.model
        )

        if model is None:

            raise Exception(
                f"Model '{request.model}' not found."
            )

        # Step 2: Find provider
        provider = await self.provider_repository.get_by_id(
            model.provider_id
        )

        if provider is None:

            raise Exception(
                "Provider not found."
            )

        # Step 3: Create adapter
        adapter = ProviderFactory.get_adapter(
            provider.adapter
        )

        # Step 4: Execute request
        response = await adapter.chat(
            provider=provider,
            model=model,
            request=request,
        )

        return ResponseNormalizer.normalize(
            response)