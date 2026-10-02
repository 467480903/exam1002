"""Proxy: cache and control access to an expensive image service."""

class ImageService:
    def download(self, name):
        print(f"Downloading {name}...")
        return f"data for {name}"


class ImageProxy:
    def __init__(self, service):
        self.service, self.cache = service, {}

    def get(self, name):
        if name not in self.cache:
            self.cache[name] = self.service.download(name)
        return self.cache[name]


if __name__ == "__main__":
    image = ImageProxy(ImageService())
    print(image.get("logo.png"))
    print(image.get("logo.png"))  # second call uses the cache

