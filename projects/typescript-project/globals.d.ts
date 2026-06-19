// Minimal ambient globals for verifying type-system documentation snippets.
//
// The reference project compiles snippets with `lib: ES2022` and NO `DOM`, so
// that domain type names the docs legitimately define (Event, Comment,
// Selection, Permissions, ...) don't collide with browser globals. `console`
// is the one runtime global the snippets commonly use, so declare just that.
// verify_typescript.py passes this file alongside each snippet.

declare var console: {
  log(...args: unknown[]): void;
  error(...args: unknown[]): void;
  warn(...args: unknown[]): void;
  info(...args: unknown[]): void;
  debug(...args: unknown[]): void;
};
