// eslint-plugin/tests/rules/no-duplicate-discriminant-values.test.ts
import { ruleTester } from "../helpers/rule-tester";
import rule from "../../src/rules/no-duplicate-discriminant-values";

ruleTester.run("no-duplicate-discriminant-values", rule, {
  valid: [
    `type Good =
      | { kind: "a"; x: number }
      | { kind: "b"; y: string };`,
    `type State =
      | { status: "loading" }
      | { status: "loaded"; data: any }
      | { status: "error"; message: string };`,
    `interface SingleMember {
      type: "only";
      value: number;
    }`,
    `type MixedUnion =
      | { kind: "a"; x: number }
      | { kind: "b"; y: string }
      | { kind: "c"; z: boolean };`,
  ],
  invalid: [
    {
      code: `type Bad =
      | { kind: "a"; x: number }
      | { kind: "a"; y: string };`,
      errors: [{ messageId: "duplicateDiscriminant" }],
    },
    {
      code: `type Duplicate =
      | { type: "x"; foo: number }
      | { type: "y"; bar: string }
      | { type: "x"; baz: boolean };`,
      errors: [{ messageId: "duplicateDiscriminant" }],
    },
    {
      code: `type ThreeSame =
      | { status: "pending"; a: number }
      | { status: "pending"; b: number }
      | { status: "pending"; c: number };`,
      errors: [{ messageId: "duplicateDiscriminant" }],
    },
    {
      code: `type MultipleDuplicates =
      | { kind: "a"; x: number }
      | { kind: "b"; y: string }
      | { kind: "a"; z: boolean }
      | { kind: "b"; w: number };`,
      errors: [{ messageId: "duplicateDiscriminant" }],
    },
  ],
});
