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

## 5. Gotchas and Limitations

1. **`this` cannot be used in static methods** — static methods belong to the class constructor, not instances; `this` in a static method refers to the constructor type, and `this` as a return type in a static context has different and often less useful semantics.
2. **Requires subclassing or interface implementation** — polymorphic `this` only matters when there is a subclass or implementor; in a standalone class with no subclasses, `this` is equivalent to the concrete class type.
3. **Copying instances breaks `this`** — if a method creates a new instance using `new (this.constructor as new () => this)()`, TypeScript cannot verify the constructor is actually the subclass constructor at compile time; this pattern requires `as` casts.
4. **`this is T` requires `T` to be a subtype** — the predicated type must be assignable from the declared type of `this`; `this is string` in a class method is always an error.
5. **Return type `this` is widened on assignment** — assigning a method that returns `this` to a variable of a base class function type loses the polymorphism: `const fn: (n: string) => Builder = new UserQueryBuilder().where` collapses `this` to `Builder`.
6. **Mixins and `this` interact subtly** — mixin patterns that merge multiple class bodies can cause `this` to resolve to unexpected types; test mixin chains explicitly when polymorphic `this` methods are involved.

## 6. Use-Case Cross-References

- [-> UC-09](../usecases/UC09-builder-config.md) Implement fluent builder chains where subclass methods remain visible after calling base class setters, using polymorphic `this` as the return type
