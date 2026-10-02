/** Builder: construct a report step by step. */
public class Builder {
    static class Report {
        private final String title;
        private final String sections;
        private final String footer;

        private Report(ReportBuilder builder) {
            title = builder.title; sections = builder.sections.toString(); footer = builder.footer;
        }
        public String toString() { return title + ": " + sections + " (" + footer + ")"; }
    }
    static class ReportBuilder {
        private String title = "Untitled";
        private final StringBuilder sections = new StringBuilder();
        private String footer = "";
        ReportBuilder title(String value) { title = value; return this; }
        ReportBuilder section(String value) {
            if (sections.length() > 0) sections.append(" | ");
            sections.append(value); return this;
        }
        ReportBuilder footer(String value) { footer = value; return this; }
        Report build() { return new Report(this); }
    }

    public static void main(String[] args) {
        Report report = new ReportBuilder().title("Sales").section("January")
                .section("February").footer("Confidential").build();
        System.out.println(report);
    }
}

