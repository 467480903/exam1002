/** Mediator: a chat room coordinates messages between users. */
import java.util.ArrayList;
import java.util.List;

public class Mediator {
    static class ChatRoom {
        private final List<User> users = new ArrayList<>();
        void add(User user) { users.add(user); user.room = this; }
        void broadcast(User sender, String message) {
            for (User user : users) if (user != sender)
                System.out.println(user.name + " receives: " + message);
        }
    }
    static class User {
        private final String name;
        private ChatRoom room;
        User(String name) { this.name = name; }
        void say(String message) { room.broadcast(this, message); }
    }

    public static void main(String[] args) {
        ChatRoom room = new ChatRoom();
        User alice = new User("Alice"), bob = new User("Bob");
        room.add(alice); room.add(bob); alice.say("Hello!");
    }
}

