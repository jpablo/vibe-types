# Polymorphic `this` Type

> **Since:** TypeScript 1.7

## 1. What It Is

In TypeScript, using `this` as a return type annotation in a method declaration creates a **polymorphic `this` type**: it represents the type of the receiver, resolved to the actual concrete class (or interface implementor) at each call site. When a base class method returns `this`, calling that method on an instance of a derived class returns the derived class type, not the base class type. This is the key mechanism for **fluent builder chains** where the subclass's own methods remain visible after calling a base class method. TypeScript also supports `this is T` as a **type predicate return type** for methods — a way to narrow the class instance type within the calling scope when the method returns `true`.

## 2. What Constraint It Lets You Express

**Methods return the receiver's own type; builder chains preserve the full subclass type through every chained call, so derived class methods remain accessible.**

- A base class `Builder` with `setName(n: string): this` ensures that `DerivedBuilder.setName("x")` returns `DerivedBuilder`, not `Builder`.
- Without polymorphic `this`, a base class method returning `Builder` would hide all `DerivedBuilder`-specific methods after the first chained call.
- `this is T` predicates allow methods like `isAdmin(): this is AdminUser` to narrow class instances without external helper functions.

## 3. Minimal Snippet

```typescript
// --- Polymorphic this in a fluent builder ---
class QueryBuilder {
  protected filters: string[] = [];
  protected limitValue?: number;

  where(condition: string): this {
    this.filters.push(condition);
    return this; // returns the concrete subclass type
  }

  limit(n: number): this {
    this.limitValue = n;
    return this;
  }

  build(): string {
    const where = this.filters.length
      ? `WHERE ${this.filters.join(" AND ")}`
      : "";
    const limit = this.limitValue != null ? ` LIMIT ${this.limitValue}` : "";
    return `SELECT * FROM table ${where}${limit}`.trim();
  }
}

class UserQueryBuilder extends QueryBuilder {
  onlyActive(): this {
    return this.where("active = true");
  }
}

const query = new UserQueryBuilder()
  .onlyActive()    // OK — returns UserQueryBuilder
  .where("age > 18")  // OK — returns UserQueryBuilder
  .limit(10)       // OK — returns UserQueryBuilder
  .build();        // OK — returns string

// Without `this` return type, .onlyActive() would return QueryBuilder
// and .limit(10) would return QueryBuilder, losing .onlyActive() in subsequent calls.

// --- this is T type predicate ---
class User {
  constructor(
    public name: string,
    public role: "user" | "admin"
  ) {}

  isAdmin(): this is AdminUser {
    return this.role === "admin";
  }
}

class AdminUser extends User {
  constructor(name: string) {
    super(name, "admin");
  }

  deleteAll(): void {
    console.log("Deleting all records...");
  }
}

function process(user: User) {
  if (user.isAdmin()) {
    user.deleteAll(); // OK — narrowed to AdminUser
  }
}
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Callable Typing** [-> T22](T22-callable-typing.md) | Polymorphic `this` is a special return type for callable methods; it interacts with overload resolution — a base class overload returning `this` must be compatible with the derived class's overloaded return type. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | `this is T` predicates plug directly into TypeScript's control-flow analysis; after an `if (x.isAdmin())` call, the compiler narrows `x` to `AdminUser` in the true branch, exactly like a standalone type predicate function. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | Polymorphic `this` and generic constraints interact when a generic method returns `this`; the generic parameter is resolved against the concrete subclass, allowing parameterized builders where type parameters accumulate across chained calls. |
| **Structural Typing** [-> T07](T07-structural-typing.md) | `this` can appear in interface method signatures (`clone(): this`), constraining each implementor to return its own concrete type — analogous to Rust's `Self` in trait definitions and Python's `Self` in Protocols. |

## 5. Gotchas and Limitations

1. **`this` cannot be used in static methods** — static methods belong to the class constructor, not instances; `this` in a static method refers to the constructor type, and `this` as a return type in a static context has different and often less useful semantics.
2. **Requires subclassing or interface implementation** — polymorphic `this` only matters when there is a subclass or implementor; in a standalone class with no subclasses, `this` is equivalent to the concrete class type.
3. **Copying instances breaks `this`** — if a method creates a new instance using `new (this.constructor as new () => this)()`, TypeScript cannot verify the constructor is actually the subclass constructor at compile time; this pattern requires `as` casts.
4. **`this is T` requires `T` to be a subtype** — the predicated type must be assignable from the declared type of `this`; `this is string` in a class method is always an error.
5. **Return type `this` is widened on assignment** — assigning a method that returns `this` to a variable of a base class function type loses the polymorphism: `const fn: (n: string) => Builder = new UserQueryBuilder().where` collapses `this` to `Builder`.
6. **Mixins and `this` interact subtly** — mixin patterns that merge multiple class bodies can cause `this` to resolve to unexpected types; test mixin chains explicitly when polymorphic `this` methods are involved.

## 6. Beginner Mental Model

Think of `this` as a pronoun that means "my own type right now." When a `QueryBuilder` method says `: this`, it promises to return a `QueryBuilder`. When `UserQueryBuilder` inherits that method, `this` automatically means `UserQueryBuilder` — not `QueryBuilder`.

Compared to other languages: Python 3.11 added an explicit `Self` keyword (PEP 673) for the same purpose. Rust uses `Self` as a keyword inside `impl` blocks and trait definitions. TypeScript's polymorphic `this` achieves the same result without a separate keyword — the type of `this` is already the concrete type, and annotating a return as `this` tells the checker to preserve it.

The old workaround (before polymorphic `this`) was a bound generic parameter:

```typescript
// Old pattern — verbose and requires an extra type parameter at every use site
class QueryBuilderOld<T extends QueryBuilderOld<T>> {
  where(condition: string): T {
    // ...
    return this as unknown as T; // requires unsafe cast
  }
}

