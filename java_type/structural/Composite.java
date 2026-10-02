/** Composite: files and folders expose the same display operation. */
import java.util.ArrayList;
import java.util.List;

public class Composite {
    interface Entry { String display(String indent); }
    static class FileEntry implements Entry {
        private final String name;
        FileEntry(String name) { this.name = name; }
        public String display(String indent) { return indent + name; }
    }
    static class Folder implements Entry {
        private final String name;
        private final List<Entry> children = new ArrayList<>();
        Folder(String name) { this.name = name; }
        Folder add(Entry child) { children.add(child); return this; }
        public String display(String indent) {
            StringBuilder result = new StringBuilder(indent).append(name);
            for (Entry child : children) result.append("\n").append(child.display(indent + "  "));
            return result.toString();
        }
    }

    public static void main(String[] args) {
        Folder project = new Folder("project").add(new FileEntry("README.md"))
                .add(new Folder("src").add(new FileEntry("Main.java")));
        System.out.println(project.display(""));
    }
}

