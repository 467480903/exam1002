/** Abstract Factory: create matching families of UI components. */
public class AbstractFactory {
    interface UIFactory { String button(); String checkbox(); }
    static class LightFactory implements UIFactory {
        public String button() { return "Light button"; }
        public String checkbox() { return "Light checkbox"; }
    }
    static class DarkFactory implements UIFactory {
        public String button() { return "Dark button"; }
        public String checkbox() { return "Dark checkbox"; }
    }
    static String render(UIFactory factory) {
        return factory.button() + " + " + factory.checkbox();
    }

    public static void main(String[] args) {
        System.out.println(render(new LightFactory()));
        System.out.println(render(new DarkFactory()));
    }
}

