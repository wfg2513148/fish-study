import tempfile
import unittest
import zipfile
from pathlib import Path

from fish_study_wiki.zip_inventory import decode_zip_name, inventory_zip


class ZipInventoryTests(unittest.TestCase):
    def test_decode_gbk_zip_name(self):
        mojibake = "第1章 直线的相交.pptx".encode("gbk").decode("cp437")
        self.assertEqual(decode_zip_name(mojibake), "第1章 直线的相交.pptx")

    def test_inventory_zip_returns_decoded_file_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.zip"
            raw_name = "第1章 直线的相交.pptx".encode("gbk").decode("cp437")
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(raw_name, b"demo")

            rows = inventory_zip(path)

        self.assertEqual(rows[0]["name"], "第1章 直线的相交.pptx")
        self.assertEqual(rows[0]["size"], 4)


if __name__ == "__main__":
    unittest.main()
