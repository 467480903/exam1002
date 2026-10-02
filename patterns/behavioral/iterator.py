"""Iterator: traverse a playlist without exposing its list directly."""

class Playlist:
    def __init__(self, songs): self._songs = list(songs)
    def __iter__(self): return iter(self._songs)


if __name__ == "__main__":
    for song in Playlist(["Intro", "First song", "Finale"]):
        print(song)

