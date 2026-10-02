/** Flyweight: share style data between many tree objects. */
import java.util.HashMap;
import java.util.Map;

public class Flyweight {
    static class TreeStyle {
        private static final Map<String, TreeStyle> STYLES = new HashMap<>();
        final String color;
        private TreeStyle(String color) { this.color = color; }
        static TreeStyle forColor(String color) {
            return STYLES.computeIfAbsent(color, TreeStyle::new);
        }
    }
    static class Tree {
        final int x, y;
        final TreeStyle style;
        Tree(int x, int y, String color) { this.x = x; this.y = y; style = TreeStyle.forColor(color); }
    }

    public static void main(String[] args) {
        Tree first = new Tree(1, 2, "green");
        Tree second = new Tree(10, 20, "green");
        System.out.println(first.style == second.style);
    }
}

