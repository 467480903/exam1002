/** Facade: hide several home-theater steps behind one method. */
public class Facade {
    static class Projector { String on() { return "projector on"; } }
    static class SoundSystem { String on() { return "sound on"; } }
    static class Player { String play(String movie) { return "playing " + movie; } }
    static class HomeTheater {
        private final Projector projector = new Projector();
        private final SoundSystem sound = new SoundSystem();
        private final Player player = new Player();
        String watch(String movie) {
            return projector.on() + ", " + sound.on() + ", " + player.play(movie);
        }
    }

    public static void main(String[] args) {
        System.out.println(new HomeTheater().watch("The Matrix"));
    }
}

