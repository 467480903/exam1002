"""Singleton: make one shared configuration object."""

class AppConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.debug = False
        return cls._instance


if __name__ == "__main__":
    first = AppConfig()
    first.debug = True
    second = AppConfig()
    print(second.debug)          # True: both names point to one object
    print(first is second)       # True

