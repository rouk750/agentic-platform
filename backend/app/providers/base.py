from abc import ABC, abstractmethod
from typing import Optional, Any
from app.models.settings import LLMProfile
from pydantic import ValidationError

class BaseLLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    Defines the contract for creating LLM clients (LangChain runnables).
    """

    @abstractmethod
    def create_client(self, profile: LLMProfile, api_key: Optional[str] = None) -> Any:
        """
        Creates and returns a LangChain-compatible LLM/Chat model.
        
        :param profile: The LLMProfile configuration
        :param api_key: The decrypted API key (if applicable)
        :return: A LangChain runnable (ChatModel)
        """
        pass

    async def test_connection(self, profile: LLMProfile, api_key: Optional[str] = None) -> None:
        """
        Tests the connection to the provider.
        Default implementation tries to invoke the model with a simple prompt.
        Override for more efficient checks (e.g. Ollama tags).
        """
        client = self.create_client(profile, api_key)
        # We assume standard LangChain chat model
        if hasattr(client, "ainvoke"):
            # Use a very short prompt to minimize cost/time
            await client.ainvoke("Hi")
        else:
             # Fallback sync
            client.invoke("Hi")
