/** Adapter: make a legacy printer fit a modern interface. */
public class Adapter {
    interface Printer { String print(String text); }
    static class LegacyPrinter {
        String printText(String text) { return "Legacy printer -> " + text; }
    }
    static class PrinterAdapter implements Printer {
        private final LegacyPrinter printer;
        PrinterAdapter(LegacyPrinter printer) { this.printer = printer; }
        public String print(String text) { return printer.printText(text); }
    }

    public static void main(String[] args) {
        System.out.println(new PrinterAdapter(new LegacyPrinter()).print("Hello"));
    }
}

