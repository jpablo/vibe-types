import { createRule } from "../utils/rule-creator";

export default createRule({
  name: "no-silent-fallback-in-default-case",
  meta: {
    type: "problem",
    docs: {
      description: "Disallow switch default cases that silently ignore unhandled cases",
    },
    messages: {
      silentDefaultCase: "Default case should throw or call assertNever() instead of silently ignoring. [T01]",
    },
    schema: [],
    fixable: undefined,
  },
  defaultOptions: [],
  create(context) {
    return {
      SwitchStatement(node) {
        const defaultCase = node.cases.find(
          (caseNode) => caseNode.test === null
        );

        if (!defaultCase) {
          return;
        }

        const hasThrow = defaultCase.consequent.some(
          (statement) =>
            statement.type === "ThrowStatement" ||
            (statement.type === "ExpressionStatement" &&
              statement.expression.type === "CallExpression" &&
              statement.expression.callee.type === "Identifier" &&
              statement.expression.callee.name === "assertNever") ||
            (statement.type === "ExpressionStatement" &&
              statement.expression.type === "CallExpression" &&
              statement.expression.callee.type === "MemberExpression" &&
              "property" in statement.expression.callee &&
              statement.expression.callee.property.type === "Identifier" &&
              statement.expression.callee.property.name === "assertNever")
        );

        if (!hasThrow) {
          context.report({
            node: defaultCase,
            messageId: "silentDefaultCase",
          });
        }
      },
    };
  },
});
