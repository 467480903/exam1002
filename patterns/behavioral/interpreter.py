"""Interpreter: evaluate a tiny language made of numbers and addition."""

class Number:
    def __init__(self, value): self.value = value
    def interpret(self): return self.value


class Add:
    def __init__(self, left, right): self.left, self.right = left, right
    def interpret(self): return self.left.interpret() + self.right.interpret()


if __name__ == "__main__":
    expression = Add(Number(2), Add(Number(3), Number(4)))
    print(expression.interpret())

