"""Abstract Factory: create matching Light or Dark UI components."""

from abc import ABC, abstractmethod


class UIComponentFactory(ABC):
    @abstractmethod
    def button(self): ...

    @abstractmethod
    def checkbox(self): ...


class LightFactory(UIComponentFactory):
    def button(self): return "Light button"
    def checkbox(self): return "Light checkbox"


class DarkFactory(UIComponentFactory):
    def button(self): return "Dark button"
    def checkbox(self): return "Dark checkbox"


def render_screen(factory):
    return f"{factory.button()} + {factory.checkbox()}"


if __name__ == "__main__":
    print(render_screen(LightFactory()))
    print(render_screen(DarkFactory()))