// Polymorphic `this` replaces this entirely — no extra type parameter needed
class QueryBuilderNew {
  where(condition: string): this {
    // ...
    return this; // no cast required
  }
}
```

## 7. Example A — Fluent Builder Preserving Subclass Methods

```typescript
class RequestBuilder {
  protected url = "";
  protected method = "GET";
  protected headers: Record<string, string> = {};

  withUrl(url: string): this {
    this.url = url;
    return this;
  }

  withMethod(method: string): this {
    this.method = method;
    return this;
  }

  withHeader(key: string, value: string): this {
    this.headers[key] = value;
    return this;
  }

  build(): Request {
    return new Request(this.url, { method: this.method, headers: this.headers });
  }
}

class AuthenticatedRequestBuilder extends RequestBuilder {
  private token = "";

  withBearerToken(token: string): this {
    this.token = token;
    return this.withHeader("Authorization", `Bearer ${token}`);
  }
}

// Every chained call returns AuthenticatedRequestBuilder, not RequestBuilder
const req = new AuthenticatedRequestBuilder()
  .withUrl("https://api.example.com/data")  // AuthenticatedRequestBuilder
  .withBearerToken("secret")               // AuthenticatedRequestBuilder
  .withMethod("POST")                      // AuthenticatedRequestBuilder
  .build();                                // Request

// Without polymorphic `this`, .withUrl() would return RequestBuilder
// and .withBearerToken() would not exist on it — compile error.
```

## 8. Example B — `this` in Interfaces and the `this` Parameter

### `this` in interface declarations

Interface methods can use `this` as a return type, constraining each implementor to return its own concrete type — the structural-typing analogue of Rust's `Self` in trait definitions:

```typescript
interface Cloneable {
  clone(): this; // each implementor must return its own type, not the interface
}

interface Serializable {
  withId(id: string): this;
}

class Document implements Cloneable, Serializable {
  constructor(
    public content: string,
    public id = ""
  ) {}

  clone(): this {
    // Object.assign preserves the subclass type at runtime;
    // the cast is necessary because the compiler can't verify
    // that Object.assign produces `this` exactly.
    return Object.assign(Object.create(Object.getPrototypeOf(this)), this) as this;
  }

