/** Memento: save and restore an editor's state. */
public class Memento {
    static class Editor {
        private String text = "";
        void setText(String text) { this.text = text; }
        String getText() { return text; }
        String save() { return text; }
        void restore(String savedState) { text = savedState; }
    }

    public static void main(String[] args) {
        Editor editor = new Editor();
        editor.setText("version 1");
        String saved = editor.save();
        editor.setText("version 2");
        editor.restore(saved);
        System.out.println(editor.getText());
    }
}

