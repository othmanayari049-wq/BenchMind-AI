from .config import Settings
from .providers import MockProvider, ModelProvider, ProviderUnavailable


def build_provider(settings: Settings) -> ModelProvider:
    if settings.model_provider.lower() == "openai":
        try:
            from .providers.openai import OpenAIProvider
        except ImportError as exc:
            raise ProviderUnavailable(
                "OpenAI provider dependencies are not installed; run pip install -e '.[openai]'"
            ) from exc
        return OpenAIProvider(
            settings.openai_api_key, settings.openai_model, settings.request_timeout_seconds
        )
    if settings.model_provider.lower() == "mock":
        return MockProvider()
    raise ProviderUnavailable(f"Unsupported model provider: {settings.model_provider}")
