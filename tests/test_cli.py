import io
import unittest
from unittest.mock import patch

from fish_study_wiki import cli


class CliTests(unittest.TestCase):
    def test_inventory_command_dispatches(self):
        with patch("fish_study_wiki.cli.run_inventory", return_value=0) as run:
            self.assertEqual(cli.main(["inventory"]), 0)

        run.assert_called_once_with()

    def test_build_command_dispatches(self):
        with patch("fish_study_wiki.cli.run_build", return_value=0) as run:
            self.assertEqual(cli.main(["build"]), 0)

        run.assert_called_once_with()

    def test_verify_command_dispatches(self):
        with patch("fish_study_wiki.cli.run_verify", return_value=0) as run:
            self.assertEqual(cli.main(["verify"]), 0)

        run.assert_called_once_with()

    def test_unknown_command_prints_usage(self):
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            with self.assertRaises(SystemExit):
                cli.main(["unknown"])

        self.assertIn("invalid choice", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
