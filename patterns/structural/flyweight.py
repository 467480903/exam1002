"""Flyweight: share one style object among many characters."""

class TreeStyle:
    _styles = {}

    def __new__(cls, color):
        if color not in cls._styles:
            instance = super().__new__(cls)
            instance.color = color
            cls._styles[color] = instance
        return cls._styles[color]


class Tree:
    def __init__(self, x, y, color):
        self.x, self.y, self.style = x, y, TreeStyle(color)


if __name__ == "__main__":
    first, second = Tree(1, 2, "green"), Tree(10, 20, "green")
    print(first.style is second.style)  # True: style is shared

