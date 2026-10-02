/** Singleton: one shared application configuration object. */
public class Singleton {
    private static final Singleton INSTANCE = new Singleton();
    private boolean debug;

    private Singleton() {}

    public static Singleton getInstance() { return INSTANCE; }
    public void setDebug(boolean debug) { this.debug = debug; }
    public boolean isDebug() { return debug; }

    public static void main(String[] args) {
        Singleton first = Singleton.getInstance();
        first.setDebug(true);
        Singleton second = Singleton.getInstance();
        System.out.println(second.isDebug());
        System.out.println(first == second);
    }
}

