from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from app.models import AuthenticatedIdentity, CallbackRequest, InitiateSSORequest, SSOInitResponse


class BaseProvider(ABC):
    provider_name: str
    flow_name: str

    @abstractmethod
    def initiate(self, req: InitiateSSORequest) -> SSOInitResponse:
        raise NotImplementedError

    @abstractmethod
    def consume_callback(self, req: CallbackRequest) -> AuthenticatedIdentity:
        raise NotImplementedError

    @staticmethod
    def _required(payload: Dict[str, Any], *fields: str) -> None:
        missing = [f for f in fields if not payload.get(f)]
        if missing:
            raise ValueError(f"Missing required callback fields: {', '.join(missing)}")
