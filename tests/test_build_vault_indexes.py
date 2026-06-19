import tempfile
import unittest
from pathlib import Path

from fish_study_wiki.models import SourceRecord
from fish_study_wiki.zip_inventory import sha256
from scripts.build_vault_indexes import validate_available_source


def source_record(local_path: str, digest: str = "abc") -> SourceRecord:
    return SourceRecord(
        source_id="demo",
        subject="数学",
        grade="七年级",
        volume="下册",
        version="浙教版",
        source_type="courseware",
        status="available",
        local_path=local_path,
        sha256=digest,
    )


class BuildVaultIndexSourceValidationTests(unittest.TestCase):
    def test_available_source_requires_local_path(self):
        source = source_record("")

        with self.assertRaisesRegex(ValueError, "available source demo has no local_path"):
            validate_available_source(source)

    def test_available_source_requires_existing_file(self):
        source = source_record("/tmp/fish-study-missing-source.zip")

        with self.assertRaisesRegex(FileNotFoundError, "demo.*file not found"):
            validate_available_source(source)

    def test_available_source_requires_matching_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.zip"
            path.write_bytes(b"demo")
            source = source_record(str(path), "wrong")

            with self.assertRaisesRegex(ValueError, "demo.*sha256 mismatch"):
                validate_available_source(source)

    def test_available_source_returns_path_when_checksum_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.zip"
            path.write_bytes(b"demo")
            source = source_record(str(path), sha256(path))

            self.assertEqual(validate_available_source(source), path)


if __name__ == "__main__":
    unittest.main()
