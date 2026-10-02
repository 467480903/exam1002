"""Strategy: choose a pricing algorithm at runtime."""

def regular_price(amount): return amount
def vip_price(amount): return amount * 0.8


class Checkout:
    def __init__(self, pricing_strategy): self.pricing_strategy = pricing_strategy
    def total(self, amount): return self.pricing_strategy(amount)


if __name__ == "__main__":
    print(Checkout(regular_price).total(100))
    print(Checkout(vip_price).total(100))

