#!/usr/bin/env python3
"""Verify canonical contract files against the repository manifest."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath


MANIFEST_NAME = "manifest.json"
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class VerificationError(Exception):
    """Raised when repository verification must fail closed."""


def load_manifest(root):
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise VerificationError(f"missing manifest: {MANIFEST_NAME}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise VerificationError(f"invalid manifest: {error}") from error

    if not isinstance(manifest, dict):
        raise VerificationError("invalid manifest object")
    schema_version = manifest.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        raise VerificationError("unsupported or invalid manifest schema_version")
    contracts = manifest.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        raise VerificationError("manifest contracts must be a non-empty array")
    return contracts


def resolve_contract(root, declared_path):
    if not isinstance(declared_path, str):
        raise VerificationError("contract path must be a string")
    portable_path = PurePosixPath(declared_path)
    if (
        "\\" in declared_path
        or portable_path.is_absolute()
        or ".." in portable_path.parts
    ):
        raise VerificationError(f"unsafe contract path: {declared_path}")

    resolved_root = root.resolve(strict=True)
    contract_path = resolved_root.joinpath(*portable_path.parts)
    component = resolved_root
    for part in portable_path.parts:
        component /= part
        if component.is_symlink():
            raise VerificationError(f"unsafe contract path: {declared_path}")

    try:
        resolved_contract = contract_path.resolve(strict=True)
        resolved_contract.relative_to(resolved_root)
    except FileNotFoundError as error:
        raise VerificationError(f"missing contract: {declared_path}") from error
    except ValueError as error:
        raise VerificationError(f"unsafe contract path: {declared_path}") from error

    if not resolved_contract.is_file():
        raise VerificationError(f"missing contract: {declared_path}")
    return resolved_contract


def verify_contract(root, entry):
    if not isinstance(entry, dict):
        raise VerificationError("contract entry must be an object")

    declared_path = entry.get("path")
    expected_version = entry.get("version")
    expected_hash = entry.get("sha256")
    evidence = entry.get("acceptance_evidence")
    if not isinstance(expected_version, str) or not expected_version:
        raise VerificationError(f"invalid version for contract: {declared_path}")
    if not isinstance(expected_hash, str) or SHA256_PATTERN.fullmatch(expected_hash) is None:
        raise VerificationError(f"invalid SHA-256 for contract: {declared_path}")
    if (
        not isinstance(evidence, dict)
        or not isinstance(evidence.get("session_id"), str)
        or not evidence["session_id"]
    ):
        raise VerificationError(f"missing acceptance evidence for contract: {declared_path}")
    if evidence.get("verdict") != "accepted":
        raise VerificationError(f"contract is not accepted: {declared_path}")

    contract_path = resolve_contract(root, declared_path)
    content = contract_path.read_bytes()
    actual_hash = hashlib.sha256(content).hexdigest()
    if actual_hash != expected_hash:
        raise VerificationError(
            f"hash mismatch for {declared_path}: expected {expected_hash}, got {actual_hash}"
        )


def verify(root):
    root = root.resolve()
    contracts = load_manifest(root)
    for entry in contracts:
        verify_contract(root, entry)
    return len(contracts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the verifier's parent repository)",
    )
    args = parser.parse_args()

    try:
        count = verify(args.root)
    except (OSError, VerificationError) as error:
        print(f"verification failed: {error}", file=sys.stderr)
        return 1

    noun = "contract" if count == 1 else "contracts"
    print(f"verified {count} {noun} from {MANIFEST_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
