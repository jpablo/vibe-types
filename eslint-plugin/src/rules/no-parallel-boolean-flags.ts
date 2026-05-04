import { createRule } from "../utils/rule-creator";
import type { TSESTree } from "@typescript-eslint/utils";

export default createRule({
  name: "no-parallel-boolean-flags",
  description: "Disallow 3+ boolean isXxx fields in favor of discriminated unions",
  meta: {
    type: "suggestion",
    docs: {
      category: "Best Practices",
    },
    schema: [
      {
        type: "object",
        properties: {
          minFlags: {
            type: "number",
            minimum: 2,
          },
        },
        additionalProperties: false,
      },
    ],
    messages: {
      useDiscriminatedUnion:
        "Use a discriminated union instead of {{count}} parallel boolean flags",
    },
  },
  defaultOptions: [{ minFlags: 3 }],
  create(context, [{ minFlags }]) {
    function checkBody(body: TSESTree.TSInterfaceBody | TSESTree.TSTypeLiteral) {
      const members = body.type === "TSInterfaceBody" ? body.body : body.members;
      const booleanFlags = members.filter(
        (member): member is TSESTree.TSPropertySignature =>
          member.type === "TSPropertySignature" &&
          member.key.type === "Identifier" &&
          member.key.name.startsWith("is") &&
          /^[A-Z]/.test(member.key.name.slice(2)) &&
          member.typeAnnotation?.typeAnnotation.type === "TSBooleanKeyword",
      );

      if (booleanFlags.length >= minFlags) {
        const parent = body.parent;
        if (
          parent.type === "TSInterfaceDeclaration" ||
          parent.type === "TSTypeAliasDeclaration"
        ) {
          context.report({
            node: parent,
            messageId: "useDiscriminatedUnion",
            data: { count: booleanFlags.length },
          });
        }
      }
    }

    return {
      TSInterfaceBody: checkBody,
      TSTypeLiteral: checkBody,
    };
  },
});
