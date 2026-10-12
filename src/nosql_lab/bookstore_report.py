#!/usr/bin/env python3
"""Print books linked to selected authors in the bookstore database."""

import logging
import os
from collections.abc import Sequence

from pymongo import MongoClient

# Read connection settings from the shell environment; never log their values.
MONGODB_ATLAS_URL = os.getenv("MONGODB_ATLAS_URL")
MONGODB_ATLAS_USER = os.getenv("MONGODB_ATLAS_USER")
MONGODB_ATLAS_PWD = os.getenv("MONGODB_ATLAS_PWD")

AUTHOR_IDS = ["author_002", "author_003", "author_004"]

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger(__name__)


def format_bookstore_report(
    author_count: int,
    authors_and_books: Sequence[tuple[str, Sequence[tuple[str, int]]]],
) -> str:
    """Format the author count and each author's linked book titles and years."""
    lines = [f"Authors: {author_count}"]
    for author_name, linked_books in authors_and_books:
        lines.extend(("", author_name))
        for title, published_year in linked_books:
            lines.append(f"  {title} ({published_year})")
    return "\n".join(lines)


def main() -> int:
    """Connect to Atlas and print the bookstore report for the selected authors."""
    client = None
    exit_code = 0
    try:
        # Reject incomplete configuration without exposing any configured values.
        missing_variables = [
            name
            for name, value in (
                ("MONGODB_ATLAS_URL", MONGODB_ATLAS_URL),
                ("MONGODB_ATLAS_USER", MONGODB_ATLAS_USER),
                ("MONGODB_ATLAS_PWD", MONGODB_ATLAS_PWD),
            )
            if not value
        ]
        if missing_variables:
            LOGGER.error(
                "Missing required environment variables: %s",
                ", ".join(missing_variables),
            )
            exit_code = 1
        else:
            # PyMongo may include connection details in exceptions, so log only
            # exception types if a connection or database operation fails.
            client = MongoClient(
                MONGODB_ATLAS_URL,
                username=MONGODB_ATLAS_USER,
                password=MONGODB_ATLAS_PWD,
            )
            client.admin.command("ping")
            LOGGER.info("Connected to MongoDB Atlas.")

            database = client["bookstore"]
            authors = database["authors"]
            books = database["books"]
            author_filter = {"_id": {"$in": list(AUTHOR_IDS)}}
            author_count = authors.count_documents(author_filter)

            # Preserve the requested author order while resolving each linked book.
            report_rows: list[tuple[str, list[tuple[str, int]]]] = []
            for author_id in AUTHOR_IDS:
                author = authors.find_one({"_id": author_id}, {"name": 1})
                if author is None:
                    continue

                linked_books = [
                    (book["title"], book["published_year"])
                    for book in books.find(
                        {"author_ids": author_id},
                        {"title": 1, "published_year": 1},
                    )
                ]
                report_rows.append((author["name"], linked_books))

            print(format_bookstore_report(author_count, report_rows))
    except Exception as error:
        # Avoid exception messages because they can contain MongoDB credentials.
        LOGGER.error(
            "Could not generate the bookstore report (%s).", type(error).__name__
        )
        exit_code = 1
    finally:
        if client is not None:
            try:
                client.close()
            except Exception as error:
                LOGGER.error(
                    "Could not close the MongoDB client (%s).", type(error).__name__
                )
                exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
