import pytest
from unittest.mock import patch, mock_open, MagicMock, ANY
import requests

import parser.parser as parser
from parser.config import OUTPUT_DIR

@pytest.mark.parametrize("test_id, input_text, expected_output",[
	("no_change", "This is a clean sentence.", "This is a clean sentence."),
	("excessive_newlines", "Hello\n\n\n\nWorld", "Hello\n\nWorld"),
	("preserve_paragraph_break", "Paragraph 1\n\nParagraph 2", "Paragraph 1\n\nParagraph 2"),
	("strip_whitespace", "  line one  \n   line two ", "line one\nline two"),
	("remove_long_non_alnum", "Delete this ---- but not this ---", "Delete this  but not this ---"),
	("remove_long_symbols", "Here is some text !@#$%^&* with symbols.", "Here is some text  with symbols."),
	("keep_short_non_alnum", "This is A-OK.", "This is A-OK."),
	("combined_cleaning", "   First line.   \n\n\n\n------\n  Second line.  ", "First line.\n\n\nSecond line."),
	("empty_string", "", ""),
	("whitespace_only", "   \n   \n ", "\n\n"),
	("non_alnum_only", "**********", "")
])
def test_clean_text(test_id, input_text, expected_output):
	"""
	Tests the clean_text function with various inputs.
	"""
	assert parser.clean_text(input_text) == expected_output

