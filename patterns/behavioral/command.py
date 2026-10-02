"""Command: turn an editor action into an object that can be undone."""

class TextEditor:
    def __init__(self): self.text = ""


class AppendCommand:
    def __init__(self, editor, text): self.editor, self.text = editor, text
    def execute(self): self.editor.text += self.text
    def undo(self): self.editor.text = self.editor.text[:-len(self.text)]


if __name__ == "__main__":
    editor = TextEditor()
    command = AppendCommand(editor, "hello")
    command.execute(); print(editor.text)
    command.undo(); print(repr(editor.text))
