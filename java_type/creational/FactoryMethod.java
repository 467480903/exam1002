/** Factory Method: subclasses decide which notification to create. */
public class FactoryMethod {
    // An interface is a contract. Every Notification must have send(...).
    // It does not say how send works; Email and Sms decide that themselves.
    interface Notification {
        String send(String message);
    }

    // A concrete product: one possible kind of Notification.
    static class Email implements Notification {
        // "public" is required because this method implements the interface method.
        public String send(String message) { return "Email: " + message; }
    }

    // Another concrete product with the same interface, but different behavior.
    static class Sms implements Notification {
        public String send(String message) { return "SMS: " + message; }
    }

    // This is the creator/factory part of the example.
    // It knows how to use a Notification, but not which concrete type it is.
    abstract static class NotificationService {
        // Each subclass must implement this factory method.
        // The return type is the interface, so the caller does not depend on Email or Sms.
        protected abstract Notification createNotification();

        // This shared business operation uses the object created by the factory method.
        // Java calls createNotification() on the actual subclass at runtime.
        String notifyUser(String message) { return createNotification().send(message); }
    }

    // Concrete creator: this service chooses Email.
    static class EmailService extends NotificationService {
        protected Notification createNotification() { return new Email(); }
    }

    // Concrete creator: this service chooses Sms.
    static class SmsService extends NotificationService {
        protected Notification createNotification() { return new Sms(); }
    }

    public static void main(String[] args) {
        // We do not create FactoryMethod here because FactoryMethod is only
        // the outer demo/container class. It is not the factory object.
        // The actual factory objects are EmailService and SmsService.

        // new EmailService() creates a service object.
        // notifyUser(...) internally calls createNotification(), which returns new Email().
        System.out.println(new EmailService().notifyUser("Order shipped"));

        // This one creates SmsService, whose factory method returns new Sms().
        System.out.println(new SmsService().notifyUser("Order shipped"));
    }
}
