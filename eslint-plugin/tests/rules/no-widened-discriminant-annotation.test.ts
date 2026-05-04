import { ruleTester } from "../helpers/rule-tester";
import rule from "../../src/rules/no-widened-discriminant-annotation";

ruleTester.run("no-widened-discriminant-annotation", rule, {
  valid: [
    `type PaymentStatus =
      | { kind: "pending", amount: number }
      | { kind: "completed", amount: number };

    const good = { kind: "pending", amount: 100 } satisfies PaymentStatus;`,
    `type PaymentStatus =
      | { kind: "pending", amount: number }
      | { kind: "completed", amount: number };

    const withAnnotation: PaymentStatus = { kind: "pending", amount: 100 };`,
    `const withConstAs = { kind: "pending", amount: 100 } as const;`,
    `const noDiscriminant = { name: "test", count: 5 };`,
    `const nonStringDiscriminant = { type: 123, value: "hello" };`,
    `function returnsObject() {
      return { kind: "pending", amount: 100 };
    }`,
  ],
  invalid: [
    {
      code: `const bad = { kind: "pending", amount: 100 };`,
      errors: [{ messageId: "noAnnotation" }],
    },
    {
      code: `const state = { status: "loading", data: null };`,
      errors: [{ messageId: "noAnnotation" }],
    },
    {
      code: `const action = { type: "INCREMENT", payload: 1 };`,
      errors: [{ messageId: "noAnnotation" }],
    },
  ],
});
