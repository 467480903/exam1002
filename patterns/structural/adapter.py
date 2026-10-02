"""Adapter: make a legacy printer look like the new printer interface."""

class LegacyPrinter:
    def print_text(self, text):
        return f"Legacy printer -> {text}"


class PrinterAdapter:
    def __init__(self, legacy_printer):
        self.legacy_printer = legacy_printer

    def print(self, text):
        return self.legacy_printer.print_text(text)


if __name__ == "__main__":
    print(PrinterAdapter(LegacyPrinter()).print("Hello"))

