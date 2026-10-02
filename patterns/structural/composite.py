"""Composite: files and folders share a display interface."""

class File:
    def __init__(self, name): self.name = name
    def display(self, indent=0): return " " * indent + self.name


class Folder:
    def __init__(self, name): self.name, self.children = name, []
    def add(self, child): self.children.append(child); return self
    def display(self, indent=0):
        lines = [" " * indent + self.name]
        lines += [child.display(indent + 2) for child in self.children]
        return "\n".join(lines)


if __name__ == "__main__":
    project = Folder("project").add(File("README.md")).add(
        Folder("src").add(File("main.py")))
    print(project.display())

