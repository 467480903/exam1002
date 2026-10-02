# Python Design Patterns

These are small, runnable examples of the 23 classic Gang of Four (GoF) design patterns.
They are intentionally simple so you can focus on the idea rather than framework code.

## Categories

- `creational/` — ways to create objects
- `structural/` — ways to combine objects and classes
- `behavioral/` — ways for objects to communicate and share responsibilities

Run any example from the project root:

```bash
python patterns/creational/factory_method.py
```

The examples use only Python's standard library. Read the source comments, change the
inputs in `main()`, and run the file again to experiment.

## Pattern index

### Creational

1. Singleton — one shared instance
2. Factory Method — subclasses choose the product
3. Abstract Factory — families of related products
4. Builder — construct a complex object step by step
5. Prototype — copy an existing object

### Structural

6. Adapter — convert one interface into another
7. Bridge — separate abstraction from implementation
8. Composite — treat objects and groups uniformly
9. Decorator — add behavior without changing the original class
10. Facade — provide a simple interface to a complex subsystem
11. Flyweight — share common object data
12. Proxy — stand in for and control access to another object

### Behavioral

13. Chain of Responsibility — pass a request through handlers
14. Command — turn a request into an object
15. Interpreter — evaluate a small language or grammar
16. Iterator — traverse a collection without exposing its internals
17. Mediator — centralize communication
18. Memento — save and restore state
19. Observer — notify subscribers about changes
20. State — change behavior when state changes
21. Strategy — swap an algorithm at runtime
22. Template Method — define algorithm steps, customize selected steps
23. Visitor — add operations without changing element classes

## Mermaid diagrams

The diagrams below show the main relationship in each pattern. In Mermaid, an arrow
means “uses”, “creates”, or “implements”, depending on the pattern.

### Creational patterns

#### 1. Singleton

```mermaid
flowchart LR
    A[Client] --> B[AppConfig.get_instance]
    B --> C{One shared instance}
    C --> B
```

#### 2. Factory Method

```mermaid
classDiagram
    NotificationService <|-- EmailService
    NotificationService <|-- SMSService
    Notification <|.. Email
    Notification <|.. SMS
    EmailService ..> Email : creates
    SMSService ..> SMS : creates
    class NotificationService { +notify(message) }
    class Notification { <<interface>> +send(message) }
```

#### 3. Abstract Factory

```mermaid
flowchart LR
    Client --> LightFactory
    Client --> DarkFactory
    LightFactory --> LightButton
    LightFactory --> LightCheckbox
    DarkFactory --> DarkButton
    DarkFactory --> DarkCheckbox
```

#### 4. Builder

```mermaid
flowchart LR
    Client --> Builder
    Builder -->|step 1| Title
    Builder -->|step 2| Sections
    Builder -->|build| Report
```

#### 5. Prototype

```mermaid
flowchart LR
    Original[Existing object] -->|clone| Copy[New object with copied data]
```

### Structural patterns

#### 6. Adapter

```mermaid
flowchart LR
    Client -->|new interface| Adapter
    Adapter -->|converts call| Legacy[Legacy service]
```

#### 7. Bridge

```mermaid
flowchart LR
    Remote[Remote control abstraction] --> Device[Device interface]
    Device --> TV
    Device --> Radio
```

#### 8. Composite

```mermaid
flowchart TD
    Root[Folder] --> File1[File]
    Root --> Sub[Folder]
    Sub --> File2[File]
```

#### 9. Decorator

```mermaid
flowchart LR
    Coffee --> Milk --> Sugar
    Sugar --> Result[Coffee with extra behavior]
```

#### 10. Facade

```mermaid
flowchart LR
    Client --> Facade
    Facade --> Projector
    Facade --> Sound[Sound system]
    Facade --> Player
```

#### 11. Flyweight

```mermaid
flowchart TD
    Tree1[Tree at position 1] --> Shared[Shared green TreeStyle]
    Tree2[Tree at position 2] --> Shared
```

#### 12. Proxy

```mermaid
flowchart LR
    Client --> Proxy
    Proxy -->|cache miss| Real[Real image service]
    Proxy -->|cache hit| Cache[Cached result]
```

### Behavioral patterns

#### 13. Chain of Responsibility

```mermaid
flowchart LR
    Request --> FAQ[FAQ handler]
    FAQ --> Human[Human handler]
    Human --> End[Handled or rejected]
```

#### 14. Command

```mermaid
flowchart LR
    User --> Invoker
    Invoker --> Command
    Command --> Editor
    Command -.->|undo| Editor
```

#### 15. Interpreter

```mermaid
flowchart TD
    Expression[2 + 3] --> Add
    Add --> Number2[2]
    Add --> Number3[3]
    Add --> Result[interpret() = 5]
```

#### 16. Iterator

```mermaid
flowchart LR
    Client --> Iterator
    Iterator --> Song1[Song 1]
    Iterator --> Song2[Song 2]
    Iterator --> Song3[Song 3]
```

#### 17. Mediator

```mermaid
flowchart TD
    Alice[User Alice] --> Room[Chat room mediator]
    Bob[User Bob] --> Room
    Room --> Alice
    Room --> Bob
```

#### 18. Memento

```mermaid
flowchart LR
    Editor -->|save| Memento[Saved state]
    Memento -->|restore| Editor
```

#### 19. Observer

```mermaid
flowchart LR
    Publisher --> Observer1[Email subscriber]
    Publisher --> Observer2[Mobile subscriber]
    Publisher -->|state changed| Observer1
    Publisher -->|state changed| Observer2
```

#### 20. State

```mermaid
stateDiagram-v2
    [*] --> Closed
    Closed --> Open: open()
    Open --> Closed: close()
```

#### 21. Strategy

```mermaid
flowchart LR
    Checkout --> Strategy
    Strategy --> Regular[Regular pricing]
    Strategy --> VIP[VIP pricing]
```

#### 22. Template Method

```mermaid
flowchart TD
    Recipe[prepare()] --> Boil[boil water]
    Boil --> Brew[brew - customized]
    Brew --> Pour[pour]
    Pour --> Extras[add extras - customized]
```

#### 23. Visitor

```mermaid
flowchart LR
    Visitor[HTML exporter] --> Paragraph
    Visitor --> Image
    Document[Document elements] --> Visitor
```
