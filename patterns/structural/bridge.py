"""Bridge: a remote control abstraction works with different devices."""

class TV:
    def on(self): return "TV on"
    def off(self): return "TV off"


class Radio:
    def on(self): return "Radio on"
    def off(self): return "Radio off"


class RemoteControl:
    def __init__(self, device):
        self.device = device

    def turn_on(self): return self.device.on()
    def turn_off(self): return self.device.off()


if __name__ == "__main__":
    for device in (TV(), Radio()):
        remote = RemoteControl(device)
        print(remote.turn_on(), ";", remote.turn_off())

