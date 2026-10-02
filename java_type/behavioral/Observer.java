/** Observer: notify subscribers when a publisher changes. */
import java.util.ArrayList;
import java.util.List;

public class Observer {
    interface Subscriber { void update(String news); }
    static class NewsPublisher {
        private final List<Subscriber> subscribers = new ArrayList<>();
        void subscribe(Subscriber subscriber) { subscribers.add(subscriber); }
        void publish(String news) { for (Subscriber subscriber : subscribers) subscriber.update(news); }
    }
    static class EmailSubscriber implements Subscriber {
        private final String address;
        EmailSubscriber(String address) { this.address = address; }
        public void update(String news) { System.out.println("Email to " + address + ": " + news); }
    }

    public static void main(String[] args) {
        NewsPublisher publisher = new NewsPublisher();
        publisher.subscribe(new EmailSubscriber("reader@example.com"));
        publisher.publish("New article published");
    }
}

