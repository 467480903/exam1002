"""Chain of Responsibility: handlers process a support request in order."""

class Handler:
    def __init__(self, next_handler=None): self.next = next_handler
    def handle(self, request):
        if self.next: return self.next.handle(request)
        return "No handler available"


class FAQHandler(Handler):
    def handle(self, request):
        return "FAQ answered" if request == "password" else super().handle(request)


class HumanHandler(Handler):
    def handle(self, request):
        return "Human support ticket created" if request == "billing" else super().handle(request)


if __name__ == "__main__":
    chain = FAQHandler(HumanHandler())
    for request in ("password", "billing", "unknown"):
        print(request, "->", chain.handle(request))

