"""Visitor: add export operations to different document elements."""

class Paragraph:
    def __init__(self, text): self.text = text
    def accept(self, visitor): return visitor.visit_paragraph(self)


class Image:
    def __init__(self, filename): self.filename = filename
    def accept(self, visitor): return visitor.visit_image(self)


class HTMLExporter:
    def visit_paragraph(self, paragraph): return f"<p>{paragraph.text}</p>"
    def visit_image(self, image): return f'<img src="{image.filename}">'


if __name__ == "__main__":
    exporter = HTMLExporter()
    document = [Paragraph("Hello"), Image("logo.png")]
    print("\n".join(element.accept(exporter) for element in document))

