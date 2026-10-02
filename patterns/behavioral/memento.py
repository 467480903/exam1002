"""Memento: save and restore a text editor's state."""

class Editor:
    def __init__(self): self.text = ""
    def save(self): return self.text
    def restore(self, memento): self.text = memento


if __name__ == "__main__":
    editor = Editor(); editor.text = "version 1"
    saved = editor.save()
    editor.text = "version 2"
    editor.restore(saved)
    print(editor.text)

