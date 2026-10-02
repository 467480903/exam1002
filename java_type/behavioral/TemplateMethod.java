/** Template Method: the recipe stays fixed while steps vary. */
public class TemplateMethod {
    static abstract class Beverage {
        final String prepare() {
            return boilWater() + " -> " + brew() + " -> " + pour() + " -> " + addExtras();
        }
        String boilWater() { return "boil water"; }
        abstract String brew();
        String pour() { return "pour into cup"; }
        abstract String addExtras();
    }
    static class Tea extends Beverage {
        String brew() { return "steep tea"; }
        String addExtras() { return "add lemon"; }
    }

    public static void main(String[] args) {
        System.out.println(new Tea().prepare());
    }
}

