import json

import pytest

from models.row import Row
from models.task import Task


class TestBuildFromString:
    def test_builds_task_with_rows_from_valid_json(self):
        task_string = json.dumps({1: {"text": "Hello.", "language": "en"}, 2: {"text": "Hola.", "language": "es"}})

        task = Task.build_from_string("my task", 0, task_string)

        assert task.name == "my task"
        assert task.index == 0
        assert len(task.rows) == 2
        assert task.rows[0].text == "Hello."
        assert task.rows[0].lang == "en"
        assert task.rows[1].text == "Hola."
        assert task.rows[1].lang == "es"

    def test_raises_on_invalid_json(self):
        with pytest.raises(ValueError, match="Invalid JSON format"):
            Task.build_from_string("task", 0, "{not valid json")

    def test_raises_when_top_level_is_not_a_dict(self):
        with pytest.raises(ValueError, match="must represent a dictionary"):
            Task.build_from_string("task", 0, json.dumps(["not", "a", "dict"]))

    def test_raises_when_entry_is_not_a_dict(self):
        task_string = json.dumps({"1": "not a dict"})

        with pytest.raises(ValueError, match="each entry must be a dictionary"):
            Task.build_from_string("task", 0, task_string)

    def test_raises_when_text_or_language_missing(self):
        task_string = json.dumps({"1": {"text": "Hello."}})

        with pytest.raises(ValueError, match="Missing 'text' or 'language'"):
            Task.build_from_string("task", 0, task_string)


class TestValidateInput:
    def test_returns_parsed_dict_for_valid_input(self):
        text = "{1: {'text': 'Hello.', 'language': 'en'}}"

        result = Task.validate_input(text)

        assert result == {1: {"text": "Hello.", "language": "en"}}

    def test_raises_when_top_level_is_not_a_dict(self):
        with pytest.raises(ValueError, match="must be a dictionary"):
            Task.validate_input("['not', 'a', 'dict']")

    def test_raises_when_key_is_not_an_integer(self):
        with pytest.raises(ValueError, match="is not an integer"):
            Task.validate_input("{'1': {'text': 'Hello.', 'language': 'en'}}")

    def test_raises_when_entry_missing_text_or_language(self):
        with pytest.raises(ValueError, match="incorrectly formatted"):
            Task.validate_input("{1: {'text': 'Hello.'}}")

    def test_raises_when_text_or_language_not_strings(self):
        with pytest.raises(ValueError, match="are not strings"):
            Task.validate_input("{1: {'text': 123, 'language': 'en'}}")

    def test_raises_on_malformed_literal(self):
        with pytest.raises(ValueError):
            Task.validate_input("not a valid python literal {{{")


def test_add_row_appends_to_task():
    task = Task(name="task", index=0)

    task.add_row(Row(text="Hello.", lang="en"))

    assert len(task.rows) == 1
    assert task.rows[0].text == "Hello."
