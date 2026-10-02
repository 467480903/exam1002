/** Prototype: make a new object by copying an existing object. */
public class Prototype {
    static class GameCharacter implements Cloneable {
        String name;
        String equipment;
        GameCharacter(String name, String equipment) { this.name = name; this.equipment = equipment; }
        public GameCharacter clone() {
            try { return (GameCharacter) super.clone(); }
            catch (CloneNotSupportedException error) { throw new AssertionError(error); }
        }
        public String toString() { return name + " with " + equipment; }
    }

    public static void main(String[] args) {
        GameCharacter original = new GameCharacter("Knight", "sword and shield");
        GameCharacter copy = original.clone();
        copy.name = "Training Knight";
        System.out.println(original);
        System.out.println(copy);
    }
}

