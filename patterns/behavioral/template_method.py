"""Template Method: the recipe stays fixed while steps vary."""

from abc import ABC, abstractmethod


class Beverage(ABC):
    def prepare(self):
        steps = [self.boil_water(), self.brew(), self.pour(), self.add_extras()]
        return " -> ".join(steps)
    def boil_water(self): return "boil water"
    @abstractmethod
    def brew(self): ...
    def pour(self): return "pour into cup"
    @abstractmethod
    def add_extras(self): ...


class Tea(Beverage):
    def brew(self): return "steep tea"
    def add_extras(self): return "add lemon"


if __name__ == "__main__":
    print(Tea().prepare())

