"""Builder: assemble a report one part at a time."""

class Report:
    def __init__(self, title, sections, footer):
        self.title, self.sections, self.footer = title, sections, footer

    def __str__(self):
        return f"{self.title}: {' | '.join(self.sections)} ({self.footer})"


class ReportBuilder:
    def __init__(self):
        self.title = "Untitled"
        self.sections = []
        self.footer = ""

    def with_title(self, title):
        self.title = title
        return self

    def add_section(self, section):
        self.sections.append(section)
        return self

    def with_footer(self, footer):
        self.footer = footer
        return self

    def build(self):
        return Report(self.title, self.sections, self.footer)


if __name__ == "__main__":
    report = (ReportBuilder().with_title("Sales")
              .add_section("January")
              .add_section("February")
              .with_footer("Confidential").build())
    print(report)

