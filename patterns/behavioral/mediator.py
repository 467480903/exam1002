"""Mediator: a chat room coordinates messages between users."""

class ChatRoom:
    def __init__(self): self.users = []
    def add(self, user): self.users.append(user); user.room = self
    def broadcast(self, sender, message):
        return [f"{user.name} receives: {message}" for user in self.users if user is not sender]


class User:
    def __init__(self, name): self.name, self.room = name, None
    def say(self, message): return self.room.broadcast(self, message)


if __name__ == "__main__":
    room, alice, bob = ChatRoom(), User("Alice"), User("Bob")
    room.add(alice); room.add(bob)
    print(alice.say("Hello!"))

