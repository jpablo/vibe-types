import { ruleTester } from "../helpers/rule-tester";
import rule from "../../src/rules/require-exhaustiveness-check";

ruleTester.run("require-exhaustiveness-check", rule, {
  valid: [
    `type Event = { kind: "click" | "hover" };

function handle(e: Event) {
  switch (e.kind) {
    case "click": console.log(e.x); break;
    default: assertNever(e);
  }
}`,
    `type Status = { kind: "idle" | "active" };

function process(s: Status) {
  switch (s.kind) {
    case "idle": return;
    case "active": return;
    default: throw new Error(s.kind);
  }
}`,
    `const values = [1, 2, 3];
for (const v of values) {
  switch (v) {
    case 1: break;
  }
}`,
  ],
  invalid: [
    {
      code: `type Event = { kind: "click" | "hover" };

function handle(e: Event) {
  switch (e.kind) {
    case "click": console.log(e.x); break;
  }
}`,
      errors: [{ messageId: "missingExhaustiveness" }],
    },
    {
      code: `type Status = { kind: "idle" | "active" };

function process(s: Status) {
  switch (s.kind) {
    case "idle": return;
    case "active": console.log(s);
  }
}`,
      errors: [{ messageId: "missingExhaustiveness" }],
    },
    {
      code: `function handle(status: { kind: "a" | "b" }) {
  switch (status.kind) {
    case "a": break;
  }
}`,
      errors: [{ messageId: "missingExhaustiveness" }],
    },
  ],
});
