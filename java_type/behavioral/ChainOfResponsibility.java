/** Chain of Responsibility: pass a request through handlers. */
public class ChainOfResponsibility {
    static abstract class Handler {
        private Handler next;
        Handler setNext(Handler next) { this.next = next; return next; }
        String pass(String request) { return next == null ? "No handler available" : next.pass(request); }
    }
    static class FaqHandler extends Handler {
        String pass(String request) { return request.equals("password") ? "FAQ answered" : super.pass(request); }
    }
    static class HumanHandler extends Handler {
        String pass(String request) { return request.equals("billing") ? "Human support ticket created" : super.pass(request); }
    }

    public static void main(String[] args) {
        Handler first = new FaqHandler();
        first.setNext(new HumanHandler());
        for (String request : new String[] { "password", "billing", "unknown" })
            System.out.println(request + " -> " + first.pass(request));
    }
}