  withId(id: string): this {
    const copy = this.clone();
    copy.id = id;
    return copy;
  }
}

class VersionedDocument extends Document {
  constructor(content: string, public version = 1) {
    super(content);
  }
}

const original = new VersionedDocument("hello", 2);
const copy = original.withId("doc-42"); // VersionedDocument, not Document
copy.version;                           // OK — subclass type preserved
```

### The `this` parameter — constraining the call context

TypeScript supports a fake `this` parameter (always the first, erased at runtime) that constrains what `this` must be at the call site. This is distinct from polymorphic `this` return types but is closely related:

```typescript
// Constrains that `greet` can only be called on objects with a `name`
function greet(this: { name: string }): string {
  return `Hello, ${this.name}`;
}

// Attaching an event listener with a specific `this` context
function handleClick(this: HTMLButtonElement, event: MouseEvent): void {
  this.disabled = true; // compiler knows `this` is HTMLButtonElement
}

// Preventing a method from being detached and called without context
class Counter {
  private count = 0;

  increment(this: Counter): void {
    this.count++;
  }
}

const c = new Counter();
const fn = c.increment;
fn(); // error: The 'this' context of type 'void' is not assignable
      //        to method's 'this' of type 'Counter'
```

## 9. Common Type-Checker Errors

### `error TS2526: A 'this' type is available only in a non-static member of a class or interface.`

`this` was used as a return type in a static method. Static methods return the constructor, not an instance. Use `InstanceType<typeof this>` or a generic `this: T` parameter instead:

```typescript
class Base {
  // error: 'this' type in a static method
  // static create(): this { return new this(); }

  // correct: use a generic `this` parameter
  static create<T extends typeof Base>(this: T): InstanceType<T> {
    return new this() as InstanceType<T>;
  }
}

class Derived extends Base {}
const d = Derived.create(); // InstanceType<typeof Derived> = Derived
```

### `error TS2677: A type predicate's type must be assignable from its parameter type`

The type in `this is T` is not a subtype of the class. The predicated type must extend the class:

```typescript
class Animal {
  // error: string is not assignable from Animal
  // isString(): this is string { return false; }

  // correct: Dog must extend Animal
  isDog(): this is Dog { return this instanceof Dog; }
}
class Dog extends Animal {}
```

### `error TS2416: Property 'x' in type 'Derived' is not assignable to the same property in base type 'Base'`

A method in a derived class overrides a base method that returns `this`, but the derived override's return type is too narrow or too wide:

```typescript
class Base {
  clone(): this { return this; }
}

class Derived extends Base {
  // error: 'Base' is not assignable to 'this'
  // clone(): Base { return new Base(); }

  // correct: either omit the return annotation (infer `this`) or keep `this`
  clone(): this { return super.clone(); }
}
```

### Widening `this` on assignment loses polymorphism

```typescript
class Builder {
  set(name: string): this { return this; }
}

class SpecialBuilder extends Builder {
  special(): this { return this; }
}

// Assigning the method to a base-typed variable collapses `this` to Builder
const fn: (name: string) => Builder = new SpecialBuilder().set;
// fn("x").special(); // error — Builder has no .special()
```

## 10. Use-Case Cross-References

- [-> UC-09](../usecases/UC09-builder-config.md) Implement fluent builder chains where subclass methods remain visible after calling base class setters, using polymorphic `this` as the return type
- [-> UC-07](../usecases/UC07-callable-contracts.md) Callable contracts and fluent interfaces that preserve subclass types through method chains

## Source Anchors

- [TypeScript Handbook — Polymorphic `this` types](https://www.typescriptlang.org/docs/handbook/2/classes.html#this-types)
- [TypeScript Handbook — `this` parameter](https://www.typescriptlang.org/docs/handbook/2/functions.html#declaring-this-in-a-function)
- [TypeScript Handbook — Type predicates (`this is T`)](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#using-type-predicates)
- TypeScript source: `src/compiler/checker.ts` — `getThisType`, `isThisType`
