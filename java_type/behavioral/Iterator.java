/** Iterator: traverse a playlist without exposing its internal list. */
import java.util.Arrays;
import java.util.List;

public class Iterator {
    static class Playlist implements Iterable<String> {
        private final List<String> songs;
        Playlist(String... songs) { this.songs = Arrays.asList(songs); }
        public java.util.Iterator<String> iterator() { return songs.iterator(); }
    }

    public static void main(String[] args) {
        for (String song : new Playlist("Intro", "First song", "Finale"))
            System.out.println(song);
    }
}
