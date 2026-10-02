/** Strategy: choose a pricing algorithm at runtime. */
public class Strategy {
    interface PricingStrategy { double price(double amount); }
    static class RegularPrice implements PricingStrategy {
        public double price(double amount) { return amount; }
    }
    static class VipPrice implements PricingStrategy {
        public double price(double amount) { return amount * 0.8; }
    }
    static class Checkout {
        private final PricingStrategy strategy;
        Checkout(PricingStrategy strategy) { this.strategy = strategy; }
        double total(double amount) { return strategy.price(amount); }
    }

    public static void main(String[] args) {
        System.out.println(new Checkout(new RegularPrice()).total(100));
        System.out.println(new Checkout(new VipPrice()).total(100));
    }
}

