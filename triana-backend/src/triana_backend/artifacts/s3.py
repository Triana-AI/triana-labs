from __future__ import annotations

import base64
import hashlib
import tempfile
from typing import Any, BinaryIO, cast

from botocore.exceptions import ClientError

from triana_backend.domain.models import (
    ArtifactAvailability,
    ArtifactIntegrityError,
    ArtifactKind,
    ArtifactRef,
    deterministic_id,
)


class S3ArtifactStore:
    """SSE-KMS content-addressed storage with verified publication."""

    def __init__(
        self,
        *,
        client: Any,
        artifact_bucket: str,
        kms_key_id: str,
        object_prefix: str = "objects/sha256",
    ) -> None:
        if not artifact_bucket or not kms_key_id:
            raise ValueError("artifact_bucket and kms_key_id are required")
        self._client = client
        self._artifact_bucket = artifact_bucket
        self._kms_key_id = kms_key_id
        self._object_prefix = object_prefix.strip("/")

    def publish_staging(
        self,
        *,
        bucket: str,
        key: str,
        expected_sha256: str,
        kind: ArtifactKind,
        media_type: str,
    ) -> ArtifactRef:
        expected_sha256 = _validate_hex_digest(expected_sha256)
        source_head = self._head_object(bucket, key)
        self._verify_encryption(source_head, expected_kms_key=None)
        source_checksum = _require_checksum(source_head)
        expected_checksum = _checksum_b64(expected_sha256)
        if source_checksum != expected_checksum:
            raise ArtifactIntegrityError("staging S3 checksum does not match request")

        spool = tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b")
        digest = hashlib.sha256()
        byte_count = 0
        source = self._client.get_object(Bucket=bucket, Key=key)["Body"]
        try:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
                byte_count += len(chunk)
                spool.write(chunk)
        finally:
            source.close()
        if digest.hexdigest() != expected_sha256:
            spool.close()
            raise ArtifactIntegrityError("staging S3 bytes do not match request digest")
        if source_head.get("ContentLength") != byte_count:
            spool.close()
            raise ArtifactIntegrityError("staging S3 size changed while reading")

        canonical_key = self._canonical_key(kind, expected_sha256)
        spool.seek(0)
        try:
            self._client.put_object(
                Bucket=self._artifact_bucket,
                Key=canonical_key,
                Body=spool,
                ContentLength=byte_count,
                ContentType=media_type,
                ChecksumSHA256=expected_checksum,
                ServerSideEncryption="aws:kms",
                SSEKMSKeyId=self._kms_key_id,
                Metadata={"sha256": expected_sha256, "artifact-kind": kind.value},
                IfNoneMatch="*",
            )
        except ClientError as error:
            # Concurrent identical publishers converge on one immutable object.
            # A precondition failure is safe only after verifying the winner.
            code = str(error.response.get("Error", {}).get("Code", ""))
            status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if code not in {"PreconditionFailed", "412"} and status != 412:
                raise
        finally:
            spool.close()

        existing = self._head_object(self._artifact_bucket, canonical_key)

        self._verify_published_head(
            existing,
            expected_sha256=expected_sha256,
            expected_checksum=expected_checksum,
            expected_size=byte_count,
            expected_kind=kind,
            expected_kms_key=None,
        )
        return ArtifactRef(
            id=deterministic_id("art", {"kind": kind.value, "sha256": expected_sha256}),
            kind=kind,
            content_sha256=expected_sha256,
            byte_count=byte_count,
            media_type=media_type,
            storage_bucket=self._artifact_bucket,
            storage_key=canonical_key,
            kms_key_id=str(existing["SSEKMSKeyId"]),
            checksum_sha256_b64=expected_checksum,
        )

    def publish_bytes(
        self, *, payload: bytes, kind: ArtifactKind, media_type: str
    ) -> ArtifactRef:
        digest = hashlib.sha256(payload).hexdigest()
        checksum = _checksum_b64(digest)
        key = self._canonical_key(kind, digest)
        try:
            self._client.put_object(
                Bucket=self._artifact_bucket,
                Key=key,
                Body=payload,
                ContentLength=len(payload),
                ContentType=media_type,
                ChecksumSHA256=checksum,
                ServerSideEncryption="aws:kms",
                SSEKMSKeyId=self._kms_key_id,
                Metadata={"sha256": digest, "artifact-kind": kind.value},
                IfNoneMatch="*",
            )
        except ClientError as error:
            code = str(error.response.get("Error", {}).get("Code", ""))
            status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if code not in {"PreconditionFailed", "412"} and status != 412:
                raise
        head = self._head_object(self._artifact_bucket, key)
        self._verify_published_head(
            head,
            expected_sha256=digest,
            expected_checksum=checksum,
            expected_size=len(payload),
            expected_kind=kind,
            expected_kms_key=None,
        )
        return ArtifactRef(
            id=deterministic_id("art", {"kind": kind.value, "sha256": digest}),
            kind=kind,
            content_sha256=digest,
            byte_count=len(payload),
            media_type=media_type,
            storage_bucket=self._artifact_bucket,
            storage_key=key,
            kms_key_id=str(head["SSEKMSKeyId"]),
            checksum_sha256_b64=checksum,
        )

    def open_verified(self, ref: ArtifactRef) -> BinaryIO:
        self._verify_published_head(
            self._head_object(ref.storage_bucket, ref.storage_key),
            expected_sha256=ref.content_sha256,
            expected_checksum=ref.checksum_sha256_b64,
            expected_size=ref.byte_count,
            expected_kind=ref.kind,
            expected_kms_key=ref.kms_key_id,
        )
        output = tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b")
        digest = hashlib.sha256()
        body = self._client.get_object(Bucket=ref.storage_bucket, Key=ref.storage_key)[
            "Body"
        ]
        try:
            while chunk := body.read(1024 * 1024):
                digest.update(chunk)
                output.write(chunk)
        finally:
            body.close()
        if digest.hexdigest() != ref.content_sha256:
            output.close()
            raise ArtifactIntegrityError("stored S3 bytes failed digest verification")
        output.seek(0)
        return cast(BinaryIO, output)

    def head(self, ref: ArtifactRef) -> ArtifactAvailability:
        try:
            head = self._head_object(ref.storage_bucket, ref.storage_key)
            self._verify_published_head(
                head,
                expected_sha256=ref.content_sha256,
                expected_checksum=ref.checksum_sha256_b64,
                expected_size=ref.byte_count,
                expected_kind=ref.kind,
                expected_kms_key=ref.kms_key_id,
            )
        except ArtifactIntegrityError as error:
            if str(error) == "S3 object is missing":
                return ArtifactAvailability.MISSING
            return ArtifactAvailability.INTEGRITY_FAILED
        return ArtifactAvailability.AVAILABLE

    def _head_object(self, bucket: str, key: str) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                self._client.head_object(
                    Bucket=bucket, Key=key, ChecksumMode="ENABLED"
                ),
            )
        except ClientError as error:
            code = str(error.response.get("Error", {}).get("Code", ""))
            if code in {"404", "NoSuchKey", "NotFound"}:
                raise ArtifactIntegrityError("S3 object is missing") from error
            raise

    def _verify_published_head(
        self,
        head: dict[str, Any],
        *,
        expected_sha256: str,
        expected_checksum: str,
        expected_size: int,
        expected_kind: ArtifactKind,
        expected_kms_key: str | None,
    ) -> None:
        self._verify_encryption(head, expected_kms_key=expected_kms_key)
        if _require_checksum(head) != expected_checksum:
            raise ArtifactIntegrityError("published S3 checksum mismatch")
        if head.get("ContentLength") != expected_size:
            raise ArtifactIntegrityError("published S3 size mismatch")
        metadata = head.get("Metadata") or {}
        if metadata.get("sha256") != expected_sha256:
            raise ArtifactIntegrityError("published S3 digest metadata mismatch")
        if metadata.get("artifact-kind") != expected_kind.value:
            raise ArtifactIntegrityError("published S3 artifact kind mismatch")

    def _canonical_key(self, kind: ArtifactKind, digest: str) -> str:
        segment = kind.value.lower()
        return f"{self._object_prefix}/{segment}/{digest[:2]}/{digest}"

    @staticmethod
    def _verify_encryption(
        head: dict[str, Any], *, expected_kms_key: str | None
    ) -> None:
        if head.get("ServerSideEncryption") != "aws:kms":
            raise ArtifactIntegrityError("S3 object is not encrypted with SSE-KMS")
        actual_kms_key = head.get("SSEKMSKeyId")
        if not actual_kms_key:
            raise ArtifactIntegrityError("S3 object has no KMS key identity")
        if expected_kms_key is not None and actual_kms_key != expected_kms_key:
            raise ArtifactIntegrityError("S3 object uses an unexpected KMS key")


def _validate_hex_digest(value: str) -> str:
    normalized = value.lower()
    if len(normalized) != 64 or any(ch not in "0123456789abcdef" for ch in normalized):
        raise ArtifactIntegrityError("expected_sha256 must be 64 lowercase hex digits")
    return normalized


def _checksum_b64(hex_digest: str) -> str:
    return base64.b64encode(bytes.fromhex(hex_digest)).decode("ascii")


def _require_checksum(head: dict[str, Any]) -> str:
    checksum = head.get("ChecksumSHA256")
    if not isinstance(checksum, str) or not checksum:
        raise ArtifactIntegrityError("S3 object has no SHA-256 object checksum")
    return checksum
