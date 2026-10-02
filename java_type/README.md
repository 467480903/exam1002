# Java Design Patterns

This folder contains standalone Java examples of the 23 classic Gang of Four design patterns.
Each file has a `main` method and can be compiled and run independently.

From the project root:

```bash
javac java_type/creational/Singleton.java
java -cp java_type/creational Singleton
```

The examples are grouped into:

- `creational` — object creation
- `structural` — object and class composition
- `behavioral` — communication and responsibility

## Pattern index

### Creational

Singleton, Factory Method, Abstract Factory, Builder, Prototype

### Structural

Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy

### Behavioral

Chain of Responsibility, Command, Interpreter, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor

Compile all examples at once with:

```bash
find java_type -name '*.java' -print0 | xargs -0 javac
```

