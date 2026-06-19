from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django_mobile_pass.apple.entities import AppleImage
from django_mobile_pass.exceptions import InvalidCertificate
from django_mobile_pass.settings import AppleSettings


def _image_bytes(image: AppleImage, path: str | None) -> bytes | None:
    if not path:
        return None
    if image.is_remote:
        import requests

        response = requests.get(path, timeout=30)
        response.raise_for_status()
        return response.content
    return Path(path).read_bytes()


def build_pkpass(pass_json: dict, images: dict[str, AppleImage], settings: AppleSettings) -> bytes:
    files: dict[str, bytes] = {
        "pass.json": json.dumps(pass_json, indent=2, sort_keys=True).encode(),
    }

    for filename, image in images.items():
        if content := _image_bytes(image, image.x1_path):
            files[f"{filename}.png"] = content
        if content := _image_bytes(image, image.x2_path):
            files[f"{filename}@2x.png"] = content
        if content := _image_bytes(image, image.x3_path):
            files[f"{filename}@3x.png"] = content

    manifest = {name: hashlib.sha1(content).hexdigest() for name, content in files.items()}
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode()
    signature = sign_manifest(manifest_bytes, settings)

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
        archive.writestr("manifest.json", manifest_bytes)
        archive.writestr("signature", signature)

    return buffer.getvalue()


def sign_manifest(manifest_bytes: bytes, settings: AppleSettings) -> bytes:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.serialization import pkcs12, pkcs7

    try:
        private_key, certificate, extra_certs = pkcs12.load_key_and_certificates(
            settings.certificate_bytes(),
            settings.certificate_password.encode() if settings.certificate_password else None,
        )
    except Exception as exc:
        raise InvalidCertificate("Unable to read the Apple certificate. Check the PKCS#12 bytes and password.") from exc

    if private_key is None or certificate is None:
        raise InvalidCertificate("The Apple PKCS#12 bundle must contain a private key and signing certificate.")

    builder = pkcs7.PKCS7SignatureBuilder().set_data(manifest_bytes).add_signer(
        certificate,
        private_key,
        hashes.SHA256(),
    )

    for extra in extra_certs or ():
        if isinstance(extra, x509.Certificate):
            builder = builder.add_certificate(extra)

    return builder.sign(
        serialization.Encoding.DER,
        [pkcs7.PKCS7Options.DetachedSignature, pkcs7.PKCS7Options.Binary],
    )
