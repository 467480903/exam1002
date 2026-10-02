"""Observer: subscribers are notified when a news publisher changes."""

class NewsPublisher:
    def __init__(self): self.subscribers, self.latest = [], None
    def subscribe(self, subscriber): self.subscribers.append(subscriber)
    def publish(self, news):
        self.latest = news
        for subscriber in self.subscribers: subscriber.update(news)


class EmailSubscriber:
    def __init__(self, address): self.address = address
    def update(self, news): print(f"Email to {self.address}: {news}")


if __name__ == "__main__":
    publisher = NewsPublisher()
    publisher.subscribe(EmailSubscriber("reader@example.com"))
    publisher.publish("New article published")

