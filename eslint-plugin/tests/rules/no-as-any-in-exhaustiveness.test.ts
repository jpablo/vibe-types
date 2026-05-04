import { ruleTester } from "../helpers/rule-tester";
import rule from "../../src/rules/no-as-any-in-exhaustiveness";

ruleTester.run("no-as-any-in-exhaustiveness", rule, {
  valid: [
    `function handle(e: Event) {
  switch (e.kind) {
    case "click": console.log(e.x); break;
    default: assertNever(e);
  }
}`,
    `function process(state: State) {
  switch (state) {
    case "loading": break;
    case "idle": break;
    default: throw new Error("Unknown state");
  }
}`,
  ],
  invalid: [
    {
      code: `function handle(e: Event) {
  switch (e.kind) {
    case "click": console.log(e.x); break;
    default: (e as any).foo();
  }
}`,
      errors: [{ messageId: "noAsAnyInDefault" }],
    },
    {
      code: `type State = "a" | "b";
function test(s: State) {
  switch (s) {
    case "a": break;
    case "b": break;
    default: const x = s as any;
  }
}`,
      errors: [{ messageId: "noAsAnyInDefault" }],
    },
  ],
});
