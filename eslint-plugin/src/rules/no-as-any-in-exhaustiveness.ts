import { createRule } from "../utils/rule-creator";

export default createRule({
  name: "no-as-any-in-exhaustiveness",
  meta: {
    type: "problem",
    docs: {
      description: "disallow using 'as any' in switch default branch to bypass exhaustiveness checking",
    },
    messages: {
      noAsAnyInDefault:
        "Do not use 'as any' in switch default branch. Use assertNever() for exhaustiveness checking instead. [T01]",
    },
    schema: [],
    fixable: undefined,
  },
  defaultOptions: [],
  create(context) {
    return {
      SwitchStatement(node) {
        const defaultCase = node.cases.find((case_) => case_.test === null);
        if (!defaultCase) return;

        for (const statement of defaultCase.consequent) {
          const anyCasts = findAnyCasts(statement);
          for (const anyCast of anyCasts) {
            context.report({
              node: anyCast,
              messageId: "noAsAnyInDefault",
            });
          }
        }
      },
    };
  },
});

function findAnyCasts(node: any): any[] {
  const results: any[] = [];

  function traverse(current: any) {
    if (!current || typeof current !== "object") return;

    if (
      current.type === "TSAsExpression" &&
      current.typeAnnotation?.type === "TSAnyKeyword"
    ) {
      results.push(current);
    }

    for (const key in current) {
      if (key === "parent" || key === "loc" || key === "range") continue;

      const value = current[key];

      if (Array.isArray(value)) {
        for (const item of value) {
          traverse(item);
        }
      } else if (typeof value === "object" && value !== null) {
        traverse(value);
      }
    }
  }

  traverse(node);
  return results;
}
