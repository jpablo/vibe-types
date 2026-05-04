import { ruleTester } from "../helpers/rule-tester";
import rule from "../../src/rules/no-parallel-boolean-flags";

ruleTester.run("no-parallel-boolean-flags", rule, {
  valid: [
    {
      code: `
interface Fine {
  isPending: boolean;
  isComplete: boolean;
}
      `,
    },
    {
      code: `
type Payment =
  | { kind: "pending" }
  | { kind: "completed"; transactionId: string }
  | { kind: "failed"; reason: string };
      `,
    },
  ],
  invalid: [
    {
      code: `
interface Payment {
  isPending: boolean;
  isCompleted: boolean;
  isFailed: boolean;
  transactionId?: string;
  reason?: string;
}
      `,
      errors: [
        {
          messageId: "useDiscriminatedUnion",
        },
      ],
    },
    {
      code: `
type Config = {
  isEnabled: boolean;
  isDebug: boolean;
  isVerbose: boolean;
}
      `,
      errors: [
        {
          messageId: "useDiscriminatedUnion",
        },
      ],
    },
  ],
});
