/** State: a door behaves differently when open or closed. */
public class State {
    interface DoorState { String open(Door door); String close(Door door); }
    static class Closed implements DoorState {
        public String open(Door door) { door.state = new Open(); return "Door opened"; }
        public String close(Door door) { return "Door is already closed"; }
    }
    static class Open implements DoorState {
        public String open(Door door) { return "Door is already open"; }
        public String close(Door door) { door.state = new Closed(); return "Door closed"; }
    }
    static class Door {
        private DoorState state = new Closed();
        String open() { return state.open(this); }
        String close() { return state.close(this); }
    }

    public static void main(String[] args) {
        Door door = new Door();
        System.out.println(door.close()); System.out.println(door.open()); System.out.println(door.close());
    }
}

