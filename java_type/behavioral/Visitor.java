/** Visitor: add export operations without changing document elements. */
public class Visitor {
    interface DocumentElement { String accept(Exporter exporter); }
    static class Paragraph implements DocumentElement {
        private final String text;
        Paragraph(String text) { this.text = text; }
        public String accept(Exporter exporter) { return exporter.visitParagraph(this); }
        String text() { return text; }
    }
    static class Image implements DocumentElement {
        private final String filename;
        Image(String filename) { this.filename = filename; }
        public String accept(Exporter exporter) { return exporter.visitImage(this); }
        String filename() { return filename; }
    }
    interface Exporter {
        String visitParagraph(Paragraph paragraph);
        String visitImage(Image image);
    }
    static class HtmlExporter implements Exporter {
        public String visitParagraph(Paragraph paragraph) { return "<p>" + paragraph.text() + "</p>"; }
        public String visitImage(Image image) { return "<img src=\"" + image.filename() + "\">"; }
    }

    public static void main(String[] args) {
        Exporter exporter = new HtmlExporter();
        System.out.println(new Paragraph("Hello").accept(exporter));
        System.out.println(new Image("logo.png").accept(exporter));
    }
}

