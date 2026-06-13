from abc import ABC
from abc import abstractmethod

from app.modules.chat.schemas import (
    ChatRequest,
)


class BaseAdapter(ABC):

    @abstractmethod
    async def chat(
        self,
        provider,
        model,
        request: ChatRequest,
    ):
        """
        Execute a chat completion request.

        Parameters
        ----------
        provider
            Provider entity from Model Vault.

        model
            Model entity from Model Vault.

        request
            Incoming ChatRequest.

        Returns
        -------
        ChatResponse
        """
        raise NotImplementedError
    
    @abstractmethod
    async def stream_chat(
        self,
        provider,
        model,
        request,
    ):
        """
        Execute a streaming chat completion request.

        Parameters
        ----------
        provider
            Provider entity from Model Vault.

        model
            Model entity from Model Vault.

        request
            Incoming ChatRequest.

        Returns
        -------
        Async generator yielding ChatResponse chunks.
        """
        raise NotImplementedError