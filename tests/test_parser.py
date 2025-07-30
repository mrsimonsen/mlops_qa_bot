import pytest
from unittest.mock import patch, mock_open, MagicMock, ANY

import parser.parser as parser
from parser.config import OUTPUT_DIR
test_cases = [
	("no change", "This is a clean sentence.", "This is a clean sentence."),
	("excessive newlines", "Hello\n\n\n\nWorld", "Hello\n\nWorld"),
	("preserve paragraph break", "Paragraph 1\n\nParagraph 2", "Paragraph 1\n\nParagraph 2"),
	("strip whitespace", "  line one  \n   line two ", "line one\nline two"),
	("remove long non-alnum", "Delete this ---- but not this ---", "Delete this  but not this ---"),
	("remove long symbols", "Here is some text !@#$%^&* with symbols.", "Here is some text  with symbols."),
	("keep short non-alnum", "This is A-OK.", "This is A-OK."),
	("combined cleaning", "   First line.   \n\n\n\n------\n  Second line.  ", "First line.\n\n\nSecond line."),
	("empty string", "", ""),
	("whitespace only", "   \n   \n ", "\n\n"),
	("non-alnum only", "**********", "")
]
@pytest.mark.parametrize(
		"test_id, input_text, expected_output",
		test_cases,
		ids=[cases[0] for cases in test_cases]
	)
def test_clean_text(test_id, input_text, expected_output):
	"""
	Tests the clean_text function with various inputs.
	"""
	assert parser.clean_text(input_text) == expected_output

test_cases = [
	("empty string", "", []),
	(
		"text shorter than chunk",
		"This is short.",
		["This is short."]
	),
	(
		"standard text multiple chunks",
		"This is a long string for testing the chunking functionality.",
		[
			"This is a long strin", #text[0:20]
			"string for testing t", #text[15:35]
			"ing the chunking fun", #text[30:50]
			"g functionality.",     #text[45:65]
			"."                     #text[60:80]
		]
	)
]
TEST_CHUNK_SIZE = 20
TEST_CHUNK_OVERLAP = 5
@pytest.mark.parametrize(
		"test_id, input_text, expected_output",
		test_cases,
		ids=[cases[0] for cases in test_cases]
)
def test_chunk_text(monkeypatch, test_id, input_text, expected_output):
	"""
	Tests chunking by first patching the config constants with smaller,
	test-friendly values and then running various text scenarios.
	"""
	monkeypatch.setattr("parser.parser.CHUNK_SIZE", TEST_CHUNK_SIZE)
	monkeypatch.setattr("parser.parser.CHUNK_OVERLAP", TEST_CHUNK_OVERLAP)

	actual_output = parser.chunk_text(input_text)

	assert actual_output == expected_output