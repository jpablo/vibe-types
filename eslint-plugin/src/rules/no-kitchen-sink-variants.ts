// eslint-plugin/src/rules/no-kitchen-sink-variants.ts
import { createRule } from "../utils/rule-creator";

export default createRule({
  name: "no-kitchen-sink-variants",
  meta: {
    type: "suggestion",
    docs: {
      description:
        "Disallow union variants with excessive fields that should be nested or split into separate types",
    },
    messages: {
      tooManyFields:
        "Union variant has {{count}} fields. Consider extracting fields into a separate named type and referencing it. [T01]",
    },
    schema: [
      {
        type: "object",
        properties: {
          maxFields: {
            type: "number",
            minimum: 1,
          },
        },
        additionalProperties: false,
      },
    ],
    fixable: undefined,
  },
  defaultOptions: [{ maxFields: 5 }],
  create(context) {
    const { maxFields = 5 } = context.options[0] ?? {};

    return {
      TSUnionType(node) {
        for (const member of node.types) {
          if (member.type === "TSTypeLiteral") {
            const fieldCount = member.members.filter(
              (m) => m.type === "TSPropertySignature"
            ).length;

            if (fieldCount > maxFields) {
              context.report({
                node: member,
                messageId: "tooManyFields",
                data: {
                  count: String(fieldCount),
                },
              });
            }
          }
        }
      },
    };
  },
});
