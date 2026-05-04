You are an expert ESLint plugin developer. Your task is to implement a single ESLint rule for TypeScript and its test file, then register the rule in the plugin's index.

## Plugin Directory Structure

The ESLint plugin lives at `eslint-plugin/` relative to the vibe-types repository root. The absolute path is provided at the end of this prompt.

```
eslint-plugin/
├── src/
│   ├── index.ts            ← register the rule here (current content provided below)
│   ├── utils/
│   │   └── rule-creator.ts ← use createRule from here
│   └── rules/
│       └── <rule-name>.ts  ← CREATE THIS FILE
└── tests/
    └── helpers/
    │   └── rule-tester.ts  ← use ruleTester from here
    └── rules/
        └── <rule-name>.test.ts  ← CREATE THIS FILE
```

## Scaffold Files (exact content — do not modify these)

### eslint-plugin/src/utils/rule-creator.ts
```typescript
import { ESLintUtils } from "@typescript-eslint/utils";

export const createRule = ESLintUtils.RuleCreator(
  (name) =>
    `https://github.com/jpablo/vibe-types/blob/main/eslint-plugin/docs/rules/${name}.md`,
);
```

### eslint-plugin/tests/helpers/rule-tester.ts
```typescript
import { RuleTester } from "@typescript-eslint/rule-tester";
import { afterAll, describe, it } from "vitest";
import * as tsParser from "@typescript-eslint/parser";

RuleTester.afterAll = afterAll;
RuleTester.describe = describe;
RuleTester.it = it;

export const ruleTester = new RuleTester({
  languageOptions: {
    parser: tsParser,
    parserOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
    },
  },
});
```

## Rule Implementation Template

Here is the exact pattern to follow for a rule file. Study it carefully.

```typescript
// eslint-plugin/src/rules/example-rule-name.ts
import { createRule } from "../utils/rule-creator";

export default createRule({
  name: "example-rule-name",
  meta: {
    type: "suggestion",   // use "problem" if the pattern is always wrong, "suggestion" if advisory
    docs: {
      description: "One-line description of what this rule flags",
    },
    messages: {
      // Define all message IDs used in context.report() calls below.
      // Use template variables like {{name}} if you need to interpolate values.
      exampleMessageId: "Describe the problem. Suggest the fix. [T01]",
      exampleWithData: "Found {{count}} instances of {{what}}. Consider using a discriminated union instead. [T01]",
    },
    schema: [
      // Define options if the rule is configurable. Empty array [] if no options.
      {
        type: "object",
        properties: {
          minCount: {
            type: "number",
            minimum: 2,
          },
        },
        additionalProperties: false,
      },
    ],
    fixable: undefined,   // set to "code" only if you provide a fixer function
  },
  defaultOptions: [{ minCount: 3 }],   // must match the schema above; use [] if no options
  create(context) {
    // Access options: const [{ minCount }] = context.options;
    // (context.options is typed based on defaultOptions)

    return {
      // Each key is an ESLint AST selector string.
      // The value is a visitor function called when a matching node is found.

      TSInterfaceBody(node) {
        // Example: count boolean isXxx fields
        const boolFlags = node.body.filter(
          (member) =>
            member.type === "TSPropertySignature" &&
            member.key.type === "Identifier" &&
            /^is[A-Z]/.test(member.key.name) &&
            member.typeAnnotation?.typeAnnotation.type === "TSBooleanKeyword",
        );
        if (boolFlags.length >= 3) {
          context.report({
            node,   // the node to underline in the editor
            messageId: "exampleWithData",
            data: {
              count: String(boolFlags.length),
              what: boolFlags
                .map((m) => (m.key.type === "Identifier" ? m.key.name : "?"))
                .join(", "),
            },
          });
        }
      },

      // Compound selector example — fires on TSAnyKeyword inside a default: branch
      "SwitchCase[test=null] TSAsExpression > TSAnyKeyword"(node) {
        context.report({ node, messageId: "exampleMessageId" });
      },
    };
  },
});
```

## Test File Template

```typescript
// eslint-plugin/tests/rules/example-rule-name.test.ts
import { ruleTester } from "../helpers/rule-tester";
import rule from "../../src/rules/example-rule-name";

ruleTester.run("example-rule-name", rule, {
  valid: [
    // Code that should NOT trigger the rule.
    // Include at least 2 valid cases.
    `interface Fine {
      isPending: boolean;
      isComplete: boolean;
    }`,
    `type State =
      | { kind: "pending" }
      | { kind: "complete" };`,
  ],
  invalid: [
    // Code that SHOULD trigger the rule.
    // Include at least 2 invalid cases.
    // Each entry must list every error the rule reports on that code snippet.
    {
      code: `interface Payment {
        isPending: boolean;
        isCompleted: boolean;
        isFailed: boolean;
      }`,
      errors: [{ messageId: "exampleWithData" }],
    },
    {
      code: `type Config = {
        isEnabled: boolean;
        isDebug: boolean;
        isVerbose: boolean;
      }`,
      errors: [{ messageId: "exampleWithData" }],
    },
  ],
});
```

## How to Register the Rule in src/index.ts

The current `src/index.ts` is provided at the end of this prompt. It contains sentinel comments that mark where to insert new content:

```
// rule-imports-start        ← add import line AFTER this comment
// rule-imports-end          ← stop before this comment

// rule-entries-start        ← add "rule-name": ruleName entry AFTER this comment
// rule-entries-end          ← stop before this comment

// recommended-rules-start   ← add "vibe-types/rule-name": "warn" AFTER this comment
// recommended-rules-end     ← stop before this comment

// strict-rules-start        ← add "vibe-types/rule-name": "warn" AFTER this comment
// strict-rules-end          ← stop before this comment
```

Add the import at the top (after `rule-imports-start`), add the rule entry in the `rules` object, and add the rule to both `recommended` and `strict` configs. Use `"warn"` for advisory rules and `"error"` for rules that always indicate a bug.

## Naming Conventions

- Rule file: `src/rules/<rule-name>.ts` where `<rule-name>` is the kebab-case `rule_name` from the spec
- Test file: `tests/rules/<rule-name>.test.ts`
- Import alias in index.ts: camelCase of the rule name (e.g., `noParallelBooleanFlags`)

Example for rule `no-parallel-boolean-flags`:
```typescript
// in index.ts, after rule-imports-start:
import noParallelBooleanFlags from "./rules/no-parallel-boolean-flags";

// in the rules object, after rule-entries-start:
"no-parallel-boolean-flags": noParallelBooleanFlags,
```

## Instructions

1. Read the RULE SPEC below to understand what antipattern to detect.
2. Use `antipattern_snippet` as the basis for your `invalid` test cases.
3. Use `correct_snippet` as the basis for your `valid` test cases.
4. Use `ast_nodes_to_visit` to know which node types to register visitors for.
5. Use `detection_algorithm` as the precise specification for your rule logic.
6. Create the rule file at `<plugin-dir>/src/rules/<rule-name>.ts`.
7. Create the test file at `<plugin-dir>/tests/rules/<rule-name>.test.ts`.
8. Edit `<plugin-dir>/src/index.ts` by inserting after the sentinel comments (keep the sentinel comments in place).

For `type-aware` rules: use `parserServices.program` and `getTypeAtLocation` from TypeScript's compiler API. Add `requiresTypeChecking: true` to the `meta.docs` object.

Do not modify any file outside `eslint-plugin/`. Do not modify the scaffold files (`rule-creator.ts`, `rule-tester.ts`).

