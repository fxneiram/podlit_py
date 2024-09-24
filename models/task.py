import ast
import json

from .row import Row


class Task:
    def __init__(self, name: str, index: int, rows=None):
        self.name = name
        self.index = index
        self.rows = rows if rows is not None else []

    def add_row(self, row: Row):
        self.rows.append(row)

    @staticmethod
    def build_from_string(name: str, index: int, task_string: str):
        try:
            task_data = json.loads(task_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        if not isinstance(task_data, dict):
            raise ValueError("The task string must represent a dictionary.")

        rows = []
        for key, value in task_data.items():
            if not isinstance(value, dict):
                raise ValueError(f"Invalid row format at key {key}: each entry must be a dictionary.")

            if "text" not in value or "language" not in value:
                raise ValueError(f"Missing 'text' or 'language' in entry at key {key}.")

            row = Row(text=value["text"], lang=value["language"])
            rows.append(row)

        return Task(name=name, index=index, rows=rows)

    @staticmethod
    def validate_input(text):
        try:
            parsed_text = ast.literal_eval(text)
            if not isinstance(parsed_text, dict):
                raise ValueError("Input must be a dictionary.")

            for key, value in parsed_text.items():
                if not isinstance(key, int):
                    raise ValueError(f"Key {key} is not an integer.")
                if "text" not in value or "language" not in value:
                    raise ValueError(f"Entry {key} is incorrectly formatted.")
                if not isinstance(value["text"], str) or not isinstance(value["language"], str):
                    raise ValueError(f"'text' or 'language' in {key} are not strings.")
            return parsed_text
        except Exception as e:
            return e

    def __repr__(self):
        return f"Task(name={self.name!r}, index={self.index!r}, rows={self.rows})"
