/** Decorator: add ingredients without changing the coffee class. */
public class Decorator {
    interface Coffee { double cost(); }
    static class BasicCoffee implements Coffee {
        public double cost() { return 3.0; }
    }
    static class Milk implements Coffee {
        private final Coffee coffee;
        Milk(Coffee coffee) { this.coffee = coffee; }
        public double cost() { return coffee.cost() + 1.0; }
    }
    static class Sugar implements Coffee {
        private final Coffee coffee;
        Sugar(Coffee coffee) { this.coffee = coffee; }
        public double cost() { return coffee.cost() + 0.5; }
    }

    public static void main(String[] args) {
        Coffee order = new Sugar(new Milk(new BasicCoffee()));
        System.out.printf("Coffee costs $%.2f%n", order.cost());
    }
}

