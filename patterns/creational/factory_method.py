"""Factory Method: subclasses decide which notification to create."""

from abc import ABC, abstractmethod


class Notification(ABC):
    @abstractmethod
    def send(self, message): ...


class Email(Notification):
    def send(self, message):
        return f"Email: {message}"


class SMS(Notification):
    def send(self, message):
        return f"SMS: {message}"


class NotificationService(ABC):
    @abstractmethod
    def create_notification(self): ...

    def notify(self, message):
        return self.create_notification().send(message)


class EmailService(NotificationService):
    def create_notification(self):
        return Email()


class SMSService(NotificationService):
    def create_notification(self):
        return SMS()


if __name__ == "__main__":
    for service in (EmailService(), SMSService()):
        print(service.notify("Your order shipped"))

