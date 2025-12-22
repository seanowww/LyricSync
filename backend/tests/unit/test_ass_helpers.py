"""
Unit tests for ASS subtitle generation helpers.
These are pure functions with no I/O - fast and deterministic.
"""
import pytest
import sys
from pathlib import Path

# Import directly from utils module to avoid importing FastAPI app
from src.utils.ass_helpers import (
    format_ass_timestamp as _format_ass_timestamp,
    escape_ass_text as _escape_ass_text,
    css_hex_to_ass as _css_hex_to_ass,
    align_to_ass as _align_to_ass,
)


class TestFormatAssTimestamp:
    """Test ASS timestamp formatting (seconds -> H:MM:SS.CC)"""

    def test_zero(self):
        assert _format_ass_timestamp(0.0) == "0:00:00.00"

    def test_whole_seconds(self):
        assert _format_ass_timestamp(5.0) == "0:00:05.00"
        assert _format_ass_timestamp(65.0) == "0:01:05.00"

    def test_with_centiseconds(self):
        assert _format_ass_timestamp(1.23) == "0:00:01.23"
        assert _format_ass_timestamp(12.45) == "0:00:12.45"

    def test_negative_clamped_to_zero(self):
        assert _format_ass_timestamp(-1.5) == "0:00:00.00"

    def test_large_values(self):
        assert _format_ass_timestamp(3661.50) == "1:01:01.50"


class TestEscapeAssText:
    """Test ASS text escaping (newlines, braces, etc.)"""

    def test_basic_text(self):
        assert _escape_ass_text("Hello") == "Hello"

    def test_newlines(self):
        assert _escape_ass_text("Line1\nLine2") == r"Line1\NLine2"

    def test_carriage_return_removed(self):
        assert _escape_ass_text("Text\r\nMore") == r"Text\NMore"

    def test_braces_escaped(self):
        assert _escape_ass_text("Text {with} braces") == r"Text \{with\} braces"

    def test_empty_string(self):
        assert _escape_ass_text("") == ""
        assert _escape_ass_text(None) == ""

    def test_multiple_escapes(self):
        assert _escape_ass_text("Line1\n{value}\rLine2") == r"Line1\N\{value\}Line2"


class TestCssHexToAss:
    """Test CSS hex color to ASS format conversion"""

    def test_white(self):
        assert _css_hex_to_ass("#FFFFFF") == "&H00FFFFFF"

    def test_black(self):
        assert _css_hex_to_ass("#000000") == "&H00000000"

    def test_red(self):
        assert _css_hex_to_ass("#FF0000") == "&H000000FF"

    def test_green(self):
        assert _css_hex_to_ass("#00FF00") == "&H0000FF00"

    def test_blue(self):
        assert _css_hex_to_ass("#0000FF") == "&H00FF0000"

    def test_without_hash(self):
        assert _css_hex_to_ass("FF0000") == "&H000000FF"

    def test_invalid_defaults_to_white(self):
        assert _css_hex_to_ass("invalid") == "&H00FFFFFF"
        assert _css_hex_to_ass("#123") == "&H00FFFFFF"
        assert _css_hex_to_ass(None) == "&H00FFFFFF"


class TestAlignToAss:
    """Test alignment conversion"""

    def test_bottom_center(self):
        assert _align_to_ass("bottom-center") == 2
        assert _align_to_ass("anything") == 2  # MVP: always returns 2

