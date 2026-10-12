"""Unit tests for bookstore report formatting and query flow."""

from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import MagicMock, call, patch

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

    def test_main_prints_joined_report_and_closes_client(self) -> None:
        """Query selected authors and linked books, print them, and close Atlas."""
        authors = MagicMock()
        authors.count_documents.return_value = 3
        authors.find_one.side_effect = [
            {"_id": "author_002", "name": "Neil Gaiman"},
            {"_id": "author_003", "name": "Terry Pratchett"},
            {"_id": "author_004", "name": "Diana Wynne Jones"},
        ]
        books = MagicMock()
        books.find.side_effect = [
            [
                {"title": "Good Omens", "published_year": 1990},
                {"title": "American Gods", "published_year": 2001},
            ],
            [
                {"title": "Good Omens", "published_year": 1990},
                {"title": "The Colour of Magic", "published_year": 1983},
            ],
            [{"title": "Howl's Moving Castle", "published_year": 1986}],
        ]
        database = MagicMock()
        collections = {"authors": authors, "books": books}
        database.__getitem__.side_effect = collections.__getitem__
        client = MagicMock()
        client.__getitem__.return_value = database
        output = StringIO()

        with (
            patch(
                "nosql_lab.bookstore_report.MONGODB_ATLAS_URL",
                "mongodb+srv://example.mongodb.net",
            ),
            patch("nosql_lab.bookstore_report.MONGODB_ATLAS_USER", "course-user"),
            patch("nosql_lab.bookstore_report.MONGODB_ATLAS_PWD", "course-password"),
            patch(
                "nosql_lab.bookstore_report.MongoClient", return_value=client
            ) as mongo_client,
            redirect_stdout(output),
        ):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        mongo_client.assert_called_once_with(
            "mongodb+srv://example.mongodb.net",
            username="course-user",
            password="course-password",
        )
        client.admin.command.assert_called_once_with("ping")
        authors.count_documents.assert_called_once_with(
            {"_id": {"$in": ["author_002", "author_003", "author_004"]}}
        )
        books.find.assert_has_calls(
            [
                call(
                    {"author_ids": "author_002"},
                    {"title": 1, "published_year": 1},
                ),
                call(
                    {"author_ids": "author_003"},
                    {"title": 1, "published_year": 1},
                ),
                call(
                    {"author_ids": "author_004"},
                    {"title": 1, "published_year": 1},
                ),
            ]
        )
        client.close.assert_called_once_with()
        self.assertEqual(
            output.getvalue().strip(),
            "Authors: 3\n\n"
            "Neil Gaiman\n"
            "  Good Omens (1990)\n"
            "  American Gods (2001)\n\n"
            "Terry Pratchett\n"
            "  Good Omens (1990)\n"
            "  The Colour of Magic (1983)\n\n"
            "Diana Wynne Jones\n"
            "  Howl's Moving Castle (1986)",
        )

    def test_database_error_returns_failure_and_closes_client(self) -> None:
        """Report database failures safely and still close an opened client."""
        client = MagicMock()
        client.admin.command.side_effect = TimeoutError("private connection detail")

        with (
            patch(
                "nosql_lab.bookstore_report.MONGODB_ATLAS_URL",
                "mongodb+srv://example.mongodb.net",
            ),
            patch("nosql_lab.bookstore_report.MONGODB_ATLAS_USER", "course-user"),
            patch("nosql_lab.bookstore_report.MONGODB_ATLAS_PWD", "course-password"),
            patch("nosql_lab.bookstore_report.MongoClient", return_value=client),
            self.assertLogs("nosql_lab.bookstore_report", level="ERROR") as logs,
        ):
            exit_code = main()

        self.assertEqual(exit_code, 1)
        client.close.assert_called_once_with()
        self.assertIn("TimeoutError", logs.output[0])
        self.assertNotIn("private connection detail", logs.output[0])

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
