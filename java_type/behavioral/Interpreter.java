/** Interpreter: evaluate a tiny expression language. */
public class Interpreter {
    interface Expression { int interpret(); }
    static class Number implements Expression {
        private final int value;
        Number(int value) { this.value = value; }
        public int interpret() { return value; }
    }
    static class Add implements Expression {
        private final Expression left, right;
        Add(Expression left, Expression right) { this.left = left; this.right = right; }
        public int interpret() { return left.interpret() + right.interpret(); }
    }

    public static void main(String[] args) {
        Expression expression = new Add(new Number(2), new Add(new Number(3), new Number(4)));
        System.out.println(expression.interpret());
    }
}

