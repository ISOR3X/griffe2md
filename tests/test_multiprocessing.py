"""Tests for generating Markdown for the multiprocessing module."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from griffe2md.main import write_package_docs


def test_generate_multiprocessing_docs() -> None:
    """Generate markdown documentation for the multiprocessing module."""
    # Get the tests directory path
    tests_dir = Path(__file__).parent
    output_file = tests_dir / "multiprocessing.md"
    write_package_docs("multiprocessing", output=str(output_file))

    # Verify the file was created
    assert output_file.exists()

    # Read the content to verify it's not empty
    content = output_file.read_text()
    assert content

    # Verify the heading level is H1
    assert content.startswith("# multiprocessing")

    # Verify links use hyphens instead of dots
    assert "#multiprocessing-" in content
    assert "#multiprocessing." not in content

    # Verify links are lowercase
    assert "#multiprocessing-connection-listener" in content.lower()
    assert "#MULTIPROCESSING-CONNECTION-LISTENER" not in content

    # Verify no � characters
    assert "�" not in content

    # Print the path to the generated file for manual inspection
    print(f"Generated markdown file: {output_file}")
