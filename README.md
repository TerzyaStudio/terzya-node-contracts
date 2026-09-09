# Terzya Node Contracts

Private, portable contracts for Terzya nodes. This repository preserves accepted contract bytes with content-addressed provenance so the same reviewed contract can be transported without carrying node state.

## Scope

The canonical unit contains only:

- accepted reusable contract content;
- a manifest binding each contract path, descriptive version provenance, SHA-256 digest, and acceptance provenance;
- deterministic verification tooling and tests.

It intentionally excludes node configuration, credentials, memory, operational receipts, client data, and deployment instructions.

## Canonicalization and activation

Canonicalization records an accepted, immutable contract in this repository. It does **not** install, register, or activate that contract on any node.

Per-node activation is a separate, authorized lifecycle step. Each target must independently bind the exact canonical digest, apply its own least-privilege configuration, verify the active runtime, and retain its own rollback evidence outside this repository.

## Verification

The manifest is the trust root for contract identity and integrity. The standard-library-only verifier treats contract content as opaque bytes and verifies only the manifest's declared path, non-empty descriptive version provenance, acceptance evidence, and SHA-256 digest; it does not parse contract content or compare version metadata within it. Invalid or missing manifests, unsafe paths or symlinks, missing contract files, invalid hashes, hash mismatches, and absent or unaccepted evidence fail closed.

```sh
python3 scripts/verify_contract.py
python3 -m unittest discover -s tests -v
```

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).
