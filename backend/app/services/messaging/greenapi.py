"""Green API, the WhatsApp gateway (https://green-api.com/en/docs/api/sending/SendMessage/).

One call sends a text: POST {url}/waInstance{id}/sendMessage/{token} with a chat id and the
message. The credentials come from the environment and never appear in a response or a log.
"""

from __future__ import annotations

import re

import httpx

from app.core.config import Settings

TIMEOUT_S = 15.0


class GatewayError(Exception):
    """The message was not sent; the text says why, without the credentials."""


class NotConfigured(GatewayError):
    pass


def normalise_phone(raw: str) -> str:
    """Digits with the country code, for example 905321234567. A Turkish 05xx number gets 90."""
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = "90" + digits[1:]
    if not 10 <= len(digits) <= 15:
        raise ValueError("A phone number needs the country code and 10 to 15 digits")
    return digits


class GreenApiClient:
    def __init__(
        self, *, base_url: str, instance_id: str, token: str, http: httpx.Client | None = None
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._instance_id = instance_id
        self._token = token
        self._http = http

    @classmethod
    def from_settings(cls, settings: Settings, http: httpx.Client | None = None) -> GreenApiClient:
        if not settings.whatsapp_configured:
            raise NotConfigured("The WhatsApp gateway is not configured on this server")
        return cls(
            base_url=settings.green_api_url,
            instance_id=settings.green_api_instance_id,
            token=settings.green_api_token,
            http=http,
        )

    def send_text(self, phone: str, text: str) -> str:
        """Send ``text`` to ``phone``; returns the gateway's message id."""
        url = f"{self._base_url}/waInstance{self._instance_id}/sendMessage/{self._token}"
        payload = {"chatId": f"{normalise_phone(phone)}@c.us", "message": text}
        try:
            if self._http is not None:
                response = self._http.post(url, json=payload, timeout=TIMEOUT_S)
            else:
                response = httpx.post(url, json=payload, timeout=TIMEOUT_S)
        except httpx.HTTPError as error:
            # The URL holds the token, so only the error class is kept.
            raise GatewayError(
                f"The gateway could not be reached ({type(error).__name__})"
            ) from None
        if response.status_code != 200:
            raise GatewayError(f"The gateway answered {response.status_code}")
        message_id = response.json().get("idMessage")
        if not message_id:
            raise GatewayError("The gateway gave no message id")
        return str(message_id)
