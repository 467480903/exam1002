/** Proxy: cache and control access to an expensive image service. */
public class Proxy {
    interface Image { String get(String name); }
    static class ImageService implements Image {
        public String get(String name) {
            System.out.println("Downloading " + name + "...");
            return "data for " + name;
        }
    }
    static class ImageProxy implements Image {
        private final ImageService service = new ImageService();
        private String cachedName;
        private String cachedData;
        public String get(String name) {
            if (!name.equals(cachedName)) {
                cachedName = name; cachedData = service.get(name);
            }
            return cachedData;
        }
    }

    public static void main(String[] args) {
        Image image = new ImageProxy();
        System.out.println(image.get("logo.png"));
        System.out.println(image.get("logo.png"));
    }
}

