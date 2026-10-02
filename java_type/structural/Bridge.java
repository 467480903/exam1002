/** Bridge: a remote control works with multiple device implementations. */
public class Bridge {
    interface Device { String on(); String off(); }
    static class TV implements Device {
        public String on() { return "TV on"; }
        public String off() { return "TV off"; }
    }
    static class Radio implements Device {
        public String on() { return "Radio on"; }
        public String off() { return "Radio off"; }
    }
    static class RemoteControl {
        private final Device device;
        RemoteControl(Device device) { this.device = device; }
        String turnOn() { return device.on(); }
        String turnOff() { return device.off(); }
    }

    public static void main(String[] args) {
        for (Device device : new Device[] { new TV(), new Radio() }) {
            RemoteControl remote = new RemoteControl(device);
            System.out.println(remote.turnOn() + "; " + remote.turnOff());
        }
    }
}

