import { ruleTester } from "../helpers/rule-tester";
import rule from "../../src/rules/no-optional-fields-for-mutually-exclusive-shapes";

ruleTester.run("no-optional-fields-for-mutually-exclusive-shapes", rule, {
  valid: [
    `interface ApiResponse {
      status: string;
      data: unknown;
    }`,
    `interface Config {
      data?: unknown;
    }`,
    `type ApiResponse =
      | { status: "success"; data: unknown }
      | { status: "error"; error: string }
      | { status: "csv"; rows: string[] };`,
    `interface Fine {
      name: string;
      age: number;
    }`,
  ],
  invalid: [
    {
      code: `interface ApiResponse {
        status: string;
        data?: unknown;
        error?: string;
        rows?: string[];
      }`,
      errors: [{ messageId: "useDiscriminatedUnion" }],
    },
    {
      code: `type ApiResponse = {
        type: string;
        data?: unknown;
        error?: string;
      }`,
      errors: [{ messageId: "useDiscriminatedUnion" }],
    },
    {
      code: `interface Payload {
        status: string;
        content?: string;
        metadata?: Record<string, unknown>;
      }`,
      errors: [{ messageId: "useDiscriminatedUnion" }],
    },
  ],
});
