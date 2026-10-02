/** Command: turn an editor action into an object that can be undone. */
public class Command {
    static class Editor { String text = ""; }
    interface Action { void execute(); void undo(); }
    static class AppendCommand implements Action {
        private final Editor editor;
        private final String text;
        AppendCommand(Editor editor, String text) { this.editor = editor; this.text = text; }
        public void execute() { editor.text += text; }
        public void undo() { editor.text = editor.text.substring(0, editor.text.length() - text.length()); }
    }

    public static void main(String[] args) {
        Editor editor = new Editor();
        Action command = new AppendCommand(editor, "hello");
        command.execute(); System.out.println(editor.text);
        command.undo(); System.out.println("'" + editor.text + "'");
    }
}

