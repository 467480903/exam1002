"""Facade: hide several home-theater steps behind one method."""

class Projector:
    def on(self): return "projector on"
class SoundSystem:
    def on(self): return "sound on"
class Player:
    def play(self, movie): return f"playing {movie}"


class HomeTheaterFacade:
    def __init__(self):
        self.projector, self.sound, self.player = Projector(), SoundSystem(), Player()

    def watch(self, movie):
        return ", ".join((self.projector.on(), self.sound.on(), self.player.play(movie)))


if __name__ == "__main__":
    print(HomeTheaterFacade().watch("The Matrix"))

