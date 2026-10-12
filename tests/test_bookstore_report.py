"""Unit tests for pure bookstore report formatting."""

import unittest
from unittest.mock import patch

from nosql_lab.bookstore_report import format_bookstore_report, main


class FormatBookstoreReportTests(unittest.TestCase):
    """Test formatting without requiring a MongoDB connection."""

    def test_formats_count_and_books_under_each_author(self) -> None:
        """List a co-authored book under both authors and retain author order."""
        report = format_bookstore_report(
            2,
            [
                ("Neil Gaiman", [("Good Omens", 1990), ("American Gods", 2001)]),
                ("Terry Pratchett", [("Good Omens", 1990)]),
            ],
        )

        self.assertEqual(
            report,
            "Authors: 2\n\n"
            "Neil Gaiman\n"
            "  Good Omens (1990)\n"
            "  American Gods (2001)\n\n"
            "Terry Pratchett\n"
            "  Good Omens (1990)",
        )

    def test_formats_empty_author_list(self) -> None:
        """Still report a count when none of the requested authors exist."""
        self.assertEqual(format_bookstore_report(0, []), "Authors: 0")

    def test_missing_environment_variables_returns_failure_without_connecting(self) -> None:
        """Report missing config safely and return a failure code before connecting."""
        with (
            patch("nosql_lab.bookstore_report.MONGODB_ATLAS_URL", None),
            patch("nosql_lab.bookstore_report.MONGODB_ATLAS_USER", None),
            patch("nosql_lab.bookstore_report.MONGODB_ATLAS_PWD", None),
            patch("nosql_lab.bookstore_report.MongoClient") as mongo_client,
            self.assertLogs("nosql_lab.bookstore_report", level="ERROR") as logs,
        ):
            exit_code = main()

        self.assertEqual(exit_code, 1)
        mongo_client.assert_not_called()
        self.assertIn("MONGODB_ATLAS_URL", logs.output[0])
        self.assertIn("MONGODB_ATLAS_USER", logs.output[0])
        self.assertIn("MONGODB_ATLAS_PWD", logs.output[0])


if __name__ == "__main__":
    unittest.main()
