from __future__ import annotations

from django_mobile_pass.exceptions import GoogleWalletRequestFailed
from django_mobile_pass.google.auth import GoogleCredentials, GoogleJwtSigner
from django_mobile_pass.settings import get_mobile_pass_settings


class GoogleWalletClient:
    def __init__(self, signer: GoogleJwtSigner | None = None):
        self.signer = signer or GoogleJwtSigner()

    def insert_class(self, resource: str, id: str, payload: dict) -> dict:
        return self._insert_or_patch(resource, id, payload)

    def insert_object(self, resource: str, id: str, payload: dict) -> dict:
        return self._insert_or_patch(resource, id, payload)

    def patch_class(self, resource: str, id: str, payload: dict) -> dict:
        return self._patch(resource, id, payload)

    def patch_object(self, resource: str, id: str, payload: dict) -> dict:
        return self._patch(resource, id, payload)

    def get_class(self, resource: str, id: str) -> dict:
        return self._request("GET", f"/{resource}/{id}")

    def list_classes(self, resource: str) -> list[dict]:
        issuer_id = GoogleCredentials.issuer_id()
        payload = self._request("GET", f"/{resource}", params={"issuerId": issuer_id})
        return payload.get("resources", [])

    def _insert_or_patch(self, resource: str, id: str, payload: dict) -> dict:
        response = self._raw_request("POST", f"/{resource}", json=payload | {"id": id})
        if response.status_code == 409:
            return self._patch(resource, id, payload)
        return self._parse(response, f"/{resource}")

    def _patch(self, resource: str, id: str, payload: dict) -> dict:
        response = self._raw_request("PATCH", f"/{resource}/{id}", json=payload)
        return self._parse(response, f"/{resource}/{id}")

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        response = self._raw_request(method, endpoint, **kwargs)
        return self._parse(response, endpoint)

    def _raw_request(self, method: str, endpoint: str, **kwargs):
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.2,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PATCH"],
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))

        return session.request(
            method,
            f"{get_mobile_pass_settings().google.api_base_url.rstrip('/')}{endpoint}",
            headers={
                "Authorization": f"Bearer {self.signer.access_token()}",
                "Accept": "application/json",
            },
            timeout=30,
            **kwargs,
        )

    @staticmethod
    def _parse(response, endpoint: str) -> dict:
        if response.ok:
            return response.json() if response.content else {}
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        raise GoogleWalletRequestFailed(
            f"Google Wallet request failed for {endpoint}",
            status=response.status_code,
            payload=payload,
        )
