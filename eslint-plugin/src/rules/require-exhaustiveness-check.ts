import { createRule } from "../utils/rule-creator";

export default createRule({
  name: "require-exhaustiveness-check",
  meta: {
    type: "suggestion",
    docs: {
      description:
        "Require a default case with exhaustiveness check when switching on a discriminant property",
    },
    messages: {
      missingExhaustiveness:
        "Switch on discriminant property '{{discriminant}}' missing default case with exhaustiveness check (e.g., assertNever). Add `default: assertNever({{discriminant}})` [T01]",
    },
    schema: [],
    fixable: undefined,
  },
  defaultOptions: [],
  create(context) {
    return {
      SwitchStatement(node) {
        const discriminant = node.discriminant;

        if (discriminant.type !== "MemberExpression") {
          return;
        }

        const hasDefaultCase = node.cases.some((caseClause) => caseClause.test === null);

        if (!hasDefaultCase) {
          const object =
            discriminant.object.type === "Identifier"
              ? discriminant.object.name
              : "expr";
          const property =
            discriminant.property.type === "Identifier"
              ? discriminant.property.name
              : "prop";
          const discriminantName = `${object}.${property}`;

          context.report({
            node,
            messageId: "missingExhaustiveness",
            data: { discriminant: discriminantName },
          });
        }
      },
    };
  },
});
