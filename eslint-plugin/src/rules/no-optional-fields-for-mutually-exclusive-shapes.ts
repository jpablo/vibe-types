import { createRule } from "../utils/rule-creator";
import type { TSESTree } from "@typescript-eslint/utils";

export default createRule({
  name: "no-optional-fields-for-mutually-exclusive-shapes",
  meta: {
    type: "suggestion",
    docs: {
      description:
        "Disallow optional fields that should be mutually exclusive variants in a discriminated union",
    },
    messages: {
      useDiscriminatedUnion:
        "Use a discriminated union instead of {{count}} optional fields that are mutually exclusive: {{fields}}. [T01]",
    },
    schema: [],
    fixable: undefined,
  },
  defaultOptions: [],
  create(context) {
    function checkBody(
      node: TSESTree.TSInterfaceBody | TSESTree.TSTypeLiteral,
    ) {
      const members = Array.isArray(node.body)
        ? node.body
        : (node.members ?? []);

      const optionalFields = members.filter(
        (member): member is TSESTree.TSPropertySignature =>
          member.type === "TSPropertySignature" &&
          member.optional === true,
      );

      if (optionalFields.length < 2) {
        return;
      }

      const hasStatusTypeField = members.some(
        (member) =>
          member.type === "TSPropertySignature" &&
          member.key.type === "Identifier" &&
          (member.key.name === "status" || member.key.name === "type"),
      );

      const fieldNames = optionalFields.map((m) =>
        m.key.type === "Identifier" ? m.key.name : "?",
      );

      const hasDataAndError =
        fieldNames.includes("data") && fieldNames.includes("error");

      if (hasStatusTypeField || hasDataAndError) {
        context.report({
          node,
          messageId: "useDiscriminatedUnion",
          data: {
            count: String(optionalFields.length),
            fields: fieldNames.join(", "),
          },
        });
      }
    }

    return {
      TSInterfaceBody: checkBody,
      TSTypeLiteral: checkBody,
    };
  },
});
