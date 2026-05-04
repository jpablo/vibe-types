// eslint-plugin/tests/rules/no-kitchen-sink-variants.test.ts
import { ruleTester } from "../helpers/rule-tester";
import rule from "../../src/rules/no-kitchen-sink-variants";

ruleTester.run("no-kitchen-sink-variants", rule, {
  valid: [
    `type ApiResponse =
      | { kind: "user"; name: string; email: string; age: number }
      | { kind: "post"; title: string; content: string; authorId: number };`,
    `type State =
      | { kind: "idle" }
      | { kind: "loading" }
      | { kind: "success"; data: unknown };`,
  ],
  invalid: [
    {
      code: `type ApiResponse =
      | { kind: "user"; name: string; email: string; age: number; role: string; avatar: string }
      | { kind: "post"; title: string; content: string; authorId: number; tags: string[]; views: number };`,
      errors: [
        { messageId: "tooManyFields" },
        { messageId: "tooManyFields" },
      ],
    },
    {
      code: `type Config =
      | { kind: "default"; isEnabled: boolean; name: string; description: string; timeout: number; retries: number };`,
      errors: [{ messageId: "tooManyFields" }],
    },
  ],
});
