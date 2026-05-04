import { ruleTester } from "../helpers/rule-tester";
import rule from "../../src/rules/no-silent-fallback-in-default-case";

ruleTester.run("no-silent-fallback-in-default-case", rule, {
  valid: [
    `function handle(e: Event) {
      switch (e.kind) {
        case "click": console.log(e.x); break;
        default: assertNever(e);
      }
    }`,
    `function handle(e: Event) {
      switch (e.kind) {
        case "click": console.log(e.x); break;
        default: throw new Error("Unhandled case");
      }
    }`,
    `function handle(e: Event) {
      switch (e.kind) {
        case "click": console.log(e.x); break;
      }
    }`,
  ],
  invalid: [
    {
      code: `function handle(e: Event) {
        switch (e.kind) {
          case "click": console.log(e.x); break;
          default: /* oh no, scroll is ignored! */
        }
      }`,
      errors: [{ messageId: "silentDefaultCase" }],
    },
    {
      code: `function handle(e: Event) {
        switch (e.kind) {
          case "click": console.log(e.x); break;
          default: break;
        }
      }`,
      errors: [{ messageId: "silentDefaultCase" }],
    },
  ],
});
