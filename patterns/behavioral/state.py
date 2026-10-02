"""State pattern: an order behaves differently in each state.

The important idea is that Order does not contain a large collection of
``if self.status == ...`` checks. The current state object handles the rules.
"""


class OrderState:
    """Base class documenting the actions an order can receive."""

    def pay(self, order): raise NotImplementedError
    def ship(self, order): raise NotImplementedError
    def cancel(self, order): raise NotImplementedError


class NewOrder(OrderState):
    """A new order can be paid or cancelled, but not shipped yet."""

    def pay(self, order):
        order.state = PaidOrder()
        return "Payment accepted; order is now paid"

    def ship(self, order):
        return "Cannot ship: the order has not been paid"

    def cancel(self, order):
        order.state = CancelledOrder()
        return "Order cancelled"


class PaidOrder(OrderState):
    """A paid order can be shipped, but it cannot be paid again."""

    def pay(self, order):
        return "Payment already received"

    def ship(self, order):
        order.state = ShippedOrder()
        return "Order shipped"

    def cancel(self, order):
        return "Cannot cancel: the order has already been paid"


class ShippedOrder(OrderState):
    """A shipped order cannot be paid, shipped, or cancelled again."""

    def pay(self, order):
        return "Cannot pay: the order has already been shipped"

    def ship(self, order):
        return "Order has already been shipped"

    def cancel(self, order):
        return "Cannot cancel: the order has already been shipped"


class CancelledOrder(OrderState):
    """A cancelled order is finished and cannot change anymore."""

    def pay(self, order):
        return "Cannot pay: the order was cancelled"

    def ship(self, order):
        return "Cannot ship: the order was cancelled"

    def cancel(self, order):
        return "Order is already cancelled"


class Order:
    """Context object: delegates each action to its current state."""

    def __init__(self):
        # The order starts in the NewOrder state.
        self.state = NewOrder()

    def pay(self):
        return self.state.pay(self)

    def ship(self):
        return self.state.ship(self)

    def cancel(self):
        return self.state.cancel(self)

    def state_name(self):
        return type(self.state).__name__


if __name__ == "__main__":
    order = Order()
    print("Initial state:", order.state_name())
    print(order.ship())  # Not allowed: the order is not paid.
    print(order.pay())   # State changes from NewOrder to PaidOrder.
    print("Current state:", order.state_name())
    print(order.ship())  # State changes from PaidOrder to ShippedOrder.
    print(order.cancel())
    print("Final state:", order.state_name())
