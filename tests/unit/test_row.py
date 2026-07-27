from models.row import Row


def test_row_stores_text_and_lang():
    row = Row(text="Hello world.", lang="en")

    assert row.text == "Hello world."
    assert row.lang == "en"


def test_row_repr_includes_text_and_lang():
    row = Row(text="Hello world.", lang="en")

    assert repr(row) == "Row(text='Hello world.', lang='en')"
