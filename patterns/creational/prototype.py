"""Prototype: create a new object by copying an existing one."""

from copy import deepcopy


class GameCharacter:
    def __init__(self, name, equipment):
        self.name, self.equipment = name, equipment

    def clone(self):
        return deepcopy(self)


if __name__ == "__main__":
    original = GameCharacter("Knight", ["sword", "shield"])
    copy = original.clone()
    copy.name = "Training Knight"
    copy.equipment.append("helmet")
    print(original.name, original.equipment)
    print(copy.name, copy.equipment)

