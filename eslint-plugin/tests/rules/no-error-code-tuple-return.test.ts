import { ruleTester } from "../helpers/rule-tester";
import rule from "../../src/rules/no-error-code-tuple-return";

ruleTester.run("no-error-code-tuple-return", rule, {
  valid: [
    `function divide(a: number, b: number): Result<number, string> {
  if (b === 0) return { ok: false, error: "division by zero" };
  return { ok: true, value: a / b };
}`,
    `function add(a: number, b: number): number {
  return a + b;
}`,
    `function getData(): { value: number; error: string | null } {
  return { value: 1, error: null };
}`,
    `function process(): [number, string] {
  return [1, "success"];
}`,
  ],
  invalid: [
    {
      code: `function divide(a: number, b: number): [number, number | null] {
  if (b === 0) return [0, 1];
  return [a / b, null];
}`,
      errors: [{ messageId: "useResultADT" }],
    },
    {
      code: `const calculate = (a: number, b: number): [number, number] => {
  if (b === 0) return [0, 1];
  return [a / b, 0];
};`,
      errors: [{ messageId: "useResultADT" }],
    },
  ],
});
