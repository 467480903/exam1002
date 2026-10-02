"""Decorator: add logging around a coffee order."""

class Coffee:
    def cost(self): return 3


class Milk:
    def __init__(self, coffee): self.coffee = coffee
    def cost(self): return self.coffee.cost() + 1


class Sugar:
    def __init__(self, coffee): self.coffee = coffee
    def cost(self): return self.coffee.cost() + 0.5


if __name__ == "__main__":
    order = Sugar(Milk(Coffee()))
    print(f"Coffee costs ${order.cost():.2f}")

