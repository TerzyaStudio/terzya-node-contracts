import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify_contract.py"
CONTRACT_PATH = Path("skills/terzya-node-session-bootstrap/SKILL.md")
CHECKOUT_SHA = "11d5960a326750d5838078e36cf38b85af677262"


class ContractVerificationTests(unittest.TestCase):
    def run_verifier(self, root):
        return subprocess.run(
            [sys.executable, str(VERIFIER), "--root", str(root)],
            capture_output=True,
            text=True,
        )

    def copy_repository_unit(self, root):
        shutil.copy2(ROOT / "manifest.json", root / "manifest.json")
        destination = root / CONTRACT_PATH
        destination.parent.mkdir(parents=True)
        shutil.copy2(ROOT / CONTRACT_PATH, destination)

    def test_repository_contract_verifies(self):
        result = self.run_verifier(ROOT)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("verified 1 contract", result.stdout)

    def test_checkout_action_is_pinned_to_reviewed_commit(self):
        workflow = (ROOT / ".github" / "workflows" / "verify.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn(f"actions/checkout@{CHECKOUT_SHA}", workflow)
        self.assertNotIn("actions/checkout@v4", workflow)

    def test_boolean_schema_version_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository_unit(root)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["schema_version"] = True
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = self.run_verifier(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("manifest schema_version", result.stderr)

    def test_missing_contract_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy2(ROOT / "manifest.json", root / "manifest.json")

            result = self.run_verifier(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing contract", result.stderr)

    def test_intermediate_symlink_escaping_root_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repository"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            shutil.copy2(ROOT / "manifest.json", root / "manifest.json")
            shutil.copy2(ROOT / CONTRACT_PATH, outside / "SKILL.md")
            (root / "skills").mkdir()
            (root / "skills" / "escape").symlink_to(outside, target_is_directory=True)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["contracts"][0]["path"] = "skills/escape/SKILL.md"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = self.run_verifier(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsafe contract path", result.stderr)

    def test_backslash_in_declared_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy2(ROOT / "manifest.json", root / "manifest.json")
            declared_path = "skills\\terzya-node-session-bootstrap\\SKILL.md"
            shutil.copy2(ROOT / CONTRACT_PATH, root / declared_path)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["contracts"][0]["path"] = declared_path
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = self.run_verifier(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsafe contract path", result.stderr)

    def test_opaque_contract_bytes_verify_when_hash_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository_unit(root)
            contract_path = root / CONTRACT_PATH
            content = b"\xffopaque contract bytes without frontmatter\x00\n"
            contract_path.write_bytes(content)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["contracts"][0]["version"] = "descriptive provenance only"
            manifest["contracts"][0]["sha256"] = hashlib.sha256(content).hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = self.run_verifier(root)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("verified 1 contract", result.stdout)

    def test_contract_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository_unit(root)
            contract_path = root / CONTRACT_PATH
            contract_path.write_bytes(contract_path.read_bytes() + b"\n")

            result = self.run_verifier(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hash mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()
