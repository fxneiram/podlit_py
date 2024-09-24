class Row:
    def __init__(self, text: str, lang: str):
        self.text = text
        self.lang = lang

    def __repr__(self):
        return f"Row(text={self.text!r}, lang={self.lang!r})"