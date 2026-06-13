from app.modules.chat.adapters.openai import (
    OpenAIAdapter,
)

PROVIDER_ADAPTERS = {
    "openai": OpenAIAdapter,
    # Future adapters
    # "anthropic": AnthropicAdapter,
    # "gemini": GeminiAdapter,
    # "ollama": OllamaAdapter,
}

class ProviderFactory:

    @staticmethod
    def get_adapter(
        adapter_name: str,
    ):

        adapter_name = adapter_name.lower() 
        if adapter_name in PROVIDER_ADAPTERS:
            return PROVIDER_ADAPTERS[adapter_name]()



        # Future adapters

        # if adapter_name == "anthropic":
        #     return AnthropicAdapter()

        # if adapter_name == "gemini":
        #     return GeminiAdapter()

        # if adapter_name == "ollama":
        #     return OllamaAdapter()

        raise ValueError(
            f"Unsupported adapter: {adapter_name}"
        )